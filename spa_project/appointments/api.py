"""
API Endpoints - Các đường dẫn API cho lịch hẹn

File này chứa TẤT CẢ các hàm API (trả về JSON) cho frontend gọi.

Cấu trúc mỗi API:
1. Kiểm tra quyền truy cập (user đã đăng nhập + là staff không?)
2. Lấy dữ liệu từ request (query params hoặc JSON body)
3. Gọi service layer để xử lý logic
4. Trả về JSON response

LUỒNG: FE (JavaScript) → Gọi API → File này → Service/Model → Trả JSON → FE render

Author: Spa ANA Team
"""

import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.db import transaction

from decimal import Decimal

from .models import Appointment, Room, Invoice, InvoicePayment
from customers.models import CustomerProfile
from spa_services.models import Service

# Import serializer (chuyển model → dict)
from .serializers import serialize_appointment

# Import validation (kiểm tra dữ liệu hợp lệ)
from .services import validate_appointment_create

# Import helper từ core
from core.api_response import staff_api, get_or_404


# =====================================================
# HELPER: Kiểm tra quyền truy cập
# =====================================================

def _is_staff(user):
    """Kiểm tra user có phải staff/admin không"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _deny():
    """Trả về lỗi 403 (Không có quyền)"""
    return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)


# =====================================================
# HELPER: Tạo Invoice + InvoicePayment
# =====================================================

def _get_variant_price(service_variant, service):
    """Lấy giá từ variant hoặc service"""
    if service_variant and hasattr(service_variant, 'price') and service_variant.price:
        return Decimal(str(service_variant.price))
    if service and hasattr(service, 'price') and service.price:
        return Decimal(str(service.price))
    return Decimal('0')


def _create_invoice_and_payment(appointment, pay_status, payment_data, created_by):
    """
    Tạo Invoice và InvoicePayment cho 1 appointment.

    pay_status: 'UNPAID' | 'PARTIAL' | 'PAID'
    payment_data: {
        'amount': Decimal (chỉ dùng khi PARTIAL),
        'payment_method': str,
        'recorded_no': str (optional),
        'note': str (optional),
    }

    Luồng:
    - Luôn tạo Invoice
    - UNPAID  → không tạo InvoicePayment
    - PARTIAL → tạo InvoicePayment với amount từ payment_data
    - PAID    → tạo InvoicePayment với amount = final_amount
    """
    subtotal = _get_variant_price(appointment.service_variant, appointment.service)
    discount = Decimal('0')
    final    = subtotal - discount

    invoice = Invoice.objects.create(
        appointment=appointment,
        subtotal_amount=subtotal,
        discount_amount=discount,
        final_amount=final,
        status=pay_status,
        created_by=created_by,
    )

    if pay_status == 'UNPAID':
        return invoice

    # PARTIAL hoặc PAID → tạo InvoicePayment
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
    """
    Validate payment fields theo pay_status.
    Trả về (is_valid: bool, error_msg: str)
    """
    if pay_status == 'UNPAID':
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
        if final_amount is not None and amount >= Decimal(str(final_amount)):
            return False, 'Số tiền thanh toán một phần phải nhỏ hơn tổng tiền'

    return True, ''


# =====================================================
# API: PHÒNG (ROOMS)
# =====================================================

@require_http_methods(["GET"])
def api_rooms_list(request):
    """
    API: Lấy danh sách phòng

    FE gọi: GET /api/rooms/
    Trả về: { success: true, rooms: [...] }
    """
    if not _is_staff(request.user):
        return _deny()

    rooms = Room.objects.filter(is_active=True).order_by('code')
    rooms_data = [
        {
            'id': room.code,
            'name': room.name,
            'capacity': room.capacity,
        }
        for room in rooms
    ]

    return JsonResponse({'success': True, 'rooms': rooms_data})


# =====================================================
# API: DANH SÁCH LỊCH HẸN
# =====================================================

@require_http_methods(["GET"])
def api_appointments_list(request):
    """
    API: Lấy danh sách lịch hẹn (có filter)

    FE gọi: GET /api/appointments/?date=2026-04-12&status=pending&q=nguyen

    Query params (tất cả optional):
    - date: lọc theo ngày (YYYY-MM-DD)
    - status: lọc theo trạng thái
    - source: lọc theo nguồn (web/admin)
    - room: lọc theo mã phòng
    - q: tìm kiếm (tên, SĐT, dịch vụ, mã lịch hẹn)
    """
    if not _is_staff(request.user):
        return _deny()

    # Scheduler chỉ hiện lịch đã xác nhận
    # ONLINE + PENDING → thuộc tab "Yêu cầu đặt lịch", không hiện ở đây
    # Chỉ lấy lịch chưa bị xóa mềm
    appointments = Appointment.objects.filter(
        deleted_at__isnull=True
    ).exclude(
        source='ONLINE', status='PENDING'
    )

    # Lọc theo ngày
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    # Lọc theo trạng thái
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Lọc theo dịch vụ
    service_filter = request.GET.get('service', '')
    if service_filter:
        appointments = appointments.filter(service__id=service_filter)

    # Lọc theo kênh liên hệ (source)
    source_filter = request.GET.get('source', '')
    if source_filter:
        appointments = appointments.filter(source=source_filter)

    # Tìm kiếm (OR trên nhiều field, icontains)
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(customer_name_snapshot__icontains=search) |
            Q(customer_phone_snapshot__icontains=search) |
            Q(customer_email_snapshot__icontains=search) |
            Q(notes__icontains=search) |
            Q(staff_notes__icontains=search) |
            Q(service__name__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(customer__user__email__icontains=search)
        )

    appointments = appointments.order_by('appointment_date', 'appointment_time')

    # Serialize (chuyển model → dict)
    data = [serialize_appointment(appt) for appt in appointments]

    return JsonResponse({'success': True, 'appointments': data})


# =====================================================
# API: CHI TIẾT 1 LỊCH HẸN
# =====================================================

@require_http_methods(["GET"])
def api_appointment_detail(request, appointment_code):
    """
    API: Lấy chi tiết 1 lịch hẹn

    FE gọi: GET /api/appointments/APT001/
    Trả về: { success: true, appointment: {...} }
    Không trả về lịch đã bị xóa mềm.
    """
    if not _is_staff(request.user):
        return _deny()

    try:
        appt = Appointment.objects.get(
            appointment_code=appointment_code,
            deleted_at__isnull=True
        )
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    return JsonResponse({'success': True, 'appointment': serialize_appointment(appt)})


# =====================================================
# API: TÌM KIẾM KHÁCH HÀNG
# =====================================================

@require_http_methods(["GET"])
def api_customer_search(request):
    """
    API: Tìm kiếm khách hàng theo tên / SĐT / email

    FE gọi: GET /api/customers/search/?q=nguyen
    Trả về: { success: true, customers: [...] }
    """
    if not _is_staff(request.user):
        return _deny()

    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'success': True, 'customers': []})

    customers = CustomerProfile.objects.filter(
        Q(full_name__icontains=q) |
        Q(phone__icontains=q) |
        Q(user__email__icontains=q)
    ).select_related('user')[:10]

    data = [
        {
            'id': c.id,
            'fullName': c.full_name,
            'phone': c.phone,
            'email': c.user.email if c.user else '',
        }
        for c in customers
    ]
    return JsonResponse({'success': True, 'customers': data})


# =====================================================
# API: TẠO LỊCH HẸN MỚI
# =====================================================

@require_http_methods(["POST"])
@staff_api
def api_appointment_create(request):
    """
    API: Tạo lịch hẹn mới (từ admin scheduler)

    FE gọi: POST /api/appointments/create/
    Body: { customerName, phone, serviceId, roomId, date, time, duration, guests, ... }

    Luồng xử lý:
    1. Parse JSON từ request body
    2. Validate dữ liệu (kiểm tra ngày, giờ, phòng trống)
    3. Tìm hoặc tạo khách hàng
    4. Tạo appointment trong database
    5. Trả về kết quả
    """
    try:
        raw_data = json.loads(request.body)

        # Chuẩn bị data để validate
        customer_id = raw_data.get('customerId') or None
        data = {
            'customer_name': raw_data.get('customerName', '').strip(),
            'phone': raw_data.get('phone', '').strip(),
            'service_id': raw_data.get('serviceId') or raw_data.get('service'),
            'variant_id': raw_data.get('variantId') or raw_data.get('variant'),
            'room_id': raw_data.get('roomId') or raw_data.get('room'),
            'date_str': raw_data.get('date', ''),
            'time_str': raw_data.get('time') or raw_data.get('start', ''),
            'duration': raw_data.get('duration') or raw_data.get('durationMin') or None,
            'guests': raw_data.get('guests', 1),
            'notes': raw_data.get('note', ''),
            'status': raw_data.get('apptStatus', 'NOT_ARRIVED'),
            'pay_status': raw_data.get('payStatus', 'UNPAID'),
        }

        # Bước 1: Validate dữ liệu
        validation = _validate_appointment_data(data)
        if not validation['valid']:
            return JsonResponse({'success': False, 'error': validation['errors'][0]}, status=400)

        cleaned = validation['cleaned_data']

        # Bước 1b: Validate payment data
        pay_status = cleaned['payment_status']
        payment_data = {
            'payment_method': raw_data.get('paymentMethod', ''),
            'amount': raw_data.get('paymentAmount', 0),
            'recorded_no': raw_data.get('paymentRecordedNo', ''),
            'note': raw_data.get('paymentNote', ''),
        }
        # Tính final_amount tạm để validate PARTIAL
        temp_price = _get_variant_price(
            cleaned.get('service_variant'), cleaned.get('service')
        )
        pay_valid, pay_error = _validate_payment_data(pay_status, payment_data, temp_price)
        if not pay_valid:
            return JsonResponse({'success': False, 'error': pay_error}, status=400)

        # Bước 2: Resolve khách hàng
        # - Nếu FE gửi customerId → dùng profile đó (đã xác nhận ✓)
        # - Nếu không có customerId → tìm theo SĐT (không tạo mới nếu đã tồn tại)
        #   Nếu SĐT chưa có trong hệ thống → tạo CustomerProfile mới
        #   Nếu SĐT đã có nhưng user chọn ✕ → customerId=null, tạo lịch guest
        #   (appointment.customer vẫn cần FK, dùng profile tìm được hoặc tạo mới)
        
        # Lấy thông tin người đặt lịch (booker) từ request
        booker_name  = raw_data.get('bookerName', '').strip()
        booker_phone = raw_data.get('bookerPhone', '').strip()
        booker_email = raw_data.get('bookerEmail', '').strip()
        
        if customer_id:
            try:
                customer = CustomerProfile.objects.get(id=customer_id)
            except CustomerProfile.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Không tìm thấy khách hàng'}, status=404)
        else:
            # Tìm theo SĐT — KHÔNG tạo mới nếu đã tồn tại (tránh duplicate)
            phone_digits = cleaned['phone']
            try:
                customer = CustomerProfile.objects.get(phone=phone_digits)
                # Tìm thấy nhưng FE không gửi customerId (user đã chọn ✕)
                # → vẫn link appointment vào profile này (FK bắt buộc)
                # nhưng snapshot lấy từ form (không phải từ profile)
            except CustomerProfile.DoesNotExist:
                # Chưa có profile → tạo mới (khách thực sự mới)
                customer = _get_or_create_customer(
                    phone=phone_digits,
                    customer_name=cleaned['customer_name']
                )

        # Bước 3: Tạo lịch hẹn với TRANSACTION LOCK để tránh race condition
        with transaction.atomic():
            # Lock các appointments trùng thời gian/phòng để tránh race condition
            room_code = cleaned['room'].code if cleaned.get('room') else None

            if room_code:
                # Lock conflicting appointments trong cùng phòng/ngày
                Appointment.objects.select_for_update().filter(
                    room__code=room_code,
                    appointment_date=cleaned['appointment_date'],
                    status__in=['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED'],
                    deleted_at__isnull=True
                ).exists()

                # Double-check availability trong transaction
                check_result = validate_appointment_create(
                    appointment_date=cleaned['appointment_date'],
                    appointment_time=cleaned['appointment_time'],
                    duration_minutes=cleaned['duration_minutes'],
                    room_code=room_code,
                    exclude_appointment_code=None,
                    guests=cleaned['guests']
                )

                if not check_result['valid']:
                    return JsonResponse({
                        'success': False,
                        'error': check_result['errors'][0]
                    }, status=400)

            # Tạo appointment
            appointment = Appointment.objects.create(
                customer=customer,
                service=cleaned['service'],
                service_variant=cleaned.get('service_variant'),
                room=cleaned.get('room'),
                booker_name=booker_name or cleaned['customer_name'],
                booker_phone=booker_phone or cleaned['phone'],
                booker_email=booker_email,
                customer_name_snapshot=cleaned['customer_name'],
                customer_phone_snapshot=cleaned.get('phone') or None,
                customer_email_snapshot=raw_data.get('email', '').strip() or None,
                appointment_date=cleaned['appointment_date'],
                appointment_time=cleaned['appointment_time'],
                duration_minutes=cleaned['duration_minutes'],
                guests=cleaned['guests'],
                notes=cleaned['notes'],
                status=cleaned['status'],
                payment_status=cleaned['payment_status'],
                source=raw_data.get('source', 'DIRECT'),
                staff_notes=raw_data.get('staffNote', '').strip(),
                created_by=request.user,
            )

            # Tạo Invoice + InvoicePayment
            _create_invoice_and_payment(
                appointment=appointment,
                pay_status=cleaned['payment_status'],
                payment_data=payment_data,
                created_by=request.user,
            )

        return JsonResponse({
            'success': True,
            'message': f'Tạo lịch hẹn thành công! Mã: {appointment.appointment_code}',
            'appointment': serialize_appointment(appointment)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


# =====================================================
# API: TẠO NHIỀU LỊCH HẸN (BATCH CREATE)
# =====================================================

@require_http_methods(["POST"])
@staff_api
def api_appointment_create_batch(request):
    """
    API: Tạo nhiều lịch hẹn cùng lúc (1 người đặt, nhiều khách)

    FE gọi: POST /api/appointments/create-batch/
    Body: {
        booker: { name, phone, email, source },
        guests: [
            { name, phone, email, customerId,
              serviceId, variantId, roomId, date, time,
              apptStatus, payStatus, note, staffNote },
            ...
        ]
    }
    """
    try:
        raw = json.loads(request.body)
        booker = raw.get('booker', {})
        guests = raw.get('guests', [])

        if not guests:
            return JsonResponse({'success': False, 'error': 'Cần ít nhất 1 khách'}, status=400)

        booker_name  = booker.get('name', '').strip()
        booker_phone = ''.join(filter(str.isdigit, booker.get('phone', '')))
        booker_email = booker.get('email', '').strip()
        source       = booker.get('source', 'DIRECT')

        if not booker_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập tên người đặt'}, status=400)
        if not booker_phone or len(booker_phone) < 9:
            return JsonResponse({'success': False, 'error': 'Số điện thoại người đặt không hợp lệ'}, status=400)

        created = []
        errors  = []

        for idx, g in enumerate(guests):
            label = f"Khách {idx + 1}"
            data = {
                'customer_name': g.get('name', '').strip(),
                'phone':         ''.join(filter(str.isdigit, g.get('phone', ''))),
                'service_id':    g.get('serviceId'),
                'variant_id':    g.get('variantId'),
                'room_id':       g.get('roomId'),
                'date_str':      g.get('date', ''),
                'time_str':      g.get('time', ''),
                'duration':      None,
                'guests':        1,
                'notes':         g.get('note', ''),
                'status':        g.get('apptStatus', 'NOT_ARRIVED'),
                'pay_status':    g.get('payStatus', 'UNPAID'),
            }

            validation = _validate_appointment_data(data)
            if not validation['valid']:
                errors.append(f"{label}: {validation['errors'][0]}")
                continue

            cleaned = validation['cleaned_data']

            # Validate payment data cho từng guest
            g_pay_status = cleaned['payment_status']
            g_payment_data = {
                'payment_method': g.get('paymentMethod', ''),
                'amount': g.get('paymentAmount', 0),
                'recorded_no': g.get('paymentRecordedNo', ''),
                'note': g.get('paymentNote', ''),
            }
            temp_price = _get_variant_price(cleaned.get('service_variant'), cleaned.get('service'))
            pay_valid, pay_error = _validate_payment_data(g_pay_status, g_payment_data, temp_price)
            if not pay_valid:
                errors.append(f"{label}: {pay_error}")
                continue

            customer_id = g.get('customerId')
            guest_phone = cleaned.get('phone') or ''   # có thể rỗng
            guest_name  = cleaned.get('customer_name', '')

            try:
                if customer_id:
                    customer = CustomerProfile.objects.get(id=customer_id)
                elif guest_phone:
                    try:
                        customer = CustomerProfile.objects.get(phone=guest_phone)
                    except CustomerProfile.DoesNotExist:
                        customer = _get_or_create_customer(
                            phone=guest_phone,
                            customer_name=guest_name
                        )
                else:
                    # Không có SĐT → tạo profile tạm bằng SĐT người đặt (chỉ để FK không null)
                    try:
                        customer = CustomerProfile.objects.get(phone=booker_phone)
                    except CustomerProfile.DoesNotExist:
                        customer = _get_or_create_customer(
                            phone=booker_phone,
                            customer_name=guest_name or booker_name
                        )
            except CustomerProfile.DoesNotExist:
                errors.append(f"{label}: Không tìm thấy khách hàng")
                continue

            try:
                with transaction.atomic():
                    room_code = cleaned['room'].code if cleaned.get('room') else None
                    if room_code:
                        check = validate_appointment_create(
                            appointment_date=cleaned['appointment_date'],
                            appointment_time=cleaned['appointment_time'],
                            duration_minutes=cleaned['duration_minutes'],
                            room_code=room_code,
                            exclude_appointment_code=None,
                            guests=1,
                        )
                        if not check['valid']:
                            errors.append(f"{label}: {check['errors'][0]}")
                            continue

                    appt = Appointment.objects.create(
                        customer=customer,
                        service=cleaned['service'],
                        service_variant=cleaned.get('service_variant'),
                        room=cleaned.get('room'),
                        booker_name=booker_name,
                        booker_phone=booker_phone,
                        booker_email=booker_email,
                        customer_name_snapshot=cleaned['customer_name'],
                        customer_phone_snapshot=cleaned.get('phone') or None,
                        customer_email_snapshot=g.get('email', '').strip() or None,
                        appointment_date=cleaned['appointment_date'],
                        appointment_time=cleaned['appointment_time'],
                        duration_minutes=cleaned['duration_minutes'],
                        guests=1,
                        notes=cleaned['notes'],
                        status=cleaned['status'],
                        payment_status=cleaned['payment_status'],
                        source=source,
                        staff_notes=g.get('staffNote', '').strip(),
                        created_by=request.user,
                    )
                    # Tạo Invoice + InvoicePayment cho từng appointment
                    _create_invoice_and_payment(
                        appointment=appt,
                        pay_status=cleaned['payment_status'],
                        payment_data=g_payment_data,
                        created_by=request.user,
                    )
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
        import traceback; traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


# =====================================================
# API: CẬP NHẬT LỊCH HẸN
# =====================================================

@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """
    API: Cập nhật lịch hẹn

    FE gọi: POST /api/appointments/APT001/update/
    Body: { customerName, phone, serviceId, roomId, date, time, ... }

    Luồng:
    1. Tìm lịch hẹn theo mã
    2. Validate dữ liệu mới TRƯỚC khi update object
    3. Cập nhật từng field nếu có trong request
    4. Lưu với transaction.atomic() để tránh race condition
    5. Trả kết quả
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    try:
        raw_data = json.loads(request.body)

        # ===== BƯỚC 1: Thu thập data MỚI (KHÔNG modify appointment object) =====
        new_booker_name  = raw_data.get('bookerName', '').strip()
        new_booker_phone = raw_data.get('bookerPhone', '').strip()
        new_booker_email = raw_data.get('bookerEmail', '').strip()

        new_customer_name = raw_data.get('customerName', '').strip()
        new_phone = raw_data.get('phone', '').strip()
        new_service_id = raw_data.get('serviceId') or raw_data.get('service')
        new_room_id = raw_data.get('roomId') or raw_data.get('room')

        # Thu thập ngày/giờ/thời lượng mới
        new_date_str = raw_data.get('date', '')
        new_time_str = raw_data.get('time') or raw_data.get('start', '')
        new_duration = raw_data.get('duration') or raw_data.get('durationMin')
        new_guests = raw_data.get('guests')
        new_notes = raw_data.get('note', '')
        new_status = raw_data.get('apptStatus')
        new_pay_status = raw_data.get('payStatus')

        # ===== BƯỚC 2: Validate ngày/giờ/phòng TRƯỚC khi update =====
        needs_validation = False
        validation_data = {
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'duration_minutes': appointment.duration_minutes or (
                appointment.service_variant.duration_minutes if appointment.service_variant else (
                    appointment.service.variants.order_by('sort_order').first().duration_minutes
                    if appointment.service else 60
                )
            ),
            'room_code': appointment.room.code if appointment.room else None,
            'guests': appointment.guests or 1
        }

        # Parse new date/time/duration nếu có
        if new_date_str:
            try:
                validation_data['appointment_date'] = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng ngày không hợp lệ (YYYY-MM-DD)'}, status=400)

        if new_time_str:
            try:
                validation_data['appointment_time'] = datetime.strptime(new_time_str, '%H:%M').time()
                needs_validation = True
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Định dạng giờ không hợp lệ (HH:MM)'}, status=400)

        if new_duration:
            try:
                validation_data['duration_minutes'] = int(new_duration)
                needs_validation = True
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Thời lượng phải là số nguyên'}, status=400)

        if new_room_id is not None:
            validation_data['room_code'] = new_room_id if new_room_id else None
            needs_validation = True

        if new_guests is not None:
            try:
                validation_data['guests'] = int(new_guests)
                needs_validation = True
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Số khách phải là số nguyên'}, status=400)

        # Validate nếu có thay đổi ngày/giờ/phòng
        if needs_validation:
            result = validate_appointment_create(
                appointment_date=validation_data['appointment_date'],
                appointment_time=validation_data['appointment_time'],
                duration_minutes=validation_data['duration_minutes'],
                room_code=validation_data['room_code'],
                exclude_appointment_code=appointment_code,
                guests=validation_data['guests']
            )
            if not result['valid']:
                return JsonResponse({'success': False, 'error': result['errors'][0]}, status=400)

        # ===== BƯỚC 3: UPDATE với transaction.atomic() để tránh race condition =====
        with transaction.atomic():
            # Lock appointment để tránh concurrent updates
            locked_appointment = Appointment.objects.select_for_update().get(
                appointment_code=appointment_code,
                deleted_at__isnull=True
            )

            # Cập nhật booker (người đặt lịch)
            if new_booker_name:
                locked_appointment.booker_name = new_booker_name
            if new_booker_phone:
                locked_appointment.booker_phone = ''.join(filter(str.isdigit, new_booker_phone))
            if new_booker_email:
                locked_appointment.booker_email = new_booker_email

            # Cập nhật customer snapshot (khách sử dụng dịch vụ)
            # customer_name_snapshot: bắt buộc — chỉ update nếu có giá trị
            if new_customer_name:
                locked_appointment.customer_name_snapshot = new_customer_name
            # customer_phone_snapshot: tuỳ chọn — None nếu rỗng
            if 'phone' in raw_data:
                phone_digits = ''.join(filter(str.isdigit, new_phone))
                locked_appointment.customer_phone_snapshot = phone_digits or None
            new_customer_email = raw_data.get('email', '').strip()
            locked_appointment.customer_email_snapshot = new_customer_email or None

            # Cập nhật dịch vụ + variant
            new_variant_id = raw_data.get('variantId') or raw_data.get('variant')
            if new_service_id:
                try:
                    locked_appointment.service = Service.objects.get(id=new_service_id)
                    # Reset variant khi đổi service (tránh variant không thuộc service mới)
                    locked_appointment.service_variant = None
                except Service.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Dịch vụ không tồn tại'}, status=404)

            if new_variant_id:
                try:
                    from spa_services.models import ServiceVariant
                    variant = ServiceVariant.objects.get(id=new_variant_id)
                    locked_appointment.service_variant = variant
                    # Nếu không có duration mới từ FE → lấy từ variant
                    if not new_duration:
                        locked_appointment.duration_minutes = variant.duration_minutes
                        # Tính lại end_time
                        from datetime import datetime as dt, timedelta
                        start = locked_appointment.appointment_time
                        start_dt = dt.combine(dt.today(), start)
                        locked_appointment.end_time = (start_dt + timedelta(minutes=variant.duration_minutes)).time()
                except ServiceVariant.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Gói dịch vụ không tồn tại'}, status=404)
            elif 'variantId' in raw_data and not new_variant_id:
                # FE gửi variantId=null → xóa variant (dùng fallback service)
                locked_appointment.service_variant = None

            # Cập nhật phòng
            if new_room_id is not None:
                if new_room_id:
                    try:
                        locked_appointment.room = Room.objects.get(code=new_room_id)
                    except Room.DoesNotExist:
                        locked_appointment.room = None
                else:
                    locked_appointment.room = None

            # Cập nhật ngày/giờ/thời lượng
            if new_date_str:
                locked_appointment.appointment_date = validation_data['appointment_date']
            if new_time_str:
                locked_appointment.appointment_time = validation_data['appointment_time']
            if new_duration:
                locked_appointment.duration_minutes = validation_data['duration_minutes']
            if new_guests is not None:
                locked_appointment.guests = validation_data['guests']

            # Cập nhật các field khác
            if new_notes:
                locked_appointment.notes = new_notes
            new_source = raw_data.get('source', '').strip()
            if new_source:
                locked_appointment.source = new_source
            if new_status:
                locked_appointment.status = new_status
            if new_pay_status:
                locked_appointment.payment_status = new_pay_status

            # Save appointment
            locked_appointment.save()

        return JsonResponse({
            'success': True,
            'message': f'Cập nhật lịch hẹn {appointment_code} thành công',
            'appointment': serialize_appointment(locked_appointment)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ'}, status=400)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=500)

        # Cập nhật các field còn lại
        guests = raw_data.get('guests')
        if guests:
            appointment.guests = int(guests)

        notes = raw_data.get('note', '')
        if notes:
            appointment.notes = notes

        status = raw_data.get('apptStatus', '')
        if status:
            appointment.status = status

        pay_status = raw_data.get('payStatus', '')
        if pay_status:
            appointment.payment_status = pay_status

        appointment.save()

        return JsonResponse({
            'success': True,
            'message': f'Cập nhật lịch hẹn {appointment_code} thành công'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


# =====================================================
# API: ĐỔI TRẠNG THÁI LỊCH HẸN
# =====================================================

@require_http_methods(["POST"])
@staff_api
def api_appointment_status(request, appointment_code):
    """
    API: Đổi trạng thái lịch hẹn

    FE gọi: POST /api/appointments/APT001/status/
    Body: { status: "completed" }

    Các trạng thái hợp lệ: pending, not_arrived, arrived, completed, cancelled
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code, deleted_at__isnull=True)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')

        # Kiểm tra status hợp lệ
        valid_statuses = ['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED', 'CANCELLED']
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


# =====================================================
# API: XÓA LỊCH HẸN
# =====================================================

@require_http_methods(["POST", "DELETE"])
@staff_api
def api_appointment_delete(request, appointment_code):
    """
    API: Xóa mềm lịch hẹn (SOFT DELETE - chỉ đánh dấu đã xóa, không xóa khỏi DB)

    FE gọi: POST /api/appointments/APT001/delete/

    Cập nhật: deleted_at, deleted_by_user, updated_at
    Dữ liệu vẫn còn trong DB để audit.
    """
    from django.utils import timezone as _tz

    try:
        appointment = Appointment.objects.get(
            appointment_code=appointment_code,
            deleted_at__isnull=True
        )
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    if not _is_staff(request.user):
        return _deny()

    try:
        customer_name = appointment.customer_name_snapshot or "Khách hàng"
        appointment_id = appointment.id

        # SOFT DELETE
        appointment.deleted_at = _tz.now()
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


# =====================================================
# API: YÊU CẦU ĐẶT LỊCH TỪ WEB
# =====================================================

@require_http_methods(["GET"])
def api_booking_requests(request):
    """
    API: Lấy danh sách yêu cầu đặt lịch từ web

    FE gọi: GET /api/booking-requests/?date=2026-04-12&status=pending

    Khác với api_appointments_list:
    - Chỉ lấy lịch có source='web' hoặc source=NULL (dữ liệu cũ)
    - Dùng cho tab "Yêu cầu đặt lịch" trong admin
    """
    if not _is_staff(request.user):
        return _deny()

    # Lấy lịch online + lịch cũ (source=NULL)
    # Chỉ lấy PENDING (chờ xử lý) và CANCELLED (đã từ chối)
    # Lịch đã xác nhận (NOT_ARRIVED trở lên) → thuộc tab "Lịch theo phòng"
    # Chỉ lấy lịch chưa bị xóa mềm
    appointments = Appointment.objects.filter(
        Q(source='ONLINE') | Q(source__isnull=True),
        status__in=['PENDING', 'CANCELLED'],
        deleted_at__isnull=True
    )

    # Lọc theo ngày
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    # Lọc theo trạng thái — chỉ cho phép PENDING hoặc CANCELLED
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter and status_filter in ['PENDING', 'CANCELLED']:
        appointments = appointments.filter(status=status_filter)

    # Tìm kiếm
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )

    # Sắp xếp: PENDING lên đầu, sau đó CANCELLED, theo thời gian tạo mới nhất
    from django.db.models import Case, When, IntegerField
    appointments = appointments.order_by(
        Case(
            When(status='PENDING', then=0),
            When(status='CANCELLED', then=1),
            default=2,
            output_field=IntegerField()
        ),
        '-created_at'
    )
    data = [serialize_appointment(appt) for appt in appointments]

    return JsonResponse({'success': True, 'appointments': data})


# =====================================================
# HELPER FUNCTIONS (dùng nội bộ trong file này)
# =====================================================

def _validate_appointment_data(data):
    """
    Validate dữ liệu lịch hẹn (dùng nội bộ)

    Kiểm tra: tên, SĐT, dịch vụ, ngày, giờ, phòng
    Returns: { 'valid': bool, 'errors': list, 'cleaned_data': dict }
    """
    errors = []
    cleaned_data = {}

    # Validate tên khách hàng — bắt buộc
    customer_name = data.get('customer_name', '').strip()
    if not customer_name:
        errors.append('Vui lòng nhập tên khách')
    else:
        cleaned_data['customer_name'] = customer_name

    # Validate SĐT — tuỳ chọn, nhưng nếu nhập phải đúng định dạng
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    if phone and len(phone) < 10:
        errors.append('Số điện thoại khách không hợp lệ')
    else:
        cleaned_data['phone'] = phone or None  # None nếu không nhập

    # Validate dịch vụ + variant
    service_id = data.get('service_id')
    if not service_id:
        errors.append('Vui lòng chọn dịch vụ')
    else:
        try:
            service = Service.objects.get(id=service_id)
            cleaned_data['service'] = service
        except Service.DoesNotExist:
            errors.append('Dịch vụ không tồn tại')

    # Validate variant (optional — nếu có thì dùng duration/price của variant)
    variant_id = data.get('variant_id')
    if variant_id:
        try:
            from spa_services.models import ServiceVariant
            variant = ServiceVariant.objects.get(id=variant_id)
            cleaned_data['service_variant'] = variant
        except (ServiceVariant.DoesNotExist, ValueError, TypeError):
            errors.append('Gói dịch vụ không tồn tại')
        except Service.DoesNotExist:
            errors.append('Dịch vụ không tồn tại')

    # Validate ngày
    date_str = data.get('date_str', '')
    if not date_str:
        errors.append('Vui lòng chọn ngày hẹn')
    else:
        try:
            cleaned_data['appointment_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Định dạng ngày không hợp lệ')

    # Validate giờ
    time_str = data.get('time_str', '')
    if not time_str:
        errors.append('Vui lòng chọn giờ hẹn')
    else:
        try:
            cleaned_data['appointment_time'] = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            errors.append('Định dạng giờ không hợp lệ')

    # Validate thời lượng — ưu tiên variant, fallback về data, rồi variant đầu tiên của service
    duration = data.get('duration', None)
    if duration:
        try:
            cleaned_data['duration_minutes'] = int(duration)
        except (ValueError, TypeError):
            cleaned_data['duration_minutes'] = 60
    elif 'service_variant' in cleaned_data:
        cleaned_data['duration_minutes'] = cleaned_data['service_variant'].duration_minutes
    elif 'service' in cleaned_data:
        first_variant = cleaned_data['service'].variants.order_by('sort_order', 'duration_minutes').first()
        cleaned_data['duration_minutes'] = first_variant.duration_minutes if first_variant else 60
    else:
        cleaned_data['duration_minutes'] = 60

    # Validate phòng (optional)
    room_id = data.get('room_id')
    room_code = None  # Initialize room_code for later use
    if room_id:
        try:
            cleaned_data['room'] = Room.objects.get(code=room_id)
            room_code = room_id  # Store room_code for validation
        except Room.DoesNotExist:
            cleaned_data['room'] = None
            room_code = None
    else:
        cleaned_data['room'] = None
        room_code = None

    # Validate số khách
    guests = data.get('guests', 1)
    try:
        guests = int(guests)
        if guests < 1:
            guests = 1
        cleaned_data['guests'] = guests
    except (ValueError, TypeError):
        cleaned_data['guests'] = 1

    # Ghi chú & trạng thái
    cleaned_data['notes'] = data.get('notes', '')
    cleaned_data['status'] = data.get('status', 'NOT_ARRIVED')
    cleaned_data['payment_status'] = data.get('pay_status', 'UNPAID')

    # Nếu có lỗi cơ bản → return luôn
    if errors:
        return {'valid': False, 'errors': errors, 'cleaned_data': cleaned_data}

    # Validate nâng cao: ngày giờ + phòng trống
    if 'appointment_date' in cleaned_data and 'appointment_time' in cleaned_data:
        validation_result = validate_appointment_create(
            appointment_date=cleaned_data['appointment_date'],
            appointment_time=cleaned_data['appointment_time'],
            duration_minutes=cleaned_data['duration_minutes'],
            room_code=room_code,
            exclude_appointment_code=None,
            guests=cleaned_data.get('guests', 1)
        )
        if not validation_result['valid']:
            errors.extend(validation_result['errors'])

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'cleaned_data': cleaned_data
    }


def _get_or_create_customer(phone, customer_name):
    """
    Tìm khách hàng theo SĐT, hoặc tạo mới nếu chưa có

    Returns: CustomerProfile object
    """
    from django.contrib.auth.models import User
    import secrets

    # Bước 1: Tìm hoặc tạo User
    try:
        user = User.objects.get(username=phone)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=phone,
            password=secrets.token_hex(16),
            first_name=customer_name.split()[0] if customer_name else '',
            last_name=' '.join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else ''
        )

    # Bước 2: Tìm hoặc tạo CustomerProfile
    customer, created = CustomerProfile.objects.get_or_create(
        phone=phone,
        defaults={'full_name': customer_name, 'user': user}
    )

    # Cập nhật tên nếu khác
    if not created and customer.full_name != customer_name:
        customer.full_name = customer_name
        customer.save()

    return customer


# =====================================================
# API: NOTIFICATION BADGE - PENDING BOOKING COUNT
# =====================================================

@require_http_methods(["GET"])
def api_booking_pending_count(request):
    """
    API: Lấy số lượng yêu cầu đặt lịch đang chờ (pending)

    FE gọi: GET /api/booking/pending-count/

    Trả về:
    {
        "success": true,
        "count": 5,  // Số lượng booking pending
        "timestamp": "2026-04-12T10:30:00"
    }

    Dùng cho notification badge trong sidebar/navbar
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
        return JsonResponse({
            'success': True,
            'count': count,
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Không thể lấy số lượng: {str(e)}',
            'count': 0
        }, status=500)
