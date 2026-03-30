"""
Views cho Appointment Management

File này chứa các views cho:
- Đặt lịch hẹn (booking page)
- Lịch hẹn của tôi (my appointments)
- Hủy lịch hẹn
- Quản lý lịch hẹn (admin scheduler)
- API endpoints cho appointments và rooms

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
import json

# TẠM IMPORT từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import Appointment
from accounts.models import CustomerProfile
from spa_services.models import Service
# Batch 1: Room bridge - import from appointments.models (managed=False)
from .models import Room

# Forms từ appointments/forms
from .forms import AppointmentForm

# Service layer từ appointments
from .services import (
    validate_appointment_create,
    check_room_availability,
    get_min_booking_date
)
from .appointment_services import (
    parse_appointment_data,
    validate_appointment_data,
    get_or_create_customer,
    create_appointment,
    update_appointment,
    serialize_appointment,
    serialize_appointments,
)

# API response từ core
from core.api_response import staff_api, get_or_404


# =====================================================
# PUBLIC APPOINTMENT PAGES
# =====================================================

def booking(request):
    """
    Đặt lịch hẹn

    QUYẾT THIẾT: BẮT BUỘC ĐĂNG NHẬP
    - Lý do: Đảm bảo thông tin khách hàng chính xác
    - Giảm spam booking
    - Dễ quản lý và liên hệ
    - Theo dõi lịch sử khách hàng

    Flow:
    1. Chưa login → Redirect sang login với next=booking
    2. Đã login nhưng chưa có profile → Tạo profile tự động
    3. Đã login + có profile → Hiển thị form booking
    4. POST → Validate → Tạo Appointment → Redirect my-appointments
    """
    # Redirect nếu chưa đăng nhập
    if not request.user.is_authenticated:
        messages.warning(request, 'Vui lòng đăng nhập để đặt lịch hên.')
        return redirect(f'/login/?next=/booking/')

    # Lấy hoặc tạo customer profile
    try:
        customer_profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        # Tạo profile tự động nếu chưa có
        customer_profile = CustomerProfile.objects.create(
            user=request.user,
            phone=request.user.username,
            full_name=request.user.get_full_name() or request.user.username,
        )
        messages.info(request, 'Hồ sơ của bạn đã được tạo. Vui lòng cập nhật thông tin đầy đủ.')

    # Lấy service được chọn từ URL parameter (nếu có)
    selected_service_id = request.GET.get('service')

    # Khởi tạo form
    form = AppointmentForm()

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Cập nhật thông tin khách hàng từ form
            customer_name = request.POST.get('customer_name', '').strip()
            customer_phone = request.POST.get('customer_phone', '').strip()
            customer_email = request.POST.get('customer_email', '').strip()

            if customer_name:
                customer_profile.full_name = customer_name
            if customer_phone:
                customer_profile.phone = customer_phone
            if customer_email:
                customer_profile.email = customer_email
            customer_profile.save()

            appointment = form.save(commit=False)
            appointment.customer = customer_profile
            appointment.source = 'web'  # Đánh dấu là đặt từ web
            appointment.status = 'pending'  # Chờ xác nhận
            appointment.save()
            messages.success(
                request,
                f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}. Vui lòng chờ xác nhận từ Spa.'
            )
            return redirect('appointments:my_appointments')
    else:
        # GET request - set initial service nếu có
        if selected_service_id:
            form.fields['service'].initial = selected_service_id

    # Lấy danh sách services cho dropdown
    services = Service.objects.filter(is_active=True)

    return render(request, 'appointments/booking.html', {
        'form': form,
        'services': services,
        'customer_profile': customer_profile,
    })


@login_required
def my_appointments(request):
    """
    Lịch hẹn của tôi

    Features:
    - Lọc theo trạng thái: ?status=pending|confirmed|completed|cancelled|all
    - Sắp xếp theo người đặt gần nhất (created_at)
    - Đếm số lượng theo từng trạng thái
    """
    try:
        customer_profile = request.user.customer_profile

        # Lọc theo status từ query parameter
        status_filter = request.GET.get('status', 'all')

        # Base query - chỉ lấy appointments của user hiện tại
        appointments = customer_profile.appointments.all()

        # Apply status filter nếu không phải 'all'
        if status_filter != 'all':
            appointments = appointments.filter(status=status_filter)

        # Sắp xếp: người đặt gần nhất lên đầu
        appointments = appointments.order_by('-created_at')

        # Đếm số lượng theo từng trạng thái
        status_counts = {}
        for status_choice, _ in Appointment.STATUS_CHOICES:
            status_counts[status_choice] = customer_profile.appointments.filter(
                status=status_choice
            ).count()
        status_counts['all'] = customer_profile.appointments.count()

    except CustomerProfile.DoesNotExist:
        appointments = Appointment.objects.none()
        status_counts = {}
        status_filter = 'all'

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


@login_required
def cancel_appointment(request, appointment_id):
    """
    Hủy lịch hẹn

    Rules:
    - Chỉ cho phép hủy khi status = 'pending' hoặc 'confirmed'
    - Chỉ chủ appointment mới được hủy
    - Dùng POST để thực sự hủy (GET hiển thị confirm)
    - Cập nhật status thành 'cancelled'
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Kiểm tra quyền: chỉ chủ appointment mới được hủy
    if appointment.customer.user != request.user:
        messages.error(request, 'Bạn không có quyền hủy lịch hẹn này.')
        return redirect('appointments:my_appointments')

    # Kiểm tra trạng thái: chỉ hủy được khi pending hoặc confirmed
    if appointment.status not in ['pending', 'confirmed']:
        messages.warning(
            request,
            f'Không thể hủy lịch hẹn này. Trạng thái hiện tại: {appointment.get_status_display()}'
        )
        return redirect('appointments:my_appointments')

    # GET: Hiển thị trang xác nhận
    if request.method == 'GET':
        return render(request, 'appointments/cancel_appointment.html', {
            'appointment': appointment
        })

    # POST: Thực hiện hủy
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(
            request,
            f'Đã hủy lịch hẹn {appointment.appointment_code}.'
        )
        return redirect('appointments:my_appointments')


