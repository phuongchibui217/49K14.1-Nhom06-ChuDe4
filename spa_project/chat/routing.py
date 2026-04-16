from django.urls import path

from .consumers import (
    AdminChatSessionConsumer,
    AdminChatSessionsConsumer,
    CustomerChatConsumer,
)


websocket_urlpatterns = [
    path("ws/chat/session/<str:chat_code>/", CustomerChatConsumer.as_asgi()),
    path("ws/admin/chat/sessions/", AdminChatSessionsConsumer.as_asgi()),
    path("ws/admin/chat/sessions/<str:chat_code>/", AdminChatSessionConsumer.as_asgi()),
]
