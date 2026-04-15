"""
URL configuration for chat app.

Chat realtime cho cả khách hàng và admin panel.
"""

from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("manage/live-chat/", views.admin_live_chat, name="admin_live_chat"),

    # Customer APIs
    path("api/chat/session/boot/", views.api_customer_chat_bootstrap, name="api_customer_chat_bootstrap"),
    path("api/chat/session/send/", views.api_customer_chat_send_new, name="api_customer_chat_send_new"),
    path("api/chat/session/<str:chat_code>/send/", views.api_customer_chat_send, name="api_customer_chat_send"),
    path("api/chat/session/<str:chat_code>/read/", views.api_customer_chat_mark_read, name="api_customer_chat_mark_read"),
    path("api/chat/session/<str:chat_code>/stream/", views.api_customer_chat_stream, name="api_customer_chat_stream"),

    # Admin APIs
    path("api/admin/chat/sessions/", views.api_admin_chat_sessions, name="api_admin_chat_sessions"),
    path("api/admin/chat/sessions/stream/", views.api_admin_chat_sessions_stream, name="api_admin_chat_sessions_stream"),
    path("api/admin/chat/sessions/<str:chat_code>/messages/", views.api_admin_chat_messages, name="api_admin_chat_messages"),
    path("api/admin/chat/sessions/<str:chat_code>/send/", views.api_admin_chat_send, name="api_admin_chat_send"),
    path("api/admin/chat/sessions/<str:chat_code>/read/", views.api_admin_chat_mark_read, name="api_admin_chat_mark_read"),
    path("api/admin/chat/sessions/<str:chat_code>/stream/", views.api_admin_chat_stream, name="api_admin_chat_stream"),
]
