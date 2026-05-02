"""
API Endpoints — Lịch hẹn (Organized by Tabs)

Cấu trúc mới: Booking + Appointment
- Booking = 1 lần đặt lịch (1 người đặt, nhiều khách)
- Appointment = từng khách / dịch vụ / phòng / khung giờ

TAB 1: Lịch theo phòng (Room Calendar)
TAB 2: Yêu cầu đặt lịch (Booking Requests)
SHARED: Endpoints dùng chung

Author: Spa ANA Team
"""

import json
import re
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.db import transaction

from .models import Appointment, Booking, Room, Invoice, InvoiceItem, InvoicePayment
from customers.models import CustomerProfile
from spa_services.models import ServiceVariant

from .serializers import serialize_appointment, serialize_booking
from .services import validate_appointment_create, _get_appt_duration
from core.api_response import staff_api, get_or_404


# ============================================================
# SECTION 2: HELPER FUNCTIONS
# ============================================================

def _is_staff(user):
    """Check if user is staff or superuser."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _deny():
    """Return 403 Forbidden response."""
    return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)


def _get_variant_price(service_variant):
    """Lấy giá từ variant."""
    if service_variant and hasattr(service_variant, 'price'):
        return Decimal(str(service_variant.price))
    return Decimal('0')


def _get_or_create_customer(phone, customer_name):
    """
    Tìm hoặc tạo CustomerProfile theo SĐT.
    Chỉ gọi khi đã xác định được phone của đúng khách sử dụng dịch vụ.
    KHÔNG dùng booker_phone để tạo profile cho guest.
    """
    from django.contrib.auth.models import User
    import secrets

    if not phone or not re.match(r'^0\d{9}$', phone):
        raise ValueError(f'SĐT không hợp lệ để tạo profile: {phone!r}')

    # Lookup qua CustomerProfile trước để tránh conflict username
    try:
        customer = CustomerProfile.objects.get(phone=phone)
        if customer_name and customer.full_name != customer_name:
            customer.full_name = customer_name
            customer.save(update_fields=['full_name'])
        return customer
    except CustomerProfile.DoesNotExist:
        pass

    # Tạo user mới với username = "guest_<phone>", thêm suffix nếu trùng
    base_username = f'guest_{phone}'
    username = base_username
    if User.objects.filter(username=username).exists():
        username = f'{base_username}_{secrets.token_hex(3)}'

    name_parts = customer_name.split() if customer_name else []
    user = User.objects.create_user(
        username=username,
        password=secrets.token_hex(16),
        first_name=name_parts[0] if name_parts else '',
        last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
    )

    customer = CustomerProfile.objects.create(
        phone=phone,
        full_name=customer_name or '',
        user=user,
    )
    return customer


def _resolve_or_create_customer(phone=None, email=None, customer_name=''):
    """
    Tìm CustomerProfile theo phone hoặc email, tạo mới nếu chưa có.

    Thứ tự ưu tiên:
    1. Có phone → tìm theo phone, tạo mới nếu không thấy (email lưu kèm)
    2. Không có phone, có email → tìm theo email (unique), không tạo mới (thiếu phone)
    3. Không có gì → trả None

    Returns: CustomerProfile hoặc None
    """
    from django.contrib.auth.models import User
    import secrets

    phone = ''.join(filter(str.isdigit, phone or ''))
    email = (email or '').strip().lower() or None

    # ── 1. Có phone ──────────────────────────────────────────────────────────
    if phone and len(phone) >= 10:
        try:
            customer = CustomerProfile.objects.get(phone=phone)
            if customer_name and customer.full_name != customer_name:
                customer.full_name = customer_name
                customer.save(update_fields=['full_name'])
            return customer
        except CustomerProfile.DoesNotExist:
            pass

        # Không tìm thấy theo phone → tạo mới
        # Nếu email đã thuộc profile khác thì không gán email (tránh unique violation)
        safe_email = email
        if email and CustomerProfile.objects.filter(email=email).exists():
            safe_email = None

        base_username = f'guest_{phone}'
        username = base_username
        if User.objects.filter(username=username).exists():
            username = f'{base_username}_{secrets.token_hex(3)}'

        name_parts = customer_name.split() if customer_name else []
        user = User.objects.create_user(
            username=username,
            password=secrets.token_hex(16),
            first_name=name_parts[0] if name_parts else '',
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            email=safe_email or '',
        )
        return CustomerProfile.objects.create(
            phone=phone,
            full_name=customer_name or '',
            email=safe_email,
            user=user,
        )

    # ── 2. Không có phone, chỉ có email ─────────────────────────────────────
    if email:
        try:
            customer = CustomerProfile.objects.get(email=email)
            if customer_name and customer.full_name != customer_name:
                customer.full_name = customer_name
                customer.save(update_fields=['full_name'])
            return customer
        except CustomerProfile.DoesNotExist:
            pass
        # Không tạo mới vì phone là NOT NULL — trả None, dùng snapshot

    return None


def _create_invoice_and_payment(booking, appointments, pay_status, payment_data, created_by):
    """
    Tạo Invoice + InvoiceItem + InvoicePayment cho 1 Booking.

    booking: Booking instance
    appointments: list of Appointment instances thuộc booking này
    pay_status: trạng thái thanh toán
    payment_data: dict chứa payment_method, amount, recorded_no, note
    created_by: User
    """
    # Tính tổng từ tất cả appointments
    subtotal = Decimal('0')
    for appt in appointments:
        subtotal += _get_variant_price(appt.service_variant)

    discount = Decimal('0')
    final = subtotal - discount

    invoice = Invoice.objects.create(
        booking=booking,
        subtotal_amount=subtotal,
        discount_type='NONE',
        discount_value=Decimal('0'),
        discount_amount=discount,
        final_amount=final,
        status=pay_status,
        created_by=created_by,
    )

    # Tạo InvoiceItem cho từng appointment
    for appt in appointments:
        unit_price = _get_variant_price(appt.service_variant)
        desc = ''
        if appt.service_variant_id:
            try:
                sv = appt.service_variant
                desc = f"{sv.service.name} — {sv.label}" if sv.service_id else sv.label or ''
            except Exception:
                pass
        InvoiceItem.objects.create(
            invoice=invoice,
            appointment=appt,
            service_variant=appt.service_variant,
            description=desc,
            quantity=1,
            unit_price=unit_price,
            line_total=unit_price,
        )

    if pay_status in ('UNPAID', 'REFUNDED'):
        return invoice

    if pay_status == 'PAID':
        pay_amount = final
    else:  # PARTIAL
        pay_amount = Decimal(str(payment_data.get('amount', 0)))

    InvoicePayment.objects.create(
        invoice=invoice,
        amount=pay_amount,
        payment_method=payment_data.get('payment_method', 'CASH'),
        transaction_status='SUCCESS',
        recorded_by=created_by,
        recorded_no=payment_data.get('recorded_no', '') or None,
        note=payment_data.get('note', '') or None,
    )

    return invoice


def _validate_status_timing(appt_date, appt_time, duration_minutes, new_status):
    """
    Validate thời điểm chuyển trạng thái ARRIVED / COMPLETED.

    Rules:
    - ARRIVED   : now >= appointment_start
    - COMPLETED : now >= appointment_start + duration_minutes

    Trả về (ok: bool, error_msg: str).
    Các status khác (NOT_ARRIVED, CANCELLED) luôn pass.
    """
    if new_status not in ('ARRIVED', 'COMPLETED'):
        return True, ''

    from django.utils import timezone as _tz
    import datetime as _dt

    # Dùng timezone local của server (settings.TIME_ZONE)
    now_local = _tz.localtime(_tz.now())
    now_date  = now_local.date()
    now_time  = now_local.time()

    # Tính start datetime
    start_dt = _dt.datetime.combine(appt_date, appt_time)
    # Tính end datetime
    end_dt   = start_dt + _dt.timedelta(minutes=int(duration_minutes or 60))

    # now datetime (naive, cùng local)
    now_dt = _dt.datetime.combine(now_date, now_time)

    if new_status == 'ARRIVED':
        if now_dt < start_dt:
            return False, 'Chưa đến giờ hẹn, không thể chuyển sang Đã đến'

    if new_status == 'COMPLETED':
        if now_dt < end_dt:
            return False, 'Chưa kết thúc giờ hẹn, không thể hoàn thành lịch'

    return True, ''


def _validate_payment_data(pay_status, payment_data, final_amount=None):
    """Validate payment fields."""
    if pay_status in ('UNPAID', 'REFUNDED'):
        return True, ''

    method = (payment_data.get('payment_method') or '').strip()
    valid_methods = ['CASH', 'CARD', 'BANK_TRANSFER', 'E_WALLET']
    if not method or method not in valid_methods:
        return False, 'Vui lòng chọn phương thức thanh toán'

    if pay_status == 'PARTIAL':
        try:
            amount = Decimal(str(payment_data.get('amount', 0)))
        except Exception:
            return False, 'Số tiền thanh toán không hợp lệ'
        if amount <= 0:
            return False, 'Số tiền thanh toán phải lớn hơn 0'
        if final_amount and amount >= Decimal(str(final_amount)):
            return False, 'Số tiền thanh toán một phần phải nhỏ hơn tổng tiền'

    return True, ''


def _validate_appointment_data(data):
    """Validate dữ liệu appointment (khách/dịch vụ/phòng/giờ) trước khi tạo."""
    import re
    _EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

    errors = []
    cleaned = {}

    # Tên khách (bắt buộc)
    customer_name = data.get('customer_name', '').strip()
    if not customer_name:
        errors.append('Vui lòng nhập tên khách')
    else:
        cleaned['customer_name'] = customer_name

    # SĐT khách (tuỳ chọn — nhưng nếu có phải đúng format VN)
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    if phone and not re.match(r'^0\d{9}$', phone):
        errors.append('Số điện thoại khách không hợp lệ (phải có 10 số và bắt đầu bằng 0)')
    else:
        cleaned['phone'] = phone or None

    # Email khách (tuỳ chọn — validate format nếu có)
    guest_email = data.get('email', '').strip()
    if guest_email and not _EMAIL_RE.match(guest_email):
        errors.append('Email không hợp lệ')
    else:
        cleaned['email'] = guest_email or None

    # Dịch vụ (tuỳ chọn — admin có thể tạo lịch không chọn dịch vụ, khách chọn sau khi tới)
    # Logic:
    #   - Không có serviceId VÀ không có variantId → cho phép (lịch chưa chọn dịch vụ)
    #   - Có serviceId nhưng không có variantId → lỗi "Vui lòng chọn gói dịch vụ"
    #   - Có variantId → validate variant tồn tại
    service_id = data.get('service_id') or data.get('serviceId')
    variant_id = data.get('variant_id') or data.get('variantId')

    # Chuẩn hoá: coi '' và None như nhau
    service_id = service_id if service_id else None
    variant_id = variant_id if variant_id else None

    if service_id and not variant_id:
        # Đã chọn dịch vụ nhưng chưa chọn gói → bắt buộc phải chọn gói
        errors.append('Vui lòng chọn gói dịch vụ')
    elif variant_id:
        try:
            variant = ServiceVariant.objects.get(id=variant_id)
            cleaned['service_variant'] = variant
        except ServiceVariant.DoesNotExist:
            errors.append('Gói dịch vụ không tồn tại')
    else:
        # Không chọn dịch vụ lẫn gói → cho phép
        cleaned['service_variant'] = None

    # Trạng thái appointment
    status = str(data.get('status') or 'NOT_ARRIVED').strip().upper()
    valid_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
    if status not in valid_statuses:
        errors.append('Trạng thái không hợp lệ')
    cleaned['status'] = status

    # Ngày (bắt buộc)
    date_str = data.get('date_str', '')
    if not date_str:
        errors.append('Vui lòng chọn ngày hẹn')
    else:
        try:
            cleaned['appointment_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Định dạng ngày không hợp lệ')

    # Giờ (bắt buộc)
    time_str = data.get('time_str', '')
    if not time_str:
        errors.append('Vui lòng chọn giờ hẹn')
    else:
        try:
            cleaned['appointment_time'] = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            errors.append('Định dạng giờ không hợp lệ')

    # Duration từ variant hoặc fallback 60
    # Fix: kiểm tra cả service_variant không None trước khi truy cập duration_minutes
    sv = cleaned.get('service_variant')
    if sv is not None:
        try:
            cleaned['duration_minutes'] = sv.duration_minutes
        except Exception:
            cleaned['duration_minutes'] = 60
    else:
        cleaned['duration_minutes'] = 60

    # Phòng (bắt buộc)
    room_id = data.get('room_id')
    if not room_id:
        errors.append('Vui lòng chọn phòng')
    else:
        try:
            cleaned['room'] = Room.objects.get(code=room_id)
        except Room.DoesNotExist:
            errors.append('Phòng không tồn tại')

    # Validate nâng cao: trùng lịch / sức chứa phòng
    if not errors and 'appointment_date' in cleaned and 'appointment_time' in cleaned:
        room_code = cleaned['room'].code if 'room' in cleaned else None
        is_staff_confirm = data.get('is_staff_confirm', False)
        validation_result = validate_appointment_create(
            appointment_date=cleaned['appointment_date'],
            appointment_time=cleaned['appointment_time'],
            duration_minutes=cleaned['duration_minutes'],
            room_code=room_code,
            exclude_appointment_code=None,
            is_staff_confirm=is_staff_confirm,
        )
        if not validation_result['valid']:
            for err_msg in validation_result['errors']:
                lower = err_msg.lower()
                if 'đủ' in lower or 'capacity' in lower or 'chỗ' in lower:
                    errors.append('Phòng đã đủ chỗ ở khung giờ này, vui lòng chọn phòng hoặc thời gian khác.')
                elif 'trùng' in lower or 'conflict' in lower or 'đã có lịch' in lower:
                    errors.append('Khung giờ đã có lịch, vui lòng chọn thời gian khác.')
                else:
                    errors.append(err_msg)

    return {'valid': len(errors) == 0, 'errors': errors, 'cleaned_data': cleaned}


# ============================================================
# SECTION 3: SHARED ENDPOINTS
# ============================================================

@require_http_methods(["GET"])
def api_appointments_search(request):
    """
    [SHARED] GET /api/appointments/search/

    Tìm kiếm lịch hẹn toàn hệ thống.
    """
    if not _is_staff(request.user):
        return _deny()

    q          = request.GET.get('q', '').strip()
    name       = request.GET.get('name', '').strip()
    code       = request.GET.get('code', '').strip()
    phone      = request.GET.get('phone', '').strip()
    email      = request.GET.get('email', '').strip()
    status     = request.GET.get('status', '').strip().upper()
    source     = request.GET.get('source', '').strip()
    service_id = request.GET.get('service', '').strip()
    room_code  = request.GET.get('room', '').strip()
    date_from  = request.GET.get('date_from', '').strip()
    date_to    = request.GET.get('date_to', '').strip()

    has_condition = any([q, name, code, phone, email, status, source, service_id, room_code, date_from, date_to])
    if not has_condition:
        return JsonResponse({'success': False, 'error': 'Vui lòng nhập điều kiện tìm kiếm'}, status=400)

    qs = Appointment.objects.filter(deleted_at__isnull=True).select_related('booking', 'customer', 'service_variant__service', 'room')

    if q:
        qs = qs.filter(
            Q(customer_name_snapshot__icontains=q) |
            Q(booking__booker_name__icontains=q) |
            Q(customer__full_name__icontains=q) |
            Q(customer_phone_snapshot__icontains=q) |
            Q(booking__booker_phone__icontains=q) |
            Q(customer_email_snapshot__icontains=q) |
            Q(booking__booker_email__icontains=q) |
            Q(appointment_code__icontains=q) |
            Q(booking__booking_code__icontains=q) |
            Q(customer__phone__icontains=q)
        )
    if name:
        qs = qs.filter(
            Q(customer_name_snapshot__icontains=name) |
            Q(booking__booker_name__icontains=name)
        )
    if code:
        qs = qs.filter(
            Q(appointment_code__icontains=code) |
            Q(booking__booking_code__icontains=code)
        )
    if phone:
        qs = qs.filter(
            Q(customer_phone_snapshot__icontains=phone) |
            Q(booking__booker_phone__icontains=phone) |
            Q(customer__phone__icontains=phone)
        )
    if email:
        qs = qs.filter(
            Q(customer_email_snapshot__icontains=email) |
            Q(booking__booker_email__icontains=email)
        )
    if status:
        # Tìm theo appointment status hoặc booking status
        qs = qs.filter(
            Q(status=status) | Q(booking__status=status)
        )
    if source:
        qs = qs.filter(booking__source=source)
    if service_id:
        qs = qs.filter(service_variant__service_id=service_id)
    if room_code:
        qs = qs.filter(room__code=room_code)
    if date_from:
        qs = qs.filter(appointment_date__gte=date_from)
    if date_to:
        qs = qs.filter(appointment_date__lte=date_to)

    results = list(qs.order_by('-appointment_date', '-appointment_time')[:100])

    if name:
        name_lower = name.lower()
        results = [a for a in results if
                   name_lower in (a.customer_name_snapshot or '').lower() or
                   name_lower in (a.booking.booker_name or '').lower()]

    return JsonResponse({'success': True, 'appointments': [serialize_appointment(a) for a in results]})


@require_http_methods(["GET"])
def api_customer_search(request):
    """
    [SHARED] GET /api/customers/search/?q=...

    Tìm khách hàng theo tên, SĐT hoặc email.

    TAB: Used by both Room Calendar and Booking Requests
    Methods: GET

    Query params:
    - q: Search query (min 2 characters)

    Returns: Max 10 customers with id, fullName, phone, email
    """
    if not _is_staff(request.user):
        return _deny()

    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'success': True, 'customers': []})

    customers = CustomerProfile.objects.filter(
        Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(user__email__icontains=q)
    ).select_related('user')[:10]

    return JsonResponse({
        'success': True,
        'customers': [
            {
                'id':       c.id,
                'fullName': c.full_name,
                'phone':    c.phone,
                'email':    c.user.email if c.user else (c.email or ''),
                'notes':    c.notes or '',
            }
            for c in customers
        ]
    })


# @require_http_methods(["GET", "POST"])
# @staff_api
# def api_appointment_rebook(request, appointment_code):
#     """
#     [DEPRECATED — 410 Gone]

