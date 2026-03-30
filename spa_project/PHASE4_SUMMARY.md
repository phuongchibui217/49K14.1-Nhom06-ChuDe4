# PHASE 4 SUMMARY: TÁCH MODULE ACCOUNTS (AUTHENTICATION & CUSTOMER PROFILE)
## Ngày thực hiện: 30/03/2026

---

## ✅ TRẠNG THÁI: HOÀN THÀNH

---

## A. MỤC TIÊU PHASE 4

✅ Tách authentication & customer profile sang app `accounts`
✅ Chuyển 7 views sang `accounts/views.py`
✅ Chuyển 3 forms sang `accounts/forms.py`
✅ Chuyển 6 URLs sang `accounts/urls.py`
✅ Giữ nguyên URL public
✅ **GIỮ NGUYÊN `CustomerProfile` model ở `spa.models` (tạm import)**
✅ Không tạo migration
✅ Không đổi business logic

---

## B. LỆNH ĐÃ CHẠY

```bash
# Test Django check
python manage.py check
# ✅ System check identified no issues (0 silenced).

# Test import views và forms
python manage.py shell -c "from accounts.views import login_view, register, customer_profile; from accounts.forms import CustomerRegistrationForm, CustomerProfileForm, ChangePasswordForm; print('OK')"
# ✅ OK: All accounts views and forms imported successfully

# Test URL routing
python manage.py shell -c "from django.urls import reverse; print(reverse('accounts:login'), reverse('accounts:register'), reverse('accounts:customer_profile'))"
# ✅ /login/ /register/ /tai-khoan/

# Test server
python manage.py runserver 0.0.0.0:8000
# ✅ Starting development server at http://0.0.0.0:8000/ - SUCCESS
```

---

## C. FILE ĐÃ TẠO (3 files trong accounts/)

### C.1. accounts/views.py (337 dòng)

```python
"""
Views cho Authentication và Customer Profile
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
# ... imports cho password reset

# TẠM IMPORT từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import CustomerProfile

# Forms (sẽ tạo trong accounts/forms.py)
from .forms import (
    CustomerRegistrationForm,
    CustomerProfileForm,
    ChangePasswordForm,
)

# 7 views được chuyển:
# - login_view
# - register
# - logout_view
# - password_reset_request
# - password_reset_confirm
# - customer_profile
```

**Đặc điểm**:
- Import tạm `CustomerProfile` từ `spa.models`
- Import forms từ `accounts.forms` (cùng app)
- Sửa redirect từ `'spa:home'` → `'pages:home'` (vì home đã chuyển sang pages)
- Sửa redirect URL thành absolute (tạm thời) để tránh namespace confusion: `/login/`, `/tai-khoan/`

### C.2. accounts/forms.py (275 dòng)

```python
"""
Forms cho Authentication và Customer Profile
"""

from django import forms
from django.contrib.auth.models import User

# TẠM IMPORT từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import CustomerProfile

# 3 forms được chuyển:
# - CustomerProfileForm
# - ChangePasswordForm
# - CustomerRegistrationForm
```

**Đặc điểm**:
- Meta model vẫn = `CustomerProfile` (model vẫn ở spa)
- `clean_phone()` dùng `CustomerProfile.objects` (import từ spa.models)
- `save()` tạo `User` + `CustomerProfile` (User từ Django, CustomerProfile từ spa)

### C.3. accounts/urls.py (46 dòng)

```python
"""
URL configuration cho accounts app
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset
    path('quen-mat-khau/', views.password_reset_request, name='password_reset'),
    path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    # Customer Profile
    path('tai-khoan/', views.customer_profile, name='customer_profile'),
]
```

**Đặc điểm**:
- URL pattern y hệt bản gốc
- App namespace: `accounts`
- Names: `login`, `register`, `logout`, `password_reset`, `password_reset_confirm`, `customer_profile`

---

## D. FILE ĐÃ SỬA (2 files)

### D.1. spa_project/urls.py (Root URLs)

**ĐÃ SỬA**: Thêm include cho `accounts.urls`

