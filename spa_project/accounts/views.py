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

from .models import CustomerProfile
from .forms import (
    CustomerRegistrationForm,
    CustomerProfileForm,
    ChangePasswordForm,
)



# =====================================================
# VIEWS - Authentication
# =====================================================


def login_view(request):
    """
    Đăng nhập với UI Toggle: Khách hàng hoặc Nhân viên

    Hỗ trợ:
    - Khách hàng → đăng nhập bằng SỐ ĐIỆN THOẠI
    - Nhân viên (Lễ tân/Chủ spa) → đăng nhập bằng USERNAME

    Flow:
    1. User chọn role (customer/staff)
    2. Nhập thông tin tương ứng
    3. Backend validate theo role
    4. Redirect theo role
    """
    # Nếu đã đăng nhập → redirect theo role
    if request.user.is_authenticated:
        return _redirect_by_role(request, request.user)

    if request.method == 'POST':
        role = request.POST.get('role', 'customer')  # Mặc định là customer
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validate theo role
        if role == 'customer':
            # KHÁCH HÀNG: Login bằng phone, phải có CustomerProfile
            try:
                profile = CustomerProfile.objects.get(phone=username)
                user = profile.user
                # Check password
                if user.check_password(password):
                    if not user.is_active:
                        messages.error(request, 'Tài khoản đã bị vô hiệu hóa.')
                        return render(request, 'accounts/login.html', {'role': role})
                    login(request, user)

                    # Xử lý remember_me
                    remember_me = request.POST.get('remember')
                    if remember_me:
                        request.session.set_expiry(1209600)  # 14 ngày
                    else:
                        request.session.set_expiry(0)  # Session cookie

                    return _redirect_by_role(request, user, show_welcome=True)
                else:
                    messages.error(request, 'Số điện thoại hoặc mật khẩu không đúng.')
            except CustomerProfile.DoesNotExist:
                messages.error(request, 'Số điện thoại chưa được đăng ký.')

        elif role == 'staff':
            # NHÂN VIÊN: Login bằng username, phải có is_staff=True
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Debug: Print user info
                print(f"DEBUG: Staff login attempt - User: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")

                if not (user.is_staff or user.is_superuser):
                    messages.error(request, 'Tài khoản này không có quyền truy cập hệ thống quản lý.')
                    return render(request, 'accounts/login.html', {'role': role})
                login(request, user)

                # Debug: Confirm login
                print(f"DEBUG: Login successful for {user.username}")

                # Xử lý remember_me
                remember_me = request.POST.get('remember')
                if remember_me:
                    request.session.set_expiry(1209600)  # 14 ngày
                else:
                    request.session.set_expiry(0)  # Session cookie

                # FORCE SAVE SESSION để đảm bảo is_staff được lưu
                # Debug: Before redirect
                print(f"DEBUG: About to redirect to /manage/appointments/")
                result = _redirect_by_role(request, user, show_welcome=True)
                print(f"DEBUG: Redirect result: {result}")
                return result
            else:
                print(f"DEBUG: Staff authentication FAILED for username: {username}")
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')

        return render(request, 'accounts/login.html', {'role': role})

    return render(request, 'accounts/login.html', {'role': 'customer'})


def _redirect_by_role(request, user, show_welcome=False):
    """
    Helper function redirect theo role

    Args:
        request: HttpRequest object
        user: User object
        show_welcome: Có hiển thị message chào mừng không

    Returns:
        HttpResponseRedirect
    """
    # Debug: Print user info
    print(f"DEBUG _redirect_by_role: User={user.username}, is_staff={user.is_staff}, is_superuser={user.is_superuser}")

    # 1. Khách hàng (có CustomerProfile)
    try:
        profile = user.customer_profile
        print(f"DEBUG: User has CustomerProfile, redirecting to my_appointments")
        if show_welcome:
            full_name = profile.full_name or user.username
            messages.success(request, f'Chào mừng {full_name}!')
        return redirect('appointments:my_appointments')
    except CustomerProfile.DoesNotExist:
        print(f"DEBUG: No CustomerProfile, checking staff status")
        pass

    # 2. Lễ tân hoặc Chủ Spa (is_staff hoặc is_superuser)
    if user.is_staff or user.is_superuser:
        print(f"DEBUG: User is staff/superuser, redirecting to /manage/appointments/")
        if show_welcome:
            full_name = user.get_full_name() or user.username
            role = "Quản trị viên" if user.is_superuser else "Nhân viên"
            messages.success(request, f'Chào mừng {full_name}! ({role})')
        # Redirect về trang quản lý lịch hẹn
        return redirect('/manage/appointments/')

    # 3. User không hợp lệ (có account nhưng không có role)
    else:
        # Logout ngay lập tức và báo lỗi
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
            # Auto-login sau đăng ký
            user = authenticate(
                request,
                username=form.cleaned_data['phone'],
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

        # Tìm user theo email
        try:
            user = User.objects.get(email=email)

            # Tạo token đặt lại mật khẩu
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Tạo link đặt lại mật khẩu
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
