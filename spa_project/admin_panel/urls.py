"""
URL configuration for admin_panel app.

Admin authentication và profile pages.
"""

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Admin Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # Admin Profile
    path('profile/', views.admin_profile, name='admin_profile'),
]
