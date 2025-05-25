from rest_framework import serializers
from django.db.models import Count, Q
from .models import Building, Machine, Reservation, WaitList, PushSubscription

class BuildingCountSerializer(serializers.ModelSerializer):
    washer_count = serializers.IntegerField(read_only=True)
    dryer_count  = serializers.IntegerField(read_only=True)

    class Meta:
        model = Building
        fields = ['id', 'name', 'washer_count', 'dryer_count']


class MachineSerializer(serializers.ModelSerializer):
    wait_count    = serializers.SerializerMethodField()
    building_name = serializers.CharField(source='building.name', read_only=True)

    class Meta:
        model  = Machine
        fields = [
            'id',
            'building',
            'building_name',
            'name',
            'machine_type',
            'is_in_use',
            'description',
            'wait_count',
        ]

    def get_wait_count(self, obj):
        # WaitList 모델의 related_name='waitlist_set' 으로 접근
        return obj.waitlist_set.count()


class WaitListSerializer(serializers.ModelSerializer):
    user_id       = serializers.CharField(source='user.student_id', read_only=True)
    machine_name  = serializers.CharField(source='machine.name', read_only=True)
    created_at    = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model  = WaitList
        fields = ['id', 'user', 'user_id', 'machine', 'machine_name', 'created_at']


class ReservationSerializer(serializers.ModelSerializer):
    user_id       = serializers.CharField(source='user.student_id', read_only=True)
    machine_name  = serializers.CharField(source='machine.name', read_only=True)
    building_name = serializers.CharField(source='machine.building.name', read_only=True)
    start_time    = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    end_time      = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model  = Reservation
        fields = [
            'id',
            'user',
            'user_id',
            'machine',
            'machine_name',
            'building_name',
            'start_time',
            'end_time',
        ]

class WashingMachineSerializer(MachineSerializer):
    """
    washer 타입(machine_type='washer') 전용 직렬화기
    """
    class Meta(MachineSerializer.Meta):
        fields = MachineSerializer.Meta.fields

class DryerSerializer(MachineSerializer):
    """
    dryer 타입(machine_type='dryer') 전용 직렬화기
    """
    class Meta(MachineSerializer.Meta):
        fields = MachineSerializer.Meta.fields