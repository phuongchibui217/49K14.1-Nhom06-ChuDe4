"""
Views - Các trang web (render HTML)

File này chỉ chứa các views trả về TRANG WEB (HTML).
Tất cả API (trả về JSON) đã được chuyển sang api.py

Phân tách rõ ràng:
- views.py  → Trả về trang HTML (render template)
- api.py    → Trả về dữ liệu JSON (frontend gọi qua fetch)

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Appointment
from customers.models import CustomerProfile
from spa_services.models import Service
from .forms import AppointmentForm
from core.decorators import customer_required


# =====================================================
# TRANG ĐẶT LỊCH (Public)
# =====================================================

@customer_required()
def booking(request):
    """
    Trang đặt lịch hẹn (cho khách hàng)

    LUỒNG:
    1. Chưa login → Redirect sang trang login
    2. Staff/admin → Redirect về /manage/appointments/
    3. Đã login + có CustomerProfile → Hiển thị form đặt lịch
    4. POST form → Validate → Tạo Appointment → Redirect sang "Lịch hẹn của tôi"
    """
    customer_profile = request.user.customer_profile

    # Lấy service được chọn từ URL (nếu có)
    selected_service_id = request.GET.get('service')
    form = AppointmentForm()

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Lấy thông tin liên hệ từ form — chỉ dùng cho booking này,
            # KHÔNG cập nhật vào account/profile của user.
            contact_name  = request.POST.get('customer_name', '').strip()
            contact_phone = request.POST.get('customer_phone', '').strip()
            contact_email = request.POST.get('customer_email', '').strip()

            # Tạo lịch hẹn
            appointment = form.save(commit=False)
            appointment.customer = customer_profile
            appointment.source = 'ONLINE'
            appointment.status = 'PENDING'
            appointment.created_by = request.user

            # Snapshot thông tin liên hệ tại thời điểm đặt lịch.
            # Fallback về profile nếu user không nhập gì.
            appointment.customer_name_snapshot  = contact_name  or customer_profile.full_name or ''
            appointment.customer_phone_snapshot = contact_phone or customer_profile.phone or ''
            appointment.customer_email_snapshot = contact_email or (customer_profile.email or '')

            # Nếu có variant → gán duration từ variant
            variant = form.cleaned_data.get('service_variant')
            if variant:
                appointment.service_variant = variant
                appointment.duration_minutes = variant.duration_minutes
            else:
                first_variant = appointment.service.variants.filter(is_active=True).order_by('sort_order', 'duration_minutes').first()
                appointment.duration_minutes = first_variant.duration_minutes if first_variant else 60

            # Tính end_time
            from datetime import datetime as _dt, timedelta as _td
            if appointment.appointment_time and appointment.duration_minutes:
                start_dt = _dt.combine(_dt.today(), appointment.appointment_time)
                appointment.end_time = (start_dt + _td(minutes=appointment.duration_minutes)).time()

            # Gán phòng mặc định nếu chưa có (required field)
            if not appointment.room_id:
                from .models import Room as _Room
                default_room = _Room.objects.filter(is_active=True).first()
                if default_room:
                    appointment.room = default_room

            appointment.save()

            messages.success(
                request,
                f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}. Vui lòng chờ xác nhận.'
            )
            return redirect('appointments:my_appointments')
    else:
        if selected_service_id:
            form.fields['service'].initial = selected_service_id

    services = Service.objects.filter(status='ACTIVE').prefetch_related('variants')

    # Truyền variants data dạng JSON để JS render dropdown động
    import json as _json
    services_with_variants = {
        str(s.id): [
            {'id': v.id, 'label': v.label, 'duration_minutes': v.duration_minutes, 'price': float(v.price)}
            for v in s.variants.filter(is_active=True).order_by('sort_order', 'duration_minutes')
        ]
        for s in services
    }

    return render(request, 'appointments/booking.html', {
        'form': form,
        'services': services,
        'services_variants_json': _json.dumps(services_with_variants),
        'customer_profile': customer_profile,
    })


# =====================================================
# TRANG LỊCH HẸN CỦA TÔI
# =====================================================

@customer_required()
def my_appointments(request):
    """
    Trang xem lịch hẹn của khách hàng

    Hỗ trợ lọc theo trạng thái: ?status=pending|confirmed|completed|cancelled|all
    """
    try:
        customer_profile = request.user.customer_profile
        status_filter = request.GET.get('status', 'all')

        appointments = customer_profile.appointments.all()

        # Customer-facing filter groups:
        #   pending   → PENDING
        #   confirmed → NOT_ARRIVED, ARRIVED  (spa đã xác nhận, chờ đến / đang phục vụ)
        #   completed → COMPLETED
        #   cancelled → CANCELLED
        CUSTOMER_STATUS_MAP = {
            'pending':   ['PENDING'],
            'confirmed': ['NOT_ARRIVED', 'ARRIVED'],
            'completed': ['COMPLETED'],
            'cancelled': ['CANCELLED'],
        }

        if status_filter != 'all' and status_filter in CUSTOMER_STATUS_MAP:
            appointments = appointments.filter(status__in=CUSTOMER_STATUS_MAP[status_filter])

        appointments = appointments.order_by('-created_at')

        base_qs = customer_profile.appointments
        status_counts = {
            'pending':   base_qs.filter(status='PENDING').count(),
            'confirmed': base_qs.filter(status__in=['NOT_ARRIVED', 'ARRIVED']).count(),
            'completed': base_qs.filter(status='COMPLETED').count(),
            'cancelled': base_qs.filter(status='CANCELLED').count(),
        }
        status_counts['all'] = base_qs.count()

    except CustomerProfile.DoesNotExist:
        appointments = Appointment.objects.none()
        status_counts = {}
        status_filter = 'all'

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


# =====================================================
# TRANG HỦY LỊCH HẸN
# =====================================================

@customer_required()
def cancel_appointment(request, appointment_id):
    """
    Hủy lịch hẹn (cho khách hàng)

    Rules:
    - Chỉ hủy được khi status = 'pending' hoặc 'confirmed'
    - Chỉ chủ lịch hẹn mới được hủy
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Kiểm tra quyền
    if appointment.customer.user != request.user:
        messages.error(request, 'Bạn không có quyền hủy lịch hẹn này.')
        return redirect('appointments:my_appointments')

    # Kiểm tra trạng thái
    if appointment.status not in ['PENDING', 'NOT_ARRIVED']:
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
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, f'Đã hủy lịch hẹn {appointment.appointment_code}.')
        return redirect('appointments:my_appointments')


# =====================================================
# TRANG QUẢN LÝ LỊCH HẸN (Admin)
# =====================================================

@login_required(login_url='accounts:login')
def admin_appointments(request):
    """
    Trang quản lý lịch hẹn (cho staff/admin)

    Hiển thị scheduler với timeline grid.
    Dữ liệu được load qua API (api.py), không render trực tiếp.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

    return render(request, 'manage/pages/admin_appointments.html')