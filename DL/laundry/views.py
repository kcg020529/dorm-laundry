from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import User, WashingMachine, WaitList, Reservation
from .serializers import (
    UserSerializer, WashingMachineSerializer, WaitListSerializer,
    ReservationSerializer, CreateReservationSerializer
)
from .tasks import send_reservation_reminder

@api_view(['POST'])
def login(request):  # ▲ 기존 로그인 수정: 비밀번호 포함
    student_id = request.data.get('student_id')
    password = request.data.get('password')
    try:
        user = User.objects.get(student_id=student_id)
        if not user.check_password(password):
            return Response({'error': '비밀번호가 틀렸습니다.'}, status=403)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response({'error': '사용자가 존재하지 않습니다.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_waitlist(request):  # ▲ 찜 등록 뷰 추가
    student_id = request.data.get('student_id')
    machine_id = request.data.get('machine_id')
    try:
        user = User.objects.get(student_id=student_id)
        machine = WashingMachine.objects.get(id=machine_id)
    except (User.DoesNotExist, WashingMachine.DoesNotExist):
        return Response({'error': '잘못된 사용자 또는 세탁기 ID'}, status=404)

    entry = WaitList.objects.create(user=user, machine=machine)
    return Response(WaitListSerializer(entry).data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_machine(request):  # ▲ 추천 세탁기 반환
    from django.db.models import Count
    machine = WashingMachine.objects.annotate(r_count=Count('waitlist')).order_by('r_count').first()
    return Response(WashingMachineSerializer(machine).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_machines(request):  # ▲ 건물 필터 포함 목록
    building_name = request.query_params.get('building')
    if building_name:
        machines = WashingMachine.objects.filter(building__name=building_name)
    else:
        machines = WashingMachine.objects.all()
    return Response(WashingMachineSerializer(machines, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reservation(request):  # ▲ 예약 생성 및 중복 방지, 알림 등록 포함
    student_id = request.data.get('student_id')
    try:
        user = User.objects.get(student_id=student_id)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, status=404)

    serializer = CreateReservationSerializer(data=request.data)
    if serializer.is_valid():
        machine = serializer.validated_data['machine']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']

        overlapping = Reservation.objects.filter(
            machine=machine,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if overlapping.exists():
            return Response({'error': '해당 시간대에 이미 예약이 있습니다.'}, status=409)

        reservation = serializer.save(user=user)
        machine.is_in_use = True
        machine.save()

        reminder_time = reservation.start_time - timedelta(minutes=10)
        send_reservation_reminder.apply_async((reservation.id,), eta=reminder_time)

        return Response(ReservationSerializer(reservation).data, status=201)

    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reservations(request):
    student_id = request.query_params.get('student_id')
    reservations = Reservation.objects.filter(user__student_id=student_id)
    return Response(ReservationSerializer(reservations, many=True).data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, pk):
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response({'error': '예약을 찾을 수 없습니다.'}, status=404)

    machine = reservation.machine
    reservation.delete()
    machine.is_in_use = False
    machine.save()
    return Response({'message': '예약이 취소되었습니다.'})