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
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.db import transaction
from django.template.loader import render_to_string

from .models import Appointment, Room
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
    appointments = Appointment.objects.exclude(
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
    """
    if not _is_staff(request.user):
        return _deny()

    try:
        appt = Appointment.objects.get(appointment_code=appointment_code)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    return JsonResponse({'success': True, 'appointment': serialize_appointment(appt)})


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

        # Bước 2: Tìm hoặc tạo khách hàng
        customer = _get_or_create_customer(
            phone=cleaned['phone'],
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
                    status__in=['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED']
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
                appointment_date=cleaned['appointment_date'],
                appointment_time=cleaned['appointment_time'],
                duration_minutes=cleaned['duration_minutes'],
                guests=cleaned['guests'],
                notes=cleaned['notes'],
                status=cleaned['status'],
                payment_status=cleaned['payment_status'],
                source='DIRECT',
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
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        raw_data = json.loads(request.body)

        # ===== BƯỚC 1: Thu thập data MỚI (KHÔNG modify appointment object) =====
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
                    appointment.service.variants.filter(is_active=True).order_by('sort_order').first().duration_minutes
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
                appointment_code=appointment_code
            )

            # Cập nhật khách hàng
            if new_customer_name:
                locked_appointment.customer.full_name = new_customer_name
                locked_appointment.customer.save()

            if new_phone:
                phone_digits = ''.join(filter(str.isdigit, new_phone))
                if phone_digits:
                    locked_appointment.customer.phone = phone_digits
                    locked_appointment.customer.save()

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
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
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
    API: Xóa lịch hẹn (HARD DELETE - xóa vĩnh viễn khỏi database)

    FE gọi: POST /api/appointments/APT001/delete/

    ⚠️ Lưu ý: Xóa thật, không thể khôi phục!
    """
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        # Lưu thông tin trước khi xóa để trả về
        customer_name = "Khách hàng"
        if appointment.customer and appointment.customer.user:
            customer_name = appointment.customer.user.get_full_name() or appointment.customer.user.username

        appointment_id = appointment.id

        # HARD DELETE
        appointment.delete()

        return JsonResponse({
            'success': True,
            'message': f'Đã xóa vĩnh viễn lịch hẹn {appointment_code}',
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
    appointments = Appointment.objects.filter(
        Q(source='ONLINE') | Q(source__isnull=True),
        status__in=['PENDING', 'CANCELLED']
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

    # Validate tên khách hàng
    customer_name = data.get('customer_name', '').strip()
    if not customer_name:
        errors.append('Vui lòng nhập tên khách hàng')
    else:
        cleaned_data['customer_name'] = customer_name

    # Validate SĐT
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    if not phone:
        errors.append('Vui lòng nhập số điện thoại')
    elif len(phone) < 10:
        errors.append('Số điện thoại không hợp lệ')
    else:
        cleaned_data['phone'] = phone

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
        first_variant = cleaned_data['service'].variants.filter(is_active=True).order_by('sort_order', 'duration_minutes').first()
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
        # Chỉ đếm PENDING — đây là yêu cầu chưa xử lý
        pending_count = Appointment.objects.filter(
            Q(source='ONLINE') | Q(source__isnull=True),
            status='PENDING'
        ).count()

        return JsonResponse({
            'success': True,
            'count': pending_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Không thể lấy số lượng: {str(e)}',
            'count': 0
        }, status=500)


def _booking_count_stream_generator():
    """
    SSE Stream generator để推送 số lượng booking pending real-time

    Yield: data: {JSON}\n\n
    """
    while True:
        try:
            # Chỉ đếm PENDING — đây là yêu cầu chưa xử lý
            pending_count = Appointment.objects.filter(
                Q(source='ONLINE') | Q(source__isnull=True),
                status='PENDING'
            ).count()

            # Format SSE response
            data = {
                'count': pending_count,
                'timestamp': datetime.now().isoformat()
            }

            yield f"data: {json.dumps(data)}\n\n"

            # Sleep 10 giây trước khi推送 tiếp
            time.sleep(10)

        except Exception as e:
            # Nếu có lỗi, log và tiếp tục
            error_data = {
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            time.sleep(10)


@require_http_methods(["GET"])
def api_booking_pending_count_stream(request):
    """
    API: SSE Stream để推送 số lượng booking pending real-time

    FE gọi: GET /api/booking/pending-count/stream/

    Server-Sent Events (SSE) stream:
    data: {"count": 5, "timestamp": "2026-04-12T10:30:00"}

    Dùng cho notification badge auto-update
    """
    if not _is_staff(request.user):
        return _deny()

    try:
        response = StreamingHttpResponse(
            _booking_count_stream_generator(),
            content_type='text/event-stream'
        )

        # Cấu hình SSE headers (KHÔNG set Connection header - WSGI tự handle)
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable Nginx buffering

        return response

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Stream error: {str(e)}'
        }, status=500)