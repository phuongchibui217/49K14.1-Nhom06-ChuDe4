from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import json
from .models import (
    Service, Appointment, CustomerProfile,
    Complaint, ComplaintReply, ComplaintHistory, Room
)
from .forms import (
    CustomerRegistrationForm, AppointmentForm,
    AdminLoginForm, ServiceForm,
    CustomerComplaintForm, GuestComplaintForm, ComplaintReplyForm,
    ComplaintStatusForm, ComplaintAssignForm,
    CustomerProfileForm, ChangePasswordForm
)
from .services import (
    validate_appointment_create,
    check_room_availability,
    get_min_booking_date
)
from .service_services import (
    validate_service_data,
    create_service as create_service_from_data,
    update_service as update_service_from_data,
    serialize_service,
)
from .appointment_services import (
    parse_appointment_data,
    validate_appointment_data,
    create_appointment as create_appointment_from_data,
    update_appointment as update_appointment_from_data,
    serialize_appointment,
    serialize_appointments,
)
from .api_response import (
    ApiResponse, staff_api, safe_api, 
    get_or_404, check_staff_permission
)


# =====================================================
# VIEWS - Trang tĩnh (Đã cập nhật dùng Model)
# =====================================================


def home(request):
    """Trang chủ - Lấy 6 dịch vụ active"""
    services = Service.objects.filter(is_active=True)[:6]
    return render(request, 'spa/pages/home.html', {'services': services})


def about(request):
    """Về Spa ANA"""
    return render(request, 'spa/pages/about.html')


def service_list(request):
    """Danh sách dịch vụ - Lọc chỉ active"""
    services = Service.objects.filter(status='active').order_by('-created_at')
    return render(request, 'spa/pages/services.html', {'services': services})


def service_detail(request, service_id):
    """Chi tiết dịch vụ - Lấy từ database"""
    service = get_object_or_404(Service, id=service_id, status='active')

    # Lấy các dịch vụ liên quan (cùng category)
    related_services = Service.objects.filter(
    ).exclude(id=service_id)[:4]

    return render(request, 'spa/pages/service_detail.html', {
        'service': service,
        'related_services': related_services
    })


# =====================================================
# VIEWS - Forms (Đã implement)
# =====================================================


def booking(request):
    """
    Đặt lịch hẹn

    QUYẾT THIẾT: BẮT BUỘC ĐĂNG NHẬP
    - Lý do: Đảm bảo thông tin khách hàng chính xác
    - Giảm spam booking
    - Dễ quản lý và liên hệ
    - Theo dõi lịch sử khách hàng

    Flow:
    1. Chưa login → Redirect sang login với next=booking
    2. Đã login nhưng chưa có profile → Tạo profile tự động
    3. Đã login + có profile → Hiển thị form booking
    4. POST → Validate → Tạo Appointment → Redirect my-appointments
    """
    # Redirect nếu chưa đăng nhập
    if not request.user.is_authenticated:
        messages.warning(request, 'Vui lòng đăng nhập để đặt lịch hẹn.')
        return redirect(f'{reverse("spa:login")}?next={reverse("spa:booking")}')

    # Lấy hoặc tạo customer profile
    try:
        customer_profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        # Tạo profile tự động nếu chưa có
        customer_profile = CustomerProfile.objects.create(
            user=request.user,
            phone=request.user.username,
            full_name=request.user.get_full_name() or request.user.username,
        )
        messages.info(request, 'Hồ sơ của bạn đã được tạo. Vui lòng cập nhật thông tin đầy đủ.')

    # Lấy service được chọn từ URL parameter (nếu có)
    selected_service_id = request.GET.get('service')

    # Khởi tạo form
    form = AppointmentForm()
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Cập nhật thông tin khách hàng từ form
            customer_name = request.POST.get('customer_name', '').strip()
            customer_phone = request.POST.get('customer_phone', '').strip()
            customer_email = request.POST.get('customer_email', '').strip()
            
            if customer_name:
                customer_profile.full_name = customer_name
            if customer_phone:
                customer_profile.phone = customer_phone
            if customer_email:
                customer_profile.email = customer_email
            customer_profile.save()
            
            appointment = form.save(commit=False)
            appointment.customer = customer_profile
            appointment.source = 'web'  # Đánh dấu là đặt từ web
            appointment.status = 'pending'  # Chờ xác nhận
            appointment.save()
            messages.success(
                request,
                f'Đặt lịch thành công! Mã lịch hẹn: {appointment.appointment_code}. Vui lòng chờ xác nhận từ Spa.'
            )
            return redirect('spa:my_appointments')
    else:
        # GET request - set initial service nếu có
        if selected_service_id:
            form.fields['service'].initial = selected_service_id

    # Lấy danh sách services cho dropdown
    services = Service.objects.filter(is_active=True)

    return render(request, 'spa/pages/booking.html', {
        'form': form,
        'services': services,
        'customer_profile': customer_profile,
    })


