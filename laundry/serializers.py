from rest_framework import serializers
from .models import User, Building, WashingMachine, WaitList

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class WashingMachineSerializer(serializers.ModelSerializer):
    building = serializers.CharField(source='building.name')
    wait_count = serializers.SerializerMethodField()  # ▲ 대기 인원수 필드 추가

    class Meta:
        model = WashingMachine
        fields = '__all__'

    def get_wait_count(self, obj):
        return obj.waitlist_set.count()  # ▲ 해당 세탁기 대기열 인원 반환

class WaitListSerializer(serializers.ModelSerializer):  # ▲ 대기열 직렬화
    class Meta:
        model = WaitList
        fields = '__all__'

