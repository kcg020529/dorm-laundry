from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, WashingMachine, Reservation
from .serializers import (
    UserSerializer, WashingMachineSerializer,
)
from django.utils import timezone
from datetime import timedelta

@api_view(['POST'])
def login(request):
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({'error': '학번이 필요합니다.'}, status=400)

    user, created = User.objects.get_or_create(student_id=student_id)
    return Response(UserSerializer(user).data)

@api_view(['GET'])
def list_machines(request):
    machines = WashingMachine.objects.all()
    return Response(WashingMachineSerializer(machines, many=True).data)

@api_view(['POST'])
def create_reservation(request):
    student_id = request.data.get('student_id')
    try:
        user = User.objects.get(student_id=student_id)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, status=404)

    serializer = CreateReservationSerializer(data=request.data)
    if serializer.is_valid():
        reservation = serializer.save(user=user)
        machine = reservation.machine
        machine.is_in_use = True
        machine.save()
        return Response(ReservationSerializer(reservation).data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def user_reservations(request):
    student_id = request.query_params.get('student_id')
    reservations = Reservation.objects.filter(user__student_id=student_id)
    return Response(ReservationSerializer(reservations, many=True).data)

@api_view(['DELETE'])
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

@api_view(['POST'])
def create_reservation(request):
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

        # 예약 시간 겹침 방지
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
        return Response(ReservationSerializer(reservation).data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def change_machine_status(request, pk):
    try:
        machine = WashingMachine.objects.get(pk=pk)
        machine.is_in_use = not machine.is_in_use
        machine.save()
        return Response({'message': '상태가 변경되었습니다.', 'is_in_use': machine.is_in_use}, status=status.HTTP_200_OK)
    except WashingMachine.DoesNotExist:
        return Response({'error': '세탁기를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def login(request):
    student_id = request.data.get('student_id')
    password = request.data.get('password')

    if not student_id or not password:
        return Response({'error': '학번과 비밀번호가 필요합니다.'}, status=400)

    try:
        user = User.objects.get(student_id=student_id)
        if not user.check_password(password):
            return Response({'error': '비밀번호가 일치하지 않습니다.'}, status=401)
    except User.DoesNotExist:
        return Response({'error': '존재하지 않는 사용자입니다.'}, status=404)

    return Response(UserSerializer(user).data)

def index_page(request):
    return render(request, 'index.html')

def machine_list_page(request):
    return render(request, 'available_machines.html')

def login_page(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            user, created = User.objects.get_or_create(student_id=student_id)
            request.session['user_id'] = user.id
            return redirect('/laundry/machines/view/')
    return render(request, 'login.html')

def machine_list_page(request):
    return render(request, 'laundry_page.html')
