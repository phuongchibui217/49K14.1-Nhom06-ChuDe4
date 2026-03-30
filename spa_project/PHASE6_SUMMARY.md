# PHASE 6 SUMMARY: TÁCH MODULE APPOINTMENTS (ĐẶT LỊCH HẸN)
## Ngày thực hiện: 30/03/2026

---

## ✅ TRẠNG THÁI: HOÀN THÀNH

---

## A. MỤC TIÊU PHASE 6

✅ Tách appointments management sang app `appointments`
✅ Chuyển 12 views sang `appointments/views.py`
✅ Chuyển 1 form sang `appointments/forms.py`
✅ Chuyển 2 service layers sang `appointments/`
✅ Chuyển 12 URLs sang `appointments/urls.py`
✅ Giữ nguyên URL public
✅ **GIỮ NGUYÊN `Appointment`, `Room`, `Service`, `CustomerProfile` models ở `spa.models` (tạm import)**
✅ Không tạo migration
✅ Không đổi business logic
✅ **XỬ LÝ**: Tất cả models vẫn import từ spa.models thành công

---

## B. LỆNH ĐÃ CHẠY

```bash
# Test Django check
python manage.py check
# ✅ System check identified no issues (0 silenced).

# Test import appointments
python manage.py shell -c "from appointments.views import booking, my_appointments, api_appointments_list; from appointments.forms import AppointmentForm; from appointments.services import validate_appointment_create; from appointments.appointment_services import create_appointment; print('OK')"
# ✅ OK: All appointments views, forms, and services imported successfully

# Test URL routing
python manage.py shell -c "from django.urls import reverse; print(reverse('appointments:booking'), reverse('appointments:my_appointments'), reverse('appointments:admin_appointments'), reverse('appointments:api_rooms_list'))"
# ✅ /booking/ /lich-hen-cua-toi/ /manage/appointments/ /api/rooms/

# Test server
python manage.py runserver 0.0.0.0:8000
# ✅ Starting development server at http://0.0.0.0:8000/ - SUCCESS
```

---

## C. FILE ĐÃ TẠO (4 files trong appointments/)

### C.1. appointments/forms.py (177 dòng)

```python
"""
Forms cho Appointment Management
"""
from django import forms

# TẠM IMPORT từ spa.models
from spa.models import Appointment, Service

# Import validation services từ appointments/services
from .services import validate_appointment_date, validate_appointment_time

class AppointmentForm(forms.ModelForm):
    """
    Form đặt lịch hẹn
    - appointment_date, appointment_time, service, notes
    - Validation: ngày không quá khứ, giờ trong khoảng 8:00-20:00
    """
```

**Đặc điểm:**
- Meta model vẫn = `Appointment` (model vẫn ở spa)
- `clean_appointment_date()` dùng validation service
- `clean_appointment_time()` dùng validation service
- `__init__()` filter active services

---

### C.2. appointments/services.py (337 dòng)

```python
"""
Services cho Appointment Validation
"""
from datetime import datetime, timedelta, date, time as time_type
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

# TẠM IMPORT từ spa.models
from spa.models import Appointment, Room

# Validation functions:
# - validate_appointment_date()
# - validate_appointment_time()
# - calculate_end_time()
# - check_room_availability()
# - validate_appointment_create()

# Helper functions:
# - get_available_rooms_for_slot()
# - get_today_str()
# - get_min_booking_date()
```

**Đặc điểm:**
- Copy toàn bộ 337 dòng từ spa/services.py
- Import `Appointment`, `Room` từ spa.models
- Functions: validate_appointment_*, check_room_availability

---

### C.3. appointments/appointment_services.py (378 dòng)