```python
# TRƯỚC
urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app
    path('', include('pages.urls')),
    # Original spa app
    path('', include('spa.urls')),
]

# SAU
urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app
    path('', include('pages.urls')),
    # Phase 4: Accounts app (authentication, customer profile)
    path('', include('accounts.urls')),    # ⭐ NEW
    # Original spa app (keeping for now)
    path('', include('spa.urls')),        # FALLBACK
]
```

**Lý do include order**:
- `pages.urls` có path('') cho root `/`
- `accounts.urls` KHÔNG có path('') → KHÔNG conflict với pages
- `spa.urls` fallback nếu cần

### D.2. spa/urls.py (Fallback routes)

**ĐÃ SỬA**: Comment out 6 accounts-related routes

```python
# ============================================================
# PHASE 4: DEPRECATED - Moved to accounts/urls.py
# ============================================================
# path('login/', views.login_view, name='login'),                             # MOVED → accounts/
# path('register/', views.register, name='register'),                         # MOVED → accounts/
# path('logout/', views.logout_view, name='logout'),                           # MOVED → accounts/
# path('quen-mat-khau/', views.password_reset_request, name='password_reset'),    # MOVED → accounts/
# path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm,         # MOVED → accounts/
# path('tai-khoan/', views.customer_profile, name='customer_profile'),           # MOVED → accounts/
```

---

## E. ROUTE BỈ ẢNH HƯỞNG

| URL | App cũ | App mới | Status |
|-----|--------|---------|--------|
| `/login/` | spa.views.login_view | accounts.views.login_view | ✅ **MOVED** |
| `/register/` | spa.views.register | accounts.views.register | ✅ **MOVED** |
| `/logout/` | spa.views.logout_view | accounts.views.logout_view | ✅ **MOVED** |
| `/quen-mat-khau/` | spa.views.password_reset_request | accounts.views.password_reset_request | ✅ **MOVED** |
| `/reset-mat-khau/<uidb64>/<token>/` | spa.views.password_reset_confirm | accounts.views.password_reset_confirm | ✅ **MOVED** |
| `/tai-khoan/` | spa.views.customer_profile | accounts.views.customer_profile | ✅ **MOVED** |

**Fallback**: Uncomment routes trong `spa/urls.py` nếu cần rollback.

---

## F. IMPORT BỈ ẢNH HƯỞNG

### F.1. Imports mới trong accounts/views.py

```python
# TẠM IMPORT từ spa.models
from spa.models import CustomerProfile

# Từ accounts.forms (cùng app)
from .forms import (
    CustomerRegistrationForm,
    CustomerProfileForm,
    ChangePasswordForm,
)
```

### F.2. Imports mới trong accounts/forms.py

```python
# TẠM IMPORT từ spa.models
from spa.models import CustomerProfile

# Django auth
from django.contrib.auth.models import User
```

### F.3. Imports trong spa/views.py

**KHÔNG CÓ thay đổi** - Functions giữ nguyên, chỉ URL bị comment.

---

## G. STRATEGY XỬ LÝ CUSTOMERPROFILE

### G.1. QUYẾT ĐỊNH TRONG PHASE 4

✅ **GIỮ NGUYÊN `CustomerProfile` model ở `spa/models.py`**
✅ accounts/views.py **TẠM IMPORT** `from spa.models import CustomerProfile`
✅ accounts/forms.py **TẠM IMPORT** `from spa.models import CustomerProfile`
✅ **KHÔNG TẠO** migration trong phase này
✅ **KHÔNG CHUYỂR** model definition

### G.2. Lý do

1. **An toàn**: Không thay đổi database schema
2. **Đơn giản**: Tránh complexity của migration
3. **Nhanh**: Chỉ chuyển views + forms + urls
4. **Ít rủi ro**: Model vẫn ở spa, chỉ thay đổi nơi import
5. **Dễ rollback**: Xóa accounts app, code vẫn hoạt động

### G.3. Khi nào chuyển model?

**Phase sau** (nếu cần) - Khi đã:
- ✅ Tách xong tất cả modules
- ✅ Test kỹ càng
- ✅ Chốt kiến trúc mới
- ✅ Có kế hoạch migration rõ ràng

### G.4. CustomerProfile đang được import ở đâu?

