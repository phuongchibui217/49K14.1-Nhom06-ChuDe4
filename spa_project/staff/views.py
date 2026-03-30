"""
Views cho Staff Management

File này chứa các views cho:
- Quản lý nhân viên từ Admin Panel (chỉ Superuser)

Author: Spa ANA Team
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# =====================================================
# ADMIN STAFF MANAGEMENT VIEWS
# =====================================================

@login_required(login_url='admin_panel:admin_login')
def admin_staff(request):
    """Quản lý nhân viên - Chỉ dành cho Superuser"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập trang này. Chỉ Superuser mới được quản lý nhân viên.')
        return redirect('appointments:admin_appointments_list')
    return render(request, 'staff/admin_staff.html')
