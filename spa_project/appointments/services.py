"""
Services cho Appointment Validation

File này chứa các hàm logic nghiệp vụ (business logic) dùng chung cho Appointment.
Tách ra khỏi views.py để:
- Code gọn hơn, dễ đọc
- Dùng lại được ở nhiều nơi (DRY)
- Dễ test riêng biệt

Author: Spa ANA Team
"""

from datetime import datetime, timedelta, date, time as time_type # xử lí thời gian datetime đầy đủ,  timedelta là khoảng thời gian
from django.utils import timezone 
from django.core.exceptions import ValidationError
from django.db.models import Q # các câu truy vấn phức tạp (Ỏ, NOT, AND phức tạp)
from .models import Appointment, Room


# =====================================================
# APPOINTMENT VALIDATION SERVICES
# =====================================================

def validate_appointment_date(appointment_date, is_staff_confirm=False): # hàm kiểm tra ngày hợp lệ
    """
    Kiểm tra ngày hẹn có hợp lệ không

    Quy tắc:
    - Không được chọn ngày trong quá khứ (chỉ áp dụng khi khách đặt online)
    - Staff xác nhận booking cũ được phép dùng ngày quá khứ
    - Sử dụng timezone của Django ( Asia/Ho_Chi_Minh)

    Args:
        appointment_date: date object - ngày cần kiểm tra
        is_staff_confirm: bool - True nếu staff đang xác nhận/sửa lịch (bỏ qua check ngày quá khứ)

    Returns:
        None

    Raises:
        ValidationError: Nếu ngày không hợp lệ
    """
    # Staff xác nhận booking → không check ngày quá khứ
    if is_staff_confirm:
        return

    # Lấy ngày hiện tại theo timezone của Django
    # QUAN TRỌNG: Dùng timezone.now().date() thay vì date.today()
    # để đảm bảo đúng múi giờ configured trong settings.TIME_ZONE
    today = timezone.now().date()

    if appointment_date < today:
        raise ValidationError(
            'Không thể đặt lịch ở ngày quá khứ. '
            f'Bạn đang chọn ngày {appointment_date.strftime("%d/%m/%Y")}, '
            f'nhưng hôm nay là {today.strftime("%d/%m/%Y")}.'
        )


def validate_appointment_time(appointment_time, appointment_date):
    """
    Kiểm tra giờ hẹn có hợp lệ không

    Quy tắc:
    - Giờ làm việc: 9:00 - 21:00 (đặt từ 9h sáng đến trước 21h)
    - Khách có thể đặt lịch cùng ngày, không cần trước 30 phút

    Args:
        appointment_time: time object - giờ cần kiểm tra
        appointment_date: date object - ngày cần kiểm tra

    Returns:
        None

    Raises:
        ValidationError: Nếu giờ không hợp lệ
    """
    # Giờ làm việc: 9:00 - 21:00 (khách đặt từ 9h đến 20h, lịch kết thúc trước 21h)
    opening_time = time_type(9, 0)
    closing_time = time_type(21, 0)

    if appointment_time < opening_time:
        raise ValidationError(
            f'Giờ làm việc bắt đầu từ 09:00. Vui lòng chọn giờ từ 09:00 đến 21:00.'
        )

    if appointment_time >= closing_time:
        raise ValidationError(
            f'Giờ làm việc kết thúc lúc 21:00. Vui lòng chọn giờ trước 21:00.'
        )


def calculate_end_time(start_time, duration_minutes): # Tính giờ kết thúc từ giờ bắt đầu và thời lượng
    """
    Tính giờ kết thúc từ giờ bắt đầu và thời lượng

    Args:
        start_time: time object - giờ bắt đầu
        duration_minutes: int - thời lượng (phút)

    Returns:
        time object - giờ kết thúc
    """
    # Combine với một ngày bất kỳ để tính toán
    base_date = date.today()
    start_datetime = datetime.combine(base_date, start_time)
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time()


