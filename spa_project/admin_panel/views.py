"""
Views cho Admin Panel

File này chứa các views cho:
- Đăng nhập/đăng xuất admin
- Profile admin

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

# Forms
from accounts.forms import AdminLoginForm


# =====================================================
# ADMIN AUTHENTICATION VIEWS
# =====================================================

def admin_login(request):
    """
    Đăng nhập Admin

    Sử dụng AdminLoginForm để:
    - Validate username/password
    - Tự động xử lý remember_me
    - Kiểm tra user.is_staff

    NOTE: Route này đã bị xóa, function chỉ giữ lại để tránh lỗi.
    Tất cả login giờ redirect qua accounts:login
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('appointments:admin_appointments')

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # Kiểm tra xem user có phải staff không
            if user.is_staff or user.is_superuser:
                from django.contrib.auth import login
                login(request, user)

                # Xử lý remember_me
                remember_me = form.cleaned_data.get('remember_me')
                if remember_me:
                    request.session.set_expiry(1209600)  # 14 ngày
                else:
                    request.session.set_expiry(0)  # Session cookie

                messages.success(request, f'Chào mừng {user.username}!')
                return redirect('appointments:admin_appointments')
            else:
                messages.error(request, 'Tài khoản này không có quyền truy cập trang Admin.')
    else:
        form = AdminLoginForm(request)

    return render(request, 'manage/pages/admin_login.html', {'form': form})


def admin_logout(request):
    """Đăng xuất Admin"""
    logout(request)
    return render(request, 'manage/pages/admin_clear-login.html')



@login_required(login_url='accounts:login')
def admin_profile(request):
    """Tài khoản cá nhân"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not full_name:
                messages.error(request, 'Vui lòng nhập họ tên.')
                return redirect('admin_panel:admin_profile')

            if not email:
                messages.error(request, 'Vui lòng nhập email.')
                return redirect('admin_panel:admin_profile')

            parts = full_name.split(None, 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ''
            request.user.email = email
            request.user.save()

            messages.success(request, 'Cập nhật thông tin thành công.')
            return redirect('admin_panel:admin_profile')

        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            pw_error = None
            if not request.user.check_password(current_password):
                pw_error = 'Mật khẩu hiện tại không đúng.'
            elif len(new_password) < 6:
                pw_error = 'Mật khẩu mới phải có ít nhất 6 ký tự.'
            elif new_password != confirm_password:
                pw_error = 'Xác nhận mật khẩu không khớp.'

            if pw_error:
                return render(request, 'admin_panel/admin_profile.html', {'pw_error': pw_error})

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

            return render(request, 'admin_panel/admin_profile.html', {'pw_success': 'Đổi mật khẩu thành công.'})

    return render(request, 'admin_panel/admin_profile.html')