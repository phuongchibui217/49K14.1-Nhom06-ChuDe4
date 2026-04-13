from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomerProfile


@login_required(login_url='accounts:login')
def admin_customers(request):
    """Quản lý khách hàng từ Admin Panel"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        # THÊM KHÁCH HÀNG
        if action == 'create':
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            dob = request.POST.get('dob', '').strip()
            channel = request.POST.get('contact_channel', '').strip()
            allergies = request.POST.get('allergies', '').strip()
            skin_condition = request.POST.get('skin_condition', '').strip()
            notes = request.POST.get('notes', '').strip()

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
                allergies=allergies,
                skin_condition=skin_condition,
                notes=notes,
            )

            messages.success(request, 'Thêm khách hàng thành công!')
            return redirect('customers:admin_customers')

        # CẬP NHẬT KHÁCH HÀNG
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
            allergies = request.POST.get('allergies', '').strip()
            skin_condition = request.POST.get('skin_condition', '').strip()
            notes = request.POST.get('notes', '').strip()

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
            customer.allergies = allergies
            customer.skin_condition = skin_condition
            customer.notes = notes
            customer.save()

            messages.success(request, 'Cập nhật khách hàng thành công!')
            return redirect('customers:admin_customers')

        # XÓA KHÁCH HÀNG
        elif action == 'delete':
            customer_id = request.POST.get('customer_id', '').strip()

            if not customer_id:
                messages.error(request, 'Không tìm thấy khách hàng cần xóa.')
                return redirect('customers:admin_customers')

            customer = get_object_or_404(CustomerProfile, pk=customer_id)
            customer.delete()

            messages.success(request, 'Xóa khách hàng thành công!')
            return redirect('customers:admin_customers')

        else:
            messages.error(request, 'Thao tác không hợp lệ.')
            return redirect('customers:admin_customers')

    customers = CustomerProfile.objects.select_related('user').filter(
        Q(user__isnull=True) | Q(user__is_staff=False, user__is_superuser=False)
    )

    return render(request, 'customers/admin_customers.html', {
        'customers': customers,
    })