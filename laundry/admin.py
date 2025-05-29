from django.contrib import admin
from .models import User, Machine, Reservation, WaitList, Building, PushSubscription

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'is_staff', 'is_active')
    search_fields = ('student_id',)
    list_filter = ('is_staff', 'is_active')


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'machine_type', 'is_in_use')
    list_filter = ('building', 'machine_type', 'is_in_use')
    search_fields = ('name',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'machine', 'start_time', 'end_time')
    list_filter = ('machine', 'start_time')
    search_fields = ('user__student_id', 'machine__name')


@admin.register(WaitList)
class WaitListAdmin(admin.ModelAdmin):
    list_display = ('user', 'machine', 'created_at')
    list_filter = ('machine',)
    search_fields = ('user__student_id',)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    search_fields = ('user__student_id', 'endpoint')