#     GET/POST /api/appointments/<code>/rebook/

#     Endpoint này đã bị loại bỏ.
#     Flow "Đặt lại" hiện tại hoạt động hoàn toàn trên frontend:
#       openRebookAsCreate() → mở modal tạo booking/appointment mới.
#     Không còn reset booking/appointment cũ về PENDING/NOT_ARRIVED nữa
#     vì dễ gây sai dữ liệu, đặc biệt với booking nhiều khách.

#     Frontend không gọi endpoint này — trả 410 Gone để tránh nhầm lẫn.
#     """
#     return JsonResponse(
#         {
#             'success': False,
#             'error': (
#                 'Endpoint này đã bị loại bỏ (410 Gone). '
#                 'Flow "Đặt lại" hiện dùng openRebookAsCreate() trên frontend '
#                 'để tạo booking/appointment mới thay vì reset dữ liệu cũ.'
#             ),
#             'deprecated': True,
#         },
#         status=410,
#     )


# ============================================================
# SECTION 4: TAB 1 - LICH THEO PHONG (ROOM CALENDAR)
# ============================================================

@require_http_methods(["GET"])
def api_rooms_list(request):
    if not _is_staff(request.user):
        return _deny()
    rooms = Room.objects.filter(is_active=True).order_by("code")
    return JsonResponse({
        "success": True,
        "rooms": [{"id": r.code, "name": r.name, "capacity": r.capacity} for r in rooms]
    })