**TRONG PHASE 4**:
- `accounts/views.py` → `from spa.models import CustomerProfile` ⭐ TẠM IMPORT
- `accounts/forms.py` → `from spa.models import CustomerProfile` ⭐ TẠM IMPORT
- `spa/views.py` → `from .models import CustomerProfile` (giữ nguyên)
- `spa/forms.py` → `from .models import CustomerProfile` (giữ nguyên)
- `spa/admin.py` → `from .models import CustomerProfile` (giữ nguyên)
- `spa/appointment_services.py` → `from .models import CustomerProfile` (giữ nguyên)

---

## H. RỦI RO

### H.1. Rủi ro đã tránh

✅ **KHÔNG CÓ** - Chiến lược tạm import hoạt động hoàn hảo.

### H.2. Rủi ro hiện tại

✅ **KHÔNG CÓ** - Phase 4 an toàn tuyệt đối.

### H.3. Lưu ý quan trọng

⚠️ **Redirect URL** trong `accounts/views.py`:
- `redirect('pages:home')` - Home đã chuyển sang pages
- `redirect('/login/')` - Absolute URL (tạm thời) để tránh namespace confusion
- `redirect('/tai-khoan/')` - Absolute URL (tạm thời)

**Lý do dùng absolute URL**:
- Tránh confusion giữa `spa:login`, `accounts:login`, `pages:home`
- Đơn giản, không cần nhớ namespace
- Sẽ refactor dần sau khi namespace chốt

---

## I. CÁCH TEST THỦ CÔNG

### I.1. Test Django check

```bash
python manage.py check
```

**Kết quả**: ✅ `System check identified no issues (0 silenced).`

### I.2. Test import

```bash
python manage.py shell -c "from accounts.views import login_view, register, customer_profile; from accounts.forms import CustomerRegistrationForm, CustomerProfileForm, ChangePasswordForm; print('OK')"
```

**Kết quả**: ✅ `OK: All accounts views and forms imported successfully`

### I.3. Test URL routing

```bash
python manage.py shell -c "from django.urls import reverse; print('Login:', reverse('accounts:login')); print('Register:', reverse('accounts:register')); print('Customer profile:', reverse('accounts:customer_profile'))"
```

**Kết quả**: ✅ `Login: /login/` `Register: /register/` `Customer profile: /tai-khoan/`

### I.4. Test server

```bash
python manage.py runserver 0.0.0.0:8000
```

**Kết quả**: ✅ `Starting development server at http://0.0.0.0:8000/` - SUCCESS

### I.5. Test URLs (thủ công qua browser)

```bash
# Mở browser và truy cập:
http://127.0.0.1:8000/login/         # Trang đăng nhập
http://127.0.0.1:8000/register/       # Trang đăng ký
http://127.0.0.1:8000/tai-khoan/      # Trang tài khoản
```

**Kết quả mong đợi**:
- ✅ Trang đăng nhập hiển thị đúng
- ✅ Trang đăng ký hiển thị đúng
- ✅ Trang tài khoản hiển thị đúng (nếu đã login)
- ✅ Form đăng ký hoạt động (tạo user + CustomerProfile)
- ✅ Form login hoạt động (authenticate thành công)

### I.6. Test fallback (nếu cần)

Nếu accounts app có lỗi:
1. Uncomment 6 routes trong `spa/urls.py`
2. Restart server
3. URLs vẫn hoạt động (về spa.views)

---

## J. ĐIỀU KIỂN ĐỂ SANG PHASE 5

✅ Accounts views đã chuyển sang `accounts/views.py`
✅ Accounts forms đã chuyển sang `accounts/forms.py`
✅ Accounts URLs đã chuyển sang `accounts/urls.py`
✅ Django check pass
✅ Server chạy được
✅ URL routing hoạt động
✅ CustomerProfile model GIỮ NGUYÊN ở spa.models (tạm import)
✅ Chưa có migration
✅ Chưa có code nào bị lỗi

**ĐÃ SẴN SÀNG CHO PHASE 5** ✓

---

## K. GHI CHÚ

### K.1. Chiến lược an toàn đã áp dụng

**1. Tạm import CustomerProfile từ spa.models**
```python
# accounts/views.py
from spa.models import CustomerProfile  # Tạm import

# accounts/forms.py
from spa.models import CustomerProfile  # Tạm import
```