@login_required
def my_appointments(request):
    """
    Lịch hẹn của tôi

    Features:
    - Lọc theo trạng thái: ?status=pending|confirmed|completed|cancelled|all
    - Sắp xếp theo người đặt gần nhất (created_at)
    - Đếm số lượng theo từng trạng thái
    """
    try:
        customer_profile = request.user.customer_profile

        # Lọc theo status từ query parameter
        status_filter = request.GET.get('status', 'all')

        # Base query - chỉ lấy appointments của user hiện tại
        appointments = customer_profile.appointments.all()

        # Apply status filter nếu không phải 'all'
        if status_filter != 'all':
            appointments = appointments.filter(status=status_filter)

        # Sắp xếp: người đặt gần nhất lên đầu
        appointments = appointments.order_by('-created_at')

        # Đếm số lượng theo từng trạng thái
        status_counts = {}
        for status_choice, _ in Appointment.STATUS_CHOICES:
            status_counts[status_choice] = customer_profile.appointments.filter(
                status=status_choice
            ).count()
        status_counts['all'] = customer_profile.appointments.count()

    except CustomerProfile.DoesNotExist:
        appointments = Appointment.objects.none()
        status_counts = {}
        status_filter = 'all'

    return render(request, 'spa/pages/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


@login_required
def cancel_appointment(request, appointment_id):
    """
    Hủy lịch hẹn

    Rules:
    - Chỉ cho phép hủy khi status = 'pending' hoặc 'confirmed'
    - Chỉ chủ appointment mới được hủy
    - Dùng POST để thực sự hủy (GET hiển thị confirm)
    - Cập nhật status thành 'cancelled'
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Kiểm tra quyền: chỉ chủ appointment mới được hủy
    if appointment.customer.user != request.user:
        messages.error(request, 'Bạn không có quyền hủy lịch hẹn này.')
        return redirect('spa:my_appointments')

    # Kiểm tra trạng thái: chỉ hủy được khi pending hoặc confirmed
    if appointment.status not in ['pending', 'confirmed']:
        messages.warning(
            request,
            f'Không thể hủy lịch hẹn này. Trạng thái hiện tại: {appointment.get_status_display()}'
        )
        return redirect('spa:my_appointments')

    # GET: Hiển thị trang xác nhận
    if request.method == 'GET':
        return render(request, 'spa/pages/cancel_appointment.html', {
            'appointment': appointment
        })

    # POST: Thực hiện hủy
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()

        messages.success(
            request,
            f'Đã hủy lịch hẹn {appointment.appointment_code}.'
        )
        return redirect('spa:my_appointments')


# =====================================================
# VIEWS - Authentication
# =====================================================


def login_view(request):
    """Đăng nhập - Username = Phone"""
    if request.user.is_authenticated:
        return redirect('spa:home')

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
            return redirect('spa:home')
        else:
            messages.error(request, 'Số điện thoại hoặc mật khẩu không đúng.')

    return render(request, 'spa/pages/login.html')


def register(request):
    """Đăng ký - Tạo User + CustomerProfile"""
    if request.user.is_authenticated:
        return redirect('spa:home')

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
            return redirect('spa:home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'spa/pages/register.html', {'form': form})


def logout_view(request):
    """Đăng xuất"""
    logout(request)
    messages.info(request, 'Đã đăng xuất!')
    return redirect('spa:home')


# =====================================================
# VIEWS - Password Reset
# =====================================================


def password_reset_request(request):
    """
    Yêu cầu đặt lại mật khẩu
    
    Sử dụng email để gửi link đặt lại mật khẩu
    """
    if request.user.is_authenticated:
        return redirect('spa:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Vui lòng nhập email.')
            return render(request, 'spa/pages/password_reset.html')
        
        # Tìm user theo email
        try:
            user = User.objects.get(email=email)
            
            # Gửi email đặt lại mật khẩu sử dụng Django's built-in
            from django.contrib.auth.views import PasswordResetView
            from django.core.mail import send_mail
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.contrib.auth.tokens import default_token_generator
            from django.conf import settings
            
            # Tạo token đặt lại mật khẩu
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Tạo link đặt lại mật khẩu
            reset_url = request.build_absolute_uri(
                reverse('spa:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
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
            return render(request, 'spa/pages/password_reset_sent.html', {
                'email': email,
            })
            
        except User.DoesNotExist:
            # Không tiết lộ user có tồn tại hay không
            messages.success(request, 'Nếu email tồn tại trong hệ thống, bạn sẽ nhận được link đặt lại mật khẩu.')
            return render(request, 'spa/pages/password_reset_sent.html', {
                'email': email,
            })
    
    return render(request, 'spa/pages/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """
    Xác nhận đặt lại mật khẩu
    
    Cho phép người dùng đặt mật khẩu mới từ link trong email
    """
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_str
    
    if request.user.is_authenticated:
        return redirect('spa:home')
    
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
                return redirect('spa:login')
        
        return render(request, 'spa/pages/password_reset_confirm.html', {
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 'Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.')
        return redirect('spa:password_reset')


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
                return redirect('spa:customer_profile')
            else:
                messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
        
        elif action == 'change_password':
            password_form = ChangePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.')
                logout(request)
                return redirect('spa:login')
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
    
    return render(request, 'spa/pages/customer_profile.html', context)


# =====================================================
# VIEWS - Admin (Giao diện quản lý)
# =====================================================


def admin_login(request):
    """
    Đăng nhập Admin

    Sử dụng AdminLoginForm để:
    - Validate username/password
    - Tự động xử lý remember_me
    - Kiểm tra user.is_staff
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('spa:admin_appointments')

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # Kiểm tra xem user có phải staff không
            if user.is_staff or user.is_superuser:
                login(request, user)

                # Xử lý remember_me
                remember_me = form.cleaned_data.get('remember_me')
                if remember_me:
                    request.session.set_expiry(1209600)  # 14 ngày
                else:
                    request.session.set_expiry(0)  # Session cookie

                messages.success(request, f'Chào mừng {user.username}!')
                return redirect('spa:admin_appointments')
            else:
                messages.error(request, 'Tài khoản này không có quyền truy cập trang Admin.')
    else:
        form = AdminLoginForm(request)

    return render(request, 'admin/pages/admin_login.html', {'form': form})


def admin_logout(request):
    """Đăng xuất Admin"""
    logout(request)
    return render(request, 'admin/pages/admin_clear-login.html')


@login_required(login_url='spa:admin_login')
def admin_appointments(request):
    """Quản lý lịch hẹn"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    return render(request, 'admin/pages/admin_appointments.html')


@login_required(login_url='spa:admin_login')
def admin_services(request):
    """
    Quản lý dịch vụ

    GET: Hiển thị danh sách dịch vụ với pagination và filter
    POST: Xử lý thêm dịch vụ mới
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')

    # GET request - hiển thị danh sách
    if request.method == 'GET':
        services_list = Service.objects.all().order_by('-created_at')

        # Search functionality
        search_query = request.GET.get('search', '')
        category_filter = request.GET.get('category', '')
        status_filter = request.GET.get('status', '')

        if search_query:
            services_list = services_list.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )

        if category_filter:
            category_map = {
                '1': 'skincare',
                '2': 'massage',
                '3': 'tattoo',
                '4': 'hair',
            }
            category_code = category_map.get(category_filter)
            if category_code:
                services_list = services_list.filter(category=category_code)

        if status_filter:
            services_list = services_list.filter(status=status_filter)

        # Pagination
        paginator = Paginator(services_list, 10)
        page_number = request.GET.get('page', 1)
        services = paginator.get_page(page_number)

        # Get next service code
        next_code = Service.generate_service_code()

        context = {
            'services': services,
            'next_service_code': next_code,
            'search_query': search_query,
            'category_filter': category_filter,
            'status_filter': status_filter,
        }
        return render(request, 'admin/pages/admin_services.html', context)

    # POST request - xử lý thêm dịch vụ mới
    elif request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                service = form.save(commit=False)
                service.created_by = request.user
                service.updated_by = request.user
                service.save()

                messages.success(
                    request,
                    f'Đã thêm dịch vụ mới: {service.name}'
                )
                return redirect('spa:admin_services')

            except Exception as e:
                messages.error(
                    request,
                    'Có lỗi khi lưu dữ liệu, vui lòng thử lại'
                )
        else:
            # Form có lỗi - hiển thị lỗi
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

        # Redirect về trang danh sách (khi lỗi)
        return redirect('spa:admin_services')


