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
from dateutil import parser  # 추가
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Building, Machine, Reservation, WaitList
from .task import send_reservation_reminder, start_reservation_task, end_reservation_task
from .forms import SignUpForm
import os
import json
import datetime

User = get_user_model()

# ── 회원가입 및 인증 ──

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.is_active = False
            user.save()

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
        return redirect('laundry:index')
    else:
        return render(request, 'laundry/activation_invalid.html')

# ── 페이지 뷰 ──

def index_page(request):
    return render(request, 'index.html')

@login_required
def machine_list_page(request):
    machines = Machine.objects.all()
    type_ = request.GET.get('type')
    building = request.GET.get('building')
    if type_:
        machines = machines.filter(machine_type=type_)
    if building:
        machines = machines.filter(building=building)
    return render(request, 'laundry/machine_list.html', {'machines': machines})

@login_required
def washer_list(request):
    machines = Machine.objects.filter(machine_type='washer')
    return render(request, 'laundry/machine_list.html', {'machines': machines})

@login_required
def dryer_list(request):
    machines = Machine.objects.filter(machine_type='dryer')
    return render(request, 'laundry/machine_list.html', {'machines': machines})

@login_required
def mypage(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-start_time')
    waitlist = WaitList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'laundry/mypage.html', {
        'reservations': reservations,
        'waitlist': waitlist
    })

@login_required
def select_building_page(request):
    type_ = request.GET.get('type', 'washer')
    building_ids = Machine.objects.values_list('building_id', flat=True).distinct()
    building_qs = Building.objects.filter(id__in=building_ids).order_by('name')
    return render(request, 'laundry/select_building.html', {
        'buildings': building_qs,
        'type': type_,
    })

@login_required
def select_machine(request):
    type_ = request.GET.get("type")
    building_id = request.GET.get("building")

    try:
        building_id = int(building_id)
    except ValueError:
        return redirect('laundry:index_page')

    building_obj = get_object_or_404(Building, id=building_id)

    machines = Machine.objects.filter(
        machine_type=type_,
        building__id=building_id
    ).order_by('name')

    return render(request, 'laundry/select_machine.html', {
        'machines': machines,
        'building_name': building_obj.name.upper(),
        'type': type_,
    })

@login_required
def building_list_with_counts(request):
    buildings = Machine.objects.values_list('building_id', flat=True).distinct()
    data = []
    for b in buildings:
        count = Machine.objects.filter(building_id=b, is_in_use=True).count()
        data.append({'building': b, 'count': count})
    return JsonResponse(data, safe=False)

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

import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reservation(request):
    try:
        user = request.user

        # ✅ request.data만 사용
        machine_id = request.data.get('machine_id')
        start_str = request.data.get('start_time')
        end_str = request.data.get('end_time')

        print("DEBUG:", machine_id, start_str, end_str)

        if not (machine_id and start_str and end_str):
            return Response({'success': False, 'message': '필수 데이터 누락'}, status=400)

        start = parser.isoparse(start_str)
        end = parser.isoparse(end_str)

        kst = timezone.get_current_timezone()
        start = start.astimezone(kst)
        end = end.astimezone(kst)
        now = timezone.localtime()  # 이미 KST


        print("📌 서버 기준 현재 시각 (now):", now.isoformat())
        print("📌 예약 요청 시작 시각 (start):", start.isoformat())

        if start < now:
            return Response({'success': False, 'message': '예약 시작 시간이 현재보다 이전입니다.'}, status=400)

        machine = get_object_or_404(Machine, pk=machine_id)

        if Reservation.objects.filter(machine=machine, end_time__gt=timezone.now()).exists():
            return Response({'success': False, 'message': '이미 사용 중인 기기입니다.'}, status=400)

        new_res = Reservation.objects.create(
            user=user,
            machine=machine,
            start_time=start,
            end_time=end
        )

        machine.is_in_use = True
        machine.save()

        start_reservation_task.apply_async(args=[new_res.id], eta=start)
        end_reservation_task.apply_async(args=[new_res.id], eta=end)

        for label, offset in [('10분 전', timedelta(minutes=10)), ('시작 시각', timedelta())]:
            eta = start - offset
            if timezone.is_naive(eta):
                eta = timezone.make_aware(eta, timezone.get_current_timezone())
            send_reservation_reminder.apply_async(args=[new_res.id, label], eta=eta)

        return Response({'success': True, 'message': '예약이 생성되었습니다.'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'success': False, 'message': f'서버 오류: {str(e)}'}, status=500)


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