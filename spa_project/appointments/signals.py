from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Appointment


@receiver(post_save, sender=Appointment)
def appointment_saved(sender, instance, **kwargs):
    pass


@receiver(post_delete, sender=Appointment)
def appointment_deleted(sender, instance, **kwargs):
    pass