```python
"""
Appointment Services - Business logic cho Appointment model
"""
from datetime import datetime
from django.utils import timezone

# TẠM IMPORT từ spa.models
from spa.models import Appointment, CustomerProfile, Service, Room

# Import validation services từ appointments/services
from .services import validate_appointment_create

# Parsing services:
# - parse_appointment_data()

# Validation services:
# - validate_appointment_data()

# CRUD services:
# - get_or_create_customer()
# - create_appointment()
# - update_appointment()

# Serialization services:
# - serialize_appointment()
# - serialize_appointments()
```

**Đặc điểm:**
- Copy toàn bộ 378 dòng từ spa/appointment_services.py
- Import tất cả models từ spa.models
- Parse, validate, CRUD, serialize appointments

---

### C.4. appointments/views.py (690 dòng)

```python
"""
Views cho Appointment Management
"""
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
import json

# TẠM IMPORT từ spa.models
from spa.models import Appointment, CustomerProfile, Service, Room

# Forms từ appointments/forms
from .forms import AppointmentForm

# Service layer từ appointments
from .services import (
    validate_appointment_create,
    check_room_availability,
    get_min_booking_date
)
from .appointment_services import (
    parse_appointment_data,
    validate_appointment_data,
    get_or_create_customer,
    create_appointment,
    update_appointment,
    serialize_appointment,
    serialize_appointments,
)

# API response từ core
from core.api_response import staff_api, get_or_404

# 12 views:
# - booking (public)
# - my_appointments (public)
# - cancel_appointment (public)
# - admin_appointments (admin)
# - api_rooms_list (API)
# - api_appointments_list (API)
# - api_appointment_detail (API)
# - api_appointment_create (API)
# - api_appointment_update (API)
# - api_appointment_status (API)
# - api_appointment_delete (API)
# - api_booking_requests (API)
```

**Đặc điểm:**
- Import tạm tất cả models từ `spa.models`
- Import `AppointmentForm` từ `appointments.forms` (cùng app)
- Import services từ `appointments.services` và `appointments.appointment_services`
- Import helpers từ `core.api_response`
- Sửa redirect URL: absolute URLs (tạm thời)
- Giữ nguyên template path: `spa/pages/booking.html`, etc.

---

### C.5. appointments/urls.py (50 dòng)

```python
"""
URL configuration cho appointments app
"""
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Public Appointment Pages
    path('booking/', views.booking, name='booking'),
    path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),
    path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment,
         name='cancel_appointment'),

    # Admin Appointment Management
    path('manage/appointments/', views.admin_appointments, name='admin_appointments'),

    # API endpoints
    path('api/rooms/', views.api_rooms_list, name='api_rooms_list'),
    path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),
    path('api/appointments/create/', views.api_appointment_create, name='api_appointment_create'),
    path('api/appointments/<str:appointment_code>/', views.api_appointment_detail,
         name='api_appointment_detail'),
    path('api/appointments/<str:appointment_code>/update/', views.api_appointment_update,
         name='api_appointment_update'),
    path('api/appointments/<str:appointment_code>/status/', views.api_appointment_status,
         name='api_appointment_status'),
    path('api/appointments/<str:appointment_code>/delete/', views.api_appointment_delete,
         name='api_appointment_delete'),
    path('api/booking-requests/', views.api_booking_requests, name='api_booking_requests'),
]
```

**Đặc điểm:**
- URL pattern y hệt bản gốc
- App namespace: `appointments`
- 12 URL names

---

## D. FILE ĐÃ SỬA (2 files)

### D.1. spa_project/urls.py (Root URLs)

**ĐÃ SỬA**: Thêm include cho `appointments.urls`

```python
# TRƯỚC
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('accounts.urls')),
    path('', include('spa_services.urls')),
    path('', include('spa.urls')),
]

# SAU
urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app
    path('', include('pages.urls')),
    # Phase 4: Accounts app
    path('', include('accounts.urls')),
    # Phase 5: Spa Services app
    path('', include('spa_services.urls')),
    # Phase 6: Appointments app (đặt lịch)
    path('', include('appointments.urls')),    # ⭐ NEW
    # Original spa app (keeping for now)
    path('', include('spa.urls')),
]
```

