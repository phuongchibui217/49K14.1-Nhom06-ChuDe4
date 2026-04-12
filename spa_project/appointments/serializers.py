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
    return {
        'id': appointment.appointment_code,           # Mã lịch hẹn (VD: APT001)
        'customerName': appointment.customer.full_name, # Tên khách
        'phone': appointment.customer.phone,            # Số điện thoại
        'email': getattr(appointment.customer.user, 'email', '') if appointment.customer.user else '',
        'service': appointment.service.name,            # Tên dịch vụ
        'serviceId': appointment.service.id,            # ID dịch vụ
        'roomId': appointment.room.code if appointment.room else '',  # Mã phòng
        'roomName': appointment.room.name if appointment.room else '', # Tên phòng
        'guests': appointment.guests,                   # Số khách
        'date': appointment.appointment_date.strftime('%Y-%m-%d'),  # Ngày (YYYY-MM-DD)
        'start': appointment.appointment_time.strftime('%H:%M'),    # Giờ bắt đầu
        'end': appointment.get_end_time_display(),      # Giờ kết thúc
        'durationMin': appointment.duration_minutes or appointment.service.duration_minutes,
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