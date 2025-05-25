from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('laundry/', include('laundry.urls')),
    path('', RedirectView.as_view(url='/laundry/login/')),  # 로그인 페이지로 리다이렉트
]