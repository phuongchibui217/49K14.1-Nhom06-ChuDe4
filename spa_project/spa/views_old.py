from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Service, Appointment, ConsultationRequest, SupportRequest, CustomerProfile


# =====================================================
# DỮ liệu mẫu tạm thời (HARDCODE - sẽ chuyển sang Model sau)
# =====================================================
SAMPLE_SERVICES = [
    {
        'id': 1,
        'name': 'Chăm sóc da mặt cao cấp',
        'description': 'Dịch vụ chăm sóc da mặt chuyên sâu với các sản phẩm cao cấp từ thiên nhiên. Quy trình bao gồm làm sạch sâu, tẩy tế bào chết, massage mặt, đắp mặt nạ dưỡng ẩm. Phù hợp cho mọi loại da, đặc biệt là da khô, da dầu hoặc da nhạy cảm.',
        'price': 800000,
        'duration': 90,
        'category': 'skincare',
        'category_name': 'Chăm sóc da',
        'image_url': 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=400',
    },
    {
        'id': 2,
        'name': 'Massage thư giãn toàn thân',
        'description': 'Liệu trình massage toàn thân với các kỹ thuật truyền thống kết hợp hiện đại. Giúp giảm stress, thư giãn cơ bắp, cải thiện tuần huyết và mang lại cảm giác thư thái tuyệt đối. Sử dụng tinh dầu massage cao cấp.',
        'price': 1200000,
        'duration': 120,
        'category': 'massage',
        'category_name': 'Massage',
        'image_url': 'https://images.unsplash.com/photo-1544161515-5766320?w=400',
    },
    {
        'id': 3,
        'name': 'Phun thêu lông mày chất lượng',
        'description': 'Dịch vụ phun thêu lông mày với mực vẽ 3D tự nhiên, không gây đau, giữ màu lâu trôi. Sử dụng mực nhập khẩu cao cấp từ Mỹ. Bảo hành 2 năm.',
        'price': 2500000,
        'duration': 180,
        'category': 'tattoo',
        'category_name': 'Phun thêu',
        'image_url': 'https://images.unsplash.com/photo-1583001936773-7c5e5a23?w=400',
    },
    {
        'id': 4,
        'name': 'Triệt lông vĩnh viễn IPL',
        'description': 'Công nghệ triệt lông IPL mới nhất, hiệu quả cao, an toàn, không gây đau. Triệt lông vĩnh viễn sau 6-8 buổi điều trị. Phù hợp cho mọi vùng da.',
        'price': 3500000,
        'duration': 60,
        'category': 'hair',
        'category_name': 'Triệt lông',
        'image_url': 'https://images.unsplash.com/photo-1522337360832-3f8d62f5?w=400',
    },
    {
        'id': 5,
        'name': 'Gội đầu dưỡng sinh',
        'description': 'Gội đầu thư giãn với tinh dầu thiên nhiên và massage vai. Giúp giảm căng thẳng, thư giãn tinh thần, mái tóc mềm mượt.',
        'price': 300000,
        'duration': 45,
        'category': 'skincare',
        'category_name': 'Chăm sóc da',
        'image_url': 'https://images.unsplash.com/photo-1527799820375-6f8e80a898?w=400',
    },
    {
        'id': 6,
        'name': 'Nails Art - Vẽ mó nghệ thuật',
        'description': 'Dịch vụ làm mó nghệ thuật với các mẫu thiết kế đa dạng, Sử dụng sơn gel cao cấp, giữ màu lâu.',
        'price': 500000,
        'duration': 90,
        'category': 'skincare',
        'category_name': 'Chăm sóc da',
        'image_url': 'https://images.unsplash.com/photo-1604654899129-3dd0f86d7a?w=400',
    },
]


def get_sample_services():
    """Lấy danh sách dịch vụ mẫu (tạm thời - sẽ chuyển sang Model)"""
    return SAMPLE_SERVICES


def get_sample_service_by_id(service_id):
    """Lấy dịch vụ mẫu theo ID (tạm thời - sẽ chuyển sang Model)"""
    for service in SAMPLE_SERVICES:
        if service['id'] == service_id:
            return service
    return None


# =====================================================
# VIEWS - Trang tĩnh
# =====================================================


def home(request):
    """Trang chủ"""
    services = get_sample_services()[:6]
    return render(request, 'spa/pages/home.html', {'services': services})


def about(request):
    """Về Spa ANA"""
    return render(request, 'spa/pages/about.html')


def service_list(request):
    """Danh sách dịch vụ"""
    services = get_sample_services()
    return render(request, 'spa/pages/services.html', {'services': services})


def service_detail(request, service_id):
    """Chi tiết dịch vụ"""
    service = get_sample_service_by_id(service_id)
    if not service:
        from django.http import Http404
        raise Http404("Dịch vụ không tồn tại")
    
    # Lấy các dịch vụ liên quan (cùng category)
    related_services = [s for s in get_sample_services() if s['id'] != service_id][:4]
    
    return render(request, 'spa/pages/service_detail.html', {
        'service': service,
        'related_services': related_services
    })


# =====================================================
# VIEWS - Form POST (sẽ implement sau)
# =====================================================


def booking(request):
    """Đặt lịch hẹn"""
    services = get_sample_services()
    
    if request.method == 'POST':
        # TODO: Implement booking logic sau
        messages.info(request, 'Đặt lịch thành công! (Chưa implement)')
        return redirect('home')
    
    return render(request, 'spa/pages/booking.html', {'services': services})


def consultation(request):
    """Đăng ký tư vấn"""
    if request.method == 'POST':
        # TODO: Implement consultation logic sau
        messages.info(request, 'Đăng ký tư vấn thành công! (Chưa implement)')
        return redirect('home')
    
    return render(request, 'spa/pages/consultation.html')


def complaint(request):
    """Góp ý/Khiếu nại"""
    if request.method == 'POST':
        # TODO: Implement complaint logic sau
        messages.info(request, 'Gửi góp ý thành công! (Chưa implement)')
        return redirect('home')
    
    return render(request, 'spa/pages/complaint.html')


@login_required
def my_appointments(request):
    """Lịch hẹn của tôi"""
    # TODO: Get appointments from database
    appointments = []  # Placeholder
    return render(request, 'spa/pages/my_appointments.html', {'appointments': appointments})


# =====================================================
# VIEWS - Authentication (sẽ implement sau)
# =====================================================


def login_view(request):
    """Đăng nhập"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        # TODO: Implement login logic sau
        username = request.POST.get('username')
        password = request.POST.get('password')
        messages.error(request, 'Chưa implement logic đăng nhập')
    
    return render(request, 'spa/pages/login.html')


def register(request):
    """Đăng ký"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        # TODO: Implement register logic sau
        messages.info(request, 'Đăng ký thành công! (Chưa implement)')
        return redirect('home')
    
    return render(request, 'spa/pages/register.html')


def logout_view(request):
    """Đăng xuất"""
    # TODO: Implement logout logic sau
    messages.info(request, 'Đã đăng xuất!')
    return redirect('home')