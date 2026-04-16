from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .realtime import (
    BOOKING_PENDING_COUNT_GROUP,
    get_pending_booking_count_payload,
)


def _is_staff(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


class BookingPendingCountConsumer(JsonWebsocketConsumer):
    group_name = BOOKING_PENDING_COUNT_GROUP

    def connect(self):
        if not _is_staff(self.scope.get("user")):
            self.close(code=4403)
            return

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send_pending_count()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def send_pending_count(self, payload=None):
        data = {'event': 'pending_count'}
        data.update(payload or get_pending_booking_count_payload())
        self.send_json(data)

    def booking_pending_count(self, event):
        self.send_pending_count(event.get('payload'))