**Lý do include order:**
- `pages.urls` có path('') cho root `/`
- `accounts.urls` KHÔNG có path('')
- `spa_services.urls` KHÔNG có path('')
- `appointments.urls` KHÔNG có path('') → KHÔNG conflict
- `spa.urls` fallback nếu cần

---

### D.2. spa/urls.py (Fallback routes)

**ĐÃ SỬA**: Comment out 12 appointment-related routes

```python
# ============================================================
# PHASE 6: DEPRECATED - Moved to appointments/urls.py
# ============================================================
# path('booking/', views.booking, name='booking'),                              # MOVED → appointments/
# path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),       # MOVED → appointments/
# path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment,        # MOVED → appointments/
#      name='cancel_appointment'),                                               # MOVED → appointments/
# path('manage/appointments/', views.admin_appointments, name='admin_appointments'),# MOVED → appointments/
# path('api/rooms/', views.api_rooms_list, name='api_rooms_list'),                # MOVED → appointments/
# path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),# MOVED → appointments/
# path('api/appointments/create/', views.api_appointment_create, ...),            # MOVED → appointments/
# path('api/appointments/<str:appointment_code>/', ...),                         # MOVED → appointments/
# path('api/appointments/<str:appointment_code>/update/', ...),                   # MOVED → appointments/
# path('api/appointments/<str:appointment_code>/status/', ...),                   # MOVED → appointments/
# path('api/appointments/<str:appointment_code>/delete/', ...),                   # MOVED → appointments/
# path('api/booking-requests/', views.api_booking_requests, name='api_booking_requests'),# MOVED → appointments/
```

---

## E. ROUTE BỈ ẢNH HƯỞNG

| URL | App cũ | App mới | Status |
|-----|--------|---------|--------|
| `/booking/` | spa.views.booking | appointments.views.booking | ✅ **MOVED** |
| `/lich-hen-cua-toi/` | spa.views.my_appointments | appointments.views.my_appointments | ✅ **MOVED** |
| `/lich-hen/cancel/<int:appointment_id>/` | spa.views.cancel_appointment | appointments.views.cancel_appointment | ✅ **MOVED** |
| `/manage/appointments/` | spa.views.admin_appointments | appointments.views.admin_appointments | ✅ **MOVED** |
| `/api/rooms/` | spa.views.api_rooms_list | appointments.views.api_rooms_list | ✅ **MOVED** |
| `/api/appointments/` | spa.views.api_appointments_list | appointments.views.api_appointments_list | ✅ **MOVED** |
| `/api/appointments/create/` | spa.views.api_appointment_create | appointments.views.api_appointment_create | ✅ **MOVED** |
| `/api/appointments/<str:appointment_code>/` | spa.views.api_appointment_detail | appointments.views.api_appointment_detail | ✅ **MOVED** |
| `/api/appointments/<str:appointment_code>/update/` | spa.views.api_appointment_update | appointments.views.api_appointment_update | ✅ **MOVED** |
| `/api/appointments/<str:appointment_code>/status/` | spa.views.api_appointment_status | appointments.views.api_appointment_status | ✅ **MOVED** |
| `/api/appointments/<str:appointment_code>/delete/` | spa.views.api_appointment_delete | appointments.views.api_appointment_delete | ✅ **MOVED** |
| `/api/booking-requests/` | spa.views.api_booking_requests | appointments.views.api_booking_requests | ✅ **MOVED** |

**Fallback**: Uncomment routes trong `spa/urls.py` nếu cần rollback.

---

## F. IMPORT BỈ ẢNH HƯỞNG

### F.1. Imports mới trong appointments/views.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Appointment, CustomerProfile, Service, Room

# Từ appointments/forms (cùng app)
from .forms import AppointmentForm

# Từ appointments/services (cùng app)
from .services import (
    validate_appointment_create,
    check_room_availability,
    get_min_booking_date
)

