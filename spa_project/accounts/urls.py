"""
URL configuration cho accounts app

Chứa URL patterns cho authentication và customer profile:
- Đăng nhập, đăng ký, đăng xuất
- Quên mật khẩu / đặt lại mật khẩu
- Trang tài khoản khách hàng

Author: Spa ANA Team
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ============================================================
    # Authentication
    # ============================================================
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ============================================================
    # Password Reset
    # ============================================================
    path('quen-mat-khau/', views.password_reset_request, name='password_reset'),
    path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    # ============================================================
    # Customer Profile
    # ============================================================
    path('tai-khoan/', views.customer_profile, name='customer_profile'),
]
