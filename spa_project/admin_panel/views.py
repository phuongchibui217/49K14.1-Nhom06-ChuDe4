"""
Views cho Admin Panel

File này chứa các views cho:
- Đăng nhập/đăng xuất admin
- Profile admin

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
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
    return render(request, 'admin_panel/admin_profile.html')
