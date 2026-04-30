"""
Serializers — chuyển Appointment model thành dict/JSON cho frontend.

Author: Spa ANA Team
"""

from .models import Appointment
from .services import _get_appt_duration, _calc_end_time


def _resolve_customer_note(appointment):
    """
    Trả về ghi chú hồ sơ của đúng khách sử dụng dịch vụ trong dòng này.

    Quy tắc:
    - Chỉ lấy customer.notes khi customer.phone khớp với customer_phone_snapshot
      (tức là profile được gán đúng là khách sử dụng dịch vụ, không phải người đặt).
    - Nếu không có customer_phone_snapshot (đặt dùm, không nhập SĐT riêng)
      → trả về '' để tránh lấy nhầm ghi chú của người đặt.
    - Nếu customer_phone_snapshot có nhưng không khớp customer.phone
      → thử lookup profile theo snapshot phone, lấy notes từ đó.
    """
    if not appointment.customer_id:
        return ''

    guest_phone = (appointment.customer_phone_snapshot or '').strip()
    if not guest_phone:
        # Không có SĐT riêng của khách → không thể xác định đúng profile → trả rỗng
        return ''

    try:
        customer = appointment.customer
        if customer.phone == guest_phone:
            # Profile đúng là khách sử dụng dịch vụ
            return customer.notes or ''
        else:
            # Profile được gán là người đặt (fallback), thử tìm đúng profile của khách
            from customers.models import CustomerProfile
            try:
                guest_profile = CustomerProfile.objects.get(phone=guest_phone)
                return guest_profile.notes or ''
            except CustomerProfile.DoesNotExist:
                # Khách chưa có hồ sơ → không có ghi chú
                return ''
    except Exception:
        return ''


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
        # Ghi chú khách: chỉ lấy từ profile nếu profile đó đúng là khách sử dụng dịch vụ
        # (customer.phone khớp customer_phone_snapshot), tránh fallback sang profile người đặt
        'customerNote': _resolve_customer_note(appointment),
    }


def serialize_appointments(appointments):
    return [serialize_appointment(appt) for appt in appointments]
