"""
Views cho Staff Management

File này chứa các views cho:
- Quản lý nhân viên từ Admin Panel (chỉ Superuser)

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .models import StaffProfile


@login_required(login_url='accounts:login')
def admin_staff(request):
    """Quản lý nhân viên - Chỉ dành cho Superuser"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập trang này. Chỉ Superuser mới được quản lý nhân viên.')
        return redirect('appointments:admin_appointments')

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        # THÊM
        if action == 'create':
            username = request.POST.get('username', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            role = request.POST.get('role', '').strip()

            if not all([username, full_name, password, confirm_password, phone, email, role]):
                messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
                return redirect('staff:admin_staff')

            if password != confirm_password:
                messages.error(request, 'Mật khẩu xác nhận không khớp.')
                return redirect('staff:admin_staff')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Tên đăng nhập đã tồn tại.')
                return redirect('staff:admin_staff')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email đã tồn tại.')
                return redirect('staff:admin_staff')

            if StaffProfile.objects.filter(phone=phone).exists():
                messages.error(request, 'Số điện thoại đã tồn tại.')
                return redirect('staff:admin_staff')

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = True
            user.is_superuser = (role == 'Admin')
            user.save()

            StaffProfile.objects.create(
                user=user,
                full_name=full_name,
                phone=phone,
                role=role
            )

            messages.success(request, 'Thêm nhân viên thành công!')
            return redirect('staff:admin_staff')

        # SỬA
        elif action == 'update':
            staff_id = request.POST.get('staff_id', '').strip()

            if not staff_id:
                messages.error(request, 'Không tìm thấy nhân viên cần cập nhật.')
                return redirect('staff:admin_staff')

            staff = get_object_or_404(StaffProfile, pk=staff_id)

            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            role = request.POST.get('role', '').strip()
            status = request.POST.get('status', '').strip()

            if not all([full_name, phone, email, role, status]):
                messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
                return redirect('staff:admin_staff')

            if StaffProfile.objects.exclude(pk=staff.pk).filter(phone=phone).exists():
                messages.error(request, 'Số điện thoại đã tồn tại.')
                return redirect('staff:admin_staff')

            if User.objects.exclude(pk=staff.user.pk).filter(email=email).exists():
                messages.error(request, 'Email đã tồn tại.')
                return redirect('staff:admin_staff')

            staff.full_name = full_name
            staff.phone = phone
            staff.role = role
            staff.save()

            staff.user.email = email
            staff.user.is_active = (status == 'active')
            staff.user.is_staff = True
            staff.user.is_superuser = (role == 'Admin')
            staff.user.save()

            messages.success(request, 'Cập nhật nhân viên thành công!')
            return redirect('staff:admin_staff')

        # KHÓA
        elif action == 'delete':
            staff_id = request.POST.get('staff_id', '').strip()

            if not staff_id:
                messages.error(request, 'Không tìm thấy nhân viên cần khóa.')
                return redirect('staff:admin_staff')

            staff = get_object_or_404(StaffProfile, pk=staff_id)
            staff.user.is_active = False
            staff.user.save()

            messages.success(request, 'Đã khóa tài khoản nhân viên!')
            return redirect('staff:admin_staff')

        else:
            messages.error(request, 'Thao tác không hợp lệ.')
            return redirect('staff:admin_staff')

    staffs = StaffProfile.objects.select_related('user').all()
    return render(request, 'staff/admin_staff.html', {
        'staffs': staffs,
    })