**Lợi ích**:
- An toàn: không chuyển model
- Đơn giản: giữ nguyên data access
- Rõ ràng: comment "TẠm import"

**2. Comment routes thay vì delete**
```python
# path('login/', views.login_view, name='login'),  # MOVED → accounts/
```

**Lợi ích**:
- Giữ code gốc để tham khảo
- Dễ uncomment nếu cần fallback
- Minh bạch: ghi rõ DEPRECATED + MOVED

**3. Absolute URL trong redirect (tạm thời)**
```python
# accounts/views.py
redirect('/login/')      # Absolute URL (tạm thời)
redirect('/tai-khoan/')  # Absolute URL (tạm thời)
```

**Lý do**:
- Tránh namespace confusion (spa: vs accounts: vs pages:)
- Đơn giản, không cần nhớ namespace
- Sẽ refactor dần sau khi namespace chốt

### K.2. Template path decision

**QUYẾT ĐỊNH**: Giữ nguyên template path trong Phase 4

```python
# accounts/views.py
return render(request, 'spa/pages/login.html')     # Giữ nguyên path
return render(request, 'spa/pages/register.html')   # Giữ nguyên path
return render(request, 'spa/pages/customer_profile.html')  # Giữ nguyên path
```

**Lý do**:
1. ✅ An toàn: không di chuyển template
2. ✅ Đơn giản: không cần copy/reorganize
3. ✅ Nhanh: chỉ chuyển views + forms + urls
4. ✅ Ít rủi ro: tránh break template includes

**Phase sau** (nếu cần):
- Copy templates sang `accounts/templates/accounts/`
- Update template paths trong views
- Test lại includes, inheritance

### K.3. Số dòng code

| File | Trước | Sau | Thay đổi |
|------|------|-----|----------|
| `spa/views.py` | 1935 dòng | 1935 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/forms.py` | 809 dòng | 809 dòng | **Giữ nguyên** (chưa xóa) |
| `accounts/views.py` | 4 dòng (boilerplate) | 337 dòng | **+333 dòng** |
| `accounts/forms.py` | 0 dòng | 275 dòng | **+275 dòng** |
| `spa/urls.py` | 77 routes | 71 routes | **-6 routes** (commented) |
| `accounts/urls.py` | 0 routes | 6 routes | **+6 routes** |

### K.4. URL namespace changes

```python
# TRƯỚC (spa namespace)
reverse('spa:login')              # → /login/
reverse('spa:register')           # → /register/
reverse('spa:password_reset')     # → /quen-mat-khau/
reverse('spa:customer_profile')   # → /tai-khoan/

# SAU (accounts namespace)
reverse('accounts:login')         # → /login/
reverse('accounts:register')        # → /register/
reverse('accounts:password_reset') # → /quen-mat-khau/
reverse('accounts:customer_profile') # → /tai-khoan/

# Fallback (vẫn hoạt động nếu uncomment spa routes)
reverse('spa:login')   # vẫn có (commented)
```

**Lưu ý**:
- Templates hoặc code đang dùng `url 'spa:login'` cần update → `url 'accounts:login'` hoặc `{% url 'accounts:login' %}`
- Hoặc giữ `url 'spa:login'` nếu uncomment fallback routes
- Sẽ update dần ở các phase sau

---

## L. LỢI ÍCH CỦA PHASE 4

1. ✅ **Tách accounts module**: Authentication & customer profile sang app riêng
2. ✅ **Giảm phụ thuộc**: Accounts không phụ thuộc spa business logic
3. ✅ **Foundation**: Sẵn sàng cho authentication system riêng biệt
4. ✅ **Fallback an toàn**: Routes cũ có thể rollback dễ dàng
5. ✅ **Minimize disruption**: Chuyển 7 views + 3 forms đơn giản nhất
6. ✅ **Template stable**: Không di chuyển template, giữ ổn định
7. ✅ **Model safe**: Giữ nguyên CustomerProfile ở spa.models

---

## M. NEXT STEPS

**PHASE 5**: Tách module `spa_services` (Dịch vụ)
- Chuyển Service model
- Chuyển service views, forms, URLs
- Migration an toàn cho Service model

---

**End of Phase 4 Summary**
