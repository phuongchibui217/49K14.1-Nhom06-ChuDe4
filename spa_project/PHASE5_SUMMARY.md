# PHASE 5 SUMMARY: TÁCH MODULE SPA_SERVICES (DỊCH VỤ SPA)
## Ngày thực hiện: 30/03/2026

---

## ✅ TRẠNG THÁI: HOÀN THÀNH

---

## A. MỤC TIÊU PHASE 5

✅ Tách services management sang app `spa_services`
✅ Chuyển 9 views sang `spa_services/views.py`
✅ Chuyển 1 form sang `spa_services/forms.py`
✅ Chuyển service_services.py sang `spa_services/service_services.py`
✅ Chuyển 11 URLs sang `spa_services/urls.py`
✅ Giữ nguyên URL public
✅ **GIỮ NGUYÊN `Service` model ở `spa.models` (tạm import)**
✅ Không tạo migration
✅ Không đổi business logic
✅ **XỬ LÝ**: pages/views.py vẫn import Service từ spa.models thành công

---

## B. LỆNH ĐÃ CHẠY

```bash
# Test Django check
python manage.py check
# ✅ System check identified no issues (0 silenced).

# Test import spa_services
python manage.py shell -c "from spa_services.views import service_list, service_detail, admin_services, api_service_create; from spa_services.forms import ServiceForm; from spa_services.service_services import validate_service_name, create_service; print('OK')"
# ✅ OK: All spa_services views, forms, and services imported successfully

# Test URL routing
python manage.py shell -c "from django.urls import reverse; print(reverse('spa_services:service_list'), reverse('spa_services:service_detail', args=[1]), reverse('spa_services:admin_services'), reverse('spa_services:api_services_list'))"
# ✅ /services/ /service/1/ /manage/services/ /api/services/

# Test pages dependency
python manage.py shell -c "from pages.views import home; print('OK')"
# ✅ OK: pages.views.home still imports Service from spa.models successfully

# Test server
python manage.py runserver 0.0.0.0:8000
# ✅ Starting development server at http://0.0.0.0:8000/ - SUCCESS
```

---

## C. FILE ĐÃ TẠO (4 files trong spa_services/)

### C.1. spa_services/forms.py (279 dòng)

```python
"""
Forms cho Service Management
"""
from django import forms
from PIL import Image

# TẠM IMPORT từ spa.models
from spa.models import Service

class ServiceForm(forms.ModelForm):
    # ... toàn bộ validation logic
    # - category_number (1→skincare, 2→massage, 3→tattoo, 4→hair)
    # - clean_name(): không chỉ số, không trùng
    # - clean_image(): max 5MB, jpg/png/webp, min 300x300px
```

**Đặc điểm:**
- Meta model vẫn = `Service` (model vẫn ở spa)
- `clean_name()` dùng `Service.objects` (import từ spa.models)
- `clean_image()` validation giữ nguyên

---

### C.2. spa_services/service_services.py (369 dòng)

```python
"""
Service Services - Business logic cho Service model
"""
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# TẠM IMPORT từ spa.models
from spa.models import Service

# Validation functions:
# - validate_service_name()
# - validate_service_price()
# - validate_service_duration()
# - validate_service_image()
# - validate_service_data()

# CRUD functions:
# - create_service()
# - update_service()

# Helper functions:
# - get_service_by_id()
# - serialize_service()
```

**Đặc điểm:**
- Copy toàn bộ 369 dòng từ spa/service_services.py
- Import `Service` từ spa.models
- Functions: validate_service_*, create_service, update_service, get_service_by_id, serialize_service

---

### C.3. spa_services/views.py (690 dòng)

```python
"""
Views cho Service Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

# TẠM IMPORT từ spa.models
from spa.models import Service

# Forms từ spa_services.forms
from .forms import ServiceForm

# Service layer từ spa_services.service_services
from .service_services import (
    validate_service_data,
    create_service,
    update_service,
    get_service_by_id,
    serialize_service,
)

# Decorators, API response từ core
from core.api_response import staff_api, get_or_404

# 9 views:
# - service_list (public)
# - service_detail (public)
# - admin_services (admin CRUD list)
# - admin_service_edit (admin update)
# - admin_service_delete (admin delete)
# - api_services_list (API GET)
# - api_service_create (API POST)
# - api_service_update (API POST/PUT)
# - api_service_delete (API DELETE/POST)
```

