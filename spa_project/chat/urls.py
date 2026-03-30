"""
URL configuration for chat app.

Chat trực tuyến cho Admin Panel.
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Admin Live Chat
    path('manage/live-chat/', views.admin_live_chat, name='admin_live_chat'),
]
