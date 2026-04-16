from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import CustomerProfile
from .forms import CustomerProfileForm, ChangePasswordForm
from core.decorators import customer_required


@login_required(login_url='accounts:login')
def admin_customers(request):
    """Quản lý khách hàng từ Admin Panel"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'create':
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            dob = request.POST.get('dob', '').strip()
            channel = request.POST.get('contact_channel', '').strip()
            notes = request.POST.get('notes', '').strip()
            gender = request.POST.get('gender', '').strip()
            address = request.POST.get('address', '').strip()

            if not full_name or not phone:
                messages.error(request, 'Vui lòng nhập đầy đủ họ tên và số điện thoại.')
                return redirect('customers:admin_customers')

            if CustomerProfile.objects.filter(phone=phone).exists():
                messages.error(request, 'Số điện thoại đã tồn tại.')
                return redirect('customers:admin_customers')

            CustomerProfile.objects.create(
                full_name=full_name,
                phone=phone,
                dob=dob or None,
                contact_channel=channel or '',
                notes=notes,
                gender=gender or None,
                address=address,
            )
            messages.success(request, 'Thêm khách hàng thành công!')
            return redirect('customers:admin_customers')

        elif action == 'update':
            customer_id = request.POST.get('customer_id', '').strip()
            if not customer_id:
                messages.error(request, 'Không tìm thấy khách hàng cần cập nhật.')
                return redirect('customers:admin_customers')

            customer = get_object_or_404(CustomerProfile, pk=customer_id)
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            dob = request.POST.get('dob', '').strip()
            channel = request.POST.get('contact_channel', '').strip()
            notes = request.POST.get('notes', '').strip()
            gender = request.POST.get('gender', '').strip()
            address = request.POST.get('address', '').strip()

            if not full_name or not phone:
                messages.error(request, 'Vui lòng nhập đầy đủ họ tên và số điện thoại.')
                return redirect('customers:admin_customers')

            if CustomerProfile.objects.exclude(pk=customer.pk).filter(phone=phone).exists():
                messages.error(request, 'Số điện thoại đã tồn tại.')
                return redirect('customers:admin_customers')

            customer.full_name = full_name
            customer.phone = phone
            customer.dob = dob or None
            customer.contact_channel = channel or ''
            customer.notes = notes
            customer.gender = gender or None
            customer.address = address
            customer.save()
            messages.success(request, 'Cập nhật khách hàng thành công!')
            return redirect('customers:admin_customers')

        else:
            messages.error(request, 'Thao tác không hợp lệ.')
            return redirect('customers:admin_customers')

    customers = CustomerProfile.objects.select_related('user').filter(
        Q(user__isnull=True) | Q(user__is_staff=False, user__is_superuser=False)
    )
    return render(request, 'customers/admin_customers.html', {'customers': customers})


@customer_required()
def customer_profile(request):
    """Tài khoản cá nhân của khách hàng"""
    profile = request.user.customer_profile

    profile_form = CustomerProfileForm(instance=profile)
    password_form = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_profile':
            profile_form = CustomerProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Cập nhật thông tin thành công!')
                return redirect('customers:customer_profile')
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

    appointments_count = profile.appointments.count()
    completed_appointments = profile.appointments.filter(status='COMPLETED').count()
    pending_appointments = profile.appointments.filter(status='PENDING').count()

    return render(request, 'accounts/customer_profile.html', {
        'customer_profile': profile,
        'profile_form': profile_form,
        'password_form': password_form or ChangePasswordForm(request.user),
        'appointments_count': appointments_count,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
    })