# =====================================================
# Service Management Views (Sửa, Xóa)
# =====================================================

@login_required(login_url='spa:admin_login')
def admin_service_edit(request, service_id):
    """
    Sửa dịch vụ
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')

    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)

        if form.is_valid():
            try:
                updated_service = form.save(commit=False)
                updated_service.updated_by = request.user
                updated_service.save()

                messages.success(
                    request,
                    f'Đã cập nhật dịch vụ: {updated_service.name}'
                )
                return redirect('spa:admin_services')

            except Exception as e:
                messages.error(
                    request,
                    'Có lỗi khi lưu dữ liệu, vui lòng thử lại'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('spa:admin_services')


@login_required(login_url='spa:admin_login')
def admin_service_delete(request, service_id):
    """
    Xóa dịch vụ
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')

    if request.method == 'POST':
        service = get_object_or_404(Service, id=service_id)

        try:
            service_name = service.name
            service.delete()
            messages.success(
                request,
                f'Đã xóa dịch vụ: {service_name}'
            )
        except Exception as e:
            messages.error(
                request,
                'Có lỗi khi xóa dịch vụ, vui lòng thử lại'
            )

    return redirect('spa:admin_services')


# API endpoints for Services CRUD
@require_http_methods(["GET"])
def api_services_list(request):
    """API: Lấy danh sách dịch vụ"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Không có quyền truy cập'}, status=403)

    # Filter by search parameter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        # Check if search is a number (searching by ID)
        if search_query.isdigit():
            services = Service.objects.filter(id=int(search_query))
        else:
            # Search by name or code
            services = Service.objects.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )
    else:
        services = Service.objects.all().order_by('-created_at')

    services_data = []

    for service in services:
        services_data.append({
            'id': service.id,
            'code': service.code or '',
            'name': service.name,
            'category': service.category,
            'categoryName': service.get_category_name(),
            'description': service.short_description or service.description[:100] if service.description else '',
            'price': float(service.price),
            'duration': service.duration_minutes,
            'duration_minutes': service.duration_minutes,
            'status': service.status if hasattr(service, 'status') else ('active' if service.is_active else 'inactive'),
            'image': service.image.url if service.image else 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100'
        })

    return JsonResponse({'services': services_data})


@require_http_methods(["POST"])
@staff_api
def api_service_create(request):
    """
    API: Thêm dịch vụ mới
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    - Validation đầy đủ
    """

    try:
        # Check if multipart/form-data (for file upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '1')
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '0')
            duration = request.POST.get('duration', '60')
            status = request.POST.get('status', 'active')
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            category = data.get('category', '1')
            description = data.get('description', '').strip()
            price = data.get('price', '0')
            duration = data.get('duration', '60')
            status = data.get('status', 'active')
            image_file = None

        # Validation
        if not name:
            return JsonResponse({'error': 'Vui lòng nhập tên dịch vụ!'}, status=400)

        if len(name) < 5:
            return JsonResponse({'error': 'Tên dịch vụ phải có ít nhất 5 ký tự!'}, status=400)

        if len(name) > 200:
            return JsonResponse({'error': 'Tên dịch vụ không được quá 200 ký tự!'}, status=400)

        # Check if service name already exists
        if Service.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': f'Dịch vụ "{name}" đã tồn tại!'}, status=400)

        # Validate and convert price
        try:
            price = float(price)
            if price < 0:
                return JsonResponse({'error': 'Giá không được âm!'}, status=400)
            if price > 999999999:
                return JsonResponse({'error': 'Giá không được quá 999,999,999 VNĐ!'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Giá không hợp lệ!'}, status=400)

        # Validate duration
        try:
            duration = int(duration)
            if duration < 5:
                return JsonResponse({'error': 'Thời gian phải ít nhất 5 phút!'}, status=400)
            if duration > 480:  # 8 hours
                return JsonResponse({'error': 'Thời gian không được quá 480 phút (8 tiếng)!'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Thời gian không hợp lệ!'}, status=400)

        # Map category number to model choice
        category_reverse_map = {
            '1': 'skincare',
            '2': 'massage',
            '3': 'tattoo',
            '4': 'hair',
        }

        # Create service
        service = Service.objects.create(
            name=name,
            category=category_reverse_map.get(str(category), 'skincare'),
            short_description=description[:300] if len(description) > 300 else description,
            description=description,
            price=price,
            duration_minutes=duration,
            is_active=status == 'active'
        )

        # Handle image upload
        if image_file:
            # Validate file size (max 5MB)
            if image_file.size > 5 * 1024 * 1024:
                service.delete()
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)

            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                service.delete()
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)

            service.image = image_file
            service.save()

        # Generate service code
        service_count = Service.objects.filter(id__lte=service.id).count()
        service_code = f'DV{str(service_count).zfill(3)}'

        return JsonResponse({
            'success': True,
            'message': f'Đã thêm dịch vụ: {service.name}',
            'service': {
                'id': service.id,
                'code': service_code,
                'name': service.name,
                'categoryName': service.get_category_name(),
                'image': service.image.url if service.image else 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100'
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_service_update(request, service_id):
    """
    API: Cập nhật dịch vụ
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy service hoặc trả về 404
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    try:

        # Check if multipart/form-data (for file upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '1')
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price', '0')
            duration = request.POST.get('duration', '60')
            status = request.POST.get('status', 'active')
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            category = data.get('category', '1')
            description = data.get('description', '').strip()
            price = data.get('price', '0')
            duration = data.get('duration', '60')
            status = data.get('status', 'active')
            image_file = None

        # Validation
        if not name:
            return JsonResponse({'error': 'Vui lòng nhập tên dịch vụ!'}, status=400)

        if len(name) < 5:
            return JsonResponse({'error': 'Tên dịch vụ phải có ít nhất 5 ký tự!'}, status=400)

        if len(name) > 200:
            return JsonResponse({'error': 'Tên dịch vụ không được quá 200 ký tự!'}, status=400)

        # Check if service name already exists (excluding current service)
        if Service.objects.filter(name__iexact=name).exclude(id=service_id).exists():
            return JsonResponse({'error': f'Dịch vụ "{name}" đã tồn tại!'}, status=400)

        # Validate and convert price
        try:
            price = float(price)
            if price < 0:
                return JsonResponse({'error': 'Giá không được âm!'}, status=400)
            if price > 999999999:
                return JsonResponse({'error': 'Giá không được quá 999,999,999 VNĐ!'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Giá không hợp lệ!'}, status=400)

        # Validate duration
        try:
            duration = int(duration)
            if duration < 5:
                return JsonResponse({'error': 'Thời gian phải ít nhất 5 phút!'}, status=400)
            if duration > 480:
                return JsonResponse({'error': 'Thời gian không được quá 480 phút (8 tiếng)!'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Thời gian không hợp lệ!'}, status=400)

        # Map category number to model choice
        category_reverse_map = {
            '1': 'skincare',
            '2': 'massage',
            '3': 'tattoo',
            '4': 'hair',
        }

        # Update service
        service.name = name
        service.category = category_reverse_map.get(str(category), service.category)
        service.short_description = description[:300] if len(description) > 300 else description
        service.description = description
        service.price = price
        service.duration_minutes = duration
        service.is_active = status == 'active'

        # Handle image upload
        if image_file:
            # Validate file size (max 5MB)
            if image_file.size > 5 * 1024 * 1024:
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)

            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)

            # Delete old image if exists
            if service.image and service.image.name:
                service.image.delete(save=False)

            service.image = image_file

        service.save()

        return JsonResponse({
            'success': True,
            'message': f'Đã cập nhật dịch vụ: {service.name}'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["DELETE", "POST"])
@staff_api
def api_service_delete(request, service_id):
    """
    API: Xóa dịch vụ
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy service hoặc trả về 404
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    try:
        service_name = service.name
        service.delete()

        return JsonResponse({
            'success': True,
            'message': f'Đã xóa dịch vụ: {service_name}'
        })
    except Exception as e:
        return ApiResponse.error(f'Lỗi khi xóa dịch vụ: {str(e)}')



@login_required(login_url='spa:admin_login')
def admin_customers(request):
    """Quản lý khách hàng"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    return render(request, 'admin/pages/admin_customers.html')


@login_required(login_url='spa:admin_login')
def admin_staff(request):
    """Quản lý nhân viên - Chỉ dành cho Superuser"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập trang này. Chỉ Superuser mới được quản lý nhân viên.')
        return redirect('spa:admin_appointments')
    return render(request, 'admin/pages/admin_staff.html')


@login_required(login_url='spa:admin_login')
def admin_complaints(request):
    """Quản lý khiếu nại - Danh sách"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaints_list = Complaint.objects.all().order_by('-created_at')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        complaints_list = complaints_list.filter(
            Q(code__icontains=search) |
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(title__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        complaints_list = complaints_list.filter(status=status)
    
    # Filter by type
    complaint_type = request.GET.get('type', '')
    if complaint_type:
        complaints_list = complaints_list.filter(complaint_type=complaint_type)
    
    # Pagination
    paginator = Paginator(complaints_list, 10)
    page = request.GET.get('page', 1)
    complaints = paginator.get_page(page)
    
    context = {
        'complaints': complaints,
        'search': search,
        'status_filter': status,
        'type_filter': complaint_type,
    }
    return render(request, 'admin/pages/admin_complaints.html', context)


@login_required(login_url='spa:admin_login')
def admin_live_chat(request):
    """Chat trực tuyến"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    return render(request, 'admin/pages/live_chat_admin.html')


@login_required(login_url='spa:admin_login')
def admin_profile(request):
    """Tài khoản cá nhân"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    return render(request, 'admin/pages/profile.html')


# =====================================================
# Admin Complaint Management Views
# =====================================================

@login_required(login_url='spa:admin_login')
def admin_complaint_detail(request, complaint_id):
    """Chi tiết khiếu nại"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    replies = complaint.replies.filter(is_internal=False).order_by('created_at')
    all_replies = complaint.replies.all().order_by('created_at')
    history = complaint.history.all()[:50]
    
    reply_form = ComplaintReplyForm()
    status_form = ComplaintStatusForm(instance=complaint)
    assign_form = ComplaintAssignForm(instance=complaint)
    
    context = {
        'complaint': complaint,
        'replies': replies,
        'all_replies': all_replies,
        'history': history,
        'reply_form': reply_form,
        'status_form': status_form,
        'assign_form': assign_form,
    }
    return render(request, 'admin/pages/admin_complaint_detail.html', context)


@login_required(login_url='spa:admin_login')
def admin_complaint_take(request, complaint_id):
    """Nhận xử lý khiếu nại"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if complaint.assigned_to:
        messages.warning(request, 'Khiếu nại này đã được phân công.')
    else:
        complaint.assigned_to = request.user
        complaint.status = 'assigned'
        complaint.save()
        
        ComplaintHistory.log(
            complaint=complaint,
            action='took_ownership',
            new_value=request.user.get_full_name() or request.user.username,
            note='Nhân viên tự nhận xử lý',
            performed_by=request.user
        )
        messages.success(request, 'Bạn đã nhận xử lý khiếu nại này.')
    
    return redirect('spa:admin_complaint_detail', complaint_id=complaint_id)


@login_required(login_url='spa:admin_login')
def admin_complaint_assign(request, complaint_id):
    """Phân công người phụ trách"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        form = ComplaintAssignForm(request.POST, instance=complaint)
        if form.is_valid():
            old_assignee = complaint.assigned_to
            complaint = form.save(commit=False)
            complaint.status = 'assigned'
            complaint.save()
            
            ComplaintHistory.log(
                complaint=complaint,
                action='assigned',
                old_value=old_assignee.get_full_name() if old_assignee else '',
                new_value=complaint.assigned_to.get_full_name() or complaint.assigned_to.username,
                performed_by=request.user
            )
            messages.success(request, f'Đã phân công cho {complaint.assigned_to.get_full_name() or complaint.assigned_to.username}.')
    return redirect('spa:admin_complaint_detail', complaint_id=complaint_id)


@login_required(login_url='spa:admin_login')
def admin_complaint_reply(request, complaint_id):
    """Phản hồi khiếu nại"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        form = ComplaintReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.complaint = complaint
            reply.sender = request.user
            reply.sender_role = 'manager' if request.user.is_superuser else 'staff'
            reply.sender_name = request.user.get_full_name() or request.user.username
            reply.save()
            
            ComplaintHistory.log(
                complaint=complaint,
                action='replied',
                note=f'Phản hồi bởi {reply.sender_name}',
                performed_by=request.user
            )
            messages.success(request, 'Đã gửi phản hồi.')
    
    return redirect('spa:admin_complaint_detail', complaint_id=complaint_id)


@login_required(login_url='spa:admin_login')
def admin_complaint_status(request, complaint_id):
    """Cập nhật trạng thái khiếu nại"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        old_status = complaint.get_status_display()
        new_status_code = request.POST.get('status')
        
        if new_status_code in dict(Complaint.STATUS_CHOICES):
            complaint.status = new_status_code
            complaint.save()
            
            ComplaintHistory.log(
                complaint=complaint,
                action='status_changed',
                old_value=old_status,
                new_value=complaint.get_status_display(),
                performed_by=request.user
            )
            messages.success(request, f'Đã cập nhật trạng thái: {complaint.get_status_display()}')
    
    return redirect('spa:admin_complaint_detail', complaint_id=complaint_id)


@login_required(login_url='spa:admin_login')
def admin_complaint_complete(request, complaint_id):
    """Đánh dấu hoàn thành"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('spa:home')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        resolution = request.POST.get('resolution', '').strip()
        
        if not resolution:
            messages.error(request, 'Vui lòng nhập kết quả xử lý.')
        elif not complaint.assigned_to:
            messages.error(request, 'Khiếu nại chưa được phân công.')
        else:
            from django.utils import timezone
            complaint.resolution = resolution
            complaint.status = 'resolved'
            complaint.resolved_at = timezone.now()
            complaint.save()
            
            ComplaintHistory.log(
                complaint=complaint,
                action='resolved',
                note=resolution,
                performed_by=request.user
            )
            messages.success(request, 'Đã đánh dấu hoàn thành khiếu nại.')
    
    return redirect('spa:admin_complaint_detail', complaint_id=complaint_id)


# =====================================================
# Customer Complaint Views
# =====================================================

@login_required
def customer_complaint_create(request):
    """Khách hàng gửi khiếu nại"""
    # Lấy hoặc tạo CustomerProfile cho user
    customer_profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.username,
        }
    )

    if request.method == 'POST':
        form = CustomerComplaintForm(request.POST)
        
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.customer = customer_profile
            complaint.full_name = customer_profile.full_name
            complaint.phone = customer_profile.phone
            complaint.save()
            
            # Log history (bọc trong try để không ảnh hưởng luồng chính)
            try:
                ComplaintHistory.log(
                    complaint=complaint,
                    action='created',
                    note='Khách hàng tạo khiếu nại',
                    performed_by=request.user
                )
            except Exception as e:
                print(f"Warning: Could not log complaint history: {e}")
            
            messages.success(request, f'Đã gửi khiếu nại thành công! Mã khiếu nại: {complaint.code}')
            return redirect('spa:customer_complaint_list')
    else:
        # GET request - luôn dùng CustomerComplaintForm
        form = CustomerComplaintForm()
    
    return render(request, 'spa/pages/customer_complaint_create.html', {
        'form': form,
        'customer_profile': customer_profile,
    })


@login_required
def customer_complaint_list(request):
    """Danh sách khiếu nại của khách hàng"""
    # Dùng cùng logic với create để đảm bảo nhất quán
    customer_profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.username,
        }
    )
    complaints = customer_profile.complaints.all().order_by('-created_at')
    
    return render(request, 'spa/pages/customer_complaint_list.html', {
        'complaints': complaints,
        'customer_profile': customer_profile,
    })


