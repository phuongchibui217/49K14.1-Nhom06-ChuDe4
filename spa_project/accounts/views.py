"""
Views cho Authentication

File này chứa các views cho:
- Đăng nhập, đăng ký, đăng xuất
- Quên mật khẩu / đặt lại mật khẩu

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
from django.urls import reverse
from customers.models import CustomerProfile
from customers.forms import CustomerRegistrationForm


# =====================================================
# VIEWS - Authentication
# =====================================================


def login_view(request):
    """
    Đăng nhập với UI Toggle: Khách hàng hoặc Nhân viên
    """
    if request.user.is_authenticated:
        return _redirect_by_role(request, request.user)

    if request.method == 'POST':
        role = request.POST.get('role', 'customer')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Tài khoản đã bị vô hiệu hóa.')
                return render(request, 'accounts/login.html', {'role': role})

            if role == 'staff' and not (user.is_staff or user.is_superuser):
                messages.error(request, 'Tài khoản này không có quyền truy cập hệ thống quản lý.')
                return render(request, 'accounts/login.html', {'role': role})

            if role == 'customer' and (user.is_staff or user.is_superuser):
                messages.error(request, 'Vui lòng đăng nhập bằng tab Nhân viên.')
                return render(request, 'accounts/login.html', {'role': role})

            login(request, user)

            remember_me = request.POST.get('remember')
            if remember_me:
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return _redirect_by_role(request, user, show_welcome=True)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')

        return render(request, 'accounts/login.html', {'role': role})

    return render(request, 'accounts/login.html', {'role': 'customer'})


def _redirect_by_role(request, user, show_welcome=False):
    """Helper function redirect theo role"""
    if user.is_staff or user.is_superuser:
        if show_welcome:
            full_name = user.get_full_name() or user.username
            role = "Quản trị viên" if user.is_superuser else "Nhân viên"
            messages.success(request, f'Chào mừng {full_name}! ({role})')
        return redirect('/manage/appointments/')

    try:
        profile = user.customer_profile
        if show_welcome:
            full_name = profile.full_name or user.username
            messages.success(request, f'Chào mừng {full_name}!')
        return redirect('appointments:my_appointments')
    except CustomerProfile.DoesNotExist:
        pass

    logout(request)
    messages.error(
        request,
        'Tài khoản chưa được phân quyền. Vui lòng liên hệ quản trị viên.'
    )
    return redirect('pages:home')


def register(request):
    """Đăng ký - Tạo User + CustomerProfile"""
    if request.user.is_authenticated:
        return redirect('pages:home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(
                request,
                f'Đăng ký thành công! Chào mừng {profile.full_name}'
            )
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user is not None:
                login(request, user)
            return redirect('pages:home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    """Đăng xuất"""
    logout(request)
    messages.info(request, 'Đã đăng xuất!')
    return redirect('pages:home')


# =====================================================
# VIEWS - Password Reset
# =====================================================


def password_reset_request(request):
    """Yêu cầu đặt lại mật khẩu"""
    if request.user.is_authenticated:
        return redirect('pages:home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Vui lòng nhập email.')
            return render(request, 'accounts/password_reset.html')

        user = User.objects.filter(email__iexact=email).first()
        profile = getattr(user, 'customer_profile', None) if user else None

        if user is None:
            messages.success(
                request,
                'Vui lòng kiểm tra email để đặt lại mật khẩu.'
            )
            return render(request, 'accounts/password_reset_sent.html', {
                'email': email,
            })

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = request.build_absolute_uri(
            reverse('accounts:password_reset_confirm', kwargs={
                'uidb64': uid,
                'token': token,
            })
        )

        display_name = (profile.full_name if profile else None) or user.username
        subject = 'Đặt lại mật khẩu - Spa ANA'
        message = f'''
Xin chào {display_name},

Bạn đã yêu cầu đặt lại mật khẩu tại Spa ANA.

Vui lòng click vào link dưới để đặt lại mật khẩu mới:
{reset_url}

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

        messages.success(
            request,
            f'Link đặt lại mật khẩu đã được gửi đến {email}.'
        )
        return render(request, 'accounts/password_reset_sent.html', {
            'email': email,
            'reset_url': reset_url
        })

    return render(request, 'accounts/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Xác nhận đặt lại mật khẩu"""
    if request.user.is_authenticated:
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
