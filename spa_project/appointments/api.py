"""
API Endpoints — Lịch hẹn (Organized by Tabs)

This file contains all appointment-related API endpoints, organized by their corresponding UI tabs:

- TAB 1: Lịch theo phòng (Room Calendar)
- TAB 2: Yêu cầu đặt lịch (Booking Requests)
- SHARED: Endpoints used by both tabs
"""

import json
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.db import transaction

from .models import Appointment, Room, Invoice, InvoicePayment
from customers.models import CustomerProfile
from spa_services.models import ServiceVariant

from .serializers import serialize_appointment
from .services import validate_appointment_create, _get_appt_duration
from core.api_response import staff_api, get_or_404


# ============================================================
# SECTION 1: IMPORTS & SETTINGS
# ============================================================
# All imports are defined above
# This section serves as documentation for module dependencies


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
    """Tìm hoặc tạo CustomerProfile theo SĐT."""
    from django.contrib.auth.models import User
    import secrets

    # Lookup qua CustomerProfile trước để tránh conflict username
    try:
        customer = CustomerProfile.objects.get(phone=phone)
        if customer_name and customer.full_name != customer_name:
            customer.full_name = customer_name
            customer.save()
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


def _create_invoice_and_payment(appointment, pay_status, payment_data, created_by):
    """Tạo Invoice + InvoicePayment."""
    subtotal = _get_variant_price(appointment.service_variant)
    discount = Decimal('0')
    final = subtotal - discount

    invoice = Invoice.objects.create(
        appointment=appointment,
        subtotal_amount=subtotal,
        discount_amount=discount,
        final_amount=final,
        status=pay_status,
        created_by=created_by,
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
    """Validate dữ liệu appointment trước khi tạo."""
    errors = []
    cleaned = {}

    # Tên khách (bắt buộc)
    customer_name = data.get('customer_name', '').strip()
    if not customer_name:
        errors.append('Vui lòng nhập tên khách')
    else:
        cleaned['customer_name'] = customer_name

    # SĐT khách (tuỳ chọn)
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    if phone and len(phone) < 10:
        errors.append('Số điện thoại khách không hợp lệ')
    else:
        cleaned['phone'] = phone or None

    # Dịch vụ (bắt buộc — phải có variant_id)
    variant_id = data.get('variant_id')
    if not variant_id:
        errors.append('Vui lòng chọn gói dịch vụ')
    else:
        try:
            variant = ServiceVariant.objects.get(id=variant_id)
            cleaned['service_variant'] = variant
        except ServiceVariant.DoesNotExist:
            errors.append('Gói dịch vụ không tồn tại')

    # Trạng thái
    status = str(data.get('status') or 'NOT_ARRIVED').strip().upper()
    valid_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
    if status not in valid_statuses:
        errors.append('Trạng thái không hợp lệ')
    cleaned['status'] = status

    # Ngày (bắt buộc — đến từ slot đã chọn)
    date_str = data.get('date_str', '')
    if not date_str:
        errors.append('Vui lòng chọn ngày hẹn')
    else:
        try:
            cleaned['appointment_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Định dạng ngày không hợp lệ')

    # Giờ (bắt buộc — đến từ slot đã chọn)
    time_str = data.get('time_str', '')
    if not time_str:
        errors.append('Vui lòng chọn giờ hẹn')
    else:
        try:
            cleaned['appointment_time'] = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            errors.append('Định dạng giờ không hợp lệ')

    # Duration từ variant hoặc fallback 60
    if 'service_variant' in cleaned:
        cleaned['duration_minutes'] = cleaned['service_variant'].duration_minutes
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

    # Ghi chú & thanh toán
    cleaned['notes'] = data.get('notes', '')
    cleaned['payment_status'] = data.get('pay_status', 'UNPAID')

    # Validate nâng cao: trùng lịch / sức chứa phòng
    if not errors and 'appointment_date' in cleaned and 'appointment_time' in cleaned:
        room_code = cleaned['room'].code if 'room' in cleaned else None
        validation_result = validate_appointment_create(
            appointment_date=cleaned['appointment_date'],
            appointment_time=cleaned['appointment_time'],
            duration_minutes=cleaned['duration_minutes'],
            room_code=room_code,
            exclude_appointment_code=None,
        )
        if not validation_result['valid']:
            # Map lỗi backend → message thân thiện theo đặc tả
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
# These endpoints are used by both TAB 1 (Room Calendar) and TAB 2 (Booking Requests)

@require_http_methods(["GET"])
def api_appointments_search(request):
    """
    [SHARED] GET /api/appointments/search/

    Tìm kiếm lịch hẹn toàn hệ thống.

    TAB: Used by both Room Calendar and Booking Requests
    Methods: GET

    Query params:
    - q: General search (name, phone, email, code)
    - name: Search by name only
    - code: Search by appointment code
    - phone: Search by phone number
    - email: Search by email
    - status: Filter by status
    - source: Filter by source (ONLINE, DIRECT)
    - service: Filter by service ID
    - room: Filter by room code
    - date_from: Filter by start date
    - date_to: Filter by end date

    Returns: Max 100 results, ordered by date/time desc
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

    # Bắt buộc ít nhất 1 điều kiện
    has_condition = any([q, name, code, phone, email, status, source, service_id, room_code, date_from, date_to])
    if not has_condition:
        return JsonResponse({'success': False, 'error': 'Vui lòng nhập ít nhất 1 điều kiện tìm kiếm'}, status=400)

    qs = Appointment.objects.filter(deleted_at__isnull=True)

    if q:
        qs = qs.filter(
            Q(customer_name_snapshot__icontains=q) |
            Q(booker_name__icontains=q) |
            Q(customer__full_name__icontains=q) |
            Q(customer_phone_snapshot__icontains=q) |
            Q(booker_phone__icontains=q) |
            Q(customer_email_snapshot__icontains=q) |
            Q(booker_email__icontains=q) |
            Q(appointment_code__icontains=q) |
            Q(customer__phone__icontains=q)
        )
    if name:
        # DB filter chỉ theo snapshot fields — không dùng customer__full_name
        # vì customer profile có thể khác với tên snapshot thực tế
        qs = qs.filter(
            Q(customer_name_snapshot__icontains=name) |
            Q(booker_name__icontains=name)
        )
    if code:
        qs = qs.filter(appointment_code__icontains=code)
    if phone:
        qs = qs.filter(
            Q(customer_phone_snapshot__icontains=phone) |
            Q(booker_phone__icontains=phone) |
            Q(customer__phone__icontains=phone)
        )
    if email:
        qs = qs.filter(
            Q(customer_email_snapshot__icontains=email) |
            Q(booker_email__icontains=email)
        )
    if status:
        qs = qs.filter(status=status)
    if source:
        qs = qs.filter(source=source)
    if service_id:
        qs = qs.filter(service_variant__service_id=service_id)
    if room_code:
        qs = qs.filter(room__code=room_code)
    if date_from:
        qs = qs.filter(appointment_date__gte=date_from)
    if date_to:
        qs = qs.filter(appointment_date__lte=date_to)

    results = list(qs.order_by('-appointment_date', '-appointment_time')[:100])

    # Filter Python cho tên — SQLite icontains không phân biệt dấu tiếng Việt
    # Chỉ filter theo snapshot fields, không dùng customer.full_name
    if name:
        name_lower = name.lower()
        results = [a for a in results if
                   name_lower in (a.customer_name_snapshot or '').lower() or
                   name_lower in (a.booker_name or '').lower()]

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
            {'id': c.id, 'fullName': c.full_name, 'phone': c.phone, 'email': c.user.email if c.user else ''}
            for c in customers
        ]
    })


@require_http_methods(["GET", "POST"])
@staff_api
def api_appointment_rebook(request, appointment_code):
    """
    [SHARED] GET/POST /api/appointments/<code>/rebook/

    GET: Trả về thông tin cần thiết để đặt lại lịch từ lịch đã hủy/từ chối
    POST: Đặt lại trạng thái về PENDING

    TAB: Used by both Room Calendar and Booking Requests
    Methods: GET, POST

    Business logic:
    - Only allows rebooking CANCELLED or REJECTED appointments
    - GET returns pre-fill data for form
    - POST changes status to PENDING
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    # Trả về thông tin cần thiết để FE pre-fill form tạo mới
    current_status = str(appointment.status or '').strip().upper()
    if current_status not in ('CANCELLED', 'REJECTED'):
        return JsonResponse(
            {
                'success': False,
                'error': 'Chỉ có thể đặt lại lịch đã hủy hoặc đã từ chối.',
                'currentStatus': appointment.status,
            },
            status=400,
        )

    if request.method == 'POST':
        appointment.status = 'PENDING'
        appointment.save(update_fields=['status', 'updated_at'])
        return JsonResponse({
            'success': True,
            'message': f'Đã đặt lại lịch hẹn {appointment.appointment_code} về trạng thái chờ xác nhận.',
            'appointment': serialize_appointment(appointment),
        })

    variant_available = False
    variant_warning = None
    if appointment.service_variant_id:
        try:
            sv = ServiceVariant.objects.get(id=appointment.service_variant_id)
            # Kiểm tra service còn active không
            if getattr(sv.service, 'status', 'ACTIVE') == 'ACTIVE':
                variant_available = True
            else:
                variant_warning = 'Dịch vụ/gói cũ không còn khả dụng, vui lòng chọn lại.'
        except ServiceVariant.DoesNotExist:
            variant_warning = 'Dịch vụ/gói cũ không còn khả dụng, vui lòng chọn lại.'

    return JsonResponse({
        'success': True,
        'rebook': {
            'bookerName':  appointment.booker_name,
            'bookerPhone': appointment.booker_phone,
            'bookerEmail': appointment.booker_email or '',
            'customerName': appointment.customer_name_snapshot,
            'customerPhone': appointment.customer_phone_snapshot or '',
            'customerEmail': appointment.customer_email_snapshot or '',
            'serviceId':   appointment.service_variant.service_id if variant_available else None,
            'variantId':   appointment.service_variant_id if variant_available else None,
            'notes':       appointment.notes or '',
            'source':      appointment.source or 'DIRECT',
            'variantWarning': variant_warning,
        }
    })


# ============================================================
# SECTION 4: TAB 1 - LỊCH THEO PHÒNG (ROOM CALENDAR)
# ============================================================
# These endpoints are specifically for the Room Calendar tab
# They handle room management and appointment CRUD operations

@require_http_methods(["GET"])
def api_rooms_list(request):
    """
    [TAB 1] GET /api/rooms/

    Danh sách tất cả phòng đang active.

    TAB: Room Calendar (Lịch theo phòng)
    Methods: GET

    Returns: List of rooms with id (code), name, capacity
    """
    if not _is_staff(request.user):
        return _deny()

    rooms = Room.objects.filter(is_active=True).order_by('code')
    return JsonResponse({
        'success': True,
        'rooms': [{'id': r.code, 'name': r.name, 'capacity': r.capacity} for r in rooms]
    })


@require_http_methods(["GET"])
def api_appointments_list(request):
    """
    [TAB 1] GET /api/appointments/

    Danh sách lịch hẹn với các bộ lọc.

    TAB: Room Calendar (Lịch theo phòng)
    Methods: GET

    Query params:
    - date: Filter by appointment date (YYYY-MM-DD)
    - status: Filter by status
    - source: Filter by source (ONLINE, DIRECT)
    - service: Filter by service ID
    - q: Search query (name, phone, email, code, notes)

    Returns: List of appointments ordered by date, time
    Excludes: ONLINE appointments with PENDING/CANCELLED/REJECTED status
    """
    if not _is_staff(request.user):
        return _deny()

    appointments = Appointment.objects.filter(deleted_at__isnull=True).exclude(
        source='ONLINE', status__in=['PENDING', 'CANCELLED', 'REJECTED']
    )

    # Filters
    if date_filter := request.GET.get('date'):
        appointments = appointments.filter(appointment_date=date_filter)
    if status_filter := request.GET.get('status', '').strip().upper():
        appointments = appointments.filter(status=status_filter)
    if source_filter := request.GET.get('source'):
        appointments = appointments.filter(source=source_filter)
    # Filter theo dịch vụ — qua service_variant__service_id
    if service_filter := request.GET.get('service'):
        appointments = appointments.filter(service_variant__service_id=service_filter)
    if search := request.GET.get('q', '').strip():
        appointments = appointments.filter(
            Q(customer_name_snapshot__icontains=search) |
            Q(customer_phone_snapshot__icontains=search) |
            Q(customer_email_snapshot__icontains=search) |
            Q(booker_name__icontains=search) |
            Q(booker_phone__icontains=search) |
            Q(appointment_code__icontains=search) |
            Q(notes__icontains=search) |
            Q(staff_notes__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search)
        )

    appointments = appointments.order_by('appointment_date', 'appointment_time')
    return JsonResponse({'success': True, 'appointments': [serialize_appointment(a) for a in appointments]})


@require_http_methods(["GET"])
def api_appointment_detail(request, appointment_code):
    """
    [TAB 1] GET /api/appointments/<code>/

    Chi tiết một lịch hẹn theo code.

    TAB: Room Calendar (Lịch theo phòng)
    Methods: GET

    Returns: Full appointment details
    """
    if not _is_staff(request.user):
        return _deny()

    try:
        appt = Appointment.objects.get(appointment_code=appointment_code, deleted_at__isnull=True)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    return JsonResponse({'success': True, 'appointment': serialize_appointment(appt)})


@require_http_methods(["POST"])
@staff_api
def api_appointment_create_batch(request):
    """
    [TAB 1] POST /api/appointments/create-batch/

    Tạo nhiều lịch hẹn cùng lúc (1 người đặt, nhiều khách).

    TAB: Room Calendar (Lịch theo phòng)
    Methods: POST

    Request body:
    {
        "booker": {
            "name": "Người đặt",
            "phone": "0123456789",
            "email": "email@example.com",
            "source": "DIRECT" // optional, default "DIRECT"
        },
        "guests": [
            {
                "name": "Khách 1",
                "phone": "0123456789",
                "email": "guest1@example.com",
                "variantId": 1,
                "roomId": "P001",
                "date": "2024-01-01",
                "time": "10:00",
                "note": "Ghi chú",
                "apptStatus": "NOT_ARRIVED",
                "payStatus": "UNPAID",
                "paymentMethod": "CASH",
                "paymentAmount": 0,
                "customerId": null // optional
            },
            // ... more guests
        ]
    }

    Returns: Created appointments with any errors
    """
    try:
        raw = json.loads(request.body)
        booker = raw.get('booker', {})
        guests = raw.get('guests', [])

        if not guests:
            return JsonResponse({'success': False, 'error': 'Vui lòng thêm ít nhất 1 khách'}, status=400)

        booker_name = booker.get('name', '').strip()
        booker_phone = ''.join(filter(str.isdigit, booker.get('phone', '')))
        booker_email = booker.get('email', '').strip()
        source = booker.get('source', 'DIRECT')

        if not booker_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập họ tên người đặt'}, status=400)
        if not booker_phone or len(booker_phone) < 9:
            return JsonResponse({'success': False, 'error': 'Số điện thoại không hợp lệ'}, status=400)

        created = []
        errors = []

        for idx, g in enumerate(guests):
            label = f"Khách {idx + 1}"
            data = {
                'customer_name': g.get('name', '').strip(),
                'phone': ''.join(filter(str.isdigit, g.get('phone', ''))),
                'variant_id': g.get('variantId'),
                'room_id': g.get('roomId'),
                'date_str': g.get('date', ''),
                'time_str': g.get('time', ''),
                'notes': g.get('note', ''),
                'status': g.get('apptStatus', 'NOT_ARRIVED'),
                'pay_status': g.get('payStatus', 'UNPAID'),
            }

            validation = _validate_appointment_data(data)
            if not validation['valid']:
                errors.append(f"{label}: {validation['errors'][0]}")
                continue

            cleaned = validation['cleaned_data']

            # Validate payment
            g_pay_status = cleaned['payment_status']
            g_payment_data = {
                'payment_method': g.get('paymentMethod', ''),
                'amount': g.get('paymentAmount', 0),
                'recorded_no': g.get('paymentRecordedNo', ''),
                'note': g.get('paymentNote', ''),
            }
            temp_price = _get_variant_price(cleaned.get('service_variant'))
            pay_valid, pay_error = _validate_payment_data(g_pay_status, g_payment_data, temp_price)
            if not pay_valid:
                errors.append(f"{label}: {pay_error}")
                continue

            # Resolve customer
            customer_id = g.get('customerId')
            guest_phone = cleaned.get('phone') or ''
            guest_name = cleaned.get('customer_name', '')

            try:
                if customer_id:
                    customer = CustomerProfile.objects.get(id=customer_id)
                elif guest_phone:
                    try:
                        customer = CustomerProfile.objects.get(phone=guest_phone)
                    except CustomerProfile.DoesNotExist:
                        customer = _get_or_create_customer(guest_phone, guest_name)
                else:
                    # Không có SĐT → dùng SĐT người đặt
                    try:
                        customer = CustomerProfile.objects.get(phone=booker_phone)
                    except CustomerProfile.DoesNotExist:
                        customer = _get_or_create_customer(booker_phone, guest_name or booker_name)
            except CustomerProfile.DoesNotExist:
                errors.append(f"{label}: Không tìm thấy khách hàng")
                continue

            try:
                with transaction.atomic():
                    appt = Appointment.objects.create(
                        customer=customer,
                        service_variant=cleaned.get('service_variant'),
                        room=cleaned['room'],
                        booker_name=booker_name,
                        booker_phone=booker_phone,
                        booker_email=booker_email or None,
                        customer_name_snapshot=cleaned['customer_name'],
                        customer_phone_snapshot=cleaned.get('phone'),
                        customer_email_snapshot=g.get('email', '').strip() or None,
                        appointment_date=cleaned['appointment_date'],
                        appointment_time=cleaned['appointment_time'],
                        notes=cleaned['notes'],
                        status=cleaned['status'],
                        payment_status=cleaned['payment_status'],
                        source=source,
                        staff_notes=g.get('staffNote', '').strip(),
                        created_by=request.user,
                    )
                    _create_invoice_and_payment(appt, cleaned['payment_status'], g_payment_data, request.user)
                    created.append(serialize_appointment(appt))
            except Exception as e:
                errors.append(f"{label}: {str(e)}")

        if not created:
            return JsonResponse({'success': False, 'error': '; '.join(errors) or 'Không tạo được lịch hẹn nào'}, status=400)

        return JsonResponse({
            'success': True,
            'message': f'Đã tạo {len(created)} lịch hẹn' + (f' ({len(errors)} lỗi)' if errors else ''),
            'appointments': created,
            'errors': errors,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Không thể tạo lịch hẹn. Vui lòng thử lại sau'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """
    [TAB 1] POST/PUT /api/appointments/<code>/update/

    Cập nhật thông tin lịch hẹn.

    TAB: Room Calendar (Lịch theo phòng)
    Methods: POST, PUT

    Request body:
    {
        "bookerName": "Người đặt",
        "bookerPhone": "0123456789",
        "bookerEmail": "email@example.com",
        "customerName": "Khách hàng",
        "phone": "0123456789",
        "email": "customer@example.com",
        "variantId": 1,
        "roomId": "P001",
        "date": "2024-01-01",
        "time": "10:00",
        "note": "Ghi chú",
        "staffNote": "Ghi chú nội bộ",
        "apptStatus": "NOT_ARRIVED",
        "payStatus": "UNPAID",
        "paymentData": {
            "payment_method": "CASH",
            "amount": 100000,
            "recorded_no": "",
            "note": ""
        }
    }

    Business rules:
    - Cannot update CANCELLED or REJECTED appointments (use rebook instead)
    - Validates room availability, date/time conflicts
    - Syncs payment status with invoice

    Returns: Updated appointment details
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    # Chặn sửa trực tiếp lịch đã hủy hoặc đã từ chối
    if appointment.status in ('CANCELLED', 'REJECTED'):
        return JsonResponse(
            {'success': False, 'error': 'Không thể sửa lịch đã hủy/từ chối. Hãy dùng chức năng "Đặt lại" để tạo lịch mới.'},
            status=400
        )

    try:
        raw_data = json.loads(request.body)

        # Thu thập data mới
        new_booker_name = raw_data.get('bookerName', '').strip()
        new_booker_phone = raw_data.get('bookerPhone', '').strip()
        new_booker_email = raw_data.get('bookerEmail', '').strip()
        new_customer_name = raw_data.get('customerName', '').strip()
        new_phone = raw_data.get('phone', '').strip()
        new_variant_id = raw_data.get('variantId')
        new_room_id = raw_data.get('roomId')
        new_date_str = raw_data.get('date', '')
        new_time_str = raw_data.get('time', '')
        new_notes = raw_data.get('note', '')
        raw_status = raw_data.get('apptStatus') or raw_data.get('status')
        new_status = str(raw_status).strip().upper() if raw_status else ''
        new_pay_status = raw_data.get('payStatus') or raw_data.get('payment_status')

        valid_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
        valid_pay_statuses = {choice[0] for choice in Appointment.PAYMENT_STATUS_CHOICES}
        if new_status and new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)
        if new_pay_status and new_pay_status not in valid_pay_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái thanh toán không hợp lệ'}, status=400)

        # Validate ngày/giờ/phòng nếu có thay đổi
        needs_validation = False
        validation_data = {
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'duration_minutes': _get_appt_duration(appointment),
            'room_code': appointment.room.code if appointment.room_id else None,
        }

        if new_date_str:
            try:
                validation_data['appointment_date'] = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng ngày không hợp lệ'}, status=400)

        if new_time_str:
            try:
                validation_data['appointment_time'] = datetime.strptime(new_time_str, '%H:%M').time()
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng giờ không hợp lệ'}, status=400)

        if new_room_id is not None:
            validation_data['room_code'] = new_room_id if new_room_id else None
            needs_validation = True

        # Nếu đổi variant → cập nhật duration
        if new_variant_id:
            try:
                variant = ServiceVariant.objects.get(id=new_variant_id)
                validation_data['duration_minutes'] = variant.duration_minutes
                needs_validation = True
            except ServiceVariant.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Gói dịch vụ không tồn tại'}, status=404)

        if needs_validation:
            result = validate_appointment_create(
                appointment_date=validation_data['appointment_date'],
                appointment_time=validation_data['appointment_time'],
                duration_minutes=validation_data['duration_minutes'],
                room_code=validation_data['room_code'],
                exclude_appointment_code=appointment_code,
            )
            if not result['valid']:
                return JsonResponse({'success': False, 'error': result['errors'][0]}, status=400)

        # UPDATE với transaction
        with transaction.atomic():
            locked = Appointment.objects.select_for_update().get(
                appointment_code=appointment_code, deleted_at__isnull=True
            )

            # Booker
            if new_booker_name:
                locked.booker_name = new_booker_name
            if new_booker_phone:
                locked.booker_phone = ''.join(filter(str.isdigit, new_booker_phone))
            if 'bookerEmail' in raw_data:
                locked.booker_email = new_booker_email or None

            # Customer snapshot
            if new_customer_name:
                locked.customer_name_snapshot = new_customer_name
            if 'phone' in raw_data:
                phone_digits = ''.join(filter(str.isdigit, new_phone))
                locked.customer_phone_snapshot = phone_digits or None
            if 'email' in raw_data:
                locked.customer_email_snapshot = raw_data.get('email', '').strip() or None

            # Variant
            if new_variant_id:
                try:
                    locked.service_variant = ServiceVariant.objects.get(id=new_variant_id)
                except ServiceVariant.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Gói dịch vụ không tồn tại'}, status=404)
            elif 'variantId' in raw_data and not new_variant_id:
                locked.service_variant = None

            # Phòng
            if new_room_id is not None:
                if new_room_id:
                    try:
                        locked.room = Room.objects.get(code=new_room_id)
                    except Room.DoesNotExist:
                        return JsonResponse({'success': False, 'error': 'Phòng không tồn tại'}, status=404)

            # Ngày giờ
            if new_date_str:
                locked.appointment_date = validation_data['appointment_date']
            if new_time_str:
                locked.appointment_time = validation_data['appointment_time']

            # Trạng thái
            if new_status:
                if new_status == 'COMPLETED' and not locked.service_variant_id:
                    return JsonResponse({'success': False, 'error': 'Phải chọn gói dịch vụ trước khi hoàn tất'}, status=400)
                locked.status = new_status
                if new_status == 'CANCELLED':
                    locked.cancelled_by = 'admin'
            if new_pay_status:
                locked.payment_status = new_pay_status
                # Đồng bộ invoice.status với payment_status
                try:
                    inv = locked.invoice
                    if inv.status != new_pay_status:
                        inv.status = new_pay_status
                        # Nếu chuyển sang PAID và chưa có payment record → tạo tự động
                        if new_pay_status == 'PAID' and not inv.payments.filter(transaction_status='SUCCESS').exists():
                            payment_data = raw_data.get('paymentData', {})
                            InvoicePayment.objects.create(
                                invoice=inv,
                                amount=inv.final_amount,
                                payment_method=payment_data.get('payment_method', 'CASH'),
                                transaction_status='SUCCESS',
                                recorded_by=request.user,
                                recorded_no=payment_data.get('recorded_no', '') or None,
                                note=payment_data.get('note', '') or None,
                            )
                        inv.save()
                except Invoice.DoesNotExist:
                    # Chưa có invoice → tạo mới
                    _create_invoice_and_payment(locked, new_pay_status, raw_data.get('paymentData', {}), request.user)

            # Ghi chú
            if new_notes:
                locked.notes = new_notes
            if 'staffNote' in raw_data:
                locked.staff_notes = raw_data.get('staffNote', '').strip()

            locked.save()

        return JsonResponse({
            'success': True,
            'message': f'Cập nhật lịch hẹn {appointment_code} thành công',
            'appointment': serialize_appointment(locked)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@staff_api
def api_appointment_status(request, appointment_code):
    """
    [TAB 1] POST /api/appointments/<code>/status/

    Đổi trạng thái lịch hẹn.

    TAB: Room Calendar (Lịch theo phòng)
    Methods: POST

    Request body:
    {
        "status": "PENDING" // or NOT_ARRIVED, ARRIVED, COMPLETED, CANCELLED, REJECTED
    }

    Valid statuses:
    - PENDING: Chờ xác nhận
    - NOT_ARRIVED: Chưa đến
    - ARRIVED: Đã đến
    - COMPLETED: Hoàn thành
    - CANCELLED: Đã hủy
    - REJECTED: Đã từ chối

    Returns: Success message with new status display name
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = str(data.get('status', '')).strip().upper()

        valid_statuses = ['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'REJECTED']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)

        appointment.status = new_status
        if new_status == 'CANCELLED':
            appointment.cancelled_by = 'admin'
        appointment.save()

        return JsonResponse({
            'success': True,
            'message': f'Đã cập nhật trạng thái: {appointment.get_status_display()}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "DELETE"])
@staff_api
def api_appointment_delete(request, appointment_code):
    """
    [TAB 1] POST/DELETE /api/appointments/<code>/delete/

    Xóa mềm lịch hẹn (soft delete).

    TAB: Room Calendar (Lịch theo phòng)
    Methods: POST, DELETE

    Business logic:
    - Sets deleted_at and deleted_by_user fields
    - Appointment is not actually removed from database
    - Can be restored by admin if needed

    Returns: Success message with deleted appointment ID and customer name
    """
    from django.utils import timezone

    try:
        appointment = Appointment.objects.get(appointment_code=appointment_code, deleted_at__isnull=True)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    if not _is_staff(request.user):
        return _deny()

    try:
        customer_name = appointment.customer_name_snapshot or "Khách hàng"
        appointment_id = appointment.id

        appointment.deleted_at = timezone.now()
        appointment.deleted_by_user = request.user
        appointment.save(update_fields=['deleted_at', 'deleted_by_user', 'updated_at'])

        return JsonResponse({
            'success': True,
            'message': f'Đã xóa lịch hẹn {appointment_code}',
            'deleted_id': appointment_id,
            'customer_name': customer_name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Không thể xóa: {str(e)}'}, status=400)


# ============================================================
# SECTION 5: TAB 2 - YÊU CẦU ĐẶT LỊCH (BOOKING REQUESTS)
# ============================================================
# These endpoints are specifically for the Booking Requests tab
# They handle online booking requests and pending appointments

@require_http_methods(["GET"])
def api_booking_requests(request):
    """
    [TAB 2] GET /api/booking-requests/

    Danh sách yêu cầu đặt lịch từ web (online bookings).

    TAB: Booking Requests (Yêu cầu đặt lịch)
    Methods: GET

    Query params:
    - date: Filter theo ngày (YYYY-MM-DD)
    - status: Filter theo status (PENDING|CANCELLED|REJECTED)
    - q: Search theo code, tên, phone
    - service: Filter theo service_id

    Business logic:
    - PENDING/CANCELLED: chỉ lấy ONLINE (web booking)
    - REJECTED: lấy tất cả source (admin có thể từ chối lịch DIRECT)
    - Sắp xếp: PENDING → CANCELLED/REJECTED → created_at desc

    Returns: List of booking requests ordered by priority (PENDING first)
    """
    if not _is_staff(request.user):
        return _deny()

    # ========== 1. BASE FILTER ==========
    appointments = Appointment.objects.filter(deleted_at__isnull=True).filter(
        Q(status='REJECTED') |
        Q(status__in=['PENDING', 'CANCELLED'], source='ONLINE') |
        Q(status__in=['PENDING', 'CANCELLED'], source__isnull=True)
    )

    # ========== 2. OPTIONAL FILTERS ==========

    # Filter by date
    if date_filter := request.GET.get('date'):
        appointments = appointments.filter(appointment_date=date_filter)

    # Filter by status
    if status_filter := request.GET.get('status', '').strip().upper():
        if status_filter in ['PENDING', 'CANCELLED', 'REJECTED']:
            appointments = appointments.filter(status=status_filter)

    # Search by code, name, phone
    if search := request.GET.get('q', '').strip():
        # Chuẩn hóa: chỉ giữ số (cho phone search)
        search_normalized = ''.join(filter(str.isdigit, search))

        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer_name_snapshot__icontains=search) |
            Q(booker_name__icontains=search) |
            Q(customer_phone_snapshot__icontains=search_normalized) |
            Q(booker_phone__icontains=search_normalized)
        )

    # Filter by service
    if service_id := request.GET.get('service', '').strip():
        appointments = appointments.filter(service_variant__service_id=service_id)

    # ========== 3. ORDERING ==========
    # Sắp xếp: PENDING (0) → CANCELLED/REJECTED (1) → Khác (2)
    # Sau đó sort theo created_at mới nhất

    from django.db.models import Case, When, IntegerField

    appointments = appointments.order_by(
        Case(
            When(status='PENDING', then=0),
            When(status='CANCELLED', then=1),
            When(status='REJECTED', then=1),
            default=2,
            output_field=IntegerField()
        ),
        '-created_at'
    )

    return JsonResponse({
        'success': True,
        'appointments': [serialize_appointment(a) for a in appointments]
    })


@require_http_methods(["GET"])
def api_booking_pending_count(request):
    """
    [TAB 2] GET /api/booking/pending-count/

    Số lượng booking đang chờ xác nhận.

    TAB: Booking Requests (Yêu cầu đặt lịch)
    Methods: GET

    Business logic:
    - Counts ONLINE bookings with PENDING status
    - Returns current timestamp for cache validation

    Returns: Count of pending bookings with timestamp
    """
    if not _is_staff(request.user):
        return _deny()

    try:
        from django.utils import timezone
        count = Appointment.objects.filter(
            Q(source='ONLINE') | Q(source__isnull=True),
            status='PENDING',
            deleted_at__isnull=True,
        ).count()
        return JsonResponse({'success': True, 'count': count, 'timestamp': timezone.now().isoformat()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Không thể lấy số lượng: {str(e)}', 'count': 0}, status=500)


# Alias: single create → batch create (backward compat với urls.py)
api_appointment_create = api_appointment_create_batch


@require_http_methods(["GET"])
def api_customer_cancelled_recent(request):
    """
    [TAB 2] GET /api/appointments/customer-cancelled-recent/

    Danh sách các lịch bị khách hủy gần đây.

    TAB: Booking Requests (Yêu cầu đặt lịch)
    Methods: GET

    Query params:
    - minutes: Số phút để tìm kiếm (default: 10)

    Business logic:
    - Finds appointments cancelled by customer within N minutes
    - Used for admin polling to show toast notifications
    - Ordered by updated_at desc (most recent first)

    Returns: Max 20 recently cancelled appointments
    """
    if not _is_staff(request.user):
        return _deny()

    from django.utils import timezone
    minutes = int(request.GET.get('minutes', 10))
    since = timezone.now() - __import__('datetime').timedelta(minutes=minutes)

    appointments = Appointment.objects.filter(
        status='CANCELLED',
        cancelled_by='customer',
        updated_at__gte=since,
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:20]

    return JsonResponse({
        'success': True,
        'appointments': [
            {
                'code': a.appointment_code,
                'customerName': a.customer_name_snapshot or a.booker_name or 'Khách',
                'cancelledAt': a.updated_at.isoformat() if a.updated_at else '',
            }
            for a in appointments
        ]
    })
