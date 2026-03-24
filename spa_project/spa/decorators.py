"""
Decorators dùng chung cho Spa ANA

File này chứa các decorator để:
- Kiểm tra quyền truy cập
- Giảm lặp code
- Dễ bảo trì

Author: Spa ANA Team
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import JsonResponse
from functools import wraps


# =====================================================
# STAFF REQUIRED DECORATOR (cho trang admin)
# =====================================================

def staff_required(login_url=None, redirect_on_fail='spa:home'):
    """
    Decorator kiểm tra user có quyền staff/superuser không
    
    Sử dụng cho: Các trang admin (render template)
    
    Hành vi:
    - Chưa đăng nhập → Redirect đến trang login
    - Đã đăng nhập nhưng không phải staff → Message lỗi + redirect
    
    Args:
        login_url: URL trang login (optional, mặc định dùng spa:admin_login)
        redirect_on_fail: URL redirect khi không có quyền (mặc định: spa:home)
    
    Usage:
        @staff_required()
        def admin_appointments(request):
            # View code here
            return render(request, 'admin/pages/admin_appointments.html')
        
        # Hoặc chỉ định login_url riêng
        @staff_required(login_url='spa:admin_login')
        def admin_services(request):
            return render(request, 'admin/pages/admin_services.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url or 'spa:admin_login')
        def _wrapped_view(request, *args, **kwargs):
            # Kiểm tra quyền staff hoặc superuser
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Không có quyền → báo lỗi + redirect
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect(redirect_on_fail)
        
        return _wrapped_view
    
    return decorator


# =====================================================
# API STAFF REQUIRED DECORATOR (cho API endpoints)
# =====================================================

def api_staff_required():
    """
    Decorator kiểm tra quyền staff/superuser cho API endpoints
    
    Sử dụng cho: Các API trả về JSON
    
    Hành vi:
    - Chưa đăng nhập → JsonResponse 401
    - Đã đăng nhập nhưng không phải staff → JsonResponse 403
    
    Returns:
        JsonResponse với format chuẩn nếu không có quyền
    
    Usage:
        @api_staff_required()
        def api_services_list(request):
            services = Service.objects.all()
            return JsonResponse({'services': list(services.values())})
        
        # Kết hợp với @csrf_exempt
        @csrf_exempt
        @api_staff_required()
        def api_service_create(request):
            # API code here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Kiểm tra đã đăng nhập chưa
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Vui lòng đăng nhập để tiếp tục.'
                }, status=401)
            
            # Kiểm tra quyền staff hoặc superuser
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Không có quyền
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền thực hiện thao tác này.'
            }, status=403)
        
        return _wrapped_view
    
    return decorator


# =====================================================
# COMBINED DECORATORS
# =====================================================

def admin_view(login_url=None):
    """
    Shortcut decorator cho admin page views
    
    Tương đương với:
        @login_required(login_url='spa:admin_login')
        + check is_staff/is_superuser
    
    Usage:
        @admin_view()
        def admin_dashboard(request):
            return render(request, 'admin/pages/dashboard.html')
    """
    return staff_required(login_url=login_url or 'spa:admin_login')


def admin_api():
    """
    Shortcut decorator cho admin API endpoints
    
    Tương đương với @api_staff_required()
    
    Usage:
        @admin_api()
        def api_get_data(request):
            return JsonResponse({'data': [...]})
    """
    return api_staff_required()


# =====================================================
# CUSTOMER REQUIRED DECORATOR
# =====================================================

def customer_required(login_url='spa:login', redirect_on_fail='spa:home'):
    """
    Decorator kiểm tra user đã đăng nhập và có CustomerProfile
    
    Sử dụng cho: Các trang dành cho khách hàng đã đăng ký
    
    Hành vi:
    - Chưa đăng nhập → Redirect đến trang login
    - Đã đăng nhập nhưng không có CustomerProfile → Tạo mới hoặc redirect
    
    Args:
        login_url: URL trang login
        redirect_on_fail: URL redirect khi không có profile
    
    Usage:
        @customer_required()
        def my_appointments(request):
            # View code here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            from .models import CustomerProfile
            
            # Kiểm tra có CustomerProfile không
            try:
                # Có profile → cho phép truy cập
                request.user.customer_profile
                return view_func(request, *args, **kwargs)
            except CustomerProfile.DoesNotExist:
                # Không có profile → tạo mới hoặc redirect
                # Tùy business logic, có thể tạo tự động hoặc báo lỗi
                messages.warning(request, 'Vui lòng hoàn tất thông tin tài khoản.')
                return redirect(redirect_on_fail)
        
        return _wrapped_view
    
    return decorator


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def is_staff_user(user):
    """
    Helper function kiểm tra user có phải staff/superuser không
    
    Dùng cho:
    - Template tags
    - Conditional logic trong view
    
    Args:
        user: User object
    
    Returns:
        bool: True nếu là staff hoặc superuser
    
    Usage:
        if is_staff_user(request.user):
            # Do something
            pass
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_customer_user(user):
    """
    Helper function kiểm tra user có phải khách hàng không
    
    Args:
        user: User object
    
    Returns:
        bool: True nếu đã đăng nhập và có CustomerProfile
    """
    if not user.is_authenticated:
        return False
    
    from .models import CustomerProfile
    return CustomerProfile.objects.filter(user=user).exists()