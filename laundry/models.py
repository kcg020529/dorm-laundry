from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField  # Django 3.1+ 에선 models.JSONField

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
    name = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.name}동"

class Machine(models.Model):
    MACHINE_TYPES = [
        ('washer', '세탁기'),
        ('dryer', '건조기'),
    ]

    building     = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='machines')
    name         = models.CharField(max_length=10)
    machine_type = models.CharField(max_length=10, choices=MACHINE_TYPES)
    is_in_use    = models.BooleanField(default=False)
    description  = models.TextField(blank=True)

    class Meta:
        unique_together = ('building', 'name', 'machine_type')

    def __str__(self):
        return f"{self.building.name}동 {self.name} ({self.get_machine_type_display()})"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.student_id} 예약 {self.machine.name} ({self.start_time} ~ {self.end_time})"

class WaitList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_info = models.JSONField()  # 브라우저에서 받은 { endpoint, keys: { p256dh, auth } }
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSub: {self.user.student_id}"