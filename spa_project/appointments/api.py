"""
API Endpoints — Lịch hẹn (refactored theo model mới)

THAY ĐỔI:
- Bỏ service_id (chỉ dùng service_variant_id)
- Bỏ end_time, duration_minutes, guests (tính từ variant)
- room_id bắt buộc NOT NULL
- customer_id luôn được set (auto find/create)
- 1 slot = 1 khách = 1 appointment

Author: Spa ANA Team
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


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _deny():
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

    try:
        user = User.objects.get(username=phone)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=phone,
            password=secrets.token_hex(16),
            first_name=customer_name.split()[0] if customer_name else '',
            last_name=' '.join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else ''
        )

    customer, created = CustomerProfile.objects.get_or_create(
        phone=phone,
        defaults={'full_name': customer_name, 'user': user}
    )

    if not created and customer.full_name != customer_name:
        customer.full_name = customer_name
        customer.save()

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

    # Variant (tuỳ chọn)
    variant_id = data.get('variant_id')
    if variant_id:
        try:
            variant = ServiceVariant.objects.get(id=variant_id)
            cleaned['service_variant'] = variant
        except ServiceVariant.DoesNotExist:
            errors.append('Gói dịch vụ không tồn tại')

    # Không cho COMPLETED nếu chưa chọn variant
    status = data.get('status', 'NOT_ARRIVED')
    if status == 'COMPLETED' and not cleaned.get('service_variant'):
        errors.append('Phải chọn gói dịch vụ trước khi hoàn tất lịch hẹn')

    # Ngày
    date_str = data.get('date_str', '')
    if not date_str:
        errors.append('Vui lòng chọn ngày hẹn')
    else:
        try:
            cleaned['appointment_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Định dạng ngày không hợp lệ')

    # Giờ
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

    # Ghi chú & trạng thái
    cleaned['notes'] = data.get('notes', '')
    cleaned['status'] = status
    cleaned['payment_status'] = data.get('pay_status', 'UNPAID')

    # Validate nâng cao: ngày giờ + phòng trống
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
            errors.extend(validation_result['errors'])

    return {'valid': len(errors) == 0, 'errors': errors, 'cleaned_data': cleaned}


# ═════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def api_rooms_list(request):
    """GET /api/rooms/ — Danh sách phòng."""
    if not _is_staff(request.user):
        return _deny()

    rooms = Room.objects.filter(is_active=True).order_by('code')
    return JsonResponse({
        'success': True,
        'rooms': [{'id': r.code, 'name': r.name, 'capacity': r.capacity} for r in rooms]
    })


@require_http_methods(["GET"])
def api_appointments_list(request):
    """GET /api/appointments/ — Danh sách lịch hẹn (có filter)."""
    if not _is_staff(request.user):
        return _deny()

    appointments = Appointment.objects.filter(deleted_at__isnull=True).exclude(
        source='ONLINE', status__in=['PENDING', 'REJECTED']
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
def api_appointments_search(request):
    """GET /api/appointments/search/ — Tìm kiếm lịch hẹn toàn hệ thống.

    Yêu cầu ít nhất 1 điều kiện (q, code, phone, email, status, source, service, room,
    date_from hoặc date_to) để tránh query toàn bộ dữ liệu.
    Trả về tối đa 100 kết quả, sắp xếp theo ngày giờ giảm dần.
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
def api_appointment_detail(request, appointment_code):
    """GET /api/appointments/<code>/ — Chi tiết 1 lịch hẹn."""
    if not _is_staff(request.user):
        return _deny()

    try:
        appt = Appointment.objects.get(appointment_code=appointment_code, deleted_at__isnull=True)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    return JsonResponse({'success': True, 'appointment': serialize_appointment(appt)})


@require_http_methods(["GET"])
def api_customer_search(request):
    """GET /api/customers/search/?q=... — Tìm khách hàng."""
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