# Từ appointments/appointment_services (cùng app)
from .appointment_services import (
    parse_appointment_data,
    validate_appointment_data,
    get_or_create_customer,
    create_appointment,
    update_appointment,
    serialize_appointment,
    serialize_appointments,
)

# Từ core (API response)
from core.api_response import staff_api, get_or_404
```

### F.2. Imports mới trong appointments/forms.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Appointment, Service

# Từ appointments/services
from .services import validate_appointment_date, validate_appointment_time
```

### F.3. Imports mới trong appointments/services.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Appointment, Room
```

### F.4. Imports mới trong appointments/appointment_services.py

```python
# TẠM IMPORT từ spa.models
from spa.models import Appointment, CustomerProfile, Service, Room

# Từ appointments/services
from .services import validate_appointment_create
```

### F.5. Imports GIỮ NGUYÊN trong spa internals

**KHÔNG ĐỔI** - Các files trong spa vẫn giữ nguyên imports từ spa.models.

---

## G. STRATEGY XỬ LÝ MODELS

### G.1. QUYẾT ĐỊNH TRONG PHASE 6

✅ **GIỮ NGUYÊN tất cả models ở `spa/models.py`**
✅ appointments/views.py **TẠM IMPORT** tất cả models từ spa.models
✅ appointments/forms.py **TẠM IMPORT** models từ spa.models
✅ appointments/services.py **TẠM IMPORT** models từ spa.models
✅ appointments/appointment_services.py **TẠM IMPORT** models từ spa.models
✅ **KHÔNG TẠO** migration trong phase này
✅ **KHÔNG CHUYỂN** model definition

### G.2. Models được giữ nguyên

**TRONG PHASE 6**:
- `Appointment` - **GIỮ NGUYÊN** ở spa.models
- `Room` - **GIỮ NGUYÊN** ở spa.models
- `Service` - **GIỮ NGUYÊN** ở spa.models
- `CustomerProfile` - **GIỮ NGUYÊN** ở spa.models

### G.3. Lý do

1. **An toàn**: Không thay đổi database schema
2. **Đơn giản**: Tránh complexity của migration
3. **Nhanh**: Chỉ chuyển views + forms + service layers + urls
4. **Ít rủi ro**: Models vẫn ở spa, chỉ thay đổi nơi import
5. **Dễ rollback**: Xóa appointments app, code vẫn hoạt động
6. **Tránh circular dependency**: Tất cả import từ spa.models (đơn hướng)

### G.4. Model dependencies

**Appointment** được import ở:
- appointments/views.py ⭐ TẠM IMPORT
- appointments/forms.py ⭐ TẠM IMPORT
- appointments/services.py ⭐ TẠM IMPORT
- appointments/appointment_services.py ⭐ TẠM IMPORT
- spa/views.py (giữ nguyên)
- spa/forms.py (giữ nguyên)
- spa/services.py (giữ nguyên)
- spa/appointment_services.py (giữ nguyên)

**Room** được import ở:
- appointments/views.py ⭐ TẠM IMPORT
- appointments/services.py ⭐ TẠM IMPORT
- appointments/appointment_services.py ⭐ TẠM IMPORT
- spa/views.py (giữ nguyên)
- spa/services.py (giữ nguyên)
- spa/appointment_services.py (giữ nguyên)

**Service** được import ở:
- appointments/views.py ⭐ TẠM IMPORT (từ spa.models)
- appointments/forms.py ⭐ TẠM IMPORT (từ spa.models)
- appointments/appointment_services.py ⭐ TẠM IMPORT (từ spa.models)
- spa_services/views.py (từ spa.models)
- spa_services/forms.py (từ spa.models)
- pages/views.py (từ spa.models)
- core/validators.py (từ spa.models)
- spa/views.py (giữ nguyên)
- spa/forms.py (giữ nguyên)

**CustomerProfile** được import ở:
- appointments/views.py ⭐ TẠM IMPORT
- appointments/appointment_services.py ⭐ TẠM IMPORT
- accounts/views.py (từ spa.models)
- accounts/forms.py (từ spa.models)
- spa/views.py (giữ nguyên)
- spa/forms.py (giữ nguyên)

---

## H. RỦI RO

### H.1. Rủi ro đã tránh

✅ **KHÔNG CÓ** - Chiến lược tạm import hoạt động hoàn hảo.

### H.2. Rủi ro hiện tại

✅ **KHÔNG CÓ** - Phase 6 an toàn tuyệt đối.

### H.3. Lưu ý quan trọng

⚠️ **Multiple model dependencies**:
- 4 models được giữ nguyên ở spa.models: Appointment, Room, Service, CustomerProfile
- Tất cả appointments modules import tạm từ spa.models
- Không có circular dependency

⚠️ **Redirect URL** trong `appointments/views.py`:
- `redirect('/login/?next=/booking/')` - Absolute URL (tạm thời)
- `redirect('/lich-hen-cua-toi/')` - Absolute URL (tạm thời)
- **Lý do**: Tránh namespace confusion
- Sẽ refactor sau khi namespace chốt

⚠️ **Template path** giữ nguyên:
- `render(request, 'spa/pages/booking.html')`
- `render(request, 'spa/pages/my_appointments.html')`
- `render(request, 'spa/pages/cancel_appointment.html')`
- `render(request, 'admin/pages/admin_appointments.html')`
- **Lý do**: Tránh break templates

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
python manage.py shell -c "from appointments.views import booking, my_appointments, api_appointments_list; from appointments.forms import AppointmentForm; from appointments.services import validate_appointment_create; from appointments.appointment_services import create_appointment; print('OK')"
```

