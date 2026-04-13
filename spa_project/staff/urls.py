"""
URL configuration for staff app.

Quản lý nhân viên từ Admin Panel.
"""

from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Trang quản lý
    path('manage/staff/', views.admin_staff, name='admin_staff'),
]