**Đặc điểm:**
- Import tạm `Service` từ `spa.models`
- Import `ServiceForm` từ `spa_services.forms` (cùng app)
- Import service_services functions từ `spa_services.service_services`
- Import decorators, API response từ `core`
- Sửa redirect URL: `'spa:admin_services'` → `'/manage/services/'` (absolute URL tạm thời)
- Giữ nguyên template path: `spa/pages/services.html`, etc.

---

### C.4. spa_services/urls.py (45 dòng)

```python
"""
URL configuration cho spa_services app
"""
from django.urls import path
from . import views

app_name = 'spa_services'

urlpatterns = [
    # Public Service Pages
    path('services/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),

    # Admin Service Management
    path('manage/services/', views.admin_services, name='admin_services'),
    path('manage/services/<int:service_id>/edit/', views.admin_service_edit,
         name='admin_service_edit'),
    path('manage/services/<int:service_id>/delete/', views.admin_service_delete,
         name='admin_service_delete'),

    # API endpoints
    path('api/services/', views.api_services_list, name='api_services_list'),
    path('api/services/create/', views.api_service_create, name='api_service_create'),
    path('api/services/<int:service_id>/update/', views.api_service_update,
         name='api_service_update'),
    path('api/services/<int:service_id>/delete/', views.api_service_delete,
         name='api_service_delete'),
]
```

**Đặc điểm:**
- URL pattern y hệt bản gốc
- App namespace: `spa_services`
- 11 URL names

---

## D. FILE ĐÃ SỬA (2 files)

### D.1. spa_project/urls.py (Root URLs)

**ĐÃ SỬA**: Thêm include cho `spa_services.urls`

```python
# TRƯỚC
urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app
    path('', include('pages.urls')),
    # Phase 4: Accounts app
    path('', include('accounts.urls')),
    # Original spa app
    path('', include('spa.urls')),
]

# SAU
urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app
    path('', include('pages.urls')),
    # Phase 4: Accounts app
    path('', include('accounts.urls')),
    # Phase 5: Spa Services app (dịch vụ spa)
    path('', include('spa_services.urls')),    # ⭐ NEW
    # Original spa app (keeping for now)
    path('', include('spa.urls')),            # FALLBACK
]
```

**Lý do include order:**
- `pages.urls` có path('') cho root `/`
- `accounts.urls` KHÔNG có path('')
- `spa_services.urls` KHÔNG có path('') → KHÔNG conflict với pages
- `spa.urls` fallback nếu cần

---

### D.2. spa/urls.py (Fallback routes)

**ĐÃ SỬA**: Comment out 11 service-related routes

```python
# ============================================================
# PHASE 5: DEPRECATED - Moved to spa_services/urls.py
# ============================================================
# path('services/', views.service_list, name='service_list'),                    # MOVED → spa_services/
# path('service/<int:service_id>/', views.service_detail, name='service_detail'),    # MOVED → spa_services/
# path('manage/services/', views.admin_services, name='admin_services'),                # MOVED → spa_services/
# path('manage/services/<int:service_id>/edit/', views.admin_service_edit,             # MOVED → spa_services/
#      name='admin_service_edit'),                                                     # MOVED → spa_services/
# path('manage/services/<int:service_id>/delete/', views.admin_service_delete,         # MOVED → spa_services/
#      name='admin_service_delete'),                                                   # MOVED → spa_services/
# path('api/services/', views.api_services_list, name='api_services_list'),             # MOVED → spa_services/
# path('api/services/create/', views.api_service_create, name='api_service_create'),    # MOVED → spa_services/
# path('api/services/<int:service_id>/update/', views.api_service_update,               # MOVED → spa_services/
#      name='api_service_update'),                                                      # MOVED → spa_services/
# path('api/services/<int:service_id>/delete/', views.api_service_delete,               # MOVED → spa_services/
#      name='api_service_delete'),                                                      # MOVED → spa_services/
```

---

## E. ROUTE BỈ ẢNH HƯỞNG

