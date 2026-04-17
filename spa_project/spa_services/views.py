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


def _save_service_image(service, image_file):
    """
    Gán image_file vào ImageField của service và lưu.
    Django ImageField tự xử lý: sinh tên file, lưu vào MEDIA_ROOT/services/,
    và lưu relative path vào DB — không cần tự ghép path thủ công.
    """
    service.image = image_file
    service.save(update_fields=['image'])


# =====================================================
# PUBLIC SERVICE PAGES
# =====================================================

def service_list(request):
    """Danh sách dịch vụ - Lọc chỉ active, tính min/max price và duration từ variants"""
    from .models import ServiceCategory
    from django.db.models import Min, Max, Count

    services = (
        Service.objects
        .filter(status='ACTIVE')
        .select_related('category')
        .prefetch_related('variants')
        .annotate(
            min_price=Min('variants__price', filter=Q(variants__is_active=True)),
            max_price=Max('variants__price', filter=Q(variants__is_active=True)),
            min_duration=Min('variants__duration_minutes', filter=Q(variants__is_active=True)),
            max_duration=Max('variants__duration_minutes', filter=Q(variants__is_active=True)),
            variant_count=Count('variants', filter=Q(variants__is_active=True)),
        )
        .order_by('-created_at')
    )
    categories = ServiceCategory.objects.filter(status='ACTIVE').order_by('sort_order', 'name')
    return render(request, 'spa_services/services.html', {
        'services': services,
        'categories': categories,
    })


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
        services_list = Service.objects.all().prefetch_related('variants').order_by('-created_at')

        # Search functionality
        search_query = request.GET.get('search', '')
        category_filter = request.GET.get('category', '')
        status_filter = request.GET.get('status', '')

        if search_query:
            services_list = services_list.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )

        if category_filter:
            services_list = services_list.filter(category__code=category_filter)

        if status_filter:
            services_list = services_list.filter(status=status_filter)

        # Pagination
        paginator = Paginator(services_list, 10)
        page_number = request.GET.get('page', 1)
        services = paginator.get_page(page_number)

        # Get next service code
        next_code = Service._generate_code()

        # Get categories from DB for form dropdown — không hardcode
        from .models import ServiceCategory
        categories = ServiceCategory.objects.filter(status='ACTIVE').order_by('sort_order')

        context = {
            'services': services,
            'categories': categories,
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
    """API: Lấy danh sách dịch vụ kèm variants"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Không có quyền truy cập'}, status=403)

    from .models import ServiceVariant

    search_query = request.GET.get('search', '')
    service_id = request.GET.get('id', '')

    if service_id:
        services = Service.objects.filter(pk=service_id)
    elif search_query:
        services = Service.objects.filter(
            Q(name__icontains=search_query) | Q(code__icontains=search_query)
        )
    else:
        services = Service.objects.all().order_by('-created_at')

    services = services.prefetch_related('variants')

    services_data = [
        {
            'id': s.id,
            'code': s.code or '',
            'name': s.name,
            'categoryId': s.category_id,
            'categoryCode': s.category.code if s.category else '',
            'categoryName': s.get_category_name(),
            'description': s.short_description or (s.description[:100] if s.description else ''),
            'short_description': s.short_description or '',
            'detail_description': s.description or '',
            'status': s.status,
            'image': s.image.url if s.image else 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100',
            'variants': [
                {
                    'id': v.id,
                    'label': v.label,
                    'duration_minutes': v.duration_minutes,
                    'price': float(v.price),
                    'sort_order': v.sort_order,
                }
                for v in s.variants.filter(is_active=True).order_by('sort_order', 'duration_minutes')
            ],
        }
        for s in services
    ]
    return JsonResponse({'services': services_data})


@require_http_methods(["POST"])
@staff_api
def api_service_create(request):
    """API: Thêm dịch vụ mới"""
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category_number', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            description = request.POST.get('description', '').strip()
            status = (request.POST.get('status', 'ACTIVE') or 'ACTIVE').upper()
            code = request.POST.get('code', '').strip().upper()
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            category = data.get('category_number', data.get('category', '')).strip()
            short_description = data.get('short_description', '').strip()
            description = data.get('description', '').strip()
            status = (data.get('status', 'ACTIVE') or 'ACTIVE').upper()
            code = data.get('code', '').strip().upper()
            image_file = None

        # Fallback: nếu short_description trống thì dùng description cắt ngắn
        if not short_description:
            short_description = description[:255] if description else ''

        if not name:
            return JsonResponse({'error': 'Vui lòng nhập tên dịch vụ!'}, status=400)
        if len(name) < 5:
            return JsonResponse({'error': 'Tên dịch vụ phải có ít nhất 5 ký tự!'}, status=400)
        if len(name) > 200:
            return JsonResponse({'error': 'Tên dịch vụ không được quá 200 ký tự!'}, status=400)
        if Service.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': f'Dịch vụ "{name}" đã tồn tại!'}, status=400)

        from .models import ServiceCategory
        try:
            category_obj = ServiceCategory.objects.get(code=str(category))
        except ServiceCategory.DoesNotExist:
            category_obj = ServiceCategory.objects.filter(status='ACTIVE').first()
            if not category_obj:
                return JsonResponse({'error': 'Không tìm thấy danh mục dịch vụ.'}, status=400)

        status = status if status in ('ACTIVE', 'INACTIVE') else 'ACTIVE'

        # Auto-generate description nếu để trống / quá ngắn
        from .description_helpers import generate_service_description, should_generate_description
        _tmp = Service(name=name, category=category_obj, short_description=short_description, description=description)
        if should_generate_description(_tmp):
            description = generate_service_description(_tmp)

        service = Service.objects.create(
            name=name,
            category=category_obj,
            short_description=short_description,
            description=description,
            status=status,
            image='',
            created_by=request.user,
            updated_by=request.user,
        )
        if code:
            if Service.objects.filter(code=code).exclude(id=service.id).exists():
                service.delete()
                return JsonResponse({'error': f'Mã dịch vụ "{code}" đã tồn tại!'}, status=400)
            service.code = code
            service.save(update_fields=['code'])

        if image_file:
            if image_file.size > 5 * 1024 * 1024:
                service.delete()
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                service.delete()
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)
            _save_service_image(service, image_file)

        # Tạo variants nếu có
        from .models import ServiceVariant
        from django.db import transaction as db_transaction
        variants_json = request.POST.get('variants_json', '[]')
        try:
            variants_data = json.loads(variants_json)
        except (json.JSONDecodeError, TypeError):
            variants_data = []

        variant_errors = []
        with db_transaction.atomic():
            for i, v in enumerate(variants_data):
                label = str(v.get('label', '')).strip()
                try:
                    duration = int(v.get('duration_minutes', 0))
                    price = float(v.get('price', 0))
                except (ValueError, TypeError):
                    variant_errors.append(f'Gói {i+1}: thời lượng hoặc giá không hợp lệ')
                    continue
                if not label:
                    variant_errors.append(f'Gói {i+1}: thiếu tên gói')
                    continue
                if duration <= 0:
                    variant_errors.append(f'Gói {i+1}: thời lượng phải > 0')
                    continue
                if price < 0:
                    variant_errors.append(f'Gói {i+1}: giá không hợp lệ')
                    continue
                ServiceVariant.objects.create(
                    service=service,
                    label=label,
                    duration_minutes=duration,
                    price=price,
                    sort_order=i,
                )

        return JsonResponse({
            'success': True,
            'message': f'Đã thêm dịch vụ: {service.name}' + (f' ({len(variants_data) - len(variant_errors)} gói)' if variants_data else ''),
            'variant_errors': variant_errors,
            'service': {
                'id': service.id,
                'code': service.code or '',
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
    """API: Cập nhật dịch vụ"""
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category_number', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            description = request.POST.get('description', '').strip()
            status = (request.POST.get('status', 'ACTIVE') or 'ACTIVE').upper()
            code = request.POST.get('code', '').strip().upper()
            image_file = request.FILES.get('image')
        else:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            category = data.get('category_number', data.get('category', '')).strip()
            short_description = data.get('short_description', '').strip()
            description = data.get('description', '').strip()
            status = (data.get('status', 'ACTIVE') or 'ACTIVE').upper()
            code = data.get('code', '').strip().upper()
            image_file = None

        # Fallback: nếu short_description trống thì dùng description cắt ngắn
        if not short_description:
            short_description = description[:255] if description else ''

        if not name:
            return JsonResponse({'error': 'Vui lòng nhập tên dịch vụ!'}, status=400)
        if len(name) < 5:
            return JsonResponse({'error': 'Tên dịch vụ phải có ít nhất 5 ký tự!'}, status=400)
        if len(name) > 200:
            return JsonResponse({'error': 'Tên dịch vụ không được quá 200 ký tự!'}, status=400)
        if Service.objects.filter(name__iexact=name).exclude(id=service_id).exists():
            return JsonResponse({'error': f'Dịch vụ "{name}" đã tồn tại!'}, status=400)

        from .models import ServiceCategory
        if category:
            try:
                service.category = ServiceCategory.objects.get(code=category)
            except ServiceCategory.DoesNotExist:
                pass

        if code and code != service.code:
            if Service.objects.filter(code=code).exclude(id=service_id).exists():
                return JsonResponse({'error': f'Mã dịch vụ "{code}" đã tồn tại!'}, status=400)
            service.code = code

        status = status if status in ('ACTIVE', 'INACTIVE') else 'ACTIVE'
        service.name = name
        service.short_description = short_description

        # Auto-generate description nếu để trống / quá ngắn
        from .description_helpers import generate_service_description, should_generate_description
        service.description = description
        if should_generate_description(service):
            service.description = generate_service_description(service)

        service.status = status
        service.updated_by = request.user

        if image_file:
            if image_file.size > 5 * 1024 * 1024:
                return JsonResponse({'error': 'Hình ảnh không được quá 5MB!'}, status=400)
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return JsonResponse({'error': 'Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WebP)!'}, status=400)
            _save_service_image(service, image_file)

        service.save()

        # Cập nhật variants: xóa hết rồi tạo lại từ variants_json
        from .models import ServiceVariant
        from django.db import transaction as db_transaction
        variants_json = request.POST.get('variants_json', None)
        if variants_json is not None:
            try:
                variants_data = json.loads(variants_json)
            except (json.JSONDecodeError, TypeError):
                variants_data = []
            with db_transaction.atomic():
                service.variants.all().delete()
                for i, v in enumerate(variants_data):
                    label = str(v.get('label', '')).strip()
                    try:
                        duration = int(v.get('duration_minutes', 0))
                        price = float(v.get('price', 0))
                    except (ValueError, TypeError):
                        continue
                    if not label or duration <= 0 or price < 0:
                        continue
                    ServiceVariant.objects.create(
                        service=service,
                        label=label,
                        duration_minutes=duration,
                        price=price,
                        sort_order=i,
                    )

        return JsonResponse({'success': True, 'message': f'Đã cập nhật dịch vụ: {service.name}'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["DELETE", "POST"])
@staff_api
def api_service_delete(request, service_id):
    """API: Xóa dịch vụ"""
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    try:
        service_name = service.name
        service.delete()
        return JsonResponse({'success': True, 'message': f'Đã xóa dịch vụ: {service_name}'})
    except Exception as e:
        from core.api_response import ApiResponse
        return ApiResponse.error(f'Lỗi khi xóa dịch vụ: {str(e)}')


# =====================================================
# API ENDPOINTS FOR SERVICE VARIANTS
# =====================================================

@require_http_methods(["GET"])
def api_variant_list(request, service_id):
    """API: Lấy danh sách variants của 1 service"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Không có quyền truy cập'}, status=403)

    from .models import ServiceVariant
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    variants = ServiceVariant.objects.filter(service=service).order_by('sort_order', 'duration_minutes')
    data = [
        {
            'id': v.id,
            'label': v.label,
            'duration_minutes': v.duration_minutes,
            'price': float(v.price),
            'sort_order': v.sort_order,
            'is_active': v.is_active,
        }
        for v in variants
    ]
    return JsonResponse({'success': True, 'variants': data})


@require_http_methods(["POST"])
@staff_api
def api_variant_create(request, service_id):
    """API: Tạo variant mới cho service"""
    from .models import ServiceVariant
    service, error = get_or_404(Service, id=service_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        label = data.get('label', '').strip()
        duration = data.get('duration_minutes')
        price = data.get('price')
        sort_order = data.get('sort_order', 0)

        if not label:
            return JsonResponse({'error': 'Vui lòng nhập tên gói'}, status=400)
        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Thời lượng không hợp lệ'}, status=400)
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Giá không hợp lệ'}, status=400)

        variant = ServiceVariant.objects.create(
            service=service,
            label=label,
            duration_minutes=duration,
            price=price,
            sort_order=sort_order,
        )
        return JsonResponse({
            'success': True,
            'message': f'Đã thêm gói: {variant.label}',
            'variant': {
                'id': variant.id,
                'label': variant.label,
                'duration_minutes': variant.duration_minutes,
                'price': float(variant.price),
                'sort_order': variant.sort_order,
                'is_active': variant.is_active,
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "PUT"])
@staff_api
def api_variant_update(request, service_id, variant_id):
    """API: Cập nhật variant"""
    from .models import ServiceVariant
    variant, error = get_or_404(ServiceVariant, id=variant_id, service_id=service_id)
    if error:
        return error

    try:
        data = json.loads(request.body)
        label = data.get('label', '').strip()
        duration = data.get('duration_minutes')
        price = data.get('price')
        sort_order = data.get('sort_order')
        is_active = data.get('is_active')

        if label:
            variant.label = label
        if duration is not None:
            try:
                duration = int(duration)
                if duration <= 0:
                    raise ValueError
                variant.duration_minutes = duration
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Thời lượng không hợp lệ'}, status=400)
        if price is not None:
            try:
                price = float(price)
                if price < 0:
                    raise ValueError
                variant.price = price
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Giá không hợp lệ'}, status=400)
        if sort_order is not None:
            variant.sort_order = int(sort_order)
        if is_active is not None:
            variant.is_active = bool(is_active)

        variant.save()
        return JsonResponse({'success': True, 'message': f'Đã cập nhật gói: {variant.label}'})
    except Exception as e:
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)


@require_http_methods(["POST", "DELETE"])
@staff_api
def api_variant_delete(request, service_id, variant_id):
    """API: Xóa variant"""
    from .models import ServiceVariant
    variant, error = get_or_404(ServiceVariant, id=variant_id, service_id=service_id)
    if error:
        return error

    try:
        label = variant.label
        variant.delete()
        return JsonResponse({'success': True, 'message': f'Đã xóa gói: {label}'})
    except Exception as e:
        return JsonResponse({'error': f'Lỗi: {str(e)}'}, status=400)
