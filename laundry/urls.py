from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token

from . import views

app_name = 'laundry'

urlpatterns = [
    # ── 메인 페이지
    path('', views.index_page, name='index_page'),

    # 1단계: 동 선택
    path('select/', views.select_building, name='select_building'),
    # 2단계: 선택한 동에서 기계 종류 선택
    path('select/<int:building_id>/', views.select_machine_type, name='select_machine_type'),
    # 3단계: 실제 기계 리스트 (GET 파라미터 building, type 사용)
    path('machines/', views.machine_list_page, name='machine_list_page'),

    # ── 마이페이지 및 통계
    path('mypage/', views.mypage, name='mypage'),
    path('buildings/', views.building_list_with_counts, name='building_counts'),

    # ── 인증
    path('login/', auth_views.LoginView.as_view(template_name='laundry/login.html'), name='login'),
    path('login/api/', obtain_auth_token, name='api_login'),

    # ── 예약 및 대기열
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('reservations/cancel/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('waitlist/join/', views.join_waitlist, name='join_waitlist'),
    path('waitlist/<int:machine_id>/', views.list_waitlist, name='list_waitlist'),

    # ── API 엔드포인트
    path('api/machines/', views.get_machine_list_api, name='get_machine_list_api'),
    path('api/remaining-time/', views.get_remaining_time_api, name='get_remaining_time_api'),

    # ── 회원가입 및 활성화
    path('signup/', views.signup_view, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
]