@require_http_methods(["GET"])
def api_appointments_list(request):
    """[TAB 1] GET /api/appointments/ - Danh sach lich hen voi cac bo loc."""
    if not _is_staff(request.user):
        return _deny()
    try:
        # BUG-07: Không exclude ONLINE PENDING nữa — hiển thị trên grid với flag isPending
        # Chỉ exclude ONLINE CANCELLED/REJECTED (không cần hiện trên grid lịch phòng)
        qs = Appointment.objects.filter(deleted_at__isnull=True).select_related(
            'booking', 'customer', 'service_variant__service', 'room'
        ).exclude(
            booking__source='ONLINE',
            booking__status__in=['CANCELLED', 'REJECTED']
        )
        if date_filter := request.GET.get('date'):
            qs = qs.filter(appointment_date=date_filter)
        if status_filter := request.GET.get('status', '').strip().upper():
            qs = qs.filter(status=status_filter)
        if source_filter := request.GET.get('source'):
            qs = qs.filter(booking__source=source_filter)
        if service_filter := request.GET.get('service'):
            qs = qs.filter(service_variant__service_id=service_filter)
        if search := request.GET.get('q', '').strip():
            # BUG-09: Thêm tìm kiếm theo booking_code
            qs = qs.filter(
                Q(customer_name_snapshot__icontains=search) |
                Q(customer_phone_snapshot__icontains=search) |
                Q(customer_email_snapshot__icontains=search) |
                Q(booking__booker_name__icontains=search) |
                Q(booking__booker_phone__icontains=search) |
                Q(appointment_code__icontains=search) |
                Q(booking__booking_code__icontains=search) |
                Q(booking__booker_notes__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__phone__icontains=search)
            )
        qs = qs.order_by('appointment_date', 'appointment_time')
        return JsonResponse({'success': True, 'appointments': [serialize_appointment(a) for a in qs]})
    except Exception:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Không thể tải lịch hẹn. Vui lòng thử lại sau.'}, status=500)


@require_http_methods(["GET"])
def api_appointment_detail(request, appointment_code):
    """[TAB 1] GET /api/appointments/<code>/ - Chi tiet lich hen."""
    if not _is_staff(request.user):
        return _deny()
    try:
        appt = Appointment.objects.select_related('booking', 'customer', 'service_variant__service', 'room').get(
            appointment_code=appointment_code, deleted_at__isnull=True
        )
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)
    return JsonResponse({'success': True, 'appointment': serialize_appointment(appt)})


@require_http_methods(["GET"])
def api_booking_detail(request, booking_code):
    """
    [TAB 1] GET /api/bookings/<booking_code>/
    Trả về toàn bộ appointments thuộc 1 booking để edit modal hiển thị đủ khách.
    """
    if not _is_staff(request.user):
        return _deny()
    try:
        booking = Booking.objects.get(booking_code=booking_code, deleted_at__isnull=True)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy booking'}, status=404)

    appointments = (
        Appointment.objects
        .filter(booking=booking, deleted_at__isnull=True)
        .select_related('booking', 'customer', 'service_variant__service', 'room')
        .order_by('appointment_date', 'appointment_time')
    )
    from .serializers import serialize_booking
    return JsonResponse({
        'success': True,
        'booking': serialize_booking(booking),
        'appointments': [serialize_appointment(a) for a in appointments],
    })


@require_http_methods(["GET"])
@staff_api
def api_booking_invoice(request, booking_code):
    """
    [TAB 1] GET /api/bookings/<booking_code>/invoice/
    Trả về dữ liệu hóa đơn đầy đủ cho popup Invoice Modal.
    """
    try:
        booking = Booking.objects.get(booking_code=booking_code, deleted_at__isnull=True)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy booking'}, status=404)

    appointments = list(
        Appointment.objects
        .filter(booking=booking, deleted_at__isnull=True)
        .select_related('service_variant__service', 'customer')
        .order_by('appointment_date', 'appointment_time')
    )

    # Tính subtotal từ appointments hiện tại (giá variant thực tế)
    subtotal = Decimal('0')
    lines = []
    for appt in appointments:
        unit_price = _get_variant_price(appt.service_variant)
        subtotal += unit_price
        svc_name = variant_label = ''
        duration_min = None
        if appt.service_variant_id:
            try:
                sv = appt.service_variant
                svc_name     = sv.service.name if sv.service_id else ''
                variant_label = sv.label or ''
                duration_min  = sv.duration_minutes
            except Exception:
                pass
        lines.append({
            'apptCode':     appt.appointment_code,
            'customerName': appt.customer_name_snapshot or '',
            'serviceName':  svc_name,
            'variantLabel': variant_label,
            'durationMin':  duration_min,
            'unitPrice':    str(unit_price),
            'quantity':     1,
            'lineTotal':    str(unit_price),
        })

    # Lấy invoice nếu đã có — đọc discount_type / discount_value từ DB
    discount_type   = 'NONE'
    discount_value  = Decimal('0')
    discount_amount = Decimal('0')
    paid_amount     = Decimal('0')
    invoice_code    = ''
    try:
        inv = booking.invoice
        discount_type   = inv.discount_type   or 'NONE'
        discount_value  = inv.discount_value  or Decimal('0')
        discount_amount = inv.discount_amount or Decimal('0')
        invoice_code    = inv.code or ''
        paid_amount     = sum(
            p.amount for p in inv.payments.filter(transaction_status='SUCCESS')
        )
    except Invoice.DoesNotExist:
        pass

    # Tính lại final từ subtotal hiện tại (variant có thể đã đổi)
    final     = subtotal - discount_amount
    remaining = max(final - paid_amount, Decimal('0'))

    return JsonResponse({
        'success': True,
        'invoice': {
            'invoiceCode':    invoice_code,
            'bookingCode':    booking.booking_code,
            'bookerName':     booking.booker_name or '',
            'bookerPhone':    booking.booker_phone or '',
            'paymentStatus':  booking.payment_status,
            'lines':          lines,
            'subtotal':       str(subtotal),
            'discountType':   discount_type,
            'discountValue':  str(discount_value),
            'discountAmount': str(discount_amount),
            'finalAmount':    str(final),
            'paidAmount':     str(paid_amount),
            'remaining':      str(remaining),
        }
    })


@require_http_methods(["POST"])
@staff_api
def api_booking_invoice_pay(request, booking_code):
    """
    [TAB 1] POST /api/bookings/<booking_code>/invoice/pay/
    Xử lý thanh toán hóa đơn từ Invoice Modal.

    Body JSON:
    {
        "discountType":   "NONE" | "AMOUNT" | "PERCENT"
        "discountValue":  <number>,   // số tiền (AMOUNT) hoặc % (PERCENT)
        "payAmount":      <number>,   // số tiền thu lần này (0 = chỉ lưu discount)
        "paymentMethod":  "CASH" | "CARD" | "BANK_TRANSFER" | "E_WALLET"
    }

    Công thức:
        subtotal       = tổng giá variant hiện tại
        discount_amount:
            NONE/0     → 0
            AMOUNT     → min(discount_value, subtotal)
            PERCENT    → round(subtotal * discount_value / 100)
        final_amount   = subtotal - discount_amount
        payment_status:
            total_paid == 0          → UNPAID
            0 < total_paid < final   → PARTIAL
            total_paid >= final      → PAID
    """
    try:
        booking = Booking.objects.get(booking_code=booking_code, deleted_at__isnull=True)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy booking'}, status=404)

    try:
        raw = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'}, status=400)

    # ── Đọc & validate input ─────────────────────────────────────────────────
    raw_dtype = (raw.get('discountType') or 'NONE').strip().upper()
    # Chấp nhận cả alias cũ 'VND' → 'AMOUNT'
    if raw_dtype == 'VND':
        raw_dtype = 'AMOUNT'
    valid_dtypes = {'NONE', 'AMOUNT', 'PERCENT'}
    if raw_dtype not in valid_dtypes:
        raw_dtype = 'NONE'

    try:
        discount_value = Decimal(str(raw.get('discountValue') or 0))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Giá trị chiết khấu không hợp lệ'}, status=400)

    try:
        pay_amount = Decimal(str(raw.get('payAmount') or 0))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Số tiền thanh toán không hợp lệ'}, status=400)

    pay_method = (raw.get('paymentMethod') or '').strip()
    valid_methods = {'CASH', 'CARD', 'BANK_TRANSFER', 'E_WALLET'}

    if pay_amount < 0:
        return JsonResponse({'success': False, 'error': 'Số tiền thanh toán không được âm'}, status=400)
    if pay_amount > 0 and pay_method not in valid_methods:
        return JsonResponse({'success': False, 'error': 'Vui lòng chọn phương thức thanh toán'}, status=400)
    if discount_value < 0:
        return JsonResponse({'success': False, 'error': 'Chiết khấu không được âm'}, status=400)
    if raw_dtype == 'PERCENT' and discount_value > 100:
        return JsonResponse({'success': False, 'error': 'Chiết khấu % không được vượt quá 100'}, status=400)

    # ── Tính subtotal từ appointments hiện tại ───────────────────────────────
    appointments = list(
        Appointment.objects
        .filter(booking=booking, deleted_at__isnull=True)
        .select_related('service_variant')
    )
    subtotal = sum(_get_variant_price(a.service_variant) for a in appointments)

    # ── Tính discount_amount theo công thức ──────────────────────────────────
    if raw_dtype == 'NONE' or discount_value == 0:
        discount_amount = Decimal('0')
        raw_dtype = 'NONE'
    elif raw_dtype == 'PERCENT':
        discount_amount = (subtotal * discount_value / Decimal('100')).quantize(Decimal('1'))
        discount_amount = max(Decimal('0'), min(discount_amount, subtotal))
    else:  # AMOUNT
        discount_amount = min(discount_value, subtotal)
        discount_amount = max(Decimal('0'), discount_amount)

    final_amount = max(subtotal - discount_amount, Decimal('0'))

    with transaction.atomic():
        locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)

        # ── Lấy hoặc tạo Invoice ─────────────────────────────────────────────
        def _rebuild_items(inv):
            inv.items.all().delete()
            for appt in appointments:
                unit_price = _get_variant_price(appt.service_variant)
                desc = ''
                if appt.service_variant_id:
                    try:
                        sv = appt.service_variant
                        desc = f"{sv.service.name} — {sv.label}" if sv.service_id else sv.label or ''
                    except Exception:
                        pass
                InvoiceItem.objects.create(
                    invoice=inv,
                    appointment=appt,
                    service_variant=appt.service_variant,
                    description=desc,
                    quantity=1,
                    unit_price=unit_price,
                    line_total=unit_price,
                )

        try:
            inv = Invoice.objects.select_for_update().get(booking=locked_booking)
            inv.subtotal_amount = subtotal
            inv.discount_type   = raw_dtype
            inv.discount_value  = discount_value
            inv.discount_amount = discount_amount
            inv.final_amount    = final_amount
            inv.save(update_fields=[
                'subtotal_amount', 'discount_type', 'discount_value',
                'discount_amount', 'final_amount',
            ])
            _rebuild_items(inv)
        except Invoice.DoesNotExist:
            inv = Invoice.objects.create(
                booking=locked_booking,
                subtotal_amount=subtotal,
                discount_type=raw_dtype,
                discount_value=discount_value,
                discount_amount=discount_amount,
                final_amount=final_amount,
                status='UNPAID',
                created_by=request.user,
            )
            _rebuild_items(inv)

        # ── Ghi nhận thanh toán lần này ──────────────────────────────────────
        if pay_amount > 0:
            InvoicePayment.objects.create(
                invoice=inv,
                amount=pay_amount,
                payment_method=pay_method,
                transaction_status='SUCCESS',
                recorded_by=request.user,
            )

        # ── Tính tổng đã trả (tất cả lần SUCCESS) ───────────────────────────
        total_paid = sum(
            p.amount for p in inv.payments.filter(transaction_status='SUCCESS')
        )

        # ── Xác định payment_status tự động ─────────────────────────────────
        # BUG-06: Chỉ auto-PAID khi final_amount == 0 VÀ booking có ít nhất 1 dịch vụ
        # (chiết khấu 100%). Nếu không có dịch vụ nào → giữ UNPAID.
        has_any_service = any(a.service_variant_id for a in appointments)
        if final_amount == 0 and has_any_service:
            # Chiết khấu 100% trên booking có dịch vụ → coi như đã thanh toán đủ
            new_pay_status = 'PAID'
        elif total_paid <= 0:
            new_pay_status = 'UNPAID'
        elif total_paid >= final_amount:
            new_pay_status = 'PAID'
        else:
            new_pay_status = 'PARTIAL'

        inv.status = new_pay_status
        inv.save(update_fields=['status'])

        locked_booking.payment_status = new_pay_status
        locked_booking.save(update_fields=['payment_status', 'updated_at'])

    remaining = max(final_amount - total_paid, Decimal('0'))

    return JsonResponse({
        'success':       True,
        'paymentStatus': new_pay_status,
        'paidAmount':    str(total_paid),
        'finalAmount':   str(final_amount),
        'discountAmount': str(discount_amount),
        'remaining':     str(remaining),
        'message':       'Cập nhật thanh toán thành công',
    })


