# 📘 HƯỚNG DẪN PHÂN QUYỀN DJANGO - SPA ANA

> **Hệ thống phân quyền hoàn chỉnh** cho 4 nhóm người dùng

---

## 📌 PHẦN 1: CUSTOM PERMISSIONS TRONG MODELS

### 1.1 Thêm Permissions vào Models

**File: appointments/models.py**

```python
from django.db import models

class Appointment(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("view_all_appointments", "Can view all appointments"),
            ("manage_own_appointments", "Can manage own appointments"),
            ("cancel_appointment", "Can cancel appointments"),
        ]
```

**File: spa_services/models.py**

```python
class Service(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("view_all_services", "Can view all services"),
            ("manage_services", "Can add/edit services"),
        ]
```

**File: complaints/models.py**

```python
class Complaint(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("view_all_complaints", "Can view all complaints"),
            ("respond_complaints", "Can respond to complaints"),
            ("manage_own_complaints", "Can manage own complaints"),
        ]
```

**File: customers/models.py** (nếu có riêng)

```python
class Customer(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("view_all_customers", "Can view all customers"),
            ("manage_customers", "Can manage customer info"),
            ("view_own_profile", "Can view own profile"),
        ]
```

---

## 📌 PHẦN 2: TẠO GROUPS

### 2.1 Cách 1: Tạo bằng Django Admin

1. Vào: `http://localhost:8000/admin/`
2. **Authentication & Authorization** → **Groups**
3. **Add Group**:

#### Group 1: Lễ tân (Receptionist)
- **Name:** `Lễ tân`
- **Permissions:**
  - ✅ appointments: Can add, change, delete appointment
  - ✅ appointments: view_all_appointments
  - ✅ customers: view_all_customers
  - ✅ customers: manage_customers
  - ✅ complaints: view_all_complaints
  - ✅ complaints: respond_complaints
  - ❌ staff: (không có quyền nào)

#### Group 2: Khách hàng (Customer)
- **Name:** `Khách hàng`
- **Permissions:**
  - ✅ appointments: Can add appointment
  - ✅ appointments: manage_own_appointments
  - ✅ appointments: cancel_appointment
  - ✅ services: view_all_services (chỉ xem)
  - ✅ complaints: Can add complaint
  - ✅ complaints: manage_own_complaints
  - ✅ customers: view_own_profile

### 2.2 Cách 2: Tạo bằng Code (Recommended)

**Tạo file:** `spa_project/create_groups.py`

