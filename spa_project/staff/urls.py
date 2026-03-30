"""
URL configuration for staff app.

Quản lý nhân viên từ Admin Panel.
"""

from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Admin Staff Management
    path('manage/staff/', views.admin_staff, name='admin_staff'),
]