@login_required
def customer_complaint_detail(request, complaint_id):
    """Chi tiết khiếu nại của khách hàng"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Kiểm tra quyền: chỉ chủ khiếu nại mới xem được
    if complaint.customer and complaint.customer.user != request.user:
        messages.error(request, 'Bạn không có quyền xem khiếu nại này.')
        return redirect('spa:customer_complaint_list')
    
    replies = complaint.replies.filter(is_internal=False).order_by('created_at')
    history = complaint.history.all()[:20]
    
    reply_form = ComplaintReplyForm()
    
    context = {
        'complaint': complaint,
        'replies': replies,
        'history': history,
        'reply_form': reply_form,
    }
    return render(request, 'spa/pages/customer_complaint_detail.html', context)


@login_required
def customer_complaint_reply(request, complaint_id):
    """Khách hàng phản hồi khiếu nại"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if complaint.customer and complaint.customer.user != request.user:
        messages.error(request, 'Bạn không có quyền phản hồi khiếu nại này.')
        return redirect('spa:customer_complaint_list')
    
    if request.method == 'POST':
        form = ComplaintReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.complaint = complaint
            reply.sender = request.user
            reply.sender_role = 'customer'
            reply.sender_name = complaint.full_name
            reply.is_internal = False
            reply.save()
            
            # Cập nhật trạng thái nếu đang chờ khách phản hồi
            if complaint.status == 'waiting_customer':
                complaint.status = 'processing'
                complaint.save()
            
            ComplaintHistory.log(
                complaint=complaint,
                action='replied',
                note='Khách hàng phản hồi bổ sung',
                performed_by=request.user
            )
            messages.success(request, 'Đã gửi phản hồi.')
    
    return redirect('spa:customer_complaint_detail', complaint_id=complaint_id)