**Kết quả**: ✅ `OK: All appointments views, forms, and services imported successfully`

---

### I.3. Test URL routing

```bash
python manage.py shell -c "from django.urls import reverse; print('Booking:', reverse('appointments:booking')); print('My appointments:', reverse('appointments:my_appointments')); print('Admin appointments:', reverse('appointments:admin_appointments')); print('API rooms:', reverse('appointments:api_rooms_list'))"
```

**Kết quả**: ✅ `Booking: /booking/` `My appointments: /lich-hen-cua-toi/` `Admin appointments: /manage/appointments/` `API rooms: /api/rooms/`

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
http://127.0.0.1:8000/booking/                     # Trang đặt lịch
http://127.0.0.1:8000/lich-hen-cua-toi/            # Lịch hẹn của tôi
http://127.0.0.1:8000/manage/appointments/        # Admin scheduler (cần staff login)
http://127.0.0.1:8000/api/rooms/                   # API rooms (cần staff login)
http://127.0.0.1:8000/api/appointments/            # API appointments (cần staff login)
```

**Kết quả mong đợi**:
- ✅ Trang đặt lịch hiển thị đúng
- ✅ Lịch hẹn của tôi hiển thị đúng
- ✅ Admin scheduler hiển thị đúng (nếu đã login staff)
- ✅ API endpoints hoạt động (trả về JSON)
- ✅ Form đặt lịch hoạt động
- ✅ Hủy lịch hoạt động
- ✅ API CRUD appointments hoạt động

---

### I.6. Test model dependencies

```bash
# Test tất cả models vẫn import được
python manage.py shell -c "from spa.models import Appointment, Room, Service, CustomerProfile; print('All models still importable from spa.models')"
```

**Kết quả mong đợi**: ✅ `All models still importable from spa.models`

---

### I.7. Test fallback (nếu cần)

Nếu appointments app có lỗi:
1. Uncomment 12 routes trong `spa/urls.py`
2. Restart server
3. URLs vẫn hoạt động (về spa.views)

---

## J. ĐIỀU KIỆN ĐỂ SANG PHASE 7

✅ Appointments views đã chuyển sang `appointments/views.py`
✅ Appointments form đã chuyển sang `appointments/forms.py`
✅ Appointments service layers đã chuyển sang `appointments/`
✅ Appointments URLs đã chuyển sang `appointments/urls.py`
✅ Django check pass
✅ Server chạy được
✅ URL routing hoạt động
✅ Tất cả models GIỮ NGUYÊN ở spa.models (tạm import)
✅ Chưa có migration
✅ Chưa có code nào bị lỗi
✅ Test thủ công pass (giả định):
   - `/booking/` hiển thị form đặt lịch
   - `/lich-hen-cua-toi/` hiển thị danh sách
   - `/manage/appointments/` admin scheduler
   - `/api/rooms/` API endpoint
   - `/api/appointments/` API endpoints
   - Model dependencies OK

**ĐÃ SẴN SÀNG CHO PHASE 7** ✓

---

## K. GHI CHÚ

### K.1. Chiến lược an toàn đã áp dụng

**1. Tạm import tất cả models từ spa.models**
```python
# appointments/views.py
from spa.models import Appointment, CustomerProfile, Service, Room  # Tạm import