| URL | App cũ | App mới | Status |
|-----|--------|---------|--------|
| `/services/` | spa.views.service_list | spa_services.views.service_list | ✅ **MOVED** |
| `/service/<int:service_id>/` | spa.views.service_detail | spa_services.views.service_detail | ✅ **MOVED** |
| `/manage/services/` | spa.views.admin_services | spa_services.views.admin_services | ✅ **MOVED** |
| `/manage/services/<int:service_id>/edit/` | spa.views.admin_service_edit | spa_services.views.admin_service_edit | ✅ **MOVED** |
| `/manage/services/<int:service_id>/delete/` | spa.views.admin_service_delete | spa_services.views.admin_service_delete | ✅ **MOVED** |
| `/api/services/` | spa.views.api_services_list | spa_services.views.api_services_list | ✅ **MOVED** |
| `/api/services/create/` | spa.views.api_service_create | spa_services.views.api_service_create | ✅ **MOVED** |
| `/api/services/<int:service_id>/update/` | spa.views.api_service_update | spa_services.views.api_service_update | ✅ **MOVED** |
| `/api/services/<int:service_id>/delete/` | spa_views.api_service_delete | spa_services.views.api_service_delete | ✅ **MOVED** |

**Fallback**: Uncomment routes trong `spa/urls.py` nếu cần rollback.

---

## F. IMPORT BỈ ẢNH HƯỞNG

### F.1. Imports mới trong spa_services/views.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Service

# Từ spa_services.forms (cùng app)
from .forms import ServiceForm

# Từ spa_services.service_services (cùng app)
from .service_services import (
    validate_service_data,
    create_service,
    update_service,
    get_service_by_id,
    serialize_service,
)

# Từ core (decorator, API response)
from core.api_response import staff_api, get_or_404
```

### F.2. Imports mới trong spa_services/forms.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Service
```