# =====================================================
# API for Admin Appointments (Scheduler)
# =====================================================

@require_http_methods(["GET"])
def api_rooms_list(request):
    """API: Lấy danh sách phòng"""
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)
    
    rooms = Room.objects.filter(is_active=True).order_by('code')
    rooms_data = []
    
    for room in rooms:
        rooms_data.append({
            'id': room.code,
            'name': room.name,
            'capacity': room.capacity,
        })
    
    return JsonResponse({'success': True, 'rooms': rooms_data})


@require_http_methods(["GET"])
def api_appointments_list(request):
    """
    API: Lấy danh sách lịch hẹn
    
    Query params:
    - date: YYYY-MM-DD (lọc theo ngày)
    - status: pending|confirmed|completed|cancelled
    - source: web|admin
    - room: room code
    - q: search term
    """
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)
    
    appointments = Appointment.objects.all()
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Filter by source
    source_filter = request.GET.get('source', '')
    if source_filter:
        appointments = appointments.filter(source=source_filter)
    
    # Filter by room
    room_filter = request.GET.get('room', '')
    if room_filter:
        appointments = appointments.filter(room__code=room_filter)
    
    # Search
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )
    
    appointments = appointments.order_by('appointment_date', 'appointment_time')
    
    appointments_data = []
    for appt in appointments:
        appointments_data.append({
            'id': appt.appointment_code,
            'customerName': appt.customer.full_name,
            'phone': appt.customer.phone,
            'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
            'service': appt.service.name,
            'serviceId': appt.service.id,
            'roomId': appt.room.code if appt.room else '',
            'roomName': appt.room.name if appt.room else '',
            'guests': appt.guests,
            'date': appt.appointment_date.strftime('%Y-%m-%d'),
            'start': appt.appointment_time.strftime('%H:%M'),
            'end': appt.get_end_time_display(),
            'durationMin': appt.duration_minutes or appt.service.duration_minutes,
            'note': appt.notes or '',
            'apptStatus': appt.status,
            'payStatus': appt.payment_status,
            'source': appt.source,
        })
    
    return JsonResponse({'success': True, 'appointments': appointments_data})


