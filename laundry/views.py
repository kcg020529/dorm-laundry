from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Machine, Reservation, WaitList, Building
from .task import (
    send_reservation_reminder,
    start_reservation_task,
    end_reservation_task
)
from .forms import SignUpForm

User = get_user_model()

# 회원가입 뷰
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.is_active = False  # 활성화 전까지 비활성화
            user.save()
            # 이메일 전송
            current_site = get_current_site(request)
            context = {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            }
            subject = 'HUFS 세탁 예약 서비스 이메일 인증'
            message = render_to_string('laundry/activation_email.html', context)
            user.email_user(subject, message)
            return render(request, 'laundry/signup_done.html')
    else:
        form = SignUpForm()
    return render(request, 'laundry/signup.html', {'form': form})

# 이메일 인증 뷰
def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('laundry:index_page')
    else:
        return render(request, 'laundry/activation_invalid.html')

# ── 페이지 뷰 ──

def index_page(request):
    return render(request, 'index.html')

def mypage(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-start_time')
    waitlist = WaitList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'laundry/mypage.html', {
        'reservations': reservations,
        'waitlist': waitlist
    })

def building_list_with_counts(request):
    buildings = Machine.objects.values_list('building', flat=True).distinct()
    data = []
    for b in buildings:
        count = Machine.objects.filter(building=b, is_in_use=True).count()
        data.append({'building': b, 'count': count})
    return JsonResponse(data, safe=False)

def select_machine_page(request):
    type_param = request.GET.get('type', 'washer')
    selected_building = request.GET.get('building', '')
    buildings = ['A', 'B', 'C', 'D', 'E']  # 필요에 따라 동 추가/삭제

    return render(request, 'laundry/select_machine.html', {
        'type': type_param,
        'selected_building': selected_building,
        'buildings': buildings,
    })

def select_building(request):
    buildings = Building.objects.all()
    return render(request, 'laundry/select_building.html', {
        'buildings': buildings
    })

def select_machine_type(request, building_id):
    building = get_object_or_404(Building, id=building_id)
    return render(request, 'laundry/select_type.html', {
        'building': building
    })

def machine_list_page(request):
    """
    3단계: GET 파라미터 ?building=<id>&type=<washer|dryer> 로
    해당 동·기계 타입의 머신 리스트를 렌더링합니다.
    """
    building_id  = request.GET.get('building')
    machine_type = request.GET.get('type')
    # 필수 파라미터가 없으면 1단계로 돌아가기
    if not building_id or machine_type not in ('washer','dryer'):
        return redirect('laundry:select_building')

    building = get_object_or_404(Building, id=building_id)
    machines = Machine.objects.filter(
        building=building,
        machine_type=machine_type
    )

    return render(request, 'laundry/machine_list.html', {
        'building':     building,
        'machines':     machines,
        'machine_type': machine_type,
    })

# ── API 뷰 ──

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_machine_list_api(request):
    machines = Machine.objects.all()
    machine_type = request.GET.get('type')
    building = request.GET.get('building')
    if machine_type:
        machines = machines.filter(machine_type=machine_type)
    if building:
        machines = machines.filter(building=building)
    data = [
        {
            'id': m.id,
            'name': m.name,
            'machine_type': m.machine_type,
            'building': m.building,
            'is_in_use': m.is_in_use
        }
        for m in machines
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_remaining_time_api(request):
    machine_id = request.GET.get('machine_id')
    try:
        machine = Machine.objects.get(pk=machine_id)
        now = timezone.now()
        active = Reservation.objects.filter(
            machine=machine,
            start_time__lte=now,
            end_time__gt=now
        ).first()
        minutes = (active.end_time - now).total_seconds() // 60 if active else None
        return Response({'minutes': int(minutes) if minutes is not None else None})
    except Machine.DoesNotExist:
        return Response({'minutes': None}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reservation(request):
    user = request.user
    machine_id = request.data.get('machine_id')
    start = request.data.get('start_time')
    end = request.data.get('end_time')
    if not (machine_id and start and end):
        return Response({'error': '모든 필드를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    machine = get_object_or_404(Machine, pk=machine_id)

    new_res = Reservation.objects.create(
        user=user,
        machine=machine,
        start_time=start,
        end_time=end
    )
    start_reservation_task.apply_async(args=[new_res.id], eta=start)
    end_reservation_task.apply_async(args=[new_res.id], eta=end)
    for label, offset in [('10분 전', timedelta(minutes=10)), ('시작 시각', timedelta())]:
        eta = start - offset
        if timezone.is_naive(eta):
            eta = timezone.make_aware(eta, timezone.get_current_timezone())
        send_reservation_reminder.apply_async(args=[new_res.id, label], eta=eta)

    return Response({'message': '예약이 생성되었습니다.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, pk=None):
    reservation = get_object_or_404(Reservation, pk=pk if pk else request.data.get('reservation_id'))
    machine = reservation.machine
    reservation.delete()
    machine.is_in_use = False
    machine.save()
    return Response({'message': '예약이 취소되었습니다.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_waitlist(request):
    user = request.user
    machine_id = request.data.get('machine_id')
    machine = get_object_or_404(Machine, pk=machine_id)
    WaitList.objects.get_or_create(user=user, machine=machine)
    return Response({'message': '대기열에 참여했습니다.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_waitlist(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    waiters = WaitList.objects.filter(machine=machine).order_by('created_at')
    data = [{'user': w.user.student_id, 'joined_at': w.created_at} for w in waiters]
    return Response(data)