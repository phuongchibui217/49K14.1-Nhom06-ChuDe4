"""
Serializers - Chuyển đổi Django Model thành Dictionary (rồi thành JSON)

Nhiệm vụ của file này: Lấy dữ liệu từ Database → Chuyển thành dict → Trả về cho FE

VÍ DỤ:
    appointment = Appointment.objects.get(...)  # Lấy từ DB
    data = serialize_appointment(appointment)    # Chuyển thành dict
    return JsonResponse(data)                    # Trả về JSON cho FE

Author: Spa ANA Team
"""

from .models import Appointment


def serialize_appointment(appointment):
    """
    Chuyển 1 đối tượng Appointment thành dictionary

    Args:
        appointment: Appointment object (từ database)

    Returns:
        dict: Dữ liệu để gửi về frontend qua JSON
    """
    # Get customer email safely
    customer_email = ''
    if appointment.customer:
        customer_email = appointment.customer.email or appointment.customer.user.email or ''

    return {
        'id': appointment.appointment_code,           # Mã lịch hẹn (VD: APT001)
        'customerName': appointment.customer.full_name if appointment.customer else '',  # Tên khách
        'phone': appointment.customer.phone if appointment.customer else '',            # Số điện thoại
        'email': customer_email,                       # Email
        'service': appointment.service.name if appointment.service else '',            # Tên dịch vụ
        'serviceId': appointment.service.id if appointment.service else None,          # ID dịch vụ
        'roomId': appointment.room.code if appointment.room else '',  # Mã phòng
        'roomName': appointment.room.name if appointment.room else '', # Tên phòng
        'guests': appointment.guests or 1,             # Số khách
        'date': appointment.appointment_date.strftime('%Y-%m-%d') if appointment.appointment_date else '',  # Ngày (YYYY-MM-DD)
        'start': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else '',    # Giờ bắt đầu
        'end': appointment.get_end_time_display(),      # Giờ kết thúc
        'durationMin': appointment.duration_minutes or (appointment.service.duration_minutes if appointment.service else 60),
        'note': appointment.notes or '',                # Ghi chú
        'apptStatus': appointment.status,               # Trạng thái lịch hẹn
        'payStatus': appointment.payment_status,        # Trạng thái thanh toán
        'source': appointment.source,                   # Nguồn (web/admin)
    }


def serialize_appointments(appointments):
    """
    Chuyển danh sách Appointment thành list of dict

    Args:
        appointments: QuerySet của Appointment

    Returns:
        list: Danh sách dict
    """
    return [serialize_appointment(appt) for appt in appointments]