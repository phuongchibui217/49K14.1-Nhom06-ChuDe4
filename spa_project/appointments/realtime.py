from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from django.utils import timezone

from .models import Appointment


BOOKING_PENDING_COUNT_GROUP = "booking.pending.count"


def get_pending_booking_count():
    return Appointment.objects.filter(
        Q(source='ONLINE') | Q(source__isnull=True),
        status='PENDING',
    ).count()


def get_pending_booking_count_payload():
    return {
        'count': get_pending_booking_count(),
        'timestamp': timezone.now().isoformat(),
    }


def notify_pending_booking_count_changed():
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        BOOKING_PENDING_COUNT_GROUP,
        {
            'type': 'booking_pending_count',
            'payload': get_pending_booking_count_payload(),
        },
    )
