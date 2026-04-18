"""
Serializers - Chuyển đổi Django Model thành Dictionary (rồi thành JSON)

Author: Spa ANA Team
"""

from .models import Appointment


def serialize_appointment(appointment):
    """Chuyển 1 đối tượng Appointment thành dictionary"""
    customer_name = (
        appointment.customer_name_snapshot
        or (appointment.customer.full_name if appointment.customer else '')
    )
    customer_phone = (
        appointment.customer_phone_snapshot
        or (appointment.customer.phone if appointment.customer else '')
    )
    customer_email = appointment.customer_email_snapshot or ''

    # Tính end_time display
    end_str = ''
    if appointment.end_time:
        end_str = appointment.end_time.strftime('%H:%M')
    elif appointment.appointment_time and appointment.duration_minutes:
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), appointment.appointment_time)
        end_str = (start_dt + timedelta(minutes=appointment.duration_minutes)).strftime('%H:%M')

    return {
        'id': appointment.appointment_code,
        'customerId': appointment.customer_id,
        'customerName': customer_name,
        'phone': customer_phone,
        'email': customer_email,
        'service': appointment.service.name if appointment.service else '',
        'serviceId': appointment.service.id if appointment.service else None,
        'variantId': appointment.service_variant.id if appointment.service_variant else None,
        'variantLabel': appointment.service_variant.label if appointment.service_variant else '',
        'roomCode': appointment.room.code if appointment.room else '',
        'roomName': appointment.room.name if appointment.room else '',
        'guests': appointment.guests or 1,
        'date': appointment.appointment_date.strftime('%Y-%m-%d') if appointment.appointment_date else '',
        'start': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else '',
        'end': end_str,
        'durationMin': appointment.duration_minutes or (
            appointment.service_variant.duration_minutes if appointment.service_variant else (
                appointment.service.variants.filter(is_active=True).order_by('sort_order').first().duration_minutes
                if appointment.service and appointment.service.variants.filter(is_active=True).exists() else 60
            )
        ),
        'note': appointment.notes or '',
        'apptStatus': appointment.status,
        'payStatus': appointment.payment_status,
        'source': appointment.source,
        'staffNotes': appointment.staff_notes or '',
    }


def serialize_appointments(appointments):
    return [serialize_appointment(appt) for appt in appointments]