@require_http_methods(["POST"])
@staff_api
def api_booking_invoice_refund(request, booking_code):
    """
    [TAB 1] POST /api/bookings/<booking_code>/invoice/refund/
    Hoàn tiền hóa đơn: đổi tất cả InvoicePayment SUCCESS → REFUNDED,
    set Invoice.status = REFUNDED, Booking.payment_status = REFUNDED.
    """
    try:
        booking = Booking.objects.get(booking_code=booking_code, deleted_at__isnull=True)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy booking'}, status=404)

    try:
        inv = booking.invoice
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy hóa đơn'}, status=404)

    if inv.status == 'REFUNDED':
        return JsonResponse({'success': False, 'error': 'Hóa đơn đã được hoàn tiền trước đó'}, status=400)

    if inv.status == 'UNPAID':
        return JsonResponse({'success': False, 'error': 'Hóa đơn chưa có thanh toán để hoàn'}, status=400)

    # BUG-10: Chặn hoàn tiền khi PARTIAL — chỉ cho refund khi PAID
    if inv.status == 'PARTIAL':
        return JsonResponse(
            {
                'success': False,
                'error': 'Không thể hoàn tiền khi chưa thanh toán đủ. '
                         'Vui lòng thu đủ tiền trước khi hoàn.',
            },
            status=400,
        )

    # Chỉ hoàn tiền khi thực sự có tiền đã thu (paidAmount > 0)
    paid_amount = sum(
        p.amount for p in inv.payments.filter(transaction_status='SUCCESS')
    )
    if paid_amount <= 0:
        return JsonResponse({'success': False, 'error': 'Không có khoản thanh toán nào để hoàn'}, status=400)

    with transaction.atomic():
        # Đổi tất cả payment SUCCESS → REFUNDED
        inv.payments.filter(transaction_status='SUCCESS').update(transaction_status='REFUNDED')

        # Cập nhật invoice và booking
        inv.status = 'REFUNDED'
        inv.save(update_fields=['status'])

        booking.payment_status = 'REFUNDED'
        booking.save(update_fields=['payment_status', 'updated_at'])

    return JsonResponse({
        'success':       True,
        'paymentStatus': 'REFUNDED',
        'message':       'Đã hoàn tiền hóa đơn',
    })


