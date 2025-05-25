from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic import RedirectView

from . import views

app_name = 'laundry'

urlpatterns = [
    # ── UI 화면
    path('', views.index_page, name='index_page'),
    path('machines/', views.machine_list_page, name='machine_list_page'),
    path('mypage/', views.mypage, name='mypage'),
    path('buildings/', views.building_list_with_counts, name='building_counts'),
    path('machines/washers/', views.washer_list, name='washer_list'),
    path('machines/dryers/', views.dryer_list, name='dryer_list'),

    # ── 인증
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='laundry/login.html'), name='login'),
    path('login/api/', obtain_auth_token, name='api_login'),

    # ── 예약 & 대기열 (페이지)
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('reservations/cancel/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('waitlist/join/', views.join_waitlist, name='join_waitlist'),
    path('waitlist/<int:machine_id>/', views.list_waitlist, name='list_waitlist'),

    # ── API 엔드포인트
    path('api/machines/', views.get_machine_list_api, name='get_machine_list_api'),
    path('api/remaining-time/', views.get_remaining_time_api, name='get_remaining_time_api'),
]