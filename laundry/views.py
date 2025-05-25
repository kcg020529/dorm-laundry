from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .task import send_reservation_reminder

from .models import User, WashingMachine, Reservation, WaitList
from .serializers import WaitListSerializer, ReservationSerializer

@api_view(['POST'])
def create_reservation(request):
    student_id = request.data.get('student_id')
    machine_id = request.data.get('machine_id')
    start_time = request.data.get('start_time')
    end_time = request.data.get('end_time')

    # 필수 입력 체크
    if not (student_id and machine_id and start_time and end_time):
        return Response({'error': '모든 필드를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 및 세탁기 존재 확인
    try:
        user = User.objects.get(student_id=student_id)
        machine = WashingMachine.objects.get(pk=machine_id)
    except (User.DoesNotExist, WashingMachine.DoesNotExist):
        return Response({'error': '유효하지 않은 사용자 또는 기기입니다.'}, status=status.HTTP_404_NOT_FOUND)

    # 예약 중복 체크
    overlapping = Reservation.objects.filter(
        machine=machine,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()
    if overlapping:
        return Response({'error': '이미 예약된 시간대입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    # 예약 생성
    reservation = Reservation.objects.create(
        user=user,
        machine=machine,
        start_time=start_time,
        end_time=end_time
    )
    machine.is_in_use = True
    machine.save()

    # 10분 전 푸시 스케줄링
    eta_10min = reservation.start_time - timedelta(minutes=10)
    if timezone.is_naive(eta_10min):
        eta_10min = timezone.make_aware(eta_10min, timezone.get_current_timezone())
    send_reservation_reminder.apply_async(
        args=[reservation.id, '10분 전'],
        eta=eta_10min
    )

    # 시작 시각 푸시 스케줄링
    eta_start = reservation.start_time
    if timezone.is_naive(eta_start):
        eta_start = timezone.make_aware(eta_start, timezone.get_current_timezone())
    send_reservation_reminder.apply_async(
        args=[reservation.id, '시작 시각'],
        eta=eta_start
    )

    return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def cancel_reservation(request, pk):
    # 예약 조회
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response({'error': '예약을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    machine = reservation.machine
    reservation.delete()
    machine.is_in_use = False
    machine.save()

    # 대기열 자동 승격
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

        # 승격된 예약 푸시 스케줄링
        eta_10m = start - timedelta(minutes=10)
        send_reservation_reminder.apply_async(
            args=[new_res.id, '10분 전'],
            eta=eta_10m
        )
        send_reservation_reminder.apply_async(
            args=[new_res.id, '시작 시각'],
            eta=start
        )

    return Response({'message': '예약이 취소되었습니다.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def join_waitlist(request):
    student_id = request.data.get('student_id')
    machine_id = request.data.get('machine_id')

    # 필수 입력 체크
    if not (student_id and machine_id):
        return Response({'error': '학번과 기기 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 및 세탁기 존재 확인
    try:
        user = User.objects.get(student_id=student_id)
        machine = WashingMachine.objects.get(pk=machine_id)
    except (User.DoesNotExist, WashingMachine.DoesNotExist):
        return Response({'error': '유효하지 않은 사용자 또는 기기입니다.'}, status=status.HTTP_404_NOT_FOUND)

    # 기기 사용 중일 때만 대기열 등록
    if not machine.is_in_use:
        return Response({'error': '기기가 사용 중일 때만 대기열 등록이 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    wait, created = WaitList.objects.get_or_create(user=user, machine=machine)
    serializer = WaitListSerializer(wait)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
def list_waitlist(request, machine_id):
    # 기기 존재 확인
    try:
        machine = WashingMachine.objects.get(pk=machine_id)
    except WashingMachine.DoesNotExist:
        return Response({'error': '존재하지 않는 기기입니다.'}, status=status.HTTP_404_NOT_FOUND)

    waitlist = WaitList.objects.filter(machine=machine).order_by('created_at')
    serializer = WaitListSerializer(waitlist, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)