@require_http_methods(["POST"])
@staff_api
def api_appointment_create_batch(request):
    """
    [TAB 1] POST /api/appointments/create-batch/
    Tao nhieu lich hen cung luc (1 nguoi dat, nhieu khach).
    Tao 1 Booking + N Appointment + 1 Invoice cho toan bo.
    """
    try:
        raw = json.loads(request.body)
        booker = raw.get('booker', {})
        guests = raw.get('guests', [])

        if not guests:
            return JsonResponse({'success': False, 'error': 'Vui lòng thêm ít nhất 1 khách'}, status=400)

        booker_name  = booker.get('name', '').strip()
        booker_phone = ''.join(filter(str.isdigit, booker.get('phone', '')))
        booker_email = booker.get('email', '').strip()
        booker_notes = booker.get('notes', '').strip()
        source       = booker.get('source', 'DIRECT')

        if not booker_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập họ tên người đặt'}, status=400)
        if not booker_phone or not re.match(r'^0\d{9}$', booker_phone):
            return JsonResponse({'success': False, 'error': 'Số điện thoại người đặt không hợp lệ (phải có 10 số và bắt đầu bằng 0)'}, status=400)
        if booker_email:
            import re as _re
            if not _re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', booker_email):
                return JsonResponse({'success': False, 'error': 'Email không hợp lệ'}, status=400)

        valid_sources = {'DIRECT', 'ONLINE', 'PHONE', 'FACEBOOK', 'ZALO'}
        if source not in valid_sources:
            source = 'DIRECT'

        # Xác định booking status:
        # - Admin tạo/rebook (fromAdmin=True hoặc source != ONLINE) → CONFIRMED
        # - Khách đặt online → PENDING (cần xác nhận)
        from_admin = bool(booker.get('fromAdmin', False))
        # Nếu admin tạo mà source vô tình là ONLINE → đổi về DIRECT để tránh hiển thị sai
        if from_admin and source == 'ONLINE':
            source = 'DIRECT'
        booking_status = 'CONFIRMED' if (from_admin or source != 'ONLINE') else 'PENDING'

        # Lay pay_status chung tu booker (hoac tu guest dau tien)
        booking_pay_status = booker.get('payStatus', 'UNPAID') or 'UNPAID'
        valid_pay = {'UNPAID', 'PARTIAL', 'PAID', 'REFUNDED'}
        if booking_pay_status not in valid_pay:
            booking_pay_status = 'UNPAID'

        created_appts = []
        errors = []

        # Validate tat ca guests truoc
        validated_guests = []
        for idx, g in enumerate(guests):
            label = f"Khach {idx + 1}"
            data = {
                'customer_name': g.get('name', '').strip(),
                'phone':         ''.join(filter(str.isdigit, g.get('phone', ''))),
                'email':         g.get('email', '').strip(),
                'service_id':    g.get('serviceId'),   # để validate "chọn dịch vụ nhưng chưa chọn gói"
                'variant_id':    g.get('variantId'),
                'room_id':       g.get('roomId'),
                'date_str':      g.get('date', ''),
                'time_str':      g.get('time', ''),
                'status':        g.get('apptStatus', 'NOT_ARRIVED'),
            }
            validation = _validate_appointment_data(data)
            if not validation['valid']:
                errors.append(f"{label}: {validation['errors'][0]}")
                continue
            validated_guests.append((idx, g, validation['cleaned_data']))

        if not validated_guests and errors:
            return JsonResponse({'success': False, 'error': '; '.join(errors)}, status=400)

        # V-11: Cross-guest conflict check — không cho 2 khách cùng phòng cùng giờ overlap
        if len(validated_guests) > 1:
            from datetime import datetime as _dt, timedelta as _td, date as _date
            def _to_minutes(t):
                """Chuyển time object sang số phút từ 00:00."""
                return t.hour * 60 + t.minute

            for i in range(len(validated_guests)):
                for j in range(i + 1, len(validated_guests)):
                    _, _, ci = validated_guests[i]
                    _, _, cj = validated_guests[j]
                    room_i = ci.get('room')
                    room_j = cj.get('room')
                    if not room_i or not room_j:
                        continue
                    if room_i.code != room_j.code:
                        continue
                    # Cùng phòng — check ngày
                    date_i = ci.get('appointment_date')
                    date_j = cj.get('appointment_date')
                    if date_i != date_j:
                        continue
                    # Cùng ngày — check giờ overlap
                    time_i = ci.get('appointment_time')
                    time_j = cj.get('appointment_time')
                    dur_i  = ci.get('duration_minutes', 60)
                    dur_j  = cj.get('duration_minutes', 60)
                    if not time_i or not time_j:
                        continue
                    start_i = _to_minutes(time_i)
                    end_i   = start_i + dur_i
                    start_j = _to_minutes(time_j)
                    end_j   = start_j + dur_j
                    if start_i < end_j and start_j < end_i:
                        return JsonResponse(
                            {
                                'success': False,
                                'error': (
                                    f'Khách {i+1} và Khách {j+1} trùng phòng và thời gian. '
                                    'Các khách trong cùng lịch hẹn không được trùng phòng và thời gian.'
                                ),
                            },
                            status=400,
                        )

        # Validate payment chung
        g_payment_data = {
            'payment_method': booker.get('paymentMethod', ''),
            'amount':         booker.get('paymentAmount', 0),
            'recorded_no':    booker.get('paymentRecordedNo', ''),
            'note':           booker.get('paymentNote', ''),
        }
        if validated_guests:
            total_price = sum(_get_variant_price(c.get('service_variant')) for _, _, c in validated_guests)
            pay_valid, pay_error = _validate_payment_data(booking_pay_status, g_payment_data, total_price)
            if not pay_valid:
                return JsonResponse({'success': False, 'error': pay_error}, status=400)

        with transaction.atomic():
            # Tao Booking
            booking = Booking.objects.create(
                booker_name=booker_name,
                booker_phone=booker_phone,
                booker_email=booker_email or None,
                booker_notes=booker_notes or None,
                status=booking_status,
                payment_status=booking_pay_status,
                source=source,
                created_by=request.user,
            )

            for idx, g, cleaned in validated_guests:
                label = f"Khach {idx + 1}"
                customer_id  = g.get('customerId')
                guest_phone  = cleaned.get('phone') or ''
                guest_email  = cleaned.get('email') or ''
                guest_name   = cleaned.get('customer_name', '')

                customer = None
                try:
                    if customer_id:
                        customer = CustomerProfile.objects.get(id=customer_id)
                    elif guest_phone or guest_email:
                        customer = _resolve_or_create_customer(
                            phone=guest_phone, email=guest_email, customer_name=guest_name,
                        )
                except CustomerProfile.DoesNotExist:
                    errors.append(f"{label}: Không tìm thấy khách hàng")
                    continue
                except Exception as e:
                    errors.append(f"{label}: Lỗi xác định khách hàng - {str(e)}")
                    continue

                try:
                    appt_status_val = cleaned['status']
                    if appt_status_val == 'COMPLETED' and booking_pay_status not in ('PAID',):
                        errors.append(f"{label}: Không thể hoàn thành lịch khi chưa thanh toán đủ")
                        continue
                    # Validate thời điểm chuyển trạng thái
                    timing_ok, timing_err = _validate_status_timing(
                        cleaned['appointment_date'], cleaned['appointment_time'],
                        cleaned['duration_minutes'], appt_status_val
                    )
                    if not timing_ok:
                        errors.append(f"{label}: {timing_err}")
                        continue
                    appt = Appointment.objects.create(
                        booking=booking,
                        customer=customer,
                        service_variant=cleaned.get('service_variant'),
                        room=cleaned['room'],
                        customer_name_snapshot=cleaned['customer_name'],
                        customer_phone_snapshot=cleaned.get('phone'),
                        customer_email_snapshot=g.get('email', '').strip() or None,
                        appointment_date=cleaned['appointment_date'],
                        appointment_time=cleaned['appointment_time'],
                        status=appt_status_val,
                    )
                    created_appts.append(appt)
                except Exception as e:
                    errors.append(f"{label}: {str(e)}")

            if not created_appts:
                raise Exception('; '.join(errors) or 'Không tạo được lịch hẹn nào')

            # Tao Invoice cho toan bo Booking
            _create_invoice_and_payment(booking, created_appts, booking_pay_status, g_payment_data, request.user)

            # Cap nhat booking status neu co appt duoc tao
            if booking_pay_status != 'UNPAID':
                booking.payment_status = booking_pay_status
                booking.save(update_fields=['payment_status'])

        return JsonResponse({
            'success': True,
            'message': f'Đã tạo {len(created_appts)} lịch hẹn',
            'appointments': [serialize_appointment(a) for a in created_appts],
            'bookingCode': booking.booking_code,
            'errors': errors,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e) or 'Không thể tạo lịch hẹn. Vui lòng thử lại sau'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """
    [TAB 1] POST /api/appointments/<code>/update/
    Cap nhat thong tin lich hen va/hoac thong tin Booking.
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    booking = appointment.booking

    if appointment.status == 'CANCELLED':
        return JsonResponse(
            {'success': False, 'error': 'Không thể sửa lịch đã hủy. Hãy dùng chức năng "Đặt lại".'},
            status=400
        )
    if appointment.status == 'COMPLETED':
        return JsonResponse(
            {'success': False, 'error': 'Không thể chỉnh sửa lịch hẹn đã hoàn thành'},
            status=400
        )

    # Chặn sửa khi booking đã CANCELLED hoặc REJECTED
    if booking and booking.status in ('CANCELLED', 'REJECTED'):
        return JsonResponse(
            {'success': False, 'error': f'Không thể sửa lịch hẹn thuộc booking đã {booking.get_status_display().lower()}.'},
            status=400
        )

    try:
        raw_data = json.loads(request.body)

        # Booker fields (cap nhat Booking)
        new_booker_name  = raw_data.get('bookerName', '').strip()
        new_booker_phone = raw_data.get('bookerPhone', '').strip()
        new_booker_email = raw_data.get('bookerEmail', '').strip()
        new_booker_notes = raw_data.get('note', '') or raw_data.get('bookerNotes', '')

        # Appointment fields
        new_customer_name = raw_data.get('customerName', '').strip()
        new_phone         = raw_data.get('phone', '').strip()
        new_variant_id    = raw_data.get('variantId')
        new_room_id       = raw_data.get('roomId')
        new_date_str      = raw_data.get('date', '')
        new_time_str      = raw_data.get('time', '')

        raw_status     = raw_data.get('apptStatus') or raw_data.get('status')
        new_appt_status = str(raw_status).strip().upper() if raw_status else ''
        # BUG-05: payment_status chỉ được thay đổi qua invoice API, không qua update endpoint
        # Bỏ qua hoàn toàn payStatus / payment_status từ request body

        valid_appt_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
        if new_appt_status and new_appt_status not in valid_appt_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)

        # Validate ngay/gio/phong neu co thay doi
        # datetime_changed: True khi admin thực sự đổi ngày HOẶC giờ → mới check giờ quá khứ
        # needs_validation:  True khi cần check trùng phòng (đổi phòng/ngày/giờ/variant)
        needs_validation = False
        datetime_changed = False
        validation_data = {
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'duration_minutes': _get_appt_duration(appointment),
            'room_code': appointment.room.code if appointment.room_id else None,
        }

        if new_date_str:
            try:
                parsed_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                if parsed_date != appointment.appointment_date:
                    datetime_changed = True
                validation_data['appointment_date'] = parsed_date
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng ngày không hợp lệ'}, status=400)

        if new_time_str:
            try:
                parsed_time = datetime.strptime(new_time_str, '%H:%M').time()
                if parsed_time != appointment.appointment_time:
                    datetime_changed = True
                validation_data['appointment_time'] = parsed_time
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng giờ không hợp lệ'}, status=400)

        if new_room_id is not None:
            validation_data['room_code'] = new_room_id if new_room_id else None
            needs_validation = True

        if new_variant_id:
            try:
                variant = ServiceVariant.objects.get(id=new_variant_id)
                validation_data['duration_minutes'] = variant.duration_minutes
                needs_validation = True
            except ServiceVariant.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gói dịch vụ không tồn tại'}, status=404)

        if needs_validation:
            # is_staff_confirm=True khi không đổi ngày/giờ → bỏ qua check giờ quá khứ
            result = validate_appointment_create(
                appointment_date=validation_data['appointment_date'],
                appointment_time=validation_data['appointment_time'],
                duration_minutes=validation_data['duration_minutes'],
                room_code=validation_data['room_code'],
                exclude_appointment_code=appointment_code,
                is_staff_confirm=(not datetime_changed),
            )
            if not result['valid']:
                return JsonResponse({'success': False, 'error': result['errors'][0]}, status=400)

        with transaction.atomic():
            locked_appt = Appointment.objects.select_for_update().get(
                appointment_code=appointment_code, deleted_at__isnull=True
            )
            locked_booking = Booking.objects.select_for_update().get(pk=locked_appt.booking_id)

            # Cap nhat Booking (booker info)
            if new_booker_name:
                locked_booking.booker_name = new_booker_name
            if new_booker_phone:
                phone_digits = ''.join(filter(str.isdigit, new_booker_phone))
                if not re.match(r'^0\d{9}$', phone_digits):
                    return JsonResponse({'success': False, 'error': 'Số điện thoại người đặt không hợp lệ (phải có 10 số và bắt đầu bằng 0)'}, status=400)
                locked_booking.booker_phone = phone_digits
            if 'bookerEmail' in raw_data:
                locked_booking.booker_email = new_booker_email or None
            if new_booker_notes:
                locked_booking.booker_notes = new_booker_notes
            locked_booking.save()

            # Cap nhat Appointment — snapshot fields
            if new_customer_name:
                locked_appt.customer_name_snapshot = new_customer_name
            if 'phone' in raw_data:
                phone_digits = ''.join(filter(str.isdigit, new_phone))
                if phone_digits and not re.match(r'^0\d{9}$', phone_digits):
                    return JsonResponse({'success': False, 'error': 'Số điện thoại khách không hợp lệ (phải có 10 số và bắt đầu bằng 0)'}, status=400)
                locked_appt.customer_phone_snapshot = phone_digits or None
            if 'email' in raw_data:
                locked_appt.customer_email_snapshot = raw_data.get('email', '').strip() or None

            # Resolve CustomerProfile (KHÔNG tạo mới trong edit)
            # Ưu tiên: customerId > phone > giữ nguyên
            new_customer_id = raw_data.get('customerId')
            if new_customer_id:
                # Có customerId → giữ nguyên FK (đã đúng profile)
                try:
                    locked_appt.customer = CustomerProfile.objects.get(id=int(new_customer_id))
                except (CustomerProfile.DoesNotExist, ValueError, TypeError):
                    pass  # Không tìm thấy → giữ nguyên customer cũ
            elif 'phone' in raw_data:
                phone_digits_for_resolve = ''.join(filter(str.isdigit, new_phone))
                if phone_digits_for_resolve and len(phone_digits_for_resolve) >= 10:
                    # Có phone → tìm profile theo phone, KHÔNG tạo mới
                    try:
                        locked_appt.customer = CustomerProfile.objects.get(phone=phone_digits_for_resolve)
                    except CustomerProfile.DoesNotExist:
                        locked_appt.customer = None  # Không tìm thấy → để null
                elif not phone_digits_for_resolve:
                    # Phone bị xóa → unlink customer
                    locked_appt.customer = None

            if new_variant_id:
                try:
                    locked_appt.service_variant = ServiceVariant.objects.get(id=new_variant_id)
                except ServiceVariant.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Gói dịch vụ không tồn tại'}, status=404)
            elif 'variantId' in raw_data and not new_variant_id:
                locked_appt.service_variant = None

            if new_room_id is not None:
                if new_room_id:
                    try:
                        locked_appt.room = Room.objects.get(code=new_room_id)
                    except Room.DoesNotExist:
                        return JsonResponse({'success': False, 'error': 'Phòng không tồn tại'}, status=404)

            if new_date_str:
                locked_appt.appointment_date = validation_data['appointment_date']
            if new_time_str:
                locked_appt.appointment_time = validation_data['appointment_time']

            if new_appt_status:
                if new_appt_status == 'COMPLETED':
                    has_variant = new_variant_id or locked_appt.service_variant_id
                    if not has_variant:
                        return JsonResponse(
                            {'success': False, 'error': 'Không thể hoàn thành lịch hẹn khi chưa có dịch vụ'},
                            status=400
                        )
                    booking_pay = booking.payment_status if booking else 'UNPAID'
                    if booking_pay not in ('PAID',):
                        return JsonResponse(
                            {'success': False, 'error': 'Không thể hoàn thành lịch khi chưa thanh toán đủ'},
                            status=400
                        )
                # Validate thời điểm chuyển trạng thái
                appt_date_for_timing = validation_data['appointment_date']
                appt_time_for_timing = validation_data['appointment_time']
                dur_for_timing = validation_data['duration_minutes']
                timing_ok, timing_err = _validate_status_timing(
                    appt_date_for_timing, appt_time_for_timing, dur_for_timing, new_appt_status
                )
                if not timing_ok:
                    return JsonResponse({'success': False, 'error': timing_err}, status=400)
                locked_appt.status = new_appt_status

            locked_appt.save()

            # BUG-05: Không cập nhật payment_status tại đây.
            # payment_status chỉ được thay đổi qua invoice API (/invoice/pay/, /invoice/refund/).

        return JsonResponse({
            'success': True,
            'message': 'Cập nhật lịch hẹn thành công',
            'appointment': serialize_appointment(locked_appt)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@staff_api
def api_booking_update_batch(request, booking_code):
    """
    [TAB 1] POST /api/bookings/<booking_code>/update-batch/

    BUG-02: Cập nhật toàn bộ booking + tất cả appointments trong 1 transaction atomic.
    Nếu bất kỳ appointment nào fail → rollback toàn bộ.

    BUG-13: Mỗi appointment nhận apptStatus riêng (không dùng shared status nữa).

    Body JSON:
    {
        "bookerName":  "...",
        "bookerPhone": "...",
        "bookerEmail": "...",
        "bookerNotes": "...",
        "guests": [
            {
                "appointmentCode": "APP0001",
                "customerName":    "...",
                "phone":           "...",
                "email":           "...",
                "variantId":       1,
                "roomId":          "P01",
                "date":            "2026-05-01",   // chỉ gửi khi thay đổi
                "time":            "10:00",         // chỉ gửi khi thay đổi
                "apptStatus":      "ARRIVED",       // trạng thái riêng từng khách
                "customerId":      123
            },
            ...
        ]
    }
    """
    try:
        booking = Booking.objects.get(booking_code=booking_code, deleted_at__isnull=True)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy booking'}, status=404)

    # Chặn sửa khi booking đã CANCELLED hoặc REJECTED
    if booking.status in ('CANCELLED', 'REJECTED'):
        return JsonResponse(
            {'success': False, 'error': f'Không thể sửa booking đã {booking.get_status_display().lower()}.'},
            status=400
        )

    try:
        raw = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'}, status=400)

    guests = raw.get('guests', [])
    if not guests:
        return JsonResponse({'success': False, 'error': 'Không có dữ liệu khách để cập nhật'}, status=400)

    # ── Validate booker fields ────────────────────────────────────────────────
    new_booker_name  = raw.get('bookerName', '').strip()
    new_booker_phone = ''.join(filter(str.isdigit, raw.get('bookerPhone', '')))
    new_booker_email = raw.get('bookerEmail', '').strip()
    new_booker_notes = raw.get('bookerNotes', '').strip()

    if not new_booker_name:
        return JsonResponse({'success': False, 'error': 'Vui lòng nhập họ tên người đặt'}, status=400)
    if not new_booker_phone or not re.match(r'^0\d{9}$', new_booker_phone):
        return JsonResponse({'success': False, 'error': 'Số điện thoại người đặt không hợp lệ (phải có 10 số và bắt đầu bằng 0)'}, status=400)

    valid_appt_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}

    # ── Pre-validate tất cả guests trước khi vào transaction ─────────────────
    # Tránh rollback giữa chừng do lỗi validate đơn giản
    pre_errors = []
    for i, g in enumerate(guests):
        label = f'Khách {i + 1}: ' if len(guests) > 1 else ''
        appt_code = (g.get('appointmentCode') or '').strip()
        if not appt_code:
            pre_errors.append(f'{label}Thiếu mã lịch hẹn')
            continue

        # Validate apptStatus nếu có
        appt_status = (g.get('apptStatus') or '').strip().upper()
        if appt_status and appt_status not in valid_appt_statuses:
            pre_errors.append(f'{label}Trạng thái không hợp lệ ({appt_status})')

        # Validate phone nếu có
        phone = ''.join(filter(str.isdigit, g.get('phone', '')))
        if phone and not re.match(r'^0\d{9}$', phone):
            pre_errors.append(f'{label}Số điện thoại khách không hợp lệ (phải có 10 số và bắt đầu bằng 0)')

        # Validate email nếu có
        import re as _re
        email = g.get('email', '').strip()
        if email and not _re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            pre_errors.append(f'{label}Email không hợp lệ')

        # Validate service/variant: có serviceId nhưng không có variantId → lỗi
        service_id = g.get('serviceId') or g.get('service_id')
        variant_id = g.get('variantId') or g.get('variant_id')
        service_id = service_id if service_id else None
        variant_id = variant_id if variant_id else None
        if service_id and not variant_id:
            pre_errors.append(f'{label}Vui lòng chọn gói dịch vụ')

    if pre_errors:
        return JsonResponse({'success': False, 'error': pre_errors[0], 'errors': pre_errors}, status=400)

    # ── Thực hiện trong 1 transaction atomic ─────────────────────────────────
    try:
        with transaction.atomic():
            # Lock booking
            locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)

            # Cập nhật booker info
            locked_booking.booker_name  = new_booker_name
            locked_booking.booker_phone = new_booker_phone
            if 'bookerEmail' in raw:
                locked_booking.booker_email = new_booker_email or None
            if 'bookerNotes' in raw:
                locked_booking.booker_notes = new_booker_notes or None
            locked_booking.save(update_fields=['booker_name', 'booker_phone', 'booker_email', 'booker_notes', 'updated_at'])

            updated_appts = []

            for i, g in enumerate(guests):
                label = f'Khách {i + 1}: ' if len(guests) > 1 else ''
                appt_code = (g.get('appointmentCode') or '').strip()

                # Lock appointment — phải thuộc booking này
                try:
                    locked_appt = Appointment.objects.select_for_update().get(
                        appointment_code=appt_code,
                        booking=locked_booking,
                        deleted_at__isnull=True,
                    )
                except Appointment.DoesNotExist:
                    raise ValueError(f'{label}Không tìm thấy lịch hẹn {appt_code} trong booking này')

                if locked_appt.status == 'CANCELLED':
                    raise ValueError(f'{label}Không thể sửa lịch đã hủy')
                if locked_appt.status == 'COMPLETED':
                    raise ValueError(f'{label}Không thể sửa lịch đã hoàn thành')

                # ── Cập nhật snapshot fields ──────────────────────────────────
                new_name = g.get('customerName', '').strip()
                if new_name:
                    locked_appt.customer_name_snapshot = new_name

                phone = ''.join(filter(str.isdigit, g.get('phone', '')))
                if 'phone' in g:
                    locked_appt.customer_phone_snapshot = phone or None

                if 'email' in g:
                    locked_appt.customer_email_snapshot = g.get('email', '').strip() or None

                # ── Resolve CustomerProfile ───────────────────────────────────
                new_customer_id = g.get('customerId')
                if new_customer_id:
                    try:
                        locked_appt.customer = CustomerProfile.objects.get(id=int(new_customer_id))
                    except (CustomerProfile.DoesNotExist, ValueError, TypeError):
                        pass
                elif 'phone' in g:
                    if phone and len(phone) >= 10:
                        try:
                            locked_appt.customer = CustomerProfile.objects.get(phone=phone)
                        except CustomerProfile.DoesNotExist:
                            locked_appt.customer = None
                    elif not phone:
                        locked_appt.customer = None

                # ── Variant ───────────────────────────────────────────────────
                variant_id = g.get('variantId') or g.get('variant_id')
                variant_id = variant_id if variant_id else None
                if variant_id:
                    try:
                        locked_appt.service_variant = ServiceVariant.objects.get(id=variant_id)
                    except ServiceVariant.DoesNotExist:
                        raise ValueError(f'{label}Gói dịch vụ không tồn tại')
                elif 'variantId' in g and not variant_id:
                    locked_appt.service_variant = None

                # ── Room ──────────────────────────────────────────────────────
                new_room_id = g.get('roomId')
                if new_room_id is not None:
                    current_room_code = locked_appt.room.code if locked_appt.room_id else None
                    if new_room_id != current_room_code:
                        if new_room_id:
                            try:
                                locked_appt.room = Room.objects.get(code=new_room_id)
                            except Room.DoesNotExist:
                                raise ValueError(f'{label}Phòng không tồn tại')

                # ── Date / Time — validate nếu thay đổi ──────────────────────
                new_date_str = g.get('date', '')
                new_time_str = g.get('time', '')
                datetime_changed = False
                needs_validation = bool(new_date_str or new_time_str or new_room_id is not None or variant_id)

                current_date = locked_appt.appointment_date
                current_time = locked_appt.appointment_time
                val_date = current_date
                val_time = current_time
                val_duration = _get_appt_duration(locked_appt)
                val_room = locked_appt.room.code if locked_appt.room_id else None

                if new_date_str:
                    try:
                        parsed_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                        if parsed_date != current_date:
                            datetime_changed = True
                        val_date = parsed_date
                    except ValueError:
                        raise ValueError(f'{label}Định dạng ngày không hợp lệ')

                if new_time_str:
                    try:
                        parsed_time = datetime.strptime(new_time_str, '%H:%M').time()
                        if parsed_time != current_time:
                            datetime_changed = True
                        val_time = parsed_time
                    except ValueError:
                        raise ValueError(f'{label}Định dạng giờ không hợp lệ')

                if new_room_id is not None:
                    val_room = new_room_id if new_room_id else None

                # Cập nhật duration từ variant mới (nếu có) để validate đúng end time
                if variant_id:
                    try:
                        val_duration = ServiceVariant.objects.get(id=variant_id).duration_minutes
                    except Exception:
                        pass

                if needs_validation:
                    val_result = validate_appointment_create(
                        appointment_date=val_date,
                        appointment_time=val_time,
                        duration_minutes=val_duration,
                        room_code=val_room,
                        exclude_appointment_code=appt_code,
                        is_staff_confirm=(not datetime_changed),
                    )
                    if not val_result['valid']:
                        raise ValueError(f'{label}{val_result["errors"][0]}')

                if new_date_str:
                    locked_appt.appointment_date = val_date
                if new_time_str:
                    locked_appt.appointment_time = val_time

                # ── BUG-13: apptStatus riêng từng khách ──────────────────────
                appt_status = (g.get('apptStatus') or '').strip().upper()
                if appt_status and appt_status in valid_appt_statuses:
                    if appt_status == 'COMPLETED' and not locked_appt.service_variant_id:
                        raise ValueError(f'{label}Không thể hoàn thành khi chưa có dịch vụ')
                    if appt_status == 'COMPLETED' and locked_booking.payment_status not in ('PAID',):
                        raise ValueError(f'{label}Không thể hoàn thành lịch khi chưa thanh toán đủ')
                    # Validate thời điểm chuyển trạng thái
                    timing_ok, timing_err = _validate_status_timing(
                        val_date, val_time, val_duration, appt_status
                    )
                    if not timing_ok:
                        raise ValueError(f'{label}{timing_err}')
                    locked_appt.status = appt_status

                locked_appt.save()
                updated_appts.append(locked_appt)

        # Serialize kết quả sau transaction
        from .serializers import serialize_appointment as _sa
        return JsonResponse({
            'success':      True,
            'message':      f'Đã cập nhật {len(updated_appts)} lịch hẹn',
            'appointments': [_sa(a) for a in updated_appts],
            'bookingCode':  booking_code,
        })

    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@staff_api
def api_appointment_status(request, appointment_code):
    """
    [TAB 1+2] POST /api/appointments/<code>/status/
    Doi trang thai lich hen.
    Appointment.status: NOT_ARRIVED, ARRIVED, COMPLETED, CANCELLED
    Booking.status: PENDING, CONFIRMED, CANCELLED, REJECTED
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = str(data.get('status', '')).strip().upper()

        # Map status: frontend co the gui Booking status hoac Appointment status
        BOOKING_STATUSES = {'PENDING', 'CONFIRMED', 'CANCELLED', 'REJECTED'}
        APPT_STATUSES    = {'NOT_ARRIVED', 'ARRIVED', 'COMPLETED', 'CANCELLED'}

        booking = appointment.booking

        if new_status in BOOKING_STATUSES:
            # Doi Booking status
            if new_status == 'CONFIRMED':
                # Xac nhan: kiem tra trung lich cho tung appointment trong booking
                from .services import validate_appointment_create, _get_appt_duration
                all_appts = list(booking.appointments.filter(deleted_at__isnull=True))
                for appt_to_check in all_appts:
                    duration  = _get_appt_duration(appt_to_check)
                    room_code = appt_to_check.room.code if appt_to_check.room_id else None
                    validation = validate_appointment_create(
                        appointment_date=appt_to_check.appointment_date,
                        appointment_time=appt_to_check.appointment_time,
                        duration_minutes=duration,
                        room_code=room_code,
                        exclude_appointment_code=appt_to_check.appointment_code,
                        is_staff_confirm=True,
                    )
                    if not validation['valid']:
                        return JsonResponse({
                            'success': False,
                            'error': f'Lịch {appt_to_check.appointment_code}: {validation["errors"][0]}',
                            'conflict': True,
                        }, status=409)
                # Xac nhan OK: chuyen tat ca appointment chua hoan thanh sang NOT_ARRIVED
                booking.appointments.filter(
                    deleted_at__isnull=True
                ).exclude(status='COMPLETED').update(status='NOT_ARRIVED')

            if new_status == 'CANCELLED':
                from django.utils import timezone
                booking.cancelled_at = timezone.now()
                # Huy tat ca appointment chua hoan thanh
                booking.appointments.filter(
                    deleted_at__isnull=True
                ).exclude(status='COMPLETED').update(status='CANCELLED')

            booking.status = new_status
            booking.save(update_fields=['status', 'cancelled_at', 'updated_at'] if new_status == 'CANCELLED' else ['status', 'updated_at'])

            return JsonResponse({
                'success': True,
                'message': f'Đã cập nhật trạng thái đặt lịch: {booking.get_status_display()}'
            })

        elif new_status in APPT_STATUSES:
            # Doi Appointment status
            if new_status == 'COMPLETED':
                if not appointment.service_variant_id:
                    return JsonResponse({'success': False, 'error': 'Không thể hoàn thành khi chưa có dịch vụ'}, status=400)
                booking_pay = booking.payment_status if booking else 'UNPAID'
                if booking_pay not in ('PAID',):
                    return JsonResponse({'success': False, 'error': 'Không thể hoàn thành lịch khi chưa thanh toán đủ'}, status=400)

            # Validate thời điểm chuyển trạng thái
            duration = _get_appt_duration(appointment)
            timing_ok, timing_err = _validate_status_timing(
                appointment.appointment_date, appointment.appointment_time, duration, new_status
            )
            if not timing_ok:
                return JsonResponse({'success': False, 'error': timing_err}, status=400)

            appointment.status = new_status
            appointment.save(update_fields=['status', 'updated_at'])

            return JsonResponse({
                'success': True,
                'message': f'Đã cập nhật trạng thái: {appointment.get_status_display()}'
            })

        else:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "DELETE"])
