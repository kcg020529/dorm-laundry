from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic import RedirectView

from .views import (
    index_page,
    signup,
    building_list_with_counts,
    machine_list,
    washer_list,
    dryer_list,
    create_reservation,
    cancel_reservation,
    join_waitlist,
    list_waitlist,
    machine_list_page,
    mypage,
    get_machine_list_api,
    get_remaining_time_api
)

app_name = 'laundry'

urlpatterns = [
    # /laundry/ 로 들어오면 index_page 로
    path('', index_page, name='index_page'),

    path('machines/', machine_list_page, name='machine_list_page'),
    path('mypage/', mypage, name='mypage'),

    # 회원가입 / 로그인
    path('signup/', signup, name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='laundry/login.html'),
        name='login'
    ),
    path('login/api/', obtain_auth_token, name='api_login'),

    # 동별 기계 개수 조회
    path('buildings/', building_list_with_counts, name='building_counts'),

    # 전체 기계 목록 조회 (machine_list 뷰를 여기서 사용합니다)
    path('machines/', machine_list, name='machine_list_api'),

    # 기계 목록 조회 (세탁기/건조기 필터 & 동 필터)
    path('machines/washers/', washer_list, name='washer_list'),
    path('machines/dryers/',   dryer_list,  name='dryer_list'),

    # 예약 생성 / 취소
    path('reservations/create/', create_reservation, name='create_reservation'),
    path('reservations/cancel/<int:pk>/', cancel_reservation, name='cancel_reservation'),

    # 대기열 참가 / 조회
    path('waitlist/join/', join_waitlist, name='join_waitlist'),
    path('waitlist/<int:machine_id>/', list_waitlist, name='list_waitlist'),

    path('api/machines/', get_machine_list_api, name='get_machine_list_api'),
    path('api/remaining-time/', get_remaining_time_api, name='get_remaining_time_api'),
]