# =====================================================
# ADMIN APPOINTMENT MANAGEMENT
# =====================================================

@login_required(login_url='/manage/login/')
def admin_appointments(request):
    """Quản lý lịch hẹn"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')
    return render(request, 'admin/pages/admin_appointments.html')


# =====================================================
# API ENDPOINTS FOR ROOMS
# =====================================================

@require_http_methods(["GET"])
def api_rooms_list(request):
    """API: Lấy danh sách phòng"""
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)

    rooms = Room.objects.filter(is_active=True).order_by('code')
    rooms_data = []

    for room in rooms:
        rooms_data.append({
            'id': room.code,
            'name': room.name,
            'capacity': room.capacity,
        })

    return JsonResponse({'success': True, 'rooms': rooms_data})


# =====================================================
# API ENDPOINTS FOR APPOINTMENTS
# =====================================================

@require_http_methods(["GET"])
def api_appointments_list(request):
    """
    API: Lấy danh sách lịch hẹn

    Query params:
    - date: YYYY-MM-DD (lọc theo ngày)
    - status: pending|confirmed|completed|cancelled
    - source: web|admin
    - room: room code
    - q: search term
    """
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)

    appointments = Appointment.objects.all()

    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Filter by source
    source_filter = request.GET.get('source', '')
    if source_filter:
        appointments = appointments.filter(source=source_filter)

    # Filter by room
    room_filter = request.GET.get('room', '')
    if room_filter:
        appointments = appointments.filter(room__code=room_filter)

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )

    appointments = appointments.order_by('appointment_date', 'appointment_time')

    appointments_data = []
    for appt in appointments:
        appointments_data.append({
            'id': appt.appointment_code,
            'customerName': appt.customer.full_name,
            'phone': appt.customer.phone,
            'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
            'service': appt.service.name,
            'serviceId': appt.service.id,
            'roomId': appt.room.code if appt.room else '',
            'roomName': appt.room.name if appt.room else '',
            'guests': appt.guests,
            'date': appt.appointment_date.strftime('%Y-%m-%d'),
            'start': appt.appointment_time.strftime('%H:%M'),
            'end': appt.get_end_time_display(),
            'durationMin': appt.duration_minutes or appt.service.duration_minutes,
            'note': appt.notes or '',
            'apptStatus': appt.status,
            'payStatus': appt.payment_status,
            'source': appt.source or 'admin',
        })

    return JsonResponse({'success': True, 'appointments': appointments_data})


@require_http_methods(["GET"])
def api_appointment_detail(request, appointment_code):
    """API: Lấy chi tiết một lịch hẹn"""
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)

    try:
        appt = Appointment.objects.get(appointment_code=appointment_code)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)

    data = {
        'id': appt.appointment_code,
        'customerName': appt.customer.full_name,
        'phone': appt.customer.phone,
        'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
        'service': appt.service.name,
        'serviceId': appt.service.id,
        'roomId': appt.room.code if appt.room else '',
        'roomName': appt.room.name if appt.room else '',
        'guests': appt.guests,
        'date': appt.appointment_date.strftime('%Y-%m-%d'),
        'start': appt.appointment_time.strftime('%H:%M'),
        'end': appt.get_end_time_display(),
        'durationMin': appt.duration_minutes or appt.service.duration_minutes,
        'note': appt.notes or '',
        'apptStatus': appt.status,
        'payStatus': appt.payment_status,
        'source': appt.source or 'admin',
    }

    return JsonResponse({'success': True, 'appointment': data})


@require_http_methods(["POST"])
@staff_api
def api_appointment_create(request):
    """
    API: Tạo lịch hẹn mới từ admin

    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    - Validation tập trung qua services.py
    """

    try:
        data = json.loads(request.body)

        # Required fields
        customer_name = data.get('customerName', '').strip()
        phone = data.get('phone', '').strip()
        service_id = data.get('serviceId') or data.get('service')
        room_id = data.get('roomId') or data.get('room')
        date_str = data.get('date', '')
        time_str = data.get('time') or data.get('start', '')
        duration = data.get('duration') or data.get('durationMin', 60)
        guests = data.get('guests', 1)
        notes = data.get('note', '')
        status = data.get('apptStatus', 'not_arrived')
        pay_status = data.get('payStatus', 'unpaid')

        # Validation
        if not customer_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập tên khách hàng'}, status=400)

        if not phone:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập số điện thoại'}, status=400)

        # Clean phone number
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 10:
            return JsonResponse({'success': False, 'error': 'Số điện thoại không hợp lệ'}, status=400)

        if not service_id:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn dịch vụ'}, status=400)

        if not date_str:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn ngày hẹn'}, status=400)

        if not time_str:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn giờ hẹn'}, status=400)

        # Get or create customer
        customer, created = CustomerProfile.objects.get_or_create(
            phone=phone,
            defaults={'full_name': customer_name}
        )
        if not created and customer.full_name != customer_name:
            customer.full_name = customer_name
            customer.save()

        # Get service
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Dịch vụ không tồn tại'}, status=400)

        # Get room
        room = None
        if room_id:
            try:
                room = Room.objects.get(code=room_id)
            except Room.DoesNotExist:
                pass

        # Parse date and time
        from datetime import datetime
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Định dạng ngày không hợp lệ'}, status=400)

        try:
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Định dạng giờ không hợp lệ'}, status=400)

        # =====================================================
        # VALIDATION: Ngày quá khứ + Phòng trống
        # Sử dụng services.py để validate tập trung
        # =====================================================
        duration_minutes = int(duration) if duration else service.duration_minutes

        # Validate ngày và giờ (bao gồm timezone)
        validation_result = validate_appointment_create(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=duration_minutes,
            room_code=room_id if room_id else None,
            exclude_appointment_code=None  # Tạo mới nên không cần exclude
        )

        if not validation_result['valid']:
            # Trả về lỗi validation (đã có message tiếng Việt rõ ràng)
            return JsonResponse({
                'success': False,
                'error': validation_result['errors'][0]  # Lấy lỗi đầu tiên
            }, status=400)

        # Create appointment
        appointment = Appointment.objects.create(
            customer=customer,
            service=service,
            room=room,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=int(duration),
            guests=int(guests),
            notes=notes,
            status=status,
            payment_status=pay_status,
            source='admin',
            created_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'message': f'Tạo lịch hẹn thành công! Mã: {appointment.appointment_code}',
            'appointment': {
                'id': appointment.appointment_code,
                'customerName': appointment.customer.full_name,
                'phone': appointment.customer.phone,
                'service': appointment.service.name,
                'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'start': appointment.appointment_time.strftime('%H:%M'),
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """
    API: Cập nhật lịch hẹn

    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        data = json.loads(request.body)

        # Update fields
        if 'customerName' in data:
            appointment.customer.full_name = data['customerName'].strip()
            appointment.customer.save()

        if 'phone' in data:
            phone = ''.join(filter(str.isdigit, data['phone']))
            appointment.customer.phone = phone
            appointment.customer.save()

        if 'serviceId' in data or 'service' in data:
            service_id = data.get('serviceId') or data.get('service')
            try:
                appointment.service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                pass

        if 'roomId' in data or 'room' in data:
            room_id = data.get('roomId') or data.get('room')
            if room_id:
                try:
                    appointment.room = Room.objects.get(code=room_id)
                except Room.DoesNotExist:
                    appointment.room = None
            else:
                appointment.room = None

        if 'date' in data:
            from datetime import datetime
            appointment.appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

        if 'time' in data or 'start' in data:
            from datetime import datetime
            time_str = data.get('time') or data.get('start')
            appointment.appointment_time = datetime.strptime(time_str, '%H:%M').time()

        if 'duration' in data or 'durationMin' in data:
            appointment.duration_minutes = int(data.get('duration') or data.get('durationMin'))

        if 'guests' in data:
            appointment.guests = int(data['guests'])

        if 'note' in data:
            appointment.notes = data['note']

        if 'apptStatus' in data:
            appointment.status = data['apptStatus']

        if 'payStatus' in data:
            appointment.payment_status = data['payStatus']

        appointment.save()

        return JsonResponse({
            'success': True,
            'message': f'Cập nhật lịch hẹn {appointment_code} thành công'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST"])
@staff_api
def api_appointment_status(request, appointment_code):
    """
    API: Đổi trạng thái lịch hẹn

    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')

        valid_statuses = ['pending', 'not_arrived', 'arrived', 'completed', 'cancelled']
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
    """
    API: Xóa lịch hẹn (HARD DELETE - xóa vĩnh viễn khỏi database)

    Thay đổi từ soft delete sang hard delete:
    - Xóa thật bản ghi khỏi database
    - Không chỉ chuyển status sang cancelled
    - Không thể khôi phục sau khi xóa

    Security:
    - CSRF protection qua @staff_api decorator
    - Chỉ staff/superuser mới được xóa
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        # Lưu thông tin để log trước khi xóa
        appointment_id = appointment.id

        # Lấy tên khách hàng từ ForeignKey
        customer_name = "Khách hàng"
        if appointment.customer and appointment.customer.user:
            customer_name = appointment.customer.user.get_full_name() or appointment.customer.user.username

        # HARD DELETE - xóa thật khỏi database
        appointment.delete()

        return JsonResponse({
            'success': True,
            'message': f'Đã xóa vĩnh viễn lịch hẹn {appointment_code}',
            'deleted_id': appointment_id,
            'customer_name': customer_name
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Không thể xóa lịch hẹn: {str(e)}'
        }, status=400)


@require_http_methods(["GET"])
def api_booking_requests(request):
    """
    API: Lấy danh sách yêu cầu đặt lịch từ web (source='web' hoặc NULL)

    Query params:
    - date: YYYY-MM-DD
    - status: pending|confirmed|cancelled
    - q: search term

    NOTE: Bao gồm cả record có source=NULL để hỗ trợ dữ liệu cũ
    """
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)

    # Lấy cả record có source='web' hoặc source=NULL (dữ liệu cũ)
    appointments = Appointment.objects.filter(Q(source='web') | Q(source__isnull=True))

    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )

    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    appointments_data = []
    for appt in appointments:
        appointments_data.append({
            'id': appt.appointment_code,
            'customerName': appt.customer.full_name,
            'phone': appt.customer.phone,
            'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
            'service': appt.service.name,
            'serviceId': appt.service.id,
            'roomId': appt.room.code if appt.room else '',
            'roomName': appt.room.name if appt.room else '',
            'guests': appt.guests,
            'date': appt.appointment_date.strftime('%Y-%m-%d'),
            'start': appt.appointment_time.strftime('%H:%M'),
            'end': appt.get_end_time_display(),
            'durationMin': appt.duration_minutes or appt.service.duration_minutes,
            'note': appt.notes or '',
            'apptStatus': appt.status,
            'payStatus': appt.payment_status,
            'source': appt.source or 'web',
        })

    return JsonResponse({'success': True, 'appointments': appointments_data})