@staff_api
def api_appointment_delete(request, appointment_code):
    """[TAB 1] POST /api/appointments/<code>/delete/ - Xoa mem lich hen."""
    from django.utils import timezone
    try:
        appointment = Appointment.objects.get(appointment_code=appointment_code, deleted_at__isnull=True)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    if not _is_staff(request.user):
        return _deny()

    if appointment.status == 'COMPLETED':
        return JsonResponse({'success': False, 'error': 'Không thể xóa lịch hẹn đã hoàn thành dịch vụ.'}, status=400)

    # BUG-04: Chặn xóa lịch đã thanh toán, thanh toán một phần, hoặc đã hoàn tiền
    booking_pay_status = ''
    if appointment.booking_id:
        try:
            booking_pay_status = appointment.booking.payment_status or ''
        except Exception:
            pass
    if booking_pay_status in ('PAID', 'PARTIAL', 'REFUNDED'):
        if booking_pay_status == 'PAID':
            err_msg = 'Không thể xóa lịch đã thanh toán. Vui lòng hoàn tiền trước nếu cần hủy.'
        elif booking_pay_status == 'PARTIAL':
            err_msg = 'Không thể xóa lịch khi booking đang có thanh toán một phần. Vui lòng hoàn tiền trước nếu cần hủy.'
        else:
            err_msg = 'Không thể xóa lịch đã hoàn tiền. Vui lòng giữ lại để đối soát.'
        return JsonResponse({'success': False, 'error': err_msg}, status=400)

    try:
        customer_name  = appointment.customer_name_snapshot or 'Khach hang'
        appointment_id = appointment.id
        appointment.deleted_at      = timezone.now()
        appointment.deleted_by_user = request.user
        appointment.save(update_fields=['deleted_at', 'deleted_by_user', 'updated_at'])
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa lịch hẹn',
            'deleted_id': appointment_id,
            'customer_name': customer_name
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Không thể xóa: {str(e)}'}, status=400)


