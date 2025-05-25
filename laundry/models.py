# laundry/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, student_id, password=None, **extra_fields):
        if not student_id:
            raise ValueError('The Student ID must be set')
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
    REQUIRED_FIELDS = []  # 기본 필수 필드 (email 등), 없으면 빈 리스트

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

class WaitList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'machine')

    def __str__(self):
        return f"{self.user.student_id} waiting for {self.machine}"