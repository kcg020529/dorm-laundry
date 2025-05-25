from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token

from .models import Machine, Reservation, WaitList
from .task import (
    send_reservation_reminder,
    start_reservation_task,
    end_reservation_task
)

User = get_user_model()

# ── 페이지 뷰 ──

def index_page(request):
    return redirect('laundry:machine_list_page')

@login_required
def machine_list_page(request):
    machines = Machine.objects.all()
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
def building_list_with_counts(request):
    buildings = Machine.objects.values_list('building', flat=True).distinct()
    data = []
    for b in buildings:
        count = Machine.objects.filter(building=b, is_in_use=True).count()
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

# ── Signup 뷰 ──

@permission_classes([AllowAny])
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('laundry:machine_list_page')
    else:
        form = UserCreationForm()
    return render(request, 'laundry/signup.html', {'form': form})