# ============================================================
# SECTION 5: TAB 2 - YEU CAU DAT LICH (BOOKING REQUESTS)
# ============================================================

@require_http_methods(["GET"])
def api_booking_requests(request):
    """
    [TAB 2] GET /api/booking-requests/
    Danh sach yeu cau dat lich online (Booking.source=ONLINE, status PENDING/CANCELLED/REJECTED).
    """
    if not _is_staff(request.user):
        return _deny()

    # Base: Booking ONLINE chua xu ly hoac da xu ly
    bookings_qs = Booking.objects.filter(
        source='ONLINE',
        status__in=['PENDING', 'CANCELLED', 'REJECTED'],
        deleted_at__isnull=True,
    )

    if date_filter := request.GET.get('date'):
        bookings_qs = bookings_qs.filter(appointments__appointment_date=date_filter).distinct()
    if status_filter := request.GET.get('status', '').strip().upper():
        if status_filter in ('PENDING', 'CANCELLED', 'REJECTED'):
            bookings_qs = bookings_qs.filter(status=status_filter)
    if search := request.GET.get('q', '').strip():
        search_norm = ''.join(filter(str.isdigit, search))
        bookings_qs = bookings_qs.filter(
            Q(booking_code__icontains=search) |
            Q(booker_name__icontains=search) |
            Q(booker_phone__icontains=search_norm) |
            Q(appointments__appointment_code__icontains=search) |
            Q(appointments__customer_name_snapshot__icontains=search)
        ).distinct()
    if service_id := request.GET.get('service', '').strip():
        bookings_qs = bookings_qs.filter(appointments__service_variant__service_id=service_id).distinct()

    from django.db.models import Case, When, IntegerField
    bookings_qs = bookings_qs.order_by(
        Case(
            When(status='PENDING', then=0),
            When(status='CANCELLED', then=1),
            When(status='REJECTED', then=1),
            default=2,
            output_field=IntegerField()
        ),
        '-created_at'
    )

    # Lay tat ca appointments cua cac bookings nay
    booking_ids = list(bookings_qs.values_list('id', flat=True))
    appointments = Appointment.objects.filter(
        booking_id__in=booking_ids,
        deleted_at__isnull=True,
    ).select_related('booking', 'customer', 'service_variant__service', 'room').order_by(
        Case(
            When(booking__status='PENDING', then=0),
            When(booking__status='CANCELLED', then=1),
            When(booking__status='REJECTED', then=1),
            default=2,
            output_field=IntegerField()
        ),
        '-booking__created_at',
        'appointment_date',
        'appointment_time',
    )

    return JsonResponse({
        'success': True,
        'appointments': [serialize_appointment(a) for a in appointments]
    })


