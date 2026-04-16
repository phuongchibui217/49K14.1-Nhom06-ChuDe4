from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Appointment
from .realtime import notify_pending_booking_count_changed


def _schedule_pending_count_broadcast():
    transaction.on_commit(notify_pending_booking_count_changed)


@receiver(post_save, sender=Appointment)
def appointment_saved(sender, instance, **kwargs):
    _schedule_pending_count_broadcast()


@receiver(post_delete, sender=Appointment)
def appointment_deleted(sender, instance, **kwargs):
    _schedule_pending_count_broadcast()