```python
"""
Tạo Groups và Permissions cho hệ thống Spa
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from appointments.models import Appointment
from spa_services.models import Service
from complaints.models import Complaint
from accounts.models import CustomerProfile

def create_groups():
    """Tạo Groups và gán Permissions"""
    
    # =====================================================
    # GROUP 1: LỄ TÂN
    # =====================================================
    receptionist_group, created = Group.objects.get_or_create(name='Lễ tân')
    
    # Permissions for Appointments
    appointment_ct = ContentType.objects.get_for_model(Appointment)
    receptionist_group.permissions.add(
        # CRUD Appointments
        Permission.objects.get(codename='add_appointment', content_type=appointment_ct),
        Permission.objects.get(codename='change_appointment', content_type=appointment_ct),
        Permission.objects.get(codename='delete_appointment', content_type=appointment_ct),
        Permission.objects.get(codename='view_appointment', content_type=appointment_ct),
        # Custom permissions
        Permission.objects.get(codename='view_all_appointments', content_type=appointment_ct),
    )
    
    # Permissions for Customers
    customer_ct = ContentType.objects.get_for_model(CustomerProfile)
    receptionist_group.permissions.add(
        Permission.objects.get(codename='view_customerprofile', content_type=customer_ct),
        Permission.objects.get(codename='change_customerprofile', content_type=customer_ct),
    )
    
    # Permissions for Complaints
    complaint_ct = ContentType.objects.get_for_model(Complaint)
    receptionist_group.permissions.add(
        Permission.objects.get(codename='view_complaint', content_type=complaint_ct),
        Permission.objects.get(codename='change_complaint', content_type=complaint_ct),
        Permission.objects.get(codename='view_all_complaints', content_type=complaint_ct),
        Permission.objects.get(codename='respond_complaints', content_type=complaint_ct),
    )
    
    # Permissions for Services (view only)
    service_ct = ContentType.objects.get_for_model(Service)
    receptionist_group.permissions.add(
        Permission.objects.get(codename='view_service', content_type=service_ct),
    )
    
    print("✅ Group 'Lễ tân' created successfully!")
    
    # =====================================================
    # GROUP 2: KHÁCH HÀNG
    # =====================================================
    customer_group, created = Group.objects.get_or_create(name='Khách hàng')
    
    # Permissions for Appointments (limited)
    customer_group.permissions.add(
        Permission.objects.get(codename='add_appointment', content_type=appointment_ct),
        Permission.objects.get(codename='view_appointment', content_type=appointment_ct),
        Permission.objects.get(codename='manage_own_appointments', content_type=appointment_ct),
        Permission.objects.get(codename='cancel_appointment', content_type=appointment_ct),
    )
    
    # Permissions for Services (view only)
    customer_group.permissions.add(
        Permission.objects.get(codename='view_service', content_type=service_ct),
        Permission.objects.get(codename='view_all_services', content_type=service_ct),
    )
    
    # Permissions for Complaints (own only)
    customer_group.permissions.add(
        Permission.objects.get(codename='add_complaint', content_type=complaint_ct),
        Permission.objects.get(codename='view_complaint', content_type=complaint_ct),
        Permission.objects.get(codename='manage_own_complaints', content_type=complaint_ct),
    )
    
    # Permissions for own profile
    customer_group.permissions.add(
        Permission.objects.get(codename='view_customerprofile', content_type=customer_ct),
        Permission.objects.get(codename='change_customerprofile', content_type=customer_ct),
        Permission.objects.get(codename='view_own_profile', content_type=customer_ct),
    )
    
    print("✅ Group 'Khách hàng' created successfully!")
    print("\n" + "="*60)
    print("GROUPS CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"1. Lễ tân: {receptionist_group.permissions.count()} permissions")
    print(f"2. Khách hàng: {customer_group.permissions.count()} permissions")

if __name__ == '__main__':
    create_groups()
```

**Chạy script:**
```bash
python create_groups.py
```

---

## 📌 PHẦN 3: DECORATORS TRONG VIEWS

### 3.1 Sử dụng @permission_required

**File: appointments/views.py**

```python
from django.contrib.auth.decorators import login_required, permission_required

# =====================================================
# LỄ TÂN: Quản lý tất cả lịch hẹn
# =====================================================

@login_required(login_url='accounts:login')
@permission_required('appointments.view_all_appointments', login_url='accounts:login', raise_exception=True)
def admin_appointments(request):
    """Quản lý tất cả lịch hẹn - Chỉ Lễ tân"""
    appointments = Appointment.objects.all()
    return render(request, 'manage/pages/admin_appointments.html', {
        'appointments': appointments
    })

@login_required(login_url='accounts:login')
@permission_required('appointments.add_appointment', login_url='accounts:login')
def create_appointment_staff(request):
    """Tạo lịch hẹn - Lễ tân tạo giúp khách"""
    if request.method == 'POST':
        # ... create appointment logic
        pass
    return render(request, 'manage/pages/create_appointment.html')

# =====================================================
# KHÁCH HÀNG: Quản lý lịch hẹn cá nhân
# =====================================================

@login_required(login_url='accounts:login')
def my_appointments(request):
    """Lịch hẹn của tôi - Tất cả user đã login"""
    # Chỉ lấy appointments của user hiện tại
    appointments = Appointment.objects.filter(
        customer__user=request.user
    )
    return render(request, 'spa/pages/my_appointments.html', {
        'appointments': appointments
    })

@login_required(login_url='accounts:login')
@permission_required('appointments.manage_own_appointments', login_url='accounts:login')
def cancel_my_appointment(request, appointment_id):
    """Hủy lịch hẹn - Chỉ appointments của mình"""
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id,
        customer__user=request.user  # Chỉ appointments của mình
    )
    # ... cancel logic
    pass
```