@require_http_methods(["POST"])
@staff_api
def api_confirm_online_request(request, booking_code):
    """
    [TAB 2] POST /api/booking-requests/<booking_code>/confirm/
    Xac nhan yeu cau dat lich online: cap nhat phong/gio/dich vu vao appointment goc
    roi confirm booking. KHONG tao Booking moi.

    Payload:
    {
      "guests": [{
        "name": "...", "phone": "...", "email": "...",
        "serviceId": ..., "variantId": ...,
        "roomId": "...", "date": "YYYY-MM-DD", "time": "HH:MM"
      }]
    }
    """
    try:
        booking = Booking.objects.get(
            booking_code=booking_code,
            source='ONLINE',
            status='PENDING',
            deleted_at__isnull=True,
        )
    except Booking.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Không tìm thấy yêu cầu đặt lịch hoặc đã được xử lý'},
            status=404,
        )

    try:
        raw = json.loads(request.body)
        guests = raw.get('guests', [])
        if not guests:
            return JsonResponse({'success': False, 'error': 'Vui lòng thêm ít nhất 1 khách'}, status=400)

        # Lay danh sach appointment hien tai cua booking goc (chua bi xoa)
        existing_appts = list(
            booking.appointments.filter(deleted_at__isnull=True).order_by('id')
        )

        # Validate tung guest — is_staff_confirm=True để cho phép ngày quá khứ
        validated = []
        for idx, g in enumerate(guests):
            label = f'Khách {idx + 1}: ' if len(guests) > 1 else ''
            data = {
                'customer_name': g.get('name', '').strip(),
                'phone':         ''.join(filter(str.isdigit, g.get('phone', ''))),
                'email':         g.get('email', '').strip(),
                'service_id':    g.get('serviceId'),
                'variant_id':    g.get('variantId'),
                'room_id':       g.get('roomId'),
                'date_str':      g.get('date', ''),
                'time_str':      g.get('time', ''),
                'status':        'NOT_ARRIVED',
                'is_staff_confirm': True,
            }
            result = _validate_appointment_data(data)
            if not result['valid']:
                return JsonResponse(
                    {'success': False, 'error': f'{label}{result["errors"][0]}',
                     'conflict': any('trùng' in e or 'đủ chỗ' in e or 'khả dụng' in e for e in result['errors'])},
                    status=409 if any('trùng' in e or 'đủ chỗ' in e for e in result['errors']) else 400,
                )
            validated.append((idx, g, result['cleaned_data']))

        with transaction.atomic():
            updated_appts = []

            for idx, g, cleaned in validated:
                if idx < len(existing_appts):
                    # Cap nhat appointment da co
                    appt = existing_appts[idx]
                    appt.service_variant        = cleaned.get('service_variant')
                    appt.room                   = cleaned['room']
                    appt.appointment_date       = cleaned['appointment_date']
                    appt.appointment_time       = cleaned['appointment_time']
                    appt.customer_name_snapshot = cleaned['customer_name']
                    appt.customer_phone_snapshot = cleaned.get('phone') or appt.customer_phone_snapshot
                    appt.customer_email_snapshot = (g.get('email', '').strip() or None) or appt.customer_email_snapshot
                    appt.status                 = 'NOT_ARRIVED'

                    # Resolve customer profile
                    phone = cleaned.get('phone') or ''
                    email = cleaned.get('email') or ''
                    cust_id = g.get('customerId')
                    if cust_id:
                        try:
                            appt.customer = CustomerProfile.objects.get(id=cust_id)
                        except CustomerProfile.DoesNotExist:
                            pass
                    elif phone or email:
                        try:
                            appt.customer = _resolve_or_create_customer(
                                phone=phone, email=email,
                                customer_name=cleaned['customer_name'],
                            )
                        except Exception:
                            pass

                    appt.save(update_fields=[
                        'service_variant', 'room', 'appointment_date', 'appointment_time',
                        'customer_name_snapshot', 'customer_phone_snapshot', 'customer_email_snapshot',
                        'status', 'customer', 'updated_at',
                    ])
                    updated_appts.append(appt)
                else:
                    # Tao them appointment moi neu guest nhieu hon appointment goc
                    phone = cleaned.get('phone') or ''
                    email = cleaned.get('email') or ''
                    cust_id = g.get('customerId')
                    customer = None
                    if cust_id:
                        try:
                            customer = CustomerProfile.objects.get(id=cust_id)
                        except CustomerProfile.DoesNotExist:
                            pass
                    elif phone or email:
                        try:
                            customer = _resolve_or_create_customer(
                                phone=phone, email=email,
                                customer_name=cleaned['customer_name'],
                            )
                        except Exception:
                            pass

                    appt = Appointment.objects.create(
                        booking=booking,
                        customer=customer,
                        service_variant=cleaned.get('service_variant'),
                        room=cleaned['room'],
                        customer_name_snapshot=cleaned['customer_name'],
                        customer_phone_snapshot=cleaned.get('phone'),
                        customer_email_snapshot=g.get('email', '').strip() or None,
                        appointment_date=cleaned['appointment_date'],
                        appointment_time=cleaned['appointment_time'],
                        status='NOT_ARRIVED',
                    )
                    updated_appts.append(appt)

            # Soft-delete cac appointment goc thua (neu guest it hon appointment goc)
            from django.utils import timezone as _tz
            for extra_appt in existing_appts[len(validated):]:
                extra_appt.deleted_at = _tz.now()
                extra_appt.deleted_by_user = request.user
                extra_appt.save(update_fields=['deleted_at', 'deleted_by_user'])

            # Tao/cap nhat Invoice cho booking — dùng get_or_create để tránh IntegrityError khi retry
            try:
                existing_invoice = booking.invoice
                # Invoice đã tồn tại → rebuild items theo appointments mới, giữ nguyên discount/payment
                existing_invoice.items.all().delete()
                subtotal = Decimal('0')
                for appt in updated_appts:
                    unit_price = _get_variant_price(appt.service_variant)
                    subtotal += unit_price
                    desc = ''
                    if appt.service_variant_id:
                        try:
                            sv = appt.service_variant
                            desc = f"{sv.service.name} — {sv.label}" if sv.service_id else sv.label or ''
                        except Exception:
                            pass
                    InvoiceItem.objects.create(
                        invoice=existing_invoice,
                        appointment=appt,
                        service_variant=appt.service_variant,
                        description=desc,
                        quantity=1,
                        unit_price=unit_price,
                        line_total=unit_price,
                    )
                existing_invoice.subtotal_amount = subtotal
                existing_invoice.final_amount = max(subtotal - existing_invoice.discount_amount, Decimal('0'))
                existing_invoice.save(update_fields=['subtotal_amount', 'final_amount'])
            except Invoice.DoesNotExist:
                # Invoice chưa có → tạo mới
                _create_invoice_and_payment(booking, updated_appts, 'UNPAID', {}, request.user)

            # Confirm booking
            booking.status = 'CONFIRMED'
            booking.save(update_fields=['status', 'updated_at'])

        return JsonResponse({
            'success': True,
            'message': 'Xác nhận yêu cầu đặt lịch thành công',
            'appointments': [serialize_appointment(a) for a in updated_appts],
            'bookingCode': booking.booking_code,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e) or 'Không thể xác nhận yêu cầu'}, status=400)


@require_http_methods(["GET"])
def api_booking_pending_count(request):
    """[TAB 2] GET /api/booking/pending-count/ - So luong booking dang cho xac nhan."""
    if not _is_staff(request.user):
        return _deny()
    try:
        from django.utils import timezone
        count = Booking.objects.filter(
            source='ONLINE',
            status='PENDING',
            deleted_at__isnull=True,
        ).count()
        return JsonResponse({'success': True, 'count': count, 'timestamp': timezone.now().isoformat()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Không thể lấy số lượng: {str(e)}', 'count': 0}, status=500)


# Alias backward compat
api_appointment_create = api_appointment_create_batch


@require_http_methods(["GET"])
def api_customer_cancelled_recent(request):
    """
    [TAB 2] GET /api/appointments/customer-cancelled-recent/
    Danh sach cac lich bi khach huy gan day (Booking.status=CANCELLED, source=ONLINE).
    """
    if not _is_staff(request.user):
        return _deny()

    from django.utils import timezone
    minutes = int(request.GET.get('minutes', 10))
    since   = timezone.now() - __import__('datetime').timedelta(minutes=minutes)

    bookings = Booking.objects.filter(
        source='ONLINE',
        status='CANCELLED',
        cancelled_at__gte=since,
        deleted_at__isnull=True,
    ).order_by('-cancelled_at')[:20]

    return JsonResponse({
        'success': True,
        'appointments': [
            {
                'code':         b.booking_code,
                'customerName': b.booker_name or 'Khach',
                'cancelledAt':  b.cancelled_at.isoformat() if b.cancelled_at else '',
            }
            for b in bookings
        ]
    })


# ============================================================
# SECTION 6: CUSTOMER NOTE UPDATE
# ============================================================

@require_http_methods(["POST"])
@staff_api
def api_customer_note_update(request, phone):
    """
    [SHARED] POST /api/customers/<phone>/note/
    Cập nhật ghi chú hồ sơ khách theo SĐT.

    Body JSON:
        { "note": "..." }

    Chỉ update field notes trên CustomerProfile.
    Không ảnh hưởng đến booking hay appointment.
    """
    phone_digits = ''.join(filter(str.isdigit, phone or ''))
    if not phone_digits or not re.match(r'^0\d{9}$', phone_digits):
        return JsonResponse({'success': False, 'error': 'Số điện thoại không hợp lệ (phải có 10 số và bắt đầu bằng 0)'}, status=400)

    try:
        raw = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'}, status=400)

    note = (raw.get('note') or '').strip()

    try:
        customer = CustomerProfile.objects.get(phone=phone_digits)
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy hồ sơ khách'}, status=404)

    customer.notes = note or None
    customer.save(update_fields=['notes', 'updated_at'])

    return JsonResponse({'success': True, 'message': 'Đã cập nhật ghi chú hồ sơ khách'})


@require_http_methods(["POST"])
@staff_api
def api_customer_note_update_by_id(request, customer_id):
    """
    [SHARED] POST /api/customers/id/<customer_id>/note/
    Cập nhật ghi chú hồ sơ khách theo ID (an toàn hơn theo phone).

    Body JSON:
        { "note": "..." }

    Chỉ update field notes trên CustomerProfile.
    Không ảnh hưởng đến booking hay appointment.
    """
    try:
        cid = int(customer_id)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'ID không hợp lệ'}, status=400)

    try:
        raw = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'}, status=400)

    note = (raw.get('note') or '').strip()

    try:
        customer = CustomerProfile.objects.get(id=cid)
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy hồ sơ khách'}, status=404)

    customer.notes = note or None
    customer.save(update_fields=['notes', 'updated_at'])

    return JsonResponse({'success': True, 'message': 'Đã cập nhật ghi chú hồ sơ khách'})