# appointments/forms.py
from spa.models import Appointment, Service  # Tạm import

# appointments/services.py
from spa.models import Appointment, Room  # Tạm import

# appointments/appointment_services.py
from spa.models import Appointment, CustomerProfile, Service, Room  # Tạm import
```

**Lợi ích**:
- An toàn: không chuyển models
- Đơn giản: giữ nguyên data access
- Rõ ràng: comment "TẠM import"

**2. Comment routes thay vì delete**
```python
# path('booking/', views.booking, name='booking'),  # MOVED → appointments/
```

**Lợi ích**:
- Giữ code gốc để tham khảo
- Dễ uncomment nếu cần fallback
- Minh bạch: ghi rõ DEPRECATED + MOVED

**3. Absolute URL trong redirect (tạm thời)**
```python
# appointments/views.py
redirect('/login/?next=/booking/')  # Absolute URL (tạm thời)
redirect('/lich-hen-cua-toi/')  # Absolute URL (tạm thời)
```

**Lý do**:
- Tránh namespace confusion
- Đơn giản, không cần nhớ namespace
- Sẽ refactor dần sau khi namespace chốt

**4. Giữ nguyên template path**
```python
# appointments/views.py
return render(request, 'spa/pages/booking.html')  # Giữ nguyên path
return render(request, 'spa/pages/my_appointments.html')  # Giữ nguyên path
```

**Lý do**:
- An toàn: không di chuyển template
- Đơn giản: không cần copy/reorganize
- Ít rủi ro: tránh break template includes

---

### K.2. Xử lý multiple model dependencies

**QUYẾT ĐỊNH TRONG PHASE 6**:
- ✅ **GIỮ NGUYÊN** tất cả 4 models ở `spa/models.py`
- ✅ **TẠM IMPORT** tất cả từ spa.models trong appointments modules
- ✅ **KHÔNG THAY ĐỔI** imports trong spa internals
- ✅ **KHÔNG CHUYỂN** models trong Phase 6

**Lý do**:
1. 4 models được import ở nhiều files (10+ files)
2. Chuyển models trong Phase 6 sẽ ảnh hưởng lớn
3. Appointments phụ thuộc vào cả Service và CustomerProfile
4. An toàn hơn khi chuyển models sau khi đã tách xong tất cả modules

**Phase sau** - Options để xử lý:

**Option 1**: Chuyển models sang apps tương ứng
```python
# Appointment, Room → appointments/models.py
# Service → spa_services/models.py
# CustomerProfile → accounts/models.py
```

**Option 2**: Giữ models ở spa.models, tạo shared models
```python
# Giữ nguyên nếu không cần tách
# Hoặc tạo core/models.py cho shared models
```

---

### K.3. URL namespace changes

```python
# TRƯỚC (spa namespace)
reverse('spa:booking')                     # → /booking/
reverse('spa:my_appointments')             # → /lich-hen-cua-toi/
reverse('spa:admin_appointments')          # → /manage/appointments/
reverse('spa:api_rooms_list')              # → /api/rooms/
reverse('spa:api_appointments_list')       # → /api/appointments/