### 3.2 Custom Decorators cho Role-Based Access

**Tạo file:** `core/decorators.py` (nếu chưa có)

```python
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def receptionist_required(view_func):
    """
    Decorator: Chỉ cho phép Lễ tân hoặc Superuser
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user is receptionist (is_staff) or superuser
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Bạn không có quyền truy cập trang này.")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def customer_required(view_func):
    """
    Decorator: Chỉ cho phép Khách hàng (có CustomerProfile)
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user has CustomerProfile
        try:
            from accounts.models import CustomerProfile
            profile = request.user.customer_profile
        except CustomerProfile.DoesNotExist:
            raise PermissionDenied("Tài khoản này không phải là khách hàng.")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def group_required(*group_names):
    """
    Decorator: Check user belongs to specific groups
    
    Usage:
        @group_required('Lễ tân', 'Chủ Spa')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @login_required(login_url='accounts:login')
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            # Check if user belongs to any of the required groups
            user_groups = request.user.groups.values_list('name', flat=True)
            if not any(group in user_groups for group in group_names):
                raise PermissionDenied(
                    f"Bạn cần thuộc về một trong các nhóm: {', '.join(group_names)}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Sử dụng Custom Decorators:**

```python
from core.decorators import receptionist_required, customer_required, group_required

# =====================================================
# CÁCH 1: DÙNG DECORATOR THEO ROLE
# =====================================================

@receptionist_required
def admin_appointments(request):
    """Chỉ Lễ tân/Superuser"""
    pass

@customer_required
def my_profile(request):
    """Chỉ Khách hàng"""
    pass

# =====================================================
# CÁCH 2: DÙNG DECORATOR THEO GROUP
# =====================================================

@group_required('Lễ tân', 'Chủ Spa')
def manage_appointments(request):
    """Chỉ Lễ tân hoặc Chủ Spa"""
    pass

@group_required('Khách hàng')
def my_appointments(request):
    """Chỉ Khách hàng"""
    pass
```

---

## 📌 PHẦN 4: TEMPLATE TAGS CHECK PERMISSIONS

### 4.1 Tạo Custom Template Tags

**Tạo file:** `spa_project/templatetags/permission_tags.py`

```python
from django import template

register = template.Library()

@register.filter
def is_receptionist(user):
    """Check if user is receptionist"""
    return user.is_staff or user.is_superuser

@register.filter
def is_customer(user):
    """Check if user is customer (has CustomerProfile)"""
    try:
        return hasattr(user, 'customer_profile') and user.customer_profile is not None
    except:
        return False

@register.filter
def has_group(user, group_name):
    """Check if user belongs to group"""
    return user.groups.filter(name=group_name).exists()

@register.simple_tag
def can_manage_appointments(user):
    """Check if user can manage appointments"""
    return user.has_perm('appointments.view_all_appointments')

@register.simple_tag
def can_view_services(user):
    """Check if user can view services"""
    return user.has_perm('spa_services.view_all_services')
```

### 4.2 Sử dụng trong Templates

**Template: manage/includes/sidebar.html**

```django
{% load permission_tags %}

