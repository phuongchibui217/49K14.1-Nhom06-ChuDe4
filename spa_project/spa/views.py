from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Service, Appointment, ConsultationRequest, SupportRequest, CustomerProfile
from .forms import (
    CustomerRegistrationForm, AppointmentForm,
    ConsultationRequestForm, SupportRequestForm
)


# =====================================================
# VIEWS - Trang tĩnh (Đã cập nhật dùng Model)
# =====================================================


def home(request):
    """Trang chủ - Lấy 6 dịch vụ active"""
    services = Service.objects.filter(is_active=True)[:6]
    return render(request, 'spa/pages/home.html', {'services': services})


def about(request):
    """Về Spa ANA"""
    return render(request, 'spa/pages/about.html')


def service_list(request):
    """Danh sách dịch vụ - Lọc chỉ active"""
    services = Service.objects.filter(is_active=True)
    return render(request, 'spa/pages/services.html', {'services': services})


def service_detail(request, service_id):
    """Chi tiết dịch vụ - Lấy từ database"""
    service = get_object_or_404(Service, id=service_id, is_active=True)

    # Lấy các dịch vụ liên quan (cùng category)
    related_services = Service.objects.filter(
        category=service.category,
        is_active=True
    ).exclude(id=service_id)[:4]

    return render(request, 'spa/pages/service_detail.html', {
        'service': service,
        'related_services': related_services
    })


# =====================================================
# VIEWS - Forms (Đã implement)
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
        messages.warning(request, 'Vui lòng đăng nhập để đặt lịch hẹn.')
        return redirect(f'{reverse("login")}?next={reverse("booking")}')

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

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.customer = customer_profile
            appointment.save()
            messages.success(
                request,
                f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}'
            )
            return redirect('my_appointments')
    else:
        form = AppointmentForm()
        if selected_service_id:
            form.fields['service'].initial = selected_service_id

    # Lấy danh sách services cho dropdown
    services = Service.objects.filter(is_active=True)

    return render(request, 'spa/pages/booking.html', {
        'form': form,
        'services': services,
        'customer_profile': customer_profile,
    })


def consultation(request):
    """Đăng ký tư vấn"""
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đăng ký tư vấn thành công! Chúng tôi sẽ liên hệ sớm.')
            return redirect('home')
    else:
        form = ConsultationRequestForm()

    return render(request, 'spa/pages/consultation.html', {'form': form})


def complaint(request):
    """Góp ý/Khiếu nại"""
    if request.method == 'POST':
        form = SupportRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gửi góp ý thành công! Cảm ơn phản hồi của bạn.')
            return redirect('home')
    else:
        form = SupportRequestForm()

    return render(request, 'spa/pages/complaint.html', {'form': form})


@login_required
def my_appointments(request):
    """
    Lịch hẹn của tôi

    Features:
    - Lọc theo trạng thái: ?status=pending|confirmed|completed|cancelled|all
    - Sắp xếp theo ngày hẹn (mới nhất trước)
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

        # Sắp xếp: ngày hẹn gần nhất lên đầu
        appointments = appointments.order_by('-appointment_date', '-appointment_time')

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

    return render(request, 'spa/pages/my_appointments.html', {
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
        return redirect('my_appointments')

    # Kiểm tra trạng thái: chỉ hủy được khi pending hoặc confirmed
    if appointment.status not in ['pending', 'confirmed']:
        messages.warning(
            request,
            f'Không thể hủy lịch hẹn này. Trạng thái hiện tại: {appointment.get_status_display()}'
        )
        return redirect('my_appointments')

    # GET: Hiển thị trang xác nhận
    if request.method == 'GET':
        return render(request, 'spa/pages/cancel_appointment.html', {
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
        return redirect('my_appointments')


# =====================================================
# VIEWS - Authentication
# =====================================================


def login_view(request):
    """Đăng nhập - Username = Phone"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')  # Đây là phone
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Chào mừng {username}!')
            next_url = request.POST.get('next', request.GET.get('next', ''))
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Số điện thoại hoặc mật khẩu không đúng.')

    return render(request, 'spa/pages/login.html')


def register(request):
    """Đăng ký - Tạo User + CustomerProfile"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(
                request,
                f'Đăng ký thành công! Chào mừng {profile.full_name}'
            )
            # Auto-login sau đăng ký
            user = authenticate(
                request,
                username=form.cleaned_data['phone'],
                password=form.cleaned_data['password1']
            )
            if user is not None:
                login(request, user)
            return redirect('home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'spa/pages/register.html', {'form': form})


def logout_view(request):
    """Đăng xuất"""
    logout(request)
    messages.info(request, 'Đã đăng xuất!')
