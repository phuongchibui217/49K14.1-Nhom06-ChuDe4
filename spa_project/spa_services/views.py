"""
Views cho Service Management

File này chứa các views cho:
- Trang danh sách dịch vụ (public)
- Trang chi tiết dịch vụ (public)
- Quản lý dịch vụ (admin)
- API endpoints cho services

Author: Spa ANA Team
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

# TẠM IMPORT từ spa.models (CHƯA chuyển model trong phase này)
from .models import Service

# Forms (sẽ tạo trong spa_services/forms.py)
from .forms import ServiceForm

# Service layer từ spa_services/service_services
from .service_services import (
    validate_service_data,
    create_service,
    update_service,
    get_service_by_id,
    serialize_service,
)

# Decorators, API response từ core
from core.api_response import staff_api, get_or_404


def _save_service_image(image_file):
    """Lưu file ảnh dịch vụ vào MEDIA_ROOT và trả về relative path."""
    import os, uuid
    from django.conf import settings
    ext = os.path.splitext(image_file.name or '')[1].lower() or '.jpg'
    filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"services/{filename}"
    abs_path = os.path.join(settings.MEDIA_ROOT, 'services', filename)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'wb') as f:
        for chunk in image_file.chunks():
            f.write(chunk)
    return rel_path


# =====================================================
# PUBLIC SERVICE PAGES
# =====================================================

def service_list(request):
    """Danh sách dịch vụ - Lọc chỉ active"""
    services = Service.objects.filter(status='ACTIVE').order_by('-created_at')
    return render(request, 'spa_services/services.html', {'services': services})


def service_detail(request, service_id):
    """Chi tiết dịch vụ - Lấy từ database"""
    service = get_object_or_404(Service, id=service_id, status='ACTIVE')

    # Lấy các dịch vụ liên quan (cùng category)
    related_services = Service.objects.filter(
        category=service.category,
        status='ACTIVE'
    ).exclude(id=service_id)[:4]

    return render(request, 'spa_services/service_detail.html', {
        'service': service,
        'related_services': related_services
    })


# =====================================================
# ADMIN SERVICE MANAGEMENT
# =====================================================

@login_required(login_url='accounts:login')
def admin_services(request):
    """
    Quản lý dịch vụ

    GET: Hiển thị danh sách dịch vụ với pagination và filter
    POST: Xử lý thêm dịch vụ mới
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

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
            _code_map = {'1': 'CAT01', '2': 'CAT02', '3': 'CAT03', '4': 'CAT04'}
            category_code = _code_map.get(category_filter)
            if category_code:
                services_list = services_list.filter(category__code=category_code)

        if status_filter:
            services_list = services_list.filter(status=status_filter)

        # Pagination
        paginator = Paginator(services_list, 10)
        page_number = request.GET.get('page', 1)
        services = paginator.get_page(page_number)

        # Get next service code
        next_code = Service._generate_code()

        context = {
            'services': services,
            'next_service_code': next_code,
            'search_query': search_query,
            'category_filter': category_filter,
            'status_filter': status_filter,
        }
        return render(request, 'manage/pages/admin_services.html', context)

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
                return redirect('spa_services:admin_services')

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
        return redirect('spa_services:admin_services')


@login_required(login_url='accounts:login')
def admin_service_edit(request, service_id):
    """
    Sửa dịch vụ
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

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
                return redirect('spa_services:admin_services')

            except Exception as e:
                messages.error(
                    request,
                    'Có lỗi khi lưu dữ liệu, vui lòng thử lại'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('spa_services:admin_services')


@login_required(login_url='accounts:login')
def admin_service_delete(request, service_id):
    """
    Xóa dịch vụ
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')

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

    return redirect('spa_services:admin_services')


# =====================================================
# API ENDPOINTS FOR SERVICES
# =====================================================

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
            'categoryId': service.category_id,
            'categoryName': service.get_category_name(),
            'description': service.short_description or service.description[:100] if service.description else '',
            'price': float(service.price),
            'duration': service.duration_minutes,
            'duration_minutes': service.duration_minutes,
            'status': service.status,
            'image': service.image if service.image else 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100'
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

        # Map category number to ServiceCategory object
        _code_map = {'1': 'CAT01', '2': 'CAT02', '3': 'CAT03', '4': 'CAT04'}
        from .models import ServiceCategory
        cat_code = _code_map.get(str(category), 'CAT01')
        try:
            category_obj = ServiceCategory.objects.get(code=cat_code)
        except ServiceCategory.DoesNotExist:
            category_obj = None

        # Create service
        service = Service.objects.create(
            name=name,
            category=category_obj,
            short_description=description[:300] if len(description) > 300 else description,
            description=description,
            price=price,
            duration_minutes=duration,
            status=status,
            is_active=status == 'ACTIVE',
            image='',
            created_by=request.user,
        )

        # Handle image upload
        if image_file:
            if image_file.size > 5 * 1024 * 1024:
                service.delete()
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                service.delete()
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)
            service.image = _save_service_image(image_file)
            service.save()

        return JsonResponse({
            'success': True,
            'message': f'Đã thêm dịch vụ: {service.name}',
            'service': {
                'id': service.id,
                'code': service.code or '',
                'name': service.name,
                'categoryName': service.get_category_name(),
                'image': service.image if service.image else 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100'
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

        # Map category number to ServiceCategory object
        _code_map = {'1': 'CAT01', '2': 'CAT02', '3': 'CAT03', '4': 'CAT04'}
        from .models import ServiceCategory
        cat_code = _code_map.get(str(category), None)
        if cat_code:
            try:
                category_obj = ServiceCategory.objects.get(code=cat_code)
                service.category = category_obj
            except ServiceCategory.DoesNotExist:
                pass  # keep existing category

        # Update service
        service.name = name
        service.short_description = description[:300] if len(description) > 300 else description
        service.description = description
        service.price = price
        service.duration_minutes = duration
        service.status = status
        service.is_active = status == 'ACTIVE'

        # Handle image upload
        if image_file:
            if image_file.size > 5 * 1024 * 1024:
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)
            service.image = _save_service_image(image_file)

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
        from core.api_response import ApiResponse
        return ApiResponse.error(f'Lỗi khi xóa dịch vụ: {str(e)}')