<nav class="admin-sidebar">
    <!-- MENU CHUNG -->
    <li>
        <a href="{% url 'pages:home' %}">
            <i class="fas fa-home"></i> Trang chủ
        </a>
    </li>

    <!-- MENU CHỈ LỄ TÂN -->
    {% if user|is_receptionist %}
    <li>
        <a href="{% url 'appointments:admin_appointments' %}">
            <i class="fas fa-calendar-check"></i> Quản lý lịch hẹn
        </a>
    </li>
    <li>
        <a href="{% url 'customers:admin_customers' %}">
            <i class="fas fa-users"></i> Quản lý khách hàng
        </a>
    </li>
    <li>
        <a href="{% url 'complaints:admin_complaints' %}">
            <i class="fas fa-exclamation-triangle"></i> Quản lý khiếu nại
        </a>
    </li>
    {% endif %}

    <!-- MENU CHỢ CHỦ SPA (SUPERUSER) -->
    {% if user.is_superuser %}
    <li>
        <a href="{% url 'staff:admin_staff' %}">
            <i class="fas fa-user-tie"></i> Quản lý nhân viên
        </a>
    </li>
    <li>
        <a href="{% url 'spa_services:admin_services' %}">
            <i class="fas fa-spa"></i> Quản lý dịch vụ
        </a>
    </li>
    {% endif %}

    <!-- MENU CHỈ KHÁCH HÀNG -->
    {% if user|is_customer %}
    <li>
        <a href="{% url 'appointments:my_appointments' %}">
            <i class="fas fa-calendar"></i> Lịch hẹn của tôi
        </a>
    </li>
    <li>
        <a href="{% url 'spa_services:service_list' %}">
            <i class="fas fa-spa"></i> Xem dịch vụ
        </a>
    </li>
    <li>
        <a href="{% url 'accounts:customer_profile' %}">
            <i class="fas fa-user"></i> Tài khoản
        </a>
    </li>
    {% endif %}
</nav>
```

**Template: spa/pages/home.html**

```django
{% load permission_tags %}

<!-- BUTTON ĐẶT LỊCH - TẤT CẢ USER -->
<a href="{% url 'appointments:booking' %}" class="btn btn-primary">
    <i class="fas fa-calendar-plus"></i> Đặt lịch ngay
</a>

<!-- BUTTON QUẢN LÝ - CHỈ LỄ TÂN -->
{% if user|is_receptionist %}
<a href="{% url 'appointments:admin_appointments' %}" class="btn btn-warning">
    <i class="fas fa-cog"></i> Quản lý hệ thống
</a>
{% endif %}
```

---

## 📌 PHẦN 5: REDIRECT THEO ROLE SAU LOGIN

### 5.1 Cải thiện Login View

**File: accounts/views.py**

```python
def _redirect_by_role(request, user, show_welcome=False):
    """
    Redirect theo role sau khi login
    
    Args:
        request: HttpRequest object
        user: User object
        show_welcome: Có hiển thị message chào mừng không
    
    Returns:
        HttpResponseRedirect
    """
    # 1. KHÁCH HÀNG (có CustomerProfile)
    try:
        from accounts.models import CustomerProfile
        profile = user.customer_profile
        if show_welcome:
            full_name = profile.full_name or user.username
            messages.success(request, f'Chào mừng {full_name}!')
        return redirect('appointments:my_appointments')
    except CustomerProfile.DoesNotExist:
        pass
    
    # 2. LỄ TÂN (is_staff=True, không phải superuser)
    if user.is_staff and not user.is_superuser:
        if show_welcome:
            full_name = user.get_full_name() or user.username
            messages.success(request, f'Chào mừng {full_name}! (Lễ tân)')
        return redirect('/manage/appointments/')
    
    # 3. CHỦ SPA (is_superuser=True)
    if user.is_superuser:
        if show_welcome:
            full_name = user.get_full_name() or user.username
            messages.success(request, f'Chào mừng {full_name}! (Quản trị viên)')
        return redirect('/manage/appointments/')
    
    # 4. USER KHÔNG HỢP LỆ
    else:
        logout(request)
        messages.error(request, 'Tài khoản chưa được phân quyền.')
        return redirect('pages:home')
```

---

## 📌 PHẦN 6: MIDDLEWARE CHECK GROUP MEMBERSHIP

### 6.1 Tạo Custom Middleware

**File:** `spa_project/middleware.py`

```python
from django.shortcuts import redirect
from django.conf import settings

