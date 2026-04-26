"""
Serializers — chuyển Appointment model thành dict/JSON cho frontend.

Author: Spa ANA Team
"""

from .models import Appointment
from .services import _get_appt_duration, _calc_end_time


def serialize_appointment(appointment):
    """Chuyển 1 Appointment thành dict."""

    # Người đặt lịch
    booker_name  = appointment.booker_name  or ''
    booker_phone = appointment.booker_phone or ''
    booker_email = appointment.booker_email or ''

    # Khách sử dụng dịch vụ (snapshot)
    customer_name  = appointment.customer_name_snapshot  or ''
    customer_phone = appointment.customer_phone_snapshot or ''
    customer_email = appointment.customer_email_snapshot or ''

    # Thời lượng và end_time tính từ service_variant (không lưu trong DB)
    duration_min = _get_appt_duration(appointment)
    end_str = ''
    if appointment.appointment_time:
        end_time = _calc_end_time(appointment.appointment_time, duration_min)
        end_str = end_time.strftime('%H:%M')

    # Service info từ variant
    service_name = ''
    service_id = None
    service_code = ''
    variant_label = ''
    if appointment.service_variant_id:
        try:
            sv = appointment.service_variant
            if sv.service_id:
                service_name = sv.service.name
                service_id = sv.service_id
                service_code = sv.service.code or ''
            variant_label = sv.label or ''
        except Exception:
            pass

    return {
        'id': appointment.appointment_code,
        'customerId': appointment.customer_id,
        # Người đặt lịch
        'bookerName':  booker_name,
        'bookerPhone': booker_phone,
        'bookerEmail': booker_email,
        # Khách sử dụng dịch vụ (snapshot)
        'customerName': customer_name,
        'phone':        customer_phone,
        'email':        customer_email,
        # Dịch vụ / gói
        'service':      service_name,
        'serviceCode':  service_code,
        'serviceId':    service_id,
        'variantId':    appointment.service_variant_id,
        'variantLabel': variant_label,
        # Phòng
        'roomCode': appointment.room.code if appointment.room_id else '',
        'roomName': appointment.room.name if appointment.room_id else '',
        # Thời gian
        'date':        appointment.appointment_date.strftime('%Y-%m-%d') if appointment.appointment_date else '',
        'start':       appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else '',
        'end':         end_str,
        'durationMin': duration_min,
        # Trạng thái
        'apptStatus':  appointment.status,
        'payStatus':   appointment.payment_status,
        'source':      appointment.source,
        'cancelledBy': appointment.cancelled_by or '',
        # Ghi chú
        'note':        appointment.notes or '',
        'staffNotes':  appointment.staff_notes or '',
        'customerNote': (appointment.customer.notes or '') if appointment.customer_id else '',
    }


def serialize_appointments(appointments):
    return [serialize_appointment(appt) for appt in appointments]
