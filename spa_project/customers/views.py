"""
Views cho Customer Management

File này chứa các views cho:
- Quản lý khách hàng từ Admin Panel

Author: Spa ANA Team
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# =====================================================
# ADMIN CUSTOMER MANAGEMENT VIEWS
# =====================================================

@login_required(login_url='accounts:login')
def admin_customers(request):
    """Quản lý khách hàng"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')
    return render(request, 'customers/admin_customers.html')