def check_room_availability(  
    room_code,
    appointment_date,
    start_time,
    duration_minutes,
    exclude_appointment_code=None,
    new_guests=1
):
    """
    Kiểm tra phòng có trống trong khung giờ đã chọn không

    Đây là hàm quan trọng để tránh double booking (đặt trùng lịch).

    Logic:
    - Lấy tất cả lịch hẹn của phòng vào ngày đó
    - Loại trừ lịch hẹn đang sửa (nếu có)
    - Kiểm tra xem khung giờ mới có giao với lịch nào không

    Args:
        room_code: str - mã phòng (ví dụ: 'P001')
        appointment_date: date - ngày hẹn
        start_time: time - giờ bắt đầu
        duration_minutes: int - thời lượng (phút)
        exclude_appointment_code: str - mã lịch hẹn cần loại trừ (khi sửa)

    Returns:
        tuple: (is_available: bool, conflict_appointment: Appointment|None, message: str)
    """
    # Nếu không có phòng thì luôn available
    if not room_code:
        return (True, None, '')

    # Kiểm tra phòng có tồn tại không
    try:
        room = Room.objects.get(code=room_code, is_active=True)
    except Room.DoesNotExist:
        return (False, None, f'Phòng {room_code} không tồn tại hoặc không hoạt động.')

    # Tính giờ kết thúc
    end_time = calculate_end_time(start_time, duration_minutes)

    # Lấy tất cả lịch hẹn của phòng vào ngày đó
    # Chỉ lấy những lịch có trạng thái không phải 'cancelled' và chưa bị xóa mềm
    queryset = Appointment.objects.filter(
        room=room,
        appointment_date=appointment_date,
        deleted_at__isnull=True,
    ).exclude(
        status='CANCELLED'
    )

    # Loại trừ lịch hẹn đang sửa (nếu có)
    if exclude_appointment_code:
        queryset = queryset.exclude(appointment_code=exclude_appointment_code)

    # Kiểm tra sức chứa phòng (capacity-based)
    # Phòng có N giường → cho phép N khách cùng lúc (tổng số khách trùng giờ <= capacity)
    total_overlapping_guests = 0
    conflicts = []

    for existing in queryset:
        existing_end = existing.end_time or calculate_end_time(
            existing.appointment_time,
            existing.duration_minutes or (
                existing.service_variant.duration_minutes if existing.service_variant else (
                    existing.service.variants.order_by('sort_order').first().duration_minutes
                    if existing.service else 60
                )
            )
        )

        # Kiểm tra giao nhau về thời gian
        if start_time < existing_end and end_time > existing.appointment_time:
            existing_guests = existing.guests or 1
            total_overlapping_guests += existing_guests
            conflicts.append({
                'appointment': existing,
                'end_time': existing_end,
                'guests': existing_guests
            })

    # So sánh tổng số khách trùng giờ với sức chứa phòng
    if total_overlapping_guests + new_guests > room.capacity:
        # Thực sự hết chỗ - báo lỗi
        conflict_info = conflicts[0] if conflicts else None
        if conflict_info:
            appt = conflict_info['appointment']
            et = conflict_info['end_time']
            return (
                False,
                appt,
                f'Phòng {room.name} đã đủ {total_overlapping_guests}/{room.capacity} giường '
                f'trong khung giờ {start_time.strftime("%H:%M")}-{end_time.strftime("%H:%M")} '
                f'ngày {appointment_date.strftime("%d/%m/%Y")}.'
            )
        return (
            False,
            None,
            f'Phòng {room.name} đã đủ chỗ trong khung giờ '
            f'{start_time.strftime("%H:%M")}-{end_time.strftime("%H:%M")} '
            f'ngày {appointment_date.strftime("%d/%m/%Y")}.'
        )

    return (True, None, '')


