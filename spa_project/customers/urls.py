"""
URL configuration for customers app.

Quản lý khách hàng từ Admin Panel.
"""

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Admin Customer Management
    path('manage/customers/', views.admin_customers, name='admin_customers'),
]