@require_http_methods(["POST"])
@staff_api
def api_appointment_create_batch(request):
    """
    POST /api/appointments/create-batch/
    Body: { booker: {...}, guests: [{...}, ...] }
    
    Tạo nhiều lịch hẹn cùng lúc (1 người đặt, nhiều khách).
    """
    try:
        raw = json.loads(request.body)
        booker = raw.get('booker', {})
        guests = raw.get('guests', [])

        if not guests:
            return JsonResponse({'success': False, 'error': 'Cần ít nhất 1 khách'}, status=400)

        booker_name = booker.get('name', '').strip()
        booker_phone = ''.join(filter(str.isdigit, booker.get('phone', '')))
        booker_email = booker.get('email', '').strip()
        source = booker.get('source', 'DIRECT')

        if not booker_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập tên người đặt'}, status=400)
        if not booker_phone or len(booker_phone) < 9:
            return JsonResponse({'success': False, 'error': 'Số điện thoại người đặt không hợp lệ'}, status=400)

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
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["GET", "POST"])
@staff_api
def api_appointment_rebook(request, appointment_code):
    """POST /api/appointments/<code>/rebook/ — Tạo lịch mới từ lịch đã hủy/từ chối."""
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    # Trả về thông tin cần thiết để FE pre-fill form tạo mới
    variant_available = False
    variant_warning = None
    if appointment.service_variant_id:
        try:
            sv = ServiceVariant.objects.get(id=appointment.service_variant_id, is_active=True)
            # Kiểm tra service còn active không
            if sv.service.is_active:
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


@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """POST /api/appointments/<code>/update/ — Cập nhật lịch hẹn."""
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
        new_status = raw_data.get('apptStatus') or raw_data.get('status')
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
    """POST /api/appointments/<code>/status/ — Đổi trạng thái."""
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')

        valid_statuses = ['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'REJECTED']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)

        appointment.status = new_status
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
    """POST /api/appointments/<code>/delete/ — Xóa mềm."""
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


@require_http_methods(["GET"])
def api_booking_requests(request):
    """GET /api/booking-requests/ — Yêu cầu đặt lịch từ web."""
    if not _is_staff(request.user):
        return _deny()

    appointments = Appointment.objects.filter(
        Q(source='ONLINE') | Q(source__isnull=True),
        status__in=['PENDING', 'CANCELLED', 'REJECTED'],
        deleted_at__isnull=True
    )

    if date_filter := request.GET.get('date'):
        appointments = appointments.filter(appointment_date=date_filter)
    if status_filter := request.GET.get('status', '').strip().upper():
        if status_filter in ['PENDING', 'CANCELLED', 'REJECTED']:
            appointments = appointments.filter(status=status_filter)
    if search := request.GET.get('q', '').strip():
        # Chuẩn hóa: nếu search là chuỗi số thì cũng tìm theo digits-only
        search_digits = ''.join(filter(str.isdigit, search))
        phone_q = (
            Q(customer_phone_snapshot__icontains=search) |
            Q(booker_phone__icontains=search)
        )
        if search_digits and search_digits != search:
            # Người dùng nhập có ký tự đặc biệt (dấu cách, gạch ngang...)
            # → tìm thêm theo digits-only
            phone_q |= (
                Q(customer_phone_snapshot__icontains=search_digits) |
                Q(booker_phone__icontains=search_digits)
            )
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer_name_snapshot__icontains=search) |
            Q(booker_name__icontains=search) |
            phone_q
        )
    if service_id := request.GET.get('service', '').strip():
        appointments = appointments.filter(service_variant__service_id=service_id)

    from django.db.models import Case, When, IntegerField
    appointments = appointments.order_by(
        Case(When(status='PENDING', then=0), When(status='CANCELLED', then=1), When(status='REJECTED', then=1), default=2, output_field=IntegerField()),
        '-created_at'
    )

    return JsonResponse({'success': True, 'appointments': [serialize_appointment(a) for a in appointments]})


@require_http_methods(["GET"])
def api_booking_pending_count(request):
    """GET /api/booking/pending-count/ — Số lượng booking pending."""
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
