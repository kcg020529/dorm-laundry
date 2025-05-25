from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .task import send_reservation_reminder

from .models import Machine, Reservation, User, Building, WaitList
from .serializers import (
    WaitListSerializer,
    ReservationSerializer,
    BuildingCountSerializer,
    MachineSerializer,
    WashingMachineSerializer,
    DryerSerializer
)
from django.contrib.auth.forms import UserCreationForm
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

# 회원가입 뷰 (Django 기본 폼 사용)
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'laundry/signup.html', {'form': form})

# 예약 생성 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reservation(request):
    student_id = request.data.get('student_id')
    machine_id = request.data.get('machine_id')
    start_time = request.data.get('start_time')
    end_time   = request.data.get('end_time')

    if not (student_id and machine_id and start_time and end_time):
        return Response(
            {'error': '모든 필드를 입력해주세요.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user    = User.objects.get(student_id=student_id)
        machine = Machine.objects.get(pk=machine_id)
    except (User.DoesNotExist, Machine.DoesNotExist):
        return Response(
            {'error': '유효하지 않은 사용자 또는 기기입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if Reservation.objects.filter(
        machine=machine,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists():
        return Response(
            {'error': '이미 예약된 시간대입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reservation = Reservation.objects.create(
        user=user,
        machine=machine,
        start_time=start_time,
        end_time=end_time
    )
    machine.is_in_use = True
    machine.save()

    # 푸시 알림 스케줄링
    for label, offset in [('10분 전', timedelta(minutes=10)), ('시작 시각', timedelta())]:
        eta = reservation.start_time - offset
        if timezone.is_naive(eta):
            eta = timezone.make_aware(eta, timezone.get_current_timezone())
        send_reservation_reminder.apply_async(
            args=[reservation.id, label],
            eta=eta
        )

    return Response(
        ReservationSerializer(reservation).data,
        status=status.HTTP_201_CREATED
    )

# 예약 취소 API
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, pk):
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {'error': '예약을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    machine = reservation.machine
    reservation.delete()
    machine.is_in_use = False
    machine.save()

    # 대기열에서 다음 사용자 자동 승격
    next_wait = WaitList.objects.filter(machine=machine).order_by('created_at').first()
    if next_wait:
        start = timezone.now()
        end = start + timedelta(hours=1)
        new_res = Reservation.objects.create(
            user=next_wait.user,
            machine=machine,
            start_time=start,
            end_time=end
        )
        machine.is_in_use = True
        machine.save()
        next_wait.delete()

        for label, offset in [('10분 전', timedelta(minutes=10)), ('시작 시각', timedelta())]:
            eta = start - offset
            if timezone.is_naive(eta):
                eta = timezone.make_aware(eta, timezone.get_current_timezone())
            send_reservation_reminder.apply_async(
                args=[new_res.id, label],
                eta=eta
            )

    return Response(
        {'message': '예약이 취소되었습니다.'},
        status=status.HTTP_200_OK
    )

# 대기열 참가 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_waitlist(request):
    student_id = request.data.get('student_id')
    machine_id = request.data.get('machine_id')

    if not (student_id and machine_id):
        return Response(
            {'error': '학번과 기기 ID가 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(student_id=student_id)
        machine = Machine.objects.get(pk=machine_id)
    except (User.DoesNotExist, Machine.DoesNotExist):
        return Response(
            {'error': '유효하지 않은 사용자 또는 기기입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not machine.is_in_use:
        return Response(
            {'error': '기기가 사용 중일 때만 대기열 등록이 가능합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    wait, created = WaitList.objects.get_or_create(user=user, machine=machine)
    serializer = WaitListSerializer(wait)
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


# 대기열 목록 조회 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_waitlist(request, machine_id):
    try:
        machine = Machine.objects.get(pk=machine_id)
    except Machine.DoesNotExist:
        return Response(
            {'error': '존재하지 않는 기기입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    waitlist = WaitList.objects.filter(machine=machine).order_by('created_at')
    serializer = WaitListSerializer(waitlist, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def washer_list(request):
    qs = Machine.objects.filter(machine_type='washer')
    serializer = WashingMachineSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dryer_list(request):
    qs = Machine.objects.filter(machine_type='dryer')
    serializer = DryerSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def building_list_with_counts(request):
    """
    A~E 동별 세탁기(washer)·건조기(dryer) 총 개수를 함께 반환합니다.
    """
    qs = Building.objects.annotate(
        washer_count=Count('machines', filter=Q(machines__machine_type='washer')),
        dryer_count=Count('machines', filter=Q(machines__machine_type='dryer'))
    ).order_by('name')
    serializer = BuildingCountSerializer(qs, many=True)
    return Response(serializer.data)

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def index_page(request):
    """
    로그인 후 첫 화면. 기계 선택 템플릿을 렌더링합니다.
    """
    return render(request, 'laundry/select_machine.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def machine_list(request):
    """
    ?type=washer|dryer, &building=<id> 파라미터로 필터링 가능한
    전체 기계 조회 API
    """
    m_type = request.GET.get('type')
    b_id   = request.GET.get('building')

    qs = Machine.objects.all()
    if m_type in ('washer', 'dryer'):
        qs = qs.filter(machine_type=m_type)
    if b_id:
        qs = qs.filter(building_id=b_id)

    serializer = MachineSerializer(qs, many=True)
    return Response(serializer.data)