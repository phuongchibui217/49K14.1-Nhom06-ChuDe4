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
from accounts.models import CustomerProfile
from spa_services.models import Service
from .forms import AppointmentForm


# =====================================================
# TRANG ĐẶT LỊCH (Public)
# =====================================================

def booking(request):
    """
    Trang đặt lịch hẹn (cho khách hàng)

    LUỒNG:
    1. Chưa login → Redirect sang trang login
    2. Đã login + chưa có profile → Tạo profile tự động
    3. Đã login + có profile → Hiển thị form đặt lịch
    4. POST form → Validate → Tạo Appointment → Redirect sang "Lịch hẹn của tôi"
    """
    # Chưa đăng nhập → chuyển sang login
    if not request.user.is_authenticated:
        messages.warning(request, 'Vui lòng đăng nhập để đặt lịch hên.')
        return redirect(f'/login/?next=/booking/')

    # Lấy hoặc tạo customer profile
    try:
        customer_profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        customer_profile = CustomerProfile.objects.create(
            user=request.user,
            phone=request.user.username,
            full_name=request.user.get_full_name() or request.user.username,
        )
        messages.info(request, 'Hồ sơ của bạn đã được tạo. Vui lòng cập nhật thông tin đầy đủ.')

    # Lấy service được chọn từ URL (nếu có)
    selected_service_id = request.GET.get('service')
    form = AppointmentForm()

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Cập nhật thông tin khách hàng
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

            # Tạo lịch hẹn
            appointment = form.save(commit=False)
            appointment.customer = customer_profile
            appointment.source = 'web'
            appointment.status = 'pending'
            appointment.save()

            messages.success(
                request,
                f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}. Vui lòng chờ xác nhận.'
            )
            return redirect('appointments:my_appointments')
    else:
        if selected_service_id:
            form.fields['service'].initial = selected_service_id

    services = Service.objects.filter(is_active=True)

    return render(request, 'appointments/booking.html', {
        'form': form,
        'services': services,
        'customer_profile': customer_profile,
    })


# =====================================================
# TRANG LỊCH HẸN CỦA TÔI
# =====================================================

@login_required
def my_appointments(request):
    """
    Trang xem lịch hẹn của khách hàng

    Hỗ trợ lọc theo trạng thái: ?status=pending|confirmed|completed|cancelled|all
    """
    try:
        customer_profile = request.user.customer_profile
        status_filter = request.GET.get('status', 'all')

        appointments = customer_profile.appointments.all()

        if status_filter != 'all':
            appointments = appointments.filter(status=status_filter)

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


# =====================================================
# TRANG HỦY LỊCH HẸN
# =====================================================

@login_required
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