def validate_appointment_create(
    appointment_date,
    appointment_time,
    duration_minutes,
    room_code=None,
    exclude_appointment_code=None,
    guests=1,
    is_staff_confirm=False
):
    """
    Validate toàn bộ trước khi tạo/sửa lịch hẹn

    Gom tất cả validation vào một chỗ để:
    - Dễ quản lý
    - Dùng lại được ở nhiều nơi (form, API, admin)
    - Tránh sót check

    tham số:
        appointment_date: date - ngày hẹn
        appointment_time: time - giờ hẹn
        duration_minutes: int - thời lượng
        room_code: str - mã phòng (optional)
        exclude_appointment_code: str - mã lịch hẹn cần loại trừ (khi sửa)
        is_staff_confirm: bool - True nếu staff đang xác nhận/sửa (bỏ qua check ngày quá khứ)

    Returns:
        dict: {'valid': bool, 'errors': list}
    """
    errors = []

    # 1. Validate ngày
    try:
        validate_appointment_date(appointment_date, is_staff_confirm=is_staff_confirm)
    except ValidationError as e:
        errors.append(str(e.message))

    # 2. Validate giờ
    try:
        validate_appointment_time(appointment_time, appointment_date)
    except ValidationError as e:
        errors.append(str(e.message))

    # 3. Validate phòng trống (dựa trên sức chứa)
    if room_code:
        is_available, conflict, message = check_room_availability(
            room_code=room_code,
            appointment_date=appointment_date,
            start_time=appointment_time,
            duration_minutes=duration_minutes,
            exclude_appointment_code=exclude_appointment_code,
            new_guests=guests
        )
        if not is_available:
            errors.append(message)

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_available_rooms_for_slot(appointment_date, start_time, duration_minutes):
    """
    Lấy danh sách phòng còn trống cho khung giờ đã chọn

    Args:
        appointment_date: date - ngày hẹn
        start_time: time - giờ bắt đầu
        duration_minutes: int - thời lượng

    Returns:
        QuerySet: Danh sách phòng trống
    """
    all_rooms = Room.objects.filter(is_active=True)
    available_rooms = []

    for room in all_rooms:
        is_available, _, _ = check_room_availability(
            room_code=room.code,
            appointment_date=appointment_date,
            start_time=start_time,
            duration_minutes=duration_minutes
        )
        if is_available:
            available_rooms.append(room)

    return available_rooms


def get_today_str():
    """
    Lấy chuỗi ngày hôm nay theo format YYYY-MM-DD

    Returns:
        str: Ngày hôm nay (ví dụ: '2024-03-20')
    """
    return timezone.now().strftime('%Y-%m-%d')


def get_min_booking_date():
    """
    Lấy ngày sớm nhất có thể đặt lịch

    Returns:
        date: Hôm nay (theo timezone)
    """
    return timezone.now().date()


# =====================================================
# RACE CONDITION NOTE
# =====================================================

"""
CẢNH BÁO VỀ RACE CONDITION
==========================

Trong môi trường multi-user, có thể xảy ra race condition khi:
1. User A check phòng trống -> OK
2. User B check phòng trống -> OK (vì A chưa lưu)
3. User A lưu lịch hẹn
4. User B lưu lịch hẹn -> TRÙNG!

GIẢI PHÁP NGẮN HẠN (đã implement):
- Check tại nhiều tầng: form, API
- Message lỗi rõ ràng để user biết

GIẢI PHÁP DÀI HẠN (nếu cần):
1. Database constraint: Thêm unique constraint trên (room, date, start_time)
   - Phức vụ: Cần xử lý end_time linh hoạt

2. Select for update: Lock row khi check
   - Ưu điểm: Đảm bảo không trùng
   - Nhược điểm: Giảm performance

3. Redis lock: Distributed lock
   - Ưu điểm: Hiệu quả cho multi-server
   - Nhược điểm: Thêm dependency

Hiện tại: Giải pháp ngắn hạn đủ dùng cho quy mô spa nhỏ.
Nếu mở rộng, cân nhắc implement select_for_update().
"""
