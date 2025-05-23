from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    student_id = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)  # ▲ 비밀번호 저장 필드 추가
    is_admin = models.BooleanField(default=False)

    def set_password(self, raw_password):  # ▲ 비밀번호 해싱 메서드 추가
        self.password = make_password(raw_password)

    def check_password(self, raw_password):  # ▲ 비밀번호 확인 메서드 추가
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.student_id

class Building(models.Model):
    name = models.CharField(max_length=1)  # A~E 동 표시

    def __str__(self):
        return f"{self.name}동"

class WashingMachine(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)  # 세탁기 이름
    is_in_use = models.BooleanField(default=False)  # 사용중 여부

    def __str__(self):
        return f"{self.building.name}동 - {self.name}"

class WaitList(models.Model):  # ▲ 새로 추가된 찜 대기열 모델
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(WashingMachine, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)  # 찜 시간

    class Meta:
        ordering = ['timestamp']  # 오래된 찜 먼저 반환

    def __str__(self):
        return f"{self.machine.name} 대기 - {self.user.student_id}"