from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Appointment, Room
from spa_services.models import Service, ServiceVariant
from .forms import AppointmentForm
from core.decorators import customer_required


# =====================================================
# TRANG ĐẶT LỊCH (Public — khách hàng) ok - booking.html
# =====================================================

@customer_required()
def booking(request):
    """Trang đặt lịch hẹn cho khách hàng."""
    customer_profile = request.user.customer_profile

    if request.method == 'POST':
        form = AppointmentForm(request.POST, customer_profile=customer_profile)
        if form.is_valid():
            # Form đã validate hết (bao gồm giờ kết thúc), chỉ cần tạo appointment
            booker_name = form.cleaned_data['booker_name']
            booker_phone = form.cleaned_data['booker_phone']

            # Customer snapshot
            customer_name_snapshot = request.POST.get('customer_name_snapshot', '').strip() or booker_name
            _raw_phone = request.POST.get('customer_phone_snapshot', '').strip()
            customer_phone_snapshot = ''.join(filter(str.isdigit, _raw_phone)) or None
            customer_email_snapshot = request.POST.get('customer_email_snapshot', '').strip() or None

            # Tìm hoặc tạo customer
            from .api import _get_or_create_customer
            customer = _get_or_create_customer(phone=booker_phone, customer_name=booker_name)

            # Gán phòng mặc định
            default_room = Room.objects.filter(is_active=True).order_by('code').first()
            if not default_room:
                messages.error(request, 'Hiện tại chưa có phòng nào. Vui lòng liên hệ trực tiếp.')
                return _render_booking_form(request, form, customer_profile)

            # Tạo appointment
            appointment = form.save(commit=False)
            appointment.customer = customer
            appointment.room = default_room
            appointment.source = 'ONLINE'
            appointment.status = 'PENDING'
            appointment.created_by = request.user
            appointment.booker_email = customer_profile.user.email
            appointment.customer_name_snapshot = customer_name_snapshot
            appointment.customer_phone_snapshot = customer_phone_snapshot
            appointment.customer_email_snapshot = customer_email_snapshot
            appointment.save()

            messages.success(request, f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}. Vui lòng chờ xác nhận.')
            return redirect('appointments:my_appointments')
    else:
        form = AppointmentForm(customer_profile=customer_profile)

    return _render_booking_form(request, form, customer_profile)


def _render_booking_form(request, form, customer_profile):
    """Helper function render booking form với services data."""
    services = Service.objects.filter(status='ACTIVE').prefetch_related('variants')

    import json as _json
    services_with_variants = {
        str(s.id): [
            {'id': v.id, 'label': v.label, 'duration_minutes': v.duration_minutes, 'price': float(v.price)}
            for v in s.variants.order_by('sort_order', 'duration_minutes')
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
# TRANG LỊCH HẸN CỦA TÔI - My_appointment.html
#  view này giống như nhân viên lễ tân: nhận yêu cầu "Cho tôi xem lịch hẹn", mở hồ sơ khách hàng, lọc lịch theo status (tất cả, đang chờ, hoàn thành), đếm có bao nhiêu lịch mỗi loại theo status, hiển thị danh sách và số lượng status-count
# =====================================================

@customer_required()
def my_appointments(request):
    """Trang xem lịch hẹn của khách hàng."""
    customer_profile = request.user.customer_profile
    status_filter = request.GET.get('status', 'all')

    appointments = customer_profile.appointments.filter(deleted_at__isnull=True)

    CUSTOMER_STATUS_MAP = {
        'pending':   ['PENDING'],
        'confirmed': ['NOT_ARRIVED', 'ARRIVED'],
        'completed': ['COMPLETED'],
        'cancelled': ['CANCELLED'],
        'rejected':  ['REJECTED'],
    }

    if status_filter != 'all' and status_filter in CUSTOMER_STATUS_MAP:
        appointments = appointments.filter(status__in=CUSTOMER_STATUS_MAP[status_filter])

    appointments = appointments.order_by('-created_at')

    base_qs = customer_profile.appointments.filter(deleted_at__isnull=True)
    status_counts = {
        'pending':   base_qs.filter(status='PENDING').count(),
        'confirmed': base_qs.filter(status__in=['NOT_ARRIVED', 'ARRIVED']).count(),
        'completed': base_qs.filter(status='COMPLETED').count(),
        'cancelled': base_qs.filter(status='CANCELLED').count(),
        'rejected':  base_qs.filter(status='REJECTED').count(),
    }
    status_counts['all'] = base_qs.count()

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


# =====================================================
# HỦY LỊCH HẸN
# =====================================================

@customer_required()
def cancel_appointment(request, appointment_id):
    """Hủy lịch hẹn (khách hàng)."""
    appointment = get_object_or_404(Appointment, id=appointment_id, deleted_at__isnull=True)

    if appointment.status not in ['PENDING', 'NOT_ARRIVED']:
        messages.warning(request, f'Không thể hủy lịch hẹn này. Trạng thái: {appointment.get_status_display()}')
        return redirect('appointments:my_appointments')

    appointment.status = 'CANCELLED'
    appointment.cancelled_by = 'customer'
    appointment.save()
    messages.success(request, f'Đã hủy lịch hẹn {appointment.appointment_code}.')
    return redirect('appointments:my_appointments')


# =====================================================
# TRANG QUẢN LÝ LỊCH HẸN (Admin)
# =====================================================

from django.contrib.auth.decorators import login_required

@login_required(login_url='accounts:login')
def admin_appointments(request):
    """Trang quản lý lịch hẹn (staff/admin)."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

    return render(request, 'manage/pages/admin_appointments.html')