class GroupRequiredMixin:
    """
    Middleware kiểm tra group membership cho URLs cụ thể
    
    Thêm vào settings.py:
    'spa_project.middleware.GroupRequiredMixin',
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs yêu cầu group 'Lễ tân'
        receptionist_urls = ['/manage/appointments/', '/manage/customers/']
        
        # URLs yêu cầu group 'Khách hàng'
        customer_urls = ['/lich-hen-cua-toi/', '/tai-khoan/']
        
        # Check nếu URL cần group 'Lễ tân'
        if request.path in receptionist_urls:
            if not request.user.is_authenticated:
                return redirect(f'/login/?next={request.path}')
            
            if not (request.user.is_staff or request.user.is_superuser):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Bạn cần là Lễ tân để truy cập trang này.")
        
        # Check nếu URL cần group 'Khách hàng'
        elif request.path in customer_urls:
            if not request.user.is_authenticated:
                return redirect(f'/login/?next={request.path}')
            
            try:
                from accounts.models import CustomerProfile
                request.user.customer_profile
            except CustomerProfile.DoesNotExist:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Bạn cần là Khách hàng để truy cập trang này.")
        
        return self.get_response(request)
```

### 6.2 Kích hoạt Middleware

**File:** `spa_project/settings.py`

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom middleware
    'spa_project.middleware.GroupRequiredMixin',
]
```

---

## 📌 PHẦN 7: BẢNG TỔNG HỢP PERMISSIONS

### 7.1 Bảng Phân Quyền

| Model | Lễ tân | Khách hàng | Chủ Spa |
|-------|--------|-----------|---------|
| **Appointments** | | | |
| View all appointments | ✅ | ❌ | ✅ |
| Add appointment | ✅ | ✅ (booking) | ✅ |
| Change appointment | ✅ | ❌ | ✅ |
| Delete appointment | ✅ | ❌ | ✅ |
| Manage own appointments | ❌ | ✅ | ✅ |
| **Customers** | | | |
| View all customers | ✅ | ❌ | ✅ |
| Manage customers | ✅ | ❌ (own only) | ✅ |
| **Complaints** | | | |
| View all complaints | ✅ | ❌ | ✅ |
| Respond complaints | ✅ | ❌ | ✅ |
| Manage own complaints | ❌ | ✅ | ✅ |
| **Services** | | | |
| View services | ✅ | ✅ | ✅ |
| Add/Change/Delete services | ❌ | ❌ | ✅ |
| **Staff** | | | |
| View staff | ❌ | ❌ | ✅ |
| Manage staff | ❌ | ❌ | ✅ |

### 7.2 Bảng Redirect sau Login

| User Type | Redirect URL | Mô tả |
|-----------|-------------|-------|
| Lễ tân | `/manage/appointments/` | Dashboard quản lý |
| Chủ Spa | `/manage/appointments/` | Dashboard quản lý |
| Khách hàng | `/lich-hen-cua-toi/` | Lịch hẹn cá nhân |

---

## 📌 PHẦN 8: VÍ DỤ THỰC TẾ

### 8.1 View với Multiple Decorators

```python
from django.contrib.auth.decorators import login_required, permission_required
from core.decorators import receptionist_required, customer_required

# LỄ TÂN: Quản lý khiếu nại
@login_required(login_url='accounts:login')
@permission_required('complaints.respond_complaints', raise_exception=True)
def respond_complaint(request, complaint_id):
    """Phản hồi khiếu nại - Chỉ Lễ tân"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        # ... response logic
        pass
    return render(request, 'manage/pages/respond_complaint.html', {
        'complaint': complaint
    })

# KHÁCH HÀNG: Gửi khiếu nại
@login_required(login_url='accounts:login')
@customer_required
def create_complaint(request):
    """Gửi khiếu nại - Chỉ Khách hàng"""
    if request.method == 'POST':
        # ... create complaint logic
        pass
    return render(request, 'spa/pages/create_complaint.html')