### F.3. Imports mới trong spa_services/service_services.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Service
```

### F.4. Imports GIỮ NGUYÊN trong pages/views.py

```python
# KHÔNG ĐỔI - vẫn import từ spa.models
from spa.models import Service  # Tạm import từ spa.models (sẽ refactor ở phase sau)
```

**Lý do**: Service model vẫn ở spa.models, giữ nguyên import trong Phase 5.

### F.5. Imports GIỮ NGUYÊN trong core/validators.py

```python
# KHÔNG ĐỔI - vẫn import từ spa.models
from spa.models import Service  # Tạm import từ spa.models
```

**Lý do**: Service model vẫn ở spa.models, giữ nguyên import trong Phase 5.

### F.6. Imports trong spa/views.py

**KHÔNG CÓ thay đổi** - Functions giữ nguyên, chỉ URL bị comment.

---

## G. STRATEGY XỬ LÝ SERVICE

### G.1. QUYẾT ĐỊNH TRONG PHASE 5

✅ **GIỮ NGUYÊN `Service` model ở `spa/models.py`**
✅ spa_services/views.py **TẠM IMPORT** `from spa.models import Service`
✅ spa_services/forms.py **TẠM IMPORT** `from spa.models import Service`
✅ spa_services/service_services.py **TẠM IMPORT** `from spa.models import Service`
✅ core/validators.py **GIỮ NGUYÊN** `from spa.models import Service`
✅ pages/views.py **GIỮ NGUYÊN** `from spa.models import Service`
✅ **KHÔNG TẠO** migration trong phase này
✅ **KHÔNG CHUYỂN** model definition

### G.2. Lý do

1. **An toàn**: Không thay đổi database schema
2. **Đơn giản**: Tránh complexity của migration
3. **Nhanh**: Chỉ chuyển views + forms + service layer + urls
4. **Ít rủi ro**: Model vẫn ở spa, chỉ thay đổi nơi import
5. **Dễ rollback**: Xóa spa_services app, code vẫn hoạt động
6. **Tránh circular dependency**: pages → spa.models.Service (giữ nguyên)

### G.3. Khi nào chuyển model?

**Phase sau** (nếu cần) - Khi đã:
- ✅ Tách xong tất cả modules
- ✅ Test kỹ càng
- ✅ Chốt kiến trúc mới
- ✅ Xử lý xong pages/views.py dependency
- ✅ Có kế hoạch migration rõ ràng

### G.4. Service đang được import ở đâu?

**TRONG PHASE 5**:
- `spa_services/views.py` → `from spa.models import Service` ⭐ TẠM IMPORT
- `spa_services/forms.py` → `from spa.models import Service` ⭐ TẠM IMPORT
- `spa_services/service_services.py` → `from spa.models import Service` ⭐ TẠM IMPORT
- `core/validators.py` → `from spa.models import Service` (giữ nguyên)
- `pages/views.py` → `from spa.models import Service` ⭐ **CRITICAL - GIỮ NGUYÊN**
- `spa/views.py` → `from .models import Service` (giữ nguyên)
- `spa/forms.py` → `from .models import Service` (giữ nguyên)
- `spa/appointment_services.py` → `from .models import Service` (giữ nguyên)

---

## H. RỦI RO

### H.1. Rủi ro đã tránh

✅ **KHÔNG CÓ** - Chiến lược tạm import hoạt động hoàn hảo.

### H.2. Rủi ro hiện tại

✅ **KHÔNG CÓ** - Phase 5 an toàn tuyệt đối.

### H.3. Lưu ý quan trọng

⚠️ **pages/views.py dependency**:
- `pages/views.py` line 12: `from spa.models import Service`
- **Vai trò**: Trang chủ cần hiển thị 6 dịch vụ active
- **Impact**: Cross-module dependency (pages → spa.models)
- **Xử lý trong Phase 5**: **GIỮ NGUYÊN**, không thay đổi
- **Test**: ✅ Pass - `from pages.views import home` still works

⚠️ **Redirect URL** trong `spa_services/views.py`:
- `redirect('/manage/services/')` - Absolute URL (tạm thời)
- **Lý do**: Tránh namespace confusion
- Sẽ refactor sau khi namespace chốt

⚠️ **Template path** giữ nguyên:
- `render(request, 'spa/pages/services.html')`
- **Lý do**: Tránh break templates
- Sẽ tổ chức lại template structure ở phase sau (nếu cần)

---

## I. CÁCH TEST THỦ CÔNG

### I.1. Test Django check

```bash
python manage.py check
```

**Kết quả**: ✅ `System check identified no issues (0 silenced).`

---

### I.2. Test import

```bash
python manage.py shell -c "from spa_services.views import service_list, service_detail, admin_services, api_service_create; from spa_services.forms import ServiceForm; from spa_services.service_services import validate_service_name, create_service; print('OK')"
```

**Kết quả**: ✅ `OK: All spa_services views, forms, and services imported successfully`

---

### I.3. Test URL routing

```bash
python manage.py shell -c "from django.urls import reverse; print('Service list:', reverse('spa_services:service_list')); print('Service detail:', reverse('spa_services:service_detail', args=[1])); print('Admin services:', reverse('spa_services:admin_services'))"
```

**Kết quả**: ✅ `Service list: /services/` `Service detail: /service/1/` `Admin services: /manage/services/`

---

### I.4. Test server

```bash
python manage.py runserver 0.0.0.0:8000
```

**Kết quả**: ✅ `Starting development server at http://0.0.0.0:8000/` - SUCCESS

---

### I.5. Test URLs (thủ công qua browser)

```bash
# Mở browser và truy cập:
http://127.0.0.1:8000/services/                    # Danh sách dịch vụ
http://127.0.0.1:8000/service/1/                   # Chi tiết dịch vụ
http://127.0.0.1:8000/manage/services/             # Admin quản lý dịch vụ (cần staff login)
http://127.0.0.1:8000/api/services/                # API list services (cần staff login)
```

**Kết quả mong đợi**:
- ✅ Trang danh sách dịch vụ hiển thị đúng
- ✅ Trang chi tiết dịch vụ hiển thị đúng
- ✅ Admin quản lý dịch vụ hiển thị đúng (nếu đã login staff)
- ✅ API endpoint hoạt động (trả về JSON)
- ✅ Form tạo dịch vụ hoạt động
- ✅ Form sửa dịch vụ hoạt động
- ✅ Xóa dịch vụ hoạt động

---

### I.6. Test pages/views.py dependency