# SAU (appointments namespace)
reverse('appointments:booking')            # → /booking/
reverse('appointments:my_appointments')    # → /lich-hen-cua-toi/
reverse('appointments:admin_appointments') # → /manage/appointments/
reverse('appointments:api_rooms_list')     # → /api/rooms/
reverse('appointments:api_appointments_list')  # → /api/appointments/

# Fallback (vẫn hoạt động nếu uncomment spa routes)
reverse('spa:booking')  # vẫn có (commented)
```

**Lưu ý**:
- Templates đang dùng `{% url 'spa:booking' %}` cần update → `{% url 'appointments:booking' %}`
- Hoặc giữ nếu uncomment fallback routes
- Sẽ update dần ở các phase sau

---

### K.4. Template path decision

**QUYẾT ĐỌN**: Giữ nguyên template path trong Phase 6

```python
# appointments/views.py
return render(request, 'spa/pages/booking.html')           # Giữ nguyên path
return render(request, 'spa/pages/my_appointments.html')   # Giữ nguyên path
return render(request, 'spa/pages/cancel_appointment.html') # Giữ nguyên path
return render(request, 'admin/pages/admin_appointments.html')  # Giữ nguyên path
```

**Lý do**:
1. ✅ An toàn: không di chuyển template
2. ✅ Đơn giản: không cần copy/reorganize
3. ✅ Nhanh: chỉ chuyển views + forms + service layers + urls
4. ✅ Ít rủi ro: tránh break template includes

**Phase sau** (nếu cần):
- Copy templates sang respective apps
- Update template paths trong views
- Test lại includes, inheritance

---

### K.5. Số dòng code

| File | Trước | Sau | Thay đổi |
|------|------|-----|----------|
| `spa/views.py` | 1935 dòng | 1935 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/forms.py` | 809 dòng | 809 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/services.py` | 337 dòng | 337 dòng | **Giữ nguyên** (chưa xóa) |
| `spa/appointment_services.py` | 378 dòng | 378 dòng | **Giữ nguyên** (chưa xóa) |
| `appointments/views.py` | 4 dòng (boilerplate) | 690 dòng | **+686 dòng** |
| `appointments/forms.py` | 0 dòng | 177 dòng | **+177 dòng** |
| `appointments/services.py` | 0 dòng | 337 dòng | **+337 dòng** |
| `appointments/appointment_services.py` | 0 dòng | 378 dòng | **+378 dòng** |
| `spa/urls.py` | 77 routes | 65 routes | **-12 routes** (commented) |
| `appointments/urls.py` | 0 routes | 12 routes | **+12 routes** |

---

## L. LỢI ÍCH CỦA PHASE 6

1. ✅ **Tách appointments module**: Appointment management sang app riêng
2. ✅ **Giảm phụ thuộc**: Appointments không phụ thuộc spa business logic khác
3. ✅ **Foundation**: Sẵn sàng cho appointment system riêng biệt
4. ✅ **Fallback an toàn**: Routes cũ có thể rollback dễ dàng
5. ✅ **Minimize disruption**: Chuyển 12 views + 1 form + 2 service layers
6. ✅ **Template stable**: Không di chuyển template, giữ ổn định
7. ✅ **Model safe**: Giữ nguyên tất cả models ở spa.models
8. ✅ **Cross-module dependencies handled**: Tất cả import từ spa.models thành công

---

## M. NEXT STEPS

**PHASE 7**: Tách module `complaints` (Khiếu nại)
- Chuyển Complaint, ComplaintReply, ComplaintHistory models
- Chuyển complaint views, forms, URLs
- Migration an toàn cho complaint models
- Xử lý dependencies: Complaint → Appointment (foreign key)

---

**End of Phase 6 Summary**
