from django.shortcuts import render, redirect, get_object_or_404
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
    """Đặt lịch hẹn"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Vui lòng đăng nhập để đặt lịch.')
        return redirect('login')

    try:
        customer_profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        messages.error(request, 'Vui lòng cập nhật thông tin profile.')
        return redirect('my_appointments')

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

    return render(request, 'spa/pages/booking.html', {'form': form})


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
    """Lịch hẹn của tôi"""
    try:
        customer_profile = request.user.customer_profile
        appointments = customer_profile.appointments.all()
    except CustomerProfile.DoesNotExist:
        appointments = []

    return render(request, 'spa/pages/my_appointments.html', {
        'appointments': appointments
    })


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
                f'Dăng ký thành công! Chào mừng {profile.full_name}'
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
    return redirect('home')
