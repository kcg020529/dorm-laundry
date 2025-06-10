# Laundry models.py
from django.db import models
from django.contrib.auth.models import User


class WashingMachine(models.Model):
    name = models.Charfield(max_length = 50) # 세탁기 이름 (문자열 필드)

    def _str_(self):                          # str 메소드(인스턴스 보기 좋게 만들어줌)
        return self.name                      # 여기까지의 모델은 세탁기 하나를 의미함

class Reservation(models.Model):              # 하나의 예약 모델 저장
    user = models.ForeignKey(User, on_delete=models.CASCADE)    # 예약 사용자   (on_delete=models.CASCADE)-> 사용자나 세탁기가 삭재되면 예약도 삭제
    machine = models.ForeignKey(WashingMachine,on_delete=models.CASCADE)    # 어떤 세탁기를 예액했는지
    start_time = models.DateTimeField() #에약 시작 시간
    end_time = models.DateTimeField()   #에약 종료 시간
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.machine.name} 예약{ self.start_time} ~ {self.end_time}" #세탁기 1번 예약 (2025-04-16 13:00 ~ 14:00)
