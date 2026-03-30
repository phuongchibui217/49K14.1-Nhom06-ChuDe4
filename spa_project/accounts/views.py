"""
Views cho Authentication và Customer Profile

File này chứa các views cho:
- Đăng nhập, đăng ký, đăng xuất
- Quên mật khẩu / đặt lại mật khẩu
- Trang tài khoản khách hàng

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

# Tạm import từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import CustomerProfile

# Forms (sẽ tạo trong accounts/forms.py)
from .forms import (
    CustomerRegistrationForm,
    CustomerProfileForm,
    ChangePasswordForm,
)


# =====================================================
# VIEWS - Authentication
# =====================================================


def login_view(request):
    """Đăng nhập - Username = Phone"""
    if request.user.is_authenticated:
        # Home đã chuyển sang pages app
        return redirect('pages:home')

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
            # Home đã chuyển sang pages app
            return redirect('pages:home')
        else:
            messages.error(request, 'Số điện thoại hoặc mật khẩu không đúng.')

    return render(request, 'accounts/login.html')


def register(request):
    """Đăng ký - Tạo User + CustomerProfile"""
    if request.user.is_authenticated:
        # Home đã chuyển sang pages app
        return redirect('pages:home')

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
            # Home đã chuyển sang pages app
            return redirect('pages:home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Đăng xuất"""
    logout(request)
    messages.info(request, 'Đã đăng xuất!')
    # Home đã chuyển sang pages app
    return redirect('pages:home')


# =====================================================
# VIEWS - Password Reset
# =====================================================


def password_reset_request(request):
    """
    Yêu cầu đặt lại mật khẩu

    Sử dụng email để gửi link đặt lại mật khẩu
    """
    if request.user.is_authenticated:
        # Home đã chuyển sang pages app
        return redirect('pages:home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Vui lòng nhập email.')
            return render(request, 'accounts/password_reset.html')

        # Tìm user theo email
        try:
            user = User.objects.get(email=email)

            # Gửi email đặt lại mật khẩu sử dụng Django's built-in
            # Tạo token đặt lại mật khẩu
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Tạo link đặt lại mật khẩu
            # Login view vẫn ở spa, nhưng redirect qua accounts
            reset_url = request.build_absolute_uri(
                '/reset-mat-khau/{0}/{1}/'.format(uid, token)
            )

            # Gửi email
            subject = 'Đặt lại mật khẩu - Spa ANA'
            message = f'''
Xin chào {user.get_full_name() or user.username},

Bạn đã yêu cầu đặt lại mật khẩu tại Spa ANA.

Vui lòng click vào link dưới để đặt lại mật khẩu mới:
{reset_url}

Link này sẽ hết hạn sau 24 giờ.

Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.

Trân trọng,
Đội ngũ Spa ANA
'''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, f'Link đặt lại mật khẩu đã được gửi đến {email}. Vui lòng kiểm tra email của bạn.')
            return render(request, 'accounts/password_reset_sent.html', {
                'email': email,
            })

        except User.DoesNotExist:
            # Không tiết lộ user có tồn tại hay không
            messages.success(request, 'Nếu email tồn tại trong hệ thống, bạn sẽ nhận được link đặt lại mật khẩu.')
            return render(request, 'accounts/password_reset_sent.html', {
                'email': email,
            })

    return render(request, 'accounts/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """
    Xác nhận đặt lại mật khẩu

    Cho phép người dùng đặt mật khẩu mới từ link trong email
    """
    if request.user.is_authenticated:
        # Home đã chuyển sang pages app
        return redirect('pages:home')

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not new_password:
                messages.error(request, 'Vui lòng nhập mật khẩu mới.')
            elif len(new_password) < 6:
                messages.error(request, 'Mật khẩu phải có ít nhất 6 ký tự.')
            elif new_password != confirm_password:
                messages.error(request, 'Mật khẩu xác nhận không khớp.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Đặt lại mật khẩu thành công! Vui lòng đăng nhập với mật khẩu mới.')
                return redirect('accounts:login')

        return render(request, 'accounts/password_reset_confirm.html', {
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 'Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.')
        return redirect('accounts:password_reset')


# =====================================================
# VIEWS - Customer Account
# =====================================================


@login_required
def customer_profile(request):
    """
    Tài khoản cá nhân của khách hàng

    Features:
    - Xem thông tin tài khoản
    - Cập nhật thông tin cá nhân
    - Đổi mật khẩu
    """
    # Lấy hoặc tạo customer profile
    try:
        customer_profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        customer_profile = CustomerProfile.objects.create(
            user=request.user,
            phone=request.user.username,
            full_name=request.user.get_full_name() or request.user.username,
        )

    # Khởi tạo forms
    profile_form = CustomerProfileForm(instance=customer_profile)
    password_form = None

    # Xử lý cập nhật thông tin
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_profile':
            profile_form = CustomerProfileForm(request.POST, instance=customer_profile)
            if profile_form.is_valid():
                # Lưu thông tin cập nhật
                profile_form.save()
                messages.success(request, 'Cập nhật thông tin thành công!')
                return redirect('accounts:customer_profile')
            else:
                messages.error(request, 'Vui lòng kiểm tra lại thông tin.')

        elif action == 'change_password':
            password_form = ChangePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.')
                logout(request)
                return redirect('accounts:login')
            else:
                messages.error(request, 'Đổi mật khẩu thất bại. Vui lòng kiểm tra lại.')

    # Thống kê
    appointments_count = customer_profile.appointments.count()
    completed_appointments = customer_profile.appointments.filter(status='completed').count()
    pending_appointments = customer_profile.appointments.filter(status='pending').count()

    context = {
        'customer_profile': customer_profile,
        'profile_form': profile_form,
        'password_form': password_form or ChangePasswordForm(request.user),
        'appointments_count': appointments_count,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
    }

    return render(request, 'accounts/customer_profile.html', context)