@require_http_methods(["GET"])
def api_appointment_detail(request, appointment_code):
    """API: Lấy chi tiết một lịch hẹn"""
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)
    
    try:
        appt = Appointment.objects.get(appointment_code=appointment_code)
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy lịch hẹn'}, status=404)
    
    data = {
        'id': appt.appointment_code,
        'customerName': appt.customer.full_name,
        'phone': appt.customer.phone,
        'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
        'service': appt.service.name,
        'serviceId': appt.service.id,
        'roomId': appt.room.code if appt.room else '',
        'roomName': appt.room.name if appt.room else '',
        'guests': appt.guests,
        'date': appt.appointment_date.strftime('%Y-%m-%d'),
        'start': appt.appointment_time.strftime('%H:%M'),
        'end': appt.get_end_time_display(),
        'durationMin': appt.duration_minutes or appt.service.duration_minutes,
        'note': appt.notes or '',
        'apptStatus': appt.status,
        'payStatus': appt.payment_status,
        'source': appt.source,
    }
    
    return JsonResponse({'success': True, 'appointment': data})


@require_http_methods(["POST"])
@staff_api
def api_appointment_create(request):
    """
    API: Tạo lịch hẹn mới từ admin
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    - Validation tập trung qua services.py
    """
    
    try:
        data = json.loads(request.body)
        
        # Required fields
        customer_name = data.get('customerName', '').strip()
        phone = data.get('phone', '').strip()
        service_id = data.get('serviceId') or data.get('service')
        room_id = data.get('roomId') or data.get('room')
        date_str = data.get('date', '')
        time_str = data.get('time') or data.get('start', '')
        duration = data.get('duration') or data.get('durationMin', 60)
        guests = data.get('guests', 1)
        notes = data.get('note', '')
        status = data.get('apptStatus', 'not_arrived')
        pay_status = data.get('payStatus', 'unpaid')
        
        # Validation
        if not customer_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập tên khách hàng'}, status=400)
        
        if not phone:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập số điện thoại'}, status=400)
        
        # Clean phone number
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 10:
            return JsonResponse({'success': False, 'error': 'Số điện thoại không hợp lệ'}, status=400)
        
        if not service_id:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn dịch vụ'}, status=400)
        
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn ngày hẹn'}, status=400)
        
        if not time_str:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn giờ hẹn'}, status=400)
        
        # Get or create customer
        customer, created = CustomerProfile.objects.get_or_create(
            phone=phone,
            defaults={'full_name': customer_name}
        )
        if not created and customer.full_name != customer_name:
            customer.full_name = customer_name
            customer.save()
        
        # Get service
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Dịch vụ không tồn tại'}, status=400)
        
        # Get room
        room = None
        if room_id:
            try:
                room = Room.objects.get(code=room_id)
            except Room.DoesNotExist:
                pass
        
        # Parse date and time
        from datetime import datetime
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Định dạng ngày không hợp lệ'}, status=400)
        
        try:
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Định dạng giờ không hợp lệ'}, status=400)
        
        # =====================================================
        # VALIDATION: Ngày quá khứ + Phòng trống
        # Sử dụng services.py để validate tập trung
        # =====================================================
        duration_minutes = int(duration) if duration else service.duration_minutes
        
        # Validate ngày và giờ (bao gồm timezone)
        validation_result = validate_appointment_create(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=duration_minutes,
            room_code=room_id if room_id else None,
            exclude_appointment_code=None  # Tạo mới nên không cần exclude
        )
        
        if not validation_result['valid']:
            # Trả về lỗi validation (đã có message tiếng Việt rõ ràng)
            return JsonResponse({
                'success': False,
                'error': validation_result['errors'][0]  # Lấy lỗi đầu tiên
            }, status=400)
        
        # Create appointment
        appointment = Appointment.objects.create(
            customer=customer,
            service=service,
            room=room,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=int(duration),
            guests=int(guests),
            notes=notes,
            status=status,
            payment_status=pay_status,
            source='admin',
            created_by=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tạo lịch hẹn thành công! Mã: {appointment.appointment_code}',
            'appointment': {
                'id': appointment.appointment_code,
                'customerName': appointment.customer.full_name,
                'phone': appointment.customer.phone,
                'service': appointment.service.name,
                'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'start': appointment.appointment_time.strftime('%H:%M'),
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_appointment_update(request, appointment_code):
    """
    API: Cập nhật lịch hẹn
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        data = json.loads(request.body)
        
        # Update fields
        if 'customerName' in data:
            appointment.customer.full_name = data['customerName'].strip()
            appointment.customer.save()
        
        if 'phone' in data:
            phone = ''.join(filter(str.isdigit, data['phone']))
            appointment.customer.phone = phone
            appointment.customer.save()
        
        if 'serviceId' in data or 'service' in data:
            service_id = data.get('serviceId') or data.get('service')
            try:
                appointment.service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                pass
        
        if 'roomId' in data or 'room' in data:
            room_id = data.get('roomId') or data.get('room')
            if room_id:
                try:
                    appointment.room = Room.objects.get(code=room_id)
                except Room.DoesNotExist:
                    appointment.room = None
            else:
                appointment.room = None
        
        if 'date' in data:
            from datetime import datetime
            appointment.appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        if 'time' in data or 'start' in data:
            from datetime import datetime
            time_str = data.get('time') or data.get('start')
            appointment.appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        if 'duration' in data or 'durationMin' in data:
            appointment.duration_minutes = int(data.get('duration') or data.get('durationMin'))
        
        if 'guests' in data:
            appointment.guests = int(data['guests'])
        
        if 'note' in data:
            appointment.notes = data['note']
        
        if 'apptStatus' in data:
            appointment.status = data['apptStatus']
        
        if 'payStatus' in data:
            appointment.payment_status = data['payStatus']
        
        appointment.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Cập nhật lịch hẹn {appointment_code} thành công'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST"])
@staff_api
def api_appointment_status(request, appointment_code):
    """
    API: Đổi trạng thái lịch hẹn
    
    ĐÃ BỔ SUNG:
    - CSRF protection qua @staff_api decorator
    - Error handling chi tiết
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')
        
        valid_statuses = ['pending', 'not_arrived', 'arrived', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Trạng thái không hợp lệ'}, status=400)
        
        appointment.status = new_status
        appointment.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã cập nhật trạng thái: {appointment.get_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "DELETE"])
@staff_api
def api_appointment_delete(request, appointment_code):
    """
    API: Xóa lịch hẹn (HARD DELETE - xóa vĩnh viễn khỏi database)

    Thay đổi từ soft delete sang hard delete:
    - Xóa thật bản ghi khỏi database
    - Không chỉ chuyển status sang cancelled
    - Không thể khôi phục sau khi xóa

    Security:
    - CSRF protection qua @staff_api decorator
    - Chỉ staff/superuser mới được xóa
    """
    # Lấy appointment hoặc trả về 404
    appointment, error = get_or_404(Appointment, appointment_code=appointment_code)
    if error:
        return error

    try:
        # Lưu thông tin để log trước khi xóa
        appointment_id = appointment.id

        # Lấy tên khách hàng từ ForeignKey
        customer_name = "Khách hàng"
        if appointment.customer and appointment.customer.user:
            customer_name = appointment.customer.user.get_full_name() or appointment.customer.user.username

        # HARD DELETE - xóa thật khỏi database
        appointment.delete()

        return JsonResponse({
            'success': True,
            'message': f'Đã xóa vĩnh viễn lịch hẹn {appointment_code}',
            'deleted_id': appointment_id,
            'customer_name': customer_name
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Không thể xóa lịch hẹn: {str(e)}'
        }, status=400)


@require_http_methods(["GET"])
def api_booking_requests(request):
    """
    API: Lấy danh sách yêu cầu đặt lịch từ web (source='web' hoặc NULL)
    
    Query params:
    - date: YYYY-MM-DD
    - status: pending|confirmed|cancelled
    - q: search term
    
    NOTE: Bao gồm cả record có source=NULL để hỗ trợ dữ liệu cũ
    """
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'success': False, 'error': 'Không có quyền truy cập'}, status=403)
    
    # Lấy cả record có source='web' hoặc source=NULL (dữ liệu cũ)
    from django.db.models import Q
    appointments = Appointment.objects.filter(Q(source='web') | Q(source__isnull=True))
    
    # Filter by date
    date_filter = request.GET.get('date', '')
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Search
    search = request.GET.get('q', '').strip()
    if search:
        appointments = appointments.filter(
            Q(appointment_code__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    appointments_data = []
    for appt in appointments:
        appointments_data.append({
            'id': appt.appointment_code,
            'customerName': appt.customer.full_name,
            'phone': appt.customer.phone,
            'email': getattr(appt.customer.user, 'email', '') if appt.customer.user else '',
            'service': appt.service.name,
            'serviceId': appt.service.id,
            'roomId': appt.room.code if appt.room else '',
            'roomName': appt.room.name if appt.room else '',
            'guests': appt.guests,
            'date': appt.appointment_date.strftime('%Y-%m-%d'),
            'start': appt.appointment_time.strftime('%H:%M'),
            'end': appt.get_end_time_display(),
            'durationMin': appt.duration_minutes or appt.service.duration_minutes,
            'note': appt.notes or '',
            'apptStatus': appt.status,
            'payStatus': appt.payment_status,
            'source': appt.source,
        })
    
    return JsonResponse({'success': True, 'appointments': appointments_data})
