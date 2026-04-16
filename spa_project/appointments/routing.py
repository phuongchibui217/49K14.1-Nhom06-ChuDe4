from django.urls import path

from .consumers import BookingPendingCountConsumer


websocket_urlpatterns = [
    path("ws/admin/booking/pending-count/", BookingPendingCountConsumer.as_asgi()),
]
