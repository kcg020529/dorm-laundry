from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('reservations/', views.create_reservation),
    path('reservations/list/', views.user_reservations),
    path('reservations/<int:pk>/', views.cancel_reservation),
    path('admin/machines/<int:pk>/status/', views.change_machine_status),
]