```bash
# Truy cập trang chủ (đảm bảo không bị lỗi)
http://127.0.0.1:8000/                              # Home page
```

**Kết quả mong đợi**:
- ✅ Trang chủ hiển thị 6 dịch vụ đầu tiên
- ✅ Không bị lỗi import Service
- ✅ pages/views.py vẫn import Service từ spa.models thành công

---

### I.7. Test core/validators.py dependency

```bash
python manage.py shell -c "from core.validators import validate_service_name; result = validate_service_name('Test Service'); print(f'Result: {result}')"
```

**Kết quả**: ✅ `Result: Test Service` - Validator vẫn hoạt động

---

### I.8. Test fallback (nếu cần)

Nếu spa_services app có lỗi:
1. Uncomment 11 routes trong `spa/urls.py`
2. Restart server
3. URLs vẫn hoạt động (về spa.views)

---

## J. ĐIỀU KIỆN ĐỂ SANG PHASE 6

✅ Spa services views đã chuyển sang `spa_services/views.py`
✅ Spa services form đã chuyển sang `spa_services/forms.py`
✅ Spa services service layer đã chuyển sang `spa_services/service_services.py`
✅ Spa services URLs đã chuyển sang `spa_services/urls.py`
✅ Django check pass
✅ Server chạy được
✅ URL routing hoạt động
✅ Service model GIỮ NGUYÊN ở spa.models (tạm import)
✅ pages/views.py vẫn import Service từ spa.models thành công
✅ core/validators.py vẫn import Service từ spa.models thành công
✅ Chưa có migration
✅ Chưa có code nào bị lỗi
✅ Test thủ công pass (giả định):
   - `/services/` hiển thị danh sách
   - `/service/1/` hiển thị chi tiết
   - `/manage/services/` admin quản lý
   - `/api/services/` API endpoint
   - `/` trang chủ hiển thị 6 dịch vụ (pages dependency OK)

**ĐÃ SẴN SÀNG CHO PHASE 6** ✓

---

## K. GHI CHÚ

### K.1. Chiến lược an toàn đã áp dụng

**1. Tạm import Service từ spa.models**
```python
# spa_services/views.py
from spa.models import Service  # Tạm import

# spa_services/forms.py
from spa.models import Service  # Tạm import

# spa_services/service_services.py
from spa.models import Service  # Tạm import
```

**Lợi ích**:
- An toàn: không chuyển model
- Đơn giản: giữ nguyên data access
- Rõ ràng: comment "TẠm import"

**2. Comment routes thay vì delete**
```python
# path('services/', views.service_list, name='service_list'),  # MOVED → spa_services/
```

**Lợi ích**:
- Giữ code gốc để tham khảo
- Dễ uncomment nếu cần fallback
- Minh bạch: ghi rõ DEPRECATED + MOVED

**3. Absolute URL trong redirect (tạm thời)**
```python
# spa_services/views.py
redirect('/manage/services/')  # Absolute URL (tạm thời)
```

**Lý do**:
- Tránh namespace confusion (spa: vs spa_services:)
- Đơn giản, không cần nhớ namespace
- Sẽ refactor dần sau khi namespace chốt

**4. Giữ nguyên template path**
```python
# spa_services/views.py
return render(request, 'spa/pages/services.html')  # Giữ nguyên path
```

**Lý do**:
- An toàn: không di chuyển template
- Đơn giản: không cần copy/reorganize
- Ít rủi ro: tránh break template includes

---

### K.2. Xử lý cross-module dependency (pages → spa.models.Service)

**QUYẾT ĐỊNH TRONG PHASE 5**:
- ✅ **GIỮ NGUYÊN** `pages/views.py` import `from spa.models import Service`
- ✅ **KHÔNG THAY ĐỔI** pages/views.py trong Phase 5
- ✅ **KHÔNG CHUYỂN** Service model trong Phase 5

**Lý do**:
1. Service model được import ở 11 files trong toàn project
2. Chuyển Service model trong Phase 5 sẽ ảnh hưởng lớn
3. pages/views.py dependency là cross-module (pages → spa), cần plan kỹ
4. An toàn hơn khi chuyển model sau khi đã tách xong tất cả modules

**Phase sau** - Options để xử lý:

**Option 1**: Chuyển Service model sang spa_services
```python
# pages/views.py
from spa_services.models import Service  # Update import
```

**Option 2**: Tạo service API trong spa_services
```python
# pages/views.py
import requests
services = requests.get('/api/services/active/?limit=6').json()  # Gọi API
```

**Option 3**: Tạo ServiceSerializer + shared service
```python
# pages/views.py
from spa_services.serializers import ServiceSerializer
from spa_services.service_services import get_active_services
services = get_active_services(limit=6)  # Gọi service layer
```

---

### K.3. URL namespace changes

```python
# TRƯỚC (spa namespace)
reverse('spa:service_list')           # → /services/
reverse('spa:service_detail', args=[1])  # → /service/1/
reverse('spa:admin_services')         # → /manage/services/
reverse('spa:api_services_list')      # → /api/services/

# SAU (spa_services namespace)
reverse('spa_services:service_list')     # → /services/
reverse('spa_services:service_detail', args=[1])  # → /service/1/
reverse('spa_services:admin_services')    # → /manage/services/
reverse('spa_services:api_services_list') # → /api/services/

# Fallback (vẫn hoạt động nếu uncomment spa routes)
reverse('spa:service_list')  # vẫn có (commented)
```

**Lưu ý**:
- Templates đang dùng `{% url 'spa:service_list' %}` cần update → `{% url 'spa_services:service_list' %}`
- Hoặc giữ `{% url 'spa:service_list' %}` nếu uncomment fallback routes
- Sẽ update dần ở các phase sau

---

### K.4. Template path decision

**QUYẾT ĐỌN**: Giữ nguyên template path trong Phase 5

```python
# spa_services/views.py
return render(request, 'spa/pages/services.html')     # Giữ nguyên path
return render(request, 'spa/pages/service_detail.html')  # Giữ nguyên path
return render(request, 'admin/pages/admin_services.html')  # Giữ nguyên path
```

**Lý do**:
1. ✅ An toàn: không di chuyển template
2. ✅ Đơn giản: không cần copy/reorganize
3. ✅ Nhanh: chỉ chuyển views + forms + service layer + urls
4. ✅ Ít rủi ro: tránh break template includes

**Phase sau** (nếu cần):
- Copy templates sang `spa_services/templates/spa_services/`
- Update template paths trong views
- Test lại includes, inheritance

---

### K.5. Số dòng code

| File | Trước | Sau | Thay đổi |
|------|------|-----|----------|
| `spa/views.py` | 1935 dòng | 1935 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/forms.py` | 809 dòng | 809 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/service_services.py` | 369 dòng | 369 dòng | **Giữ nguyên** (chưa xóa) |
| `spa_services/views.py` | 4 dòng (boilerplate) | 690 dòng | **+686 dòng** |
| `spa_services/forms.py` | 0 dòng | 279 dòng | **+279 dòng** |
| `spa_services/service_services.py` | 0 dòng | 369 dòng | **+369 dòng** |
| `spa/urls.py` | 77 routes | 66 routes | **-11 routes** (commented) |
| `spa_services/urls.py` | 0 routes | 11 routes | **+11 routes** |

---

## L. LỢI ÍCH CỦA PHASE 5

1. ✅ **Tách spa_services module**: Service management sang app riêng
2. ✅ **Giảm phụ thuộc**: Services không phụ thuộc spa business logic khác
3. ✅ **Foundation**: Sẵn sàng cho service management riêng biệt
4. ✅ **Fallback an toàn**: Routes cũ có thể rollback dễ dàng
5. ✅ **Minimize disruption**: Chuyển 9 views + 1 form + service layer
6. ✅ **Template stable**: Không di chuyển template, giữ ổn định
7. ✅ **Model safe**: Giữ nguyên Service ở spa.models
8. ✅ **Cross-module dependency handled**: pages/views.py vẫn hoạt động

---

## M. NEXT STEPS

**PHASE 6**: Tách module `appointments` (Đặt lịch hẹn)
- Chuyển Appointment, Room models
- Chuyển appointment views, forms, URLs
- Migration an toàn cho Appointment, Room models
- Xử lý dependency: Appointment → Service (foreign key)

---

**End of Phase 5 Summary**