# CHỦ SPA: Quản lý services
@login_required(login_url='accounts:login')
@permission_required('spa_services.manage_services', raise_exception=True)
def admin_services(request):
    """Quản lý dịch vụ - Chỉ Chủ Spa"""
    if not request.user.is_superuser:
        raise PermissionDenied("Chỉ Chủ Spa mới quản lý dịch vụ.")
    services = Service.objects.all()
    return render(request, 'manage/pages/admin_services.html', {
        'services': services
    })
```

### 8.2 Template với Complex Checks

```django
{% load permission_tags %}

<!-- MENU ĐA CẤP -->
<div class="sidebar">
    <!-- MENU CHO TẤT CẢ USER ĐÃ LOGIN -->
    {% if user.is_authenticated %}
    <li><a href="{% url 'spa_services:service_list' %}">Xem dịch vụ</a></li>
    {% endif %}
    
    <!-- MENU CHỈ LỄ TÂN -->
    {% if user|is_receptionist %}
    <li>
        <a href="{% url 'appointments:admin_appointments' %}">
            Quản lý lịch hẹn
        </a>
    </li>
    <li>
        {% if user|has_group:'Lễ tân' %}
        <a href="{% url 'customers:admin_customers' %}">
            Quản lý khách hàng
        </a>
        {% endif %}
    </li>
    {% endif %}
    
    <!-- MENU CHỢ CHỦ SPA -->
    {% if user.is_superuser %}
    <li><a href="{% url 'staff:admin_staff' %}">Quản lý nhân viên</a></li>
    <li><a href="{% url 'spa_services:admin_services' %}">Quản lý dịch vụ</a></li>
    {% endif %}
    
    <!-- MENU CHỈ KHÁCH HÀNG -->
    {% if user|is_customer %}
    <li><a href="{% url 'appointments:my_appointments' %}">Lịch hẹn của tôi</a></li>
    <li><a href="{% url 'accounts:customer_profile' %}">Tài khoản</a></li>
    {% endif %}
</div>
```

---

## 📌 PHẦN 9: TESTING & DEBUGGING

### 9.1 Test Permissions trong Django Shell

```python
python manage.py shell

# Test user permissions
from django.contrib.auth.models import User
user = User.objects.get(username='letan01')

# Check all permissions
print("All permissions:")
for perm in user.get_all_permissions():
    print(f"  - {perm[0]}.{perm[1]}")

# Check specific permission
print("\nHas appointment view permission:", user.has_perm('appointments.view_appointment'))
print("Is staff:", user.is_staff)
print("Groups:", [g.name for g in user.groups.all()])

# Check if user has permission for a specific object
from appointments.models import Appointment
appointment = Appointment.objects.first()
print("Can view appointment:", user.has_perm('appointments.view_appointment', appointment))
```

### 9.2 Test Redirect

```python
from django.test import Client
from django.contrib.auth.models import User

# Test login redirect
client = Client()

# Test customer login
response = client.post('/login/', {
    'role': 'customer',
    'username': '0901234567',
    'password': 'customer123'
})
print("Customer redirect:", response.url)  # Expected: /lich-hen-cua-toi/

# Test staff login
response = client.post('/login/', {
    'role': 'staff',
    'username': 'letan01',
    'password': 'letan123'
})
print("Staff redirect:", response.url)  # Expected: /manage/appointments/
```

---

## 🎯 KẾT LUẬN

Hệ thống phân quyền này:

✅ **Dễ quản lý:** Groups & Permissions trong Django Admin
✅ **Bảo mật:** Decorator + Middleware + Template tags
✅ **Linh hoạt:** Dễ thêm/bớt quyền
✅ **Chuẩn Django:** Sử dụng built-in features
✅ **Dễ mở rộng:** Dễ thêm role mới

---

**Next Steps:**
1. Tạo Groups bằng script
2. Add user vào Groups
3. Test permissions
4. Deploy!

**Last updated:** 2026-04-09
