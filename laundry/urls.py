from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page),
    path('login/api/', views.login),
    path('machines/view/', views.machine_list_page, name='machine_list_page'),
    path('machines/view/', views.machine_list_page),
    path('machines/', views.list_machines),
    path('reservations/', views.create_reservation),
    path('reservations/list/', views.user_reservations),
    path('reservations/<int:pk>/', views.cancel_reservation),
    path('admin/machines/<int:pk>/status/', views.change_machine_status),
    path('index/', views.index_page, name='index_page'),
]