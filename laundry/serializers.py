from rest_framework import serializers
from .models import User, Building, WashingMachine, Reservation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class WashingMachineSerializer(serializers.ModelSerializer):
    building = BuildingSerializer()
    class Meta:
        model = WashingMachine
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    machine = WashingMachineSerializer()
    
    class Meta:
        model = Reservation
        fields = '__all__'

class CreateReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['machine', 'start_time', 'end_time']
