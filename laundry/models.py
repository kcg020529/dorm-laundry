# laundry/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, student_id, password=None, **extra_fields):
        if not student_id:
            raise ValueError('학번은 필수입니다')
        user = self.model(student_id=student_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, student_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(student_id, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    student_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'student_id'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.student_id

class Machine(models.Model):
    MACHINE_TYPES = [
        ('washer', '세탁기'),
        ('dryer', '건조기'),
    ]
    name = models.CharField(max_length=50)
    building = models.CharField(max_length=10)
    machine_type = models.CharField(max_length=10, choices=MACHINE_TYPES)
    is_in_use = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.building}동 {self.name}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.student_id} - {self.machine} ({self.start_time} to {self.end_time})"
    
class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='end_after_start'
            ),
            models.UniqueConstraint(
                fields=['machine', 'start_time', 'end_time'],
                name='unique_machine_reservation'
            ),
        ]
        def clean(self):
            if self.end_time <= self.start_time:
                raise ValidationError("종료 시간은 시작 시간 이후여야 합니다.")

class WaitList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'machine')

    def __str__(self):
        return f"{self.user.student_id} waiting for {self.machine}"
    
class PushSubscription(models.Model):
    """
    웹푸시 알림을 위한 구독 정보 저장 모델
    endpoint: 푸시 서비스 URL
    p256dh_key, auth_key: 브라우저에서 생성된 암호화 키
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.TextField()
    p256dh_key = models.CharField(max_length=255, blank=True, default='')
    auth_key   = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSubscription for {self.user.student_id}"
    
class Building(models.Model):
    """
    기숙사 동 정보를 저장하는 모델
    """
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name