from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    student_id = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)
    is_admin = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.student_id

class Building(models.Model):
    name = models.CharField(max_length=1)  # A, B, C, D, E

    def __str__(self):
        return f"{self.name}동"

class WashingMachine(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_in_use = models.BooleanField(default=False)
    description = models.TextField(default='')  # 새 필드

    def __str__(self):
        return f"{self.building.name}동 - {self.name}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(WashingMachine, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.student_id} 예약 {self.machine.name} ({self.start_time} ~ {self.end_time})"

class WaitList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(WashingMachine, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
