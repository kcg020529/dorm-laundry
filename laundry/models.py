from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.base_user import BaseUserManager
import os
import re

class UserManager(BaseUserManager):
    def create_user(self, student_id, username, password=None, **extra_fields):
        if not student_id:
            raise ValueError('학번은 필수입니다.')
        if not username:
            raise ValueError('사용자 이름(username)은 필수입니다.')
        user = self.model(student_id=student_id, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, student_id, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(student_id, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    student_id = models.CharField(max_length=20, unique=True)
    username = models.CharField(max_length=30, unique=True, null=True, blank=False)  # ✅ 사용자 이름 필수
    email = models.EmailField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'student_id'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.student_id

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey('Machine', on_delete=models.CASCADE)
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
    machine = models.ForeignKey('Machine', on_delete=models.CASCADE)
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
    name = models.CharField(max_length=100, unique=True)

    @property
    def get_image_url(self):
        # building 이름에서 알파벳, 숫자만 추출 (예: A동 → A)
        name_safe = re.sub(r'[^\w]', '', self.name)
        static_filename = f'building_{name_safe}.jpg'

        # 반환만 하고 존재 여부는 브라우저에게 맡김 (404면 default 쓰도록)
        return f'/static/images/{static_filename}'

class Machine(models.Model):
    MACHINE_TYPES = (
        ('washer', '세탁기'),
        ('dryer', '건조기'),
    )
    name = models.CharField(max_length=100)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='machines')
    machine_type = models.CharField(max_length=10, choices=MACHINE_TYPES)
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)
    is_in_use = models.BooleanField(default=False)

    @property
    def get_image_url(self):
    # 미디어 이미지가 없는 경우에도 안전하게 fallback
        if self.machine_type == 'washer':
            return '/static/images/washer_icon.png'
        elif self.machine_type == 'dryer':
            return '/static/images/dryer_icon.png'
        return '/static/images/default_machine.png'
    
User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    student_id = models.CharField(max_length=20)
    department = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.user.username} 프로필'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)