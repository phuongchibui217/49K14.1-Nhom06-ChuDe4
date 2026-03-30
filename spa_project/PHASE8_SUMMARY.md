# PHASE 8: CONSOLIDATION & CLEANUP PLAN

**Date**: 2026-03-30
**Status**: 📋 PLANNING
**Type**: Audit & Strategy (NO CODE CHANGES)

---

## A. TỔNG QUAN TRẠNG THÁI SAU 7 PHASE

### ✅ ĐÃ HOÀN THÀNH (7 Apps)

| App | Trạng thái | Models | Views | Forms | URLs | Templates |
|-----|-----------|--------|-------|-------|------|-----------|
| **core** | ✅ Hoàn thành | 0 | 0 | 0 | 0 | 0 |
| **pages** | ✅ Hoàn thành | 0 | 2 | 0 | 2 | ❌ Vẫn spa/ |
| **accounts** | ✅ Hoàn thành | 0 | 6 | 3 | 7 | ❌ Vẫn spa/ |
| **spa_services** | ✅ Hoàn thành | 0 | 8 | 3 | 11 | ❌ Vẫn spa/ + admin/ |
| **appointments** | ✅ Hoàn thành | 0 | 12 | 2 | 14 | ❌ Vẫn spa/ + admin/ |
| **complaints** | ✅ Hoàn thành | 0 | 10 | 5 | 10 | ❌ Vẫn spa/ + admin/ |
| **spa** | ⚠️ Còn lại | **7 models** | **14 views** | **5 forms** | **9 URLs** | Tất cả |

### 📊 KẾT QUẢ TÁCH APP

- **Views đã tách**: 38/52 (73%)
- **Forms đã tách**: 13/18 (72%)
- **URLs đã tách**: 44/62 (71%)
- **Models đã tách**: 0/7 (0%) ← **GIỮ NGUYÊN theo yêu cầu**
- **Templates đã tách**: 0/23 (0%) ← **VỪNG ĐANG TẠM**

### 🎯 TRẠNG THÁI KIẾN TRÚC

```
✅ TÁCH XONG VỀ MẶT APP STRUCTURE:
   - Mỗi module có app riêng
   - Routing riêng via app_name
   - Views/forms riêng
   - URLs riêng

⚠️ VẪN PHỤ THUỘC MONOLITH `spa`:
   - ALL models vẫn ở spa.models (7 models)
   - Templates vẫn ở templates/spa/ + templates/admin/
   - Nhiều URLs vẫn dùng namespace `spa:`
   - Nhiều redirects vẫn dùng absolute paths
   - spa/views.py vẫn còn 14 views chưa tách
   - spa/forms.py vẫn còn 5 forms chưa tách
```

---

## B. DANH SÁCH IMPORT CÒN PHỤ THUỘC `spa.*`

### 📦 IMPORT TỪ `spa.models` (TẠM THỜI - CHƯA MOVE MODEL)

**Total: 15 files Python import từ spa.models**

#### 1. **accounts app** (2 files)
```python
# accounts/views.py:24
from spa.models import CustomerProfile

# accounts/forms.py:16
from spa.models import CustomerProfile
```
**Models cần**: `CustomerProfile`

#### 2. **complaints app** (2 files)
```python
# complaints/views.py:19-22
from spa.models import (
    Complaint, ComplaintReply, ComplaintHistory,
    CustomerProfile, Service
)

# complaints/forms.py:17
from spa.models import Complaint, Service, ComplaintReply
```
**Models cần**: `Complaint, ComplaintReply, ComplaintHistory, CustomerProfile, Service`

#### 3. **appointments app** (4 files)
```python
# appointments/views.py:23
from spa.models import Appointment, CustomerProfile, Service, Room

# appointments/forms.py:13
from spa.models import Appointment, Service

# appointments/appointment_services.py:21
from spa.models import Appointment, CustomerProfile, Service, Room

# appointments/services.py:19
from spa.models import Appointment, Room
```
**Models cần**: `Appointment, CustomerProfile, Service, Room`

#### 4. **spa_services app** (3 files)
```python
# spa_services/views.py:23
from spa.models import Service

# spa_services/forms.py:14
from spa.models import Service

# spa_services/service_services.py:21
from spa.models import Service
```
**Models cần**: `Service`

#### 5. **pages app** (1 file)
```python
# pages/views.py:12
from spa.models import Service  # Tạm import từ spa.models
```
**Models cần**: `Service`

#### 6. **core app** (2 files - VALIDATORS/DECORATORS)
```python
# core/validators.py:46 (trong hàm)
    from spa.models import Service

# core/validators.py:244 (trong hàm)
    from spa.models import CustomerProfile

# core/decorators.py:182 (trong hàm)
    from spa.models import CustomerProfile

# core/decorators.py:239 (trong hàm)
    from spa.models import CustomerProfile
```
**Models cần**: `Service, CustomerProfile`
**Lưu ý**: Import TRONG hàm (lazy import) để avoid circular dependency

#### 7. **spa app** (1 file - SELF IMPORT)
```python
# spa/views.py:13-16
from .models import (
    Service, Appointment, CustomerProfile,
    Complaint, ComplaintReply, ComplaintHistory, Room
)
```
**Models cần**: ALL 7 models (local import, OK)

---

### 📋 TỔNG HỢP MODEL DEPENDENCIES

| Model | Được dùng bởi apps | File count | Priority move |
|-------|-------------------|-------------|---------------|
| **Service** | spa_services, pages, complaints, appointments | 6 | **HIGH** |
| **CustomerProfile** | accounts, complaints, appointments, core | 6 | **HIGH** |
| **Appointment** | appointments | 4 | **MEDIUM** |
| **Room** | appointments | 3 | **MEDIUM** |
| **Complaint** | complaints | 2 | **LOW** |
| **ComplaintReply** | complaints | 2 | **LOW** |
| **ComplaintHistory** | complaints | 2 | **LOW** |

---

## C. DANH SÁCH URL NAMESPACE CŨ CÒN SÓT

### 📌 TEMPLATES VẪN DÙNG `spa:` NAMESPACE

**Total: 50+ occurrences across 15 templates**

#### 1. **Customer-facing templates** (10 files)

**templates/spa/pages/home.html**
```django
{% url 'spa:booking' %}          # → appointments:booking
{% url 'spa:service_list' %}     # → spa_services:service_list
{% url 'spa:about' %}            # → pages:about
```

**templates/spa/pages/about.html**
```django
{% url 'spa:service_list' %}     # → spa_services:service_list
```

**templates/spa/pages/login.html**
```django
{% url 'spa:register' %}         # → accounts:register
```

**templates/spa/pages/booking.html**
```django
{% url 'spa:booking' %}          # → appointments:booking
```

**templates/spa/pages/my_appointments.html**
```django
{% url 'spa:cancel_appointment' appointment.id %}  # → appointments:cancel_appointment
{% url 'spa:booking' %}          # → appointments:booking
```

**templates/spa/pages/customer_profile.html**
```django
{% url 'spa:my_appointments' %}          # → appointments:my_appointments
{% url 'spa:customer_complaint_list' %}  # → complaints:customer_complaint_list
{% url 'spa:customer_profile' %}         # → accounts:customer_profile
```

**templates/spa/pages/customer_complaint_list.html**
```django
{% url 'spa:home' %}                      # → pages:home
{% url 'spa:customer_complaint_create' %} # → complaints:customer_complaint_create
{% url 'spa:customer_complaint_detail' complaint.id %}  # → complaints:customer_complaint_detail
```

**templates/spa/pages/customer_complaint_create.html**
```django
{% url 'spa:home' %}                      # → pages:home
{% url 'spa:customer_complaint_list' %}  # → complaints:customer_complaint_list
```

**templates/spa/pages/customer_complaint_detail.html**
```django
{% url 'spa:home' %}                      # → pages:home
{% url 'spa:customer_complaint_list' %}  # → complaints:customer_complaint_list
{% url 'spa:customer_complaint_reply' complaint.id %}  # → complaints:customer_complaint_reply
```

**templates/spa/pages/password_reset.html**
```django
{% url 'spa:login' %}            # → accounts:login
```

#### 2. **Admin templates** (5 files)

**templates/admin/pages/admin_login.html**
```django
{% url 'spa:index' %}            # → pages:home
```

**templates/admin/pages/admin_clear-login.html**
```django
{% url 'spa:admin_login' %}      # → spa:admin_login (KEEP)
{% url 'spa:home' %}             # → pages:home
```

**templates/admin/pages/admin_complaints.html**
```django
{% url 'spa:admin_complaint_detail' complaint.id %}  # → complaints:admin_complaint_detail
```

**templates/admin/pages/admin_complaint_detail.html**
```django
{% url 'spa:admin_complaints' %}                     # → complaints:admin_complaints
{% url 'spa:admin_complaint_reply' complaint.id %}   # → complaints:admin_complaint_reply
{% url 'spa:admin_complaint_take' complaint.id %}    # → complaints:admin_complaint_take
{% url 'spa:admin_complaint_assign' complaint.id %}  # → complaints:admin_complaint_assign
{% url 'spa:admin_complaint_status' complaint.id %}  # → complaints:admin_complaint_status
```

**templates/admin/pages/admin_services.html**
```django
{% url 'spa:admin_services' %}   # → spa_services:admin_services
{% url 'spa:api_service_create' %}  # → spa_services:api_service_create
```

**templates/admin/includes/sidebar.html**
```django
{% url 'spa:admin_appointments' %}  # → appointments:admin_appointments
{% url 'spa:admin_services' %}      # → spa_services:admin_services
{% url 'spa:admin_live_chat' %}     # → spa:admin_live_chat (KEEP)
{% url 'spa:admin_complaints' %}    # → complaints:admin_complaints
{% url 'spa:admin_customers' %}     # → spa:admin_customers (KEEP)
{% url 'spa:admin_staff' %}         # → spa:admin_staff (KEEP)
{% url 'spa:admin_profile' %}       # → spa:admin_profile (KEEP)
{% url 'spa:admin_logout' %}        # → spa:admin_logout (KEEP)
```

---

## D. DANH SÁCH ABSOLUTE REDIRECTS CÒN SÓT

### 🔄 VIEWS DÙNG ABSOLUTE PATH REDIRECTS

**Total: 40+ absolute redirects across 4 apps**

#### 1. **complaints/views.py** (14 absolute redirects)
```python
# Customer redirects
redirect('/khieu-nai-cua-toi/')                    # Line 72, 110, 133
redirect('/khieu-nai-cua-toi/%d/' % complaint_id)  # Line 159
redirect('/')                                       # Line 171

# Admin redirects
redirect('/')                                       # Line 215, 243
redirect('/manage/complaints/%d/' % complaint_id)   # Line 263, 291, 321, 350, 383
```

**Nên đổi sang**:
```python
redirect('complaints:customer_complaint_list')
redirect('complaints:customer_complaint_detail', complaint_id)
redirect('complaints:admin_complaint_detail', complaint_id)
```

#### 2. **appointments/views.py** (8 absolute redirects)
```python
redirect('/lich-hen-cua-toi/')                     # Line 116, 194, 202, 218, 230
redirect('/')                                       # Line 202
```

**Nên đổi sang**:
```python
redirect('appointments:my_appointments')
redirect('pages:home')
```

#### 3. **spa_services/views.py** (10 absolute redirects)
```python
redirect('/')                                       # Line 81, 167, 206
redirect('/manage/services/')                       # Line 143, 157, 184, 196, 224
```

**Nên đổi sang**:
```python
redirect('pages:home')
redirect('spa_services:admin_services')
```

#### 4. **accounts/views.py** (4 absolute redirects)
```python
redirect('/login/')                                 # Line 213, 276
redirect('/quen-mat-khau/')                         # Line 222
redirect('/tai-khoan/')                            # Line 265
```

**Nên đổi sang**:
```python
redirect('accounts:login')
redirect('accounts:password_reset')
redirect('accounts:customer_profile')
```

---

## E. DANH SÁCH TEMPLATE PATH CŨ CÒN SÓT

### 📁 VIEWS RENDER TEMPLATES VỚI PATH CŨ

**Total: 23 template paths still pointing to spa/ or admin/**

#### 1. **complaints/views.py** (5 template paths)
```python
# Line 77
render(request, 'spa/pages/customer_complaint_create.html')

# Line 96
render(request, 'spa/pages/customer_complaint_list.html')

# Line 123
render(request, 'spa/pages/customer_complaint_detail.html')

# Line 207
render(request, 'admin/pages/admin_complaints.html')

# Line 235
render(request, 'admin/pages/admin_complaint_detail.html')
```

**Nên chuyển sang** (sau khi move templates):
```python
render(request, 'complaints/customer_complaint_create.html')
render(request, 'complaints/customer_complaint_list.html')
render(request, 'complaints/customer_complaint_detail.html')
render(request, 'complaints/admin_complaints.html')
render(request, 'complaints/admin_complaint_detail.html')
```

#### 2. **appointments/views.py** (4 template paths)
```python
# Line 125
render(request, 'spa/pages/booking.html')

# Line 171
render(request, 'spa/pages/my_appointments.html')

# Line 206
render(request, 'spa/pages/cancel_appointment.html')

# Line 231
render(request, 'admin/pages/admin_appointments.html')
```

#### 3. **spa_services/views.py** (3 template paths)
```python
# Line 48
render(request, 'spa/pages/services.html')

# Line 61
render(request, 'spa/pages/service_detail.html')

# Line 126
render(request, 'admin/pages/admin_services.html')
```

#### 4. **accounts/views.py** (7 template paths)
```python
# Line 62
render(request, 'spa/pages/login.html')

# Line 92
render(request, 'spa/pages/register.html')

# Line 123
render(request, 'spa/pages/password_reset.html')

# Line 167, 174
render(request, 'spa/pages/password_reset_sent.html')

# Line 178
render(request, 'spa/pages/password_reset.html')

# Line 215
render(request, 'spa/pages/password_reset_confirm.html')

# Line 294
render(request, 'spa/pages/customer_profile.html')
```

#### 5. **spa/views.py** (4 template paths - CHƯA TÁCH)
```python
# Các views chưa tách vẫn render templates/spa/pages/
render(request, 'spa/pages/home.html')
render(request, 'spa/pages/about.html')
render(request, 'spa/pages/service_detail.html')
render(request, 'spa/pages/services.html')
```

---

## F. ĐỀ XUẤT THỨ TỰ CLEANUP AN TOÀN

### 🎯 CHIẾN LƯỢC CLEANUP 6 PHASE

#### **PHASE 8.1: URL Namespace Migration** (KHÔNG affecting DB, LOW RISK)
**Mục tiêu**: Đổi tất cả `spa:` URL sang correct namespaces

**Files cần sửa**: 15 templates (50+ occurrences)

**Thứ tự**:
1. Customer-facing templates (10 files)
   - home.html, about.html, login.html, register.html
   - booking.html, my_appointments.html, customer_profile.html
   - customer_complaint_*.html

2. Admin templates (5 files)
   - admin_login.html, admin_complaints.html, admin_complaint_detail.html
   - admin_services.html, sidebar.html

**Testing**:
- Click all links
- Test all forms submit
- Verify breadcrumbs

**Rollback**: Comment old URLs, add new ones (không xóa ngay)

---

#### **PHASE 8.2: Absolute Redirect → Named URL** (LOW RISK)
**Mục tiêu**: Đổi absolute paths sang `reverse()` hoặc named URLs

**Files cần sửa**: 4 views files (40+ redirects)

**Thứ tự**:
1. accounts/views.py (4 redirects - EASIEST)
2. appointments/views.py (8 redirects)
3. complaints/views.py (14 redirects)
4. spa_services/views.py (10 redirects)

**Ví dụ**:
```python
# OLD
redirect('/login/')

# NEW
from django.shortcuts import redirect
return redirect('accounts:login')
```

**Testing**:
- Test all redirect flows
- Verify login/logout cycles
- Check form submission redirects

**Rollback**: Git revert (easy)

---

#### **PHASE 8.3: Move Models** (HIGH RISK - CẦN MIGRATION)
**Mục tiêu**: Di chuyển models từ spa.models sang respective apps

**Thứ tự DI CHUYỂN** (theo dependency):

**BATCH 1: Isolated models** (LOW dependency risk)
1. `Room` → appointments/models.py
   - Chỉ appointments dùng
   - ForeignKey: Appointment.room

2. `ComplaintReply` → complaints/models.py
   - Chỉ complaints dùng
   - ForeignKey: ComplaintReply.complaint

3. `ComplaintHistory` → complaints/models.py
   - Chỉ complaints dùng
   - ForeignKey: ComplaintHistory.complaint

**BATCH 2: Moderate dependency** (MEDIUM risk)
4. `Complaint` → complaints/models.py
   - Dùng bởi: complaints app
   - ForeignKey từ: ComplaintReply, ComplaintHistory
   - Reverse relation: CustomerProfile.complaints

5. `Service` → spa_services/models.py
   - Dùng bởi: spa_services, pages, appointments, complaints
   - ForeignKey từ: Appointment.service, Complaint.related_service
   - **QUAN TRỌNG**: Nhiều apps depend on this

**BATCH 3: High dependency** (HIGHEST risk)
6. `CustomerProfile` → accounts/models.py
   - Dùng bởi: accounts, appointments, complaints, core
   - ForeignKey: Appointment.customer, Complaint.customer
   - OneToOne: CustomerProfile.user

**BATCH 4: Last to move** (MOST complex)
7. `Appointment` → appointments/models.py
   - Dùng bởi: appointments app
   - ForeignKey: Appointment.service, Appointment.room, Appointment.customer
   - Reverse relation: CustomerProfile.appointments

**Migration Strategy cho mỗi batch**:
```bash
# 1. Create new model in target app
# 2. Create migration
# 3. Run migration
# 4. Test imports from all dependent apps
# 5. Update imports in dependent apps
# 6. Test thoroughly
# 7. Remove old model from spa/models.py
# 8. Create migration to delete old table
# 9. Run migration
```

**Testing cho mỗi batch**:
- Test all CRUD operations
- Test ForeignKeys still work
- Test reverse relations still work
- Run all tests
- Check Django admin

**Rollback**:
- Keep old model in spa/models.py (commented) for 1 phase
- Only delete after confirmed working

---

#### **PHASE 8.4: Move Templates** (MEDIUM RISK)
**Mục tiêu**: Di chuyển templates sang app-specific folders

**Cấu trúc mới**:
```
templates/
├── pages/
│   └── pages/
│       ├── home.html
│       └── about.html
├── accounts/
│   └── pages/
│       ├── login.html
│       ├── register.html
│       └── customer_profile.html
├── spa_services/
│   ├── pages/
│   │   ├── services.html
│   │   └── service_detail.html
│   └── admin/
│       └── admin_services.html
├── appointments/
│   ├── pages/
│   │   ├── booking.html
│   │   ├── my_appointments.html
│   │   └── cancel_appointment.html
│   └── admin/
│       └── admin_appointments.html
└── complaints/
    ├── pages/
    │   ├── customer_complaint_create.html
    │   ├── customer_complaint_list.html
    │   └── customer_complaint_detail.html
    └── admin/
        ├── admin_complaints.html
        └── admin_complaint_detail.html
```

**Thứ tự di chuyển**:
1. pages templates (2 files - EASIEST)
2. accounts templates (7 files)
3. complaints templates (5 files)
4. appointments templates (4 files)
5. spa_services templates (3 files)
6. admin templates (keep in admin/ folder)

**Sau khi move**, cập nhật views:
```python
# OLD
render(request, 'spa/pages/home.html')

# NEW
render(request, 'pages/pages/home.html')  # pages/pages/ structure
```

**Testing**:
- Test all page loads
- Check template inheritance (base.html)
- Verify static files still load
- Check forms still render

**Rollback**:
- Git revert
- Keep old templates for 1 phase

---

#### **PHASE 8.5: Tách Nốt Views/Forms Còn Lại** (LOW-MEDIUM RISK)
**Mục tiêu**: Tách nốt 14 views + 5 forms còn trong spa app

**Views còn trong spa/views.py** (chưa tách):
```python
1. home()                    # → pages/views.py
2. about()                   # → pages/views.py
3. service_list()            # → spa_services/views.py
4. service_detail()          # → spa_services/views.py
5. booking()                 # → appointments/views.py
6. my_appointments()         # → appointments/views.py
7. cancel_appointment()      # → appointments/views.py
8. login_view()              # → accounts/views.py
9. register()                # → accounts/views.py
10. logout_view()            # → accounts/views.py
11. password_reset_request() # → accounts/views.py
12. password_reset_confirm() # → accounts/views.py
13. customer_profile()       # → accounts/views.py
14. admin_login()            # → NEW admin_panel app (KHÔNG TÁCH)
15. admin_logout()           # → NEW admin_panel app (KHÔNG TÁCH)
16. admin_customers()        # → NEW admin_panel app (KHÔNG TÁCH)
17. admin_staff()            # → NEW admin_panel app (KHÔNG TÁCH)
18. admin_live_chat()        # → NEW admin_panel app (KHÔNG TÁCH)
19. admin_profile()          # → NEW admin_panel app (KHÔNG TÁCH)
```

**Forms còn trong spa/forms.py** (chưa tách):
```python
1. AdminLoginForm            # → NEW admin_panel/forms.py
2. CustomerProfileForm       # → accounts/forms.py
3. ChangePasswordForm        # → accounts/forms.py
4. CustomerRegistrationForm  # → accounts/forms.py
5. AppointmentForm           # → appointments/forms.py
```

**API views còn trong spa/views.py**:
```python
1. api_services_list()       # → spa_services/views.py
2. api_service_create()      # → spa_services/views.py
3. api_service_update()      # → spa_services/views.py
4. api_service_delete()      # → spa_services/views.py
```

**Thứ tự tách**:
1. Tách CustomerRegistrationForm, CustomerProfileForm, ChangePasswordForm → accounts/forms.py
2. Tách login_view, register, logout_view, password_reset_* → accounts/views.py
3. Tách AppointmentForm → appointments/forms.py
4. Tách booking, my_appointments, cancel_appointment → appointments/views.py
5. Tách service_list, service_detail → spa_services/views.py
6. Tách api_services_* → spa_services/views.py
7. Tách home, about → pages/views.py
8. **KHÔNG TÁCH** admin_* views → **GIỮ NGUYÊN trong new admin_panel app**

---

#### **PHASE 8.6: Tạo admin_panel App + Final Cleanup** (MEDIUM RISK)
**Mục tiêu**: Tách admin views ra app riêng, cleanup hoàn toàn

**Tạo app mới**: `admin_panel`

**Views trong admin_panel**:
- admin_login()
- admin_logout()
- admin_customers()
- admin_staff()
- admin_live_chat()
- admin_profile()
- admin_appointments() (hoặc giữ ở appointments)
- admin_services() (hoặc giữ ở spa_services)
- admin_complaints() (hoặc giữ ở complaints)

**Admin URLs consolidation**:
- `/manage/login/` → admin_panel:admin_login
- `/manage/customers/` → admin_panel:admin_customers
- `/manage/staff/` → admin_panel:admin_staff
- `/manage/profile/` → admin_panel:admin_profile
- `/manage/live-chat/` → admin_panel:admin_live_chat

**Cleanup**:
- Xóa spa/views.py
- Xóa spa/forms.py
- Xóa spa/urls.py
- Xóa spa/admin.py (nếu models đã move hết)
- Giữ lại spa/models.py (import only) để backward compatibility

---

## G. ĐỀ XUÁT STRATEGY MOVE MODELS AN TOÀN THEO TỪNG APP

### 🛡️ SAFE MODEL MIGRATION STRATEGY

#### **QUY TẮC BẮT BUỘC**:
1. ❌ **KHÔNG BAO GIỜ** move model cùng lúc với business logic
2. ✅ **LUÔN LUÔN** move model → test → import update → test lại
3. ✅ **LUÔN LUÔN** giữ old model (commented) ít nhất 1 phase
4. ✅ **LUÔN LUÔN** backup database trước migration
5. ✅ **LUÔN LUÔN** test migration trên development trước

---

#### **STRATEGY CHO TỪNG MODEL**:

### **BATCH 1: ROOM → appointments/models.py**

**Bước 1: Create model in appointments**
```python
# appointments/models.py
from django.db import models

class Room(models.Model):
    # Copy exact fields from spa.models.Room
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    # ... copy all fields

    class Meta:
        db_table = 'spa_room'  # IMPORTANT: keep old table name
```

**Bước 2: Create migration**
```bash
python manage.py makemigrations appointments
```

**Bước 3: Run migration**
```bash
python manage.py migrate appointments
```

**Bước 4: Update imports in appointments app**
```python
# appointments/views.py
# OLD: from spa.models import Room
# NEW: from appointments.models import Room
from .models import Appointment, Room  # local import
```

**Bước 5: Test**
```bash
python manage.py shell
>>> from appointments.models import Room
>>> Room.objects.count()  # Should work
```

**Bước 6: Keep old model (commented) in spa/models.py**
```python
# spa/models.py
# class Room(models.Model):  # DEPRECATED - Moved to appointments
#     ... (commented out)
```

**Bước 7: Test thorough**
- Run Django checks
- Test all appointment views
- Test admin
- Check ForeignKeys still work

**Bước 8: AFTER 1 PHASE, remove old model**
```python
# spa/models.py - Delete Room model entirely
```

**Bước 9: Create migration to delete old table (if needed)**

---

### **BATCH 2: COMPLAINT SERIES → complaints/models.py**

**Thứ tự**: ComplaintReply → ComplaintHistory → Complaint

**Reason**: ComplaintReply và ComplaintHistory không có reverse ForeignKey, dễ move nhất.

**Steps giống BATCH 1**, lặp lại cho mỗi model.

**Lưu ý**:
- Keep `db_table = 'spa_complaint'` etc.
- Move ComplaintReply trước (không dependency khác)
- Move ComplaintHistory trước (không dependency khác)
- Move Complaint SAU CÙNG (có ForeignKey từ 2 model trên)

---

### **BATCH 3: SERVICE → spa_services/models.py**

**RISK: CAUTION** - Service được dùng bởi 4 apps!

**Step thêm: BEFORE moving, check all dependent apps**
```bash
# Grep to find all Service usages
grep -r "Service\." spa_project/ --include="*.py" | grep -v ".pyc"
```

**Step thêm: Update ALL imports in ALL apps BEFORE running migration**
```python
# Update in this order:
1. spa_services/views.py → from spa_services.models import Service
2. spa_services/forms.py → from spa_services.models import Service
3. spa_services/service_services.py → from spa_services.models import Service
4. pages/views.py → from spa_services.models import Service (cross-app import)
5. appointments/views.py → from spa_services.models import Service
6. appointments/forms.py → from spa_services.models import Service
7. complaints/views.py → from spa_services.models import Service
8. complaints/forms.py → from spa_services.models import Service
9. core/validators.py → from spa_services.models import Service (lazy import)
```

**Step đặc biệt: Handle ForeignKey constraints**
```python
# appointments/models.py - BEFORE Service moved
from spa.models import Service  # OLD

class Appointment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    # ...

# AFTER Service moved to spa_services
from spa_services.models import Service  # NEW
# OR use string reference:
service = models.ForeignKey('spa_services.Service', on_delete=models.CASCADE)
```

**Test đặc biệt**:
- Test all service CRUD
- Test appointments can still select service
- Test complaints can still select service
- Test API endpoints

---

### **BATCH 4: CUSTOMERPROFILE → accounts/models.py**

**RISK: HIGH** - Dùng bởi 4 apps + có OneToOne với User!

**Lưu ý đặc biệt**:
- OneToOne với User: phải giữ nguyên
- Reverse relation: CustomerProfile.appointments, CustomerProfile.complaints

**Step đặc biệt: Check User relation**
```python
# accounts/models.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # ... copy all fields

    class Meta:
        db_table = 'spa_customerprofile'  # Keep old table name

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.get_or_create(user=instance)
```

**Step đặc biệt: Update ALL imports BEFORE migration**
```python
# Update in order:
1. accounts/views.py → from accounts.models import CustomerProfile
2. accounts/forms.py → from accounts.models import CustomerProfile
3. appointments/views.py → from accounts.models import CustomerProfile
4. appointments/appointment_services.py → from accounts.models import CustomerProfile
5. complaints/views.py → from accounts.models import CustomerProfile
6. core/decorators.py → from accounts.models import CustomerProfile (lazy import)
7. core/validators.py → from accounts.models import CustomerProfile (lazy import)
```

**Test đặc biệt**:
- Test user registration still creates profile
- Test profile edit
- Test profile display
- Test ForeignKeys from appointments still work
- Test ForeignKeys from complaints still work

---

### **BATCH 5: APPOINTMENT → appointments/models.py**

**RISK: HIGHEST** - Cuối cùng vì có ForeignKeys đến Service, Room, CustomerProfile

**Move SAU KHI**:
- ✅ Room đã move xong
- ✅ Service đã move xong
- ✅ CustomerProfile đã move xong

**Step đặc biệt: Update ForeignKey references**
```python
# appointments/models.py
from accounts.models import CustomerProfile
from spa_services.models import Service
from .models import Room

class Appointment(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    # ... copy all fields

    class Meta:
        db_table = 'spa_appointment'  # Keep old table name
```

**Test đặc biệt**:
- Test appointment creation
- Test appointment editing
- Test appointment cancellation
- Test all ForeignKeys work
- Test reverse relations work

---

### **ROLLBACK STRATEGY CHO TỪNG BATCH**

**Nếu move model thất bại**:

**Option 1: Revert code (QUICKEST)**
```bash
git revert <migration_commit>
git revert <code_changes_commit>
```

**Option 2: Manually rollback (IF database changed)**
```python
# In target app, comment out new model
# In spa/models.py, uncomment old model
python manage.py migrate <target_app> zero  # Remove new migration
```

**Option 3: Data migration (IF data exists)**
```bash
# Export data before migration
python manage.py dumpdata spa.Room > room_backup.json

# Import back if needed
python manage.py loaddata room_backup.json
```

---

## H. ĐIỀU KIỆN CẦN ĐẠT TRƯỚC KHI XÓA APP `spa`

### ✅ CHECKLIST TRƯỚC KHI DELETE SPA APP

#### **1. MODELS** (TẤT ĐÃ MOVE)
- [ ] Room → appointments/models.py ✅
- [ ] ComplaintReply → complaints/models.py ✅
- [ ] ComplaintHistory → complaints/models.py ✅
- [ ] Complaint → complaints/models.py ✅
- [ ] Service → spa_services/models.py ✅
- [ ] CustomerProfile → accounts/models.py ✅
- [ ] Appointment → appointments/models.py ✅
- [ ] spa/models.py chỉ còn import statements (không còn class Model)

**Testing**:
```bash
python manage.py check
python manage.py shell -c "from appointments.models import Room, Appointment; from complaints.models import Complaint, ComplaintReply, ComplaintHistory; from spa_services.models import Service; from accounts.models import CustomerProfile; print('OK')"
```

#### **2. VIEWS** (TẤT ĐÃ TÁCH)
- [ ] home() → pages/views.py ✅
- [ ] about() → pages/views.py ✅
- [ ] service_list() → spa_services/views.py ✅
- [ ] service_detail() → spa_services/views.py ✅
- [ ] booking() → appointments/views.py ✅
- [ ] my_appointments() → appointments/views.py ✅
- [ ] cancel_appointment() → appointments/views.py ✅
- [ ] login_view() → accounts/views.py ✅
- [ ] register() → accounts/views.py ✅
- [ ] logout_view() → accounts/views.py ✅
- [ ] password_reset_request() → accounts/views.py ✅
- [ ] password_reset_confirm() → accounts/views.py ✅
- [ ] customer_profile() → accounts/views.py ✅
- [ ] admin_* → admin_panel/views.py ✅
- [ ] api_* → respective apps ✅
- [ ] spa/views.py chỉ còn import hoặc đã xóa

**Testing**:
```bash
python manage.py check
python manage.py test
# Manually test all views in browser
```

#### **3. FORMS** (TẤT ĐÃ TÁCH)
- [ ] CustomerRegistrationForm → accounts/forms.py ✅
- [ ] CustomerProfileForm → accounts/forms.py ✅
- [ ] ChangePasswordForm → accounts/forms.py ✅
- [ ] AppointmentForm → appointments/forms.py ✅
- [ ] ServiceForm → spa_services/forms.py ✅
- [ ] CustomerComplaintForm → complaints/forms.py ✅
- [ ] GuestComplaintForm → complaints/forms.py ✅
- [ ] ComplaintReplyForm → complaints/forms.py ✅
- [ ] ComplaintStatusForm → complaints/forms.py ✅
- [ ] ComplaintAssignForm → complaints/forms.py ✅
- [ ] AdminLoginForm → admin_panel/forms.py ✅
- [ ] spa/forms.py chỉ còn import hoặc đã xóa

**Testing**:
```bash
python manage.py check
# Test all forms submit
```

#### **4. URLS** (TẤT ĐÃ COMMENT/DELETE)
- [ ] spa/urls.py chỉ còn comment hoặc admin routes
- [ ] Mọi route đã comment ghi rõ "MOVED → <app>"
- [ ] spa_project/urls.py không include spa.urls cho public routes
- [ ] Mọi app có urls.py riêng

**Testing**:
```bash
python manage.py show_urls | grep -v "^/admin/" | grep "spa:"
# Should show minimal or no spa: URLs
```

#### **5. TEMPLATES** (ĐÃ MOVE HOẶC ORGANIZED)
- [ ] templates/spa/pages/home.html → pages/pages/home.html
- [ ] templates/spa/pages/about.html → pages/pages/about.html
- [ ] templates/spa/pages/login.html → accounts/pages/login.html
- [ ] templates/spa/pages/register.html → accounts/pages/register.html
- [ ] templates/spa/pages/customer_profile.html → accounts/pages/customer_profile.html
- [ ] templates/spa/pages/password_reset*.html → accounts/pages/
- [ ] templates/spa/pages/booking*.html → appointments/pages/
- [ ] templates/spa/pages/my_appointments.html → appointments/pages/
- [ ] templates/spa/pages/services*.html → spa_services/pages/
- [ ] templates/spa/pages/customer_complaint*.html → complaints/pages/
- [ ] templates/admin/pages/admin_*.html → respective apps/admin/

**Testing**:
```bash
# Test all page loads
# Test all forms render
# Check template inheritance
```

#### **6. IMPORTS** (KHÔNG CÒN CROSS-APP IMPORT TỪ SPA)
- [ ] Không còn `from spa.models import` trong các app khác
- [ ] Không còn `from spa.forms import` trong các app khác
- [ ] Không còn `from spa.views import` trong các app khác
- [ ] Không còn `from spa.services import` trong các app khác
- [ ] Không còn `from spa.appointment_services import` trong các app khác
- [ ] Không còn `from spa.service_services import` trong các app khác

**Testing**:
```bash
grep -r "from spa\." spa_project/ --include="*.py" | grep -v "spa/models.py" | grep -v "spa/views.py" | grep -v ".pyc"
# Should return nothing or only imports from spa.models for backward compat
```

#### **7. URL NAMESPACES** (ĐÃ UPDATE ALL)
- [ ] Không còn `{% url 'spa:' %}` trong templates (trừ admin routes chưa tách)
- [ ] Mọi customer-facing templates dùng đúng namespace
- [ ] Mọi admin templates dùng đúng namespace

**Testing**:
```bash
grep -r "url 'spa:" templates/ --include="*.html"
# Should only show admin routes that haven't been moved yet
```

#### **8. REDIRECTS** (ĐÃ UPDATE ALL)
- [ ] Không còn `redirect('/...')` absolute paths trong views
- [ ] Mọi redirect dùng named URLs hoặc `reverse()`

**Testing**:
```bash
grep -r "redirect('/" spa_project/ --include="*.py"
# Should return nothing
```

#### **9. MIGRATIONS** (ĐÁP ỨNG)
- [ ] Mọi migration chạy thành công
- [ ] Không có migration pending
- [ ] Database schema stable

**Testing**:
```bash
python manage.py showmigrations
# All should be [X]
python manage.py makemigrations --check --dry-run
# Should say "No changes detected"
```

#### **10. TESTS** (ALL PASS)
- [ ] Django system check passes
- [ ] All existing tests pass
- [ ] Manual testing passes
- [ ] No errors in logs

**Testing**:
```bash
python manage.py check
python manage.py test
# Manual smoke test
```

---

### 🔥 QUY TRÌNH XÓA APP `spa` (KHI ALL CHECKLIST PASSED)

#### **BƯỚC 1: Backup**
```bash
# Backup code
git add -A
git commit -m "Before deleting spa app - final state"

# Backup database
python manage.py dumpdata > full_backup_$(date +%Y%m%d).json
```

#### **BƯỚC 2: Uninstall spa app**
```python
# spa_project/settings.py
INSTALLED_APPS = [
    # ... other apps
    # 'spa',  # COMMENT OUT
]
```

#### **BƯỚC 3: Test**
```bash
python manage.py check
python manage.py runserver
# Test thoroughly
```

#### **BƯỚC 4: Delete spa app folder**
```bash
rm -rf spa_project/spa/
```

#### **BƯỚC 5: Update URLs**
```python
# spa_project/urls.py
urlpatterns = [
    # ... other includes
    # path('', include('spa.urls')),  # REMOVE
]
```

#### **BƯỚC 6: Final test**
```bash
python manage.py check
python manage.py runserver
# SMOKE TEST EVERYTHING
```

#### **BƯỚC 7: Commit**
```bash
git add -A
git commit -m "Delete spa app - migration complete"
```

---

## 📋 SUMMARY TABLE

| Phase | Tác vụ | Số files | Risk | Ước tính thời gian |
|-------|--------|----------|------|-------------------|
| **8.1** | URL Namespace Migration | 15 templates | LOW | 2-3 hours |
| **8.2** | Absolute Redirect → Named URL | 4 views files | LOW | 1-2 hours |
| **8.3** | Move Models (5 batches) | 7 models + migrations | HIGH | 1-2 days |
| **8.4** | Move Templates | 23 templates | MEDIUM | 3-4 hours |
| **8.5** | Tách nốt Views/Forms | 14 views + 5 forms | LOW-MEDIUM | 4-6 hours |
| **8.6** | Tạo admin_panel + Delete spa | 1 new app + cleanup | MEDIUM | 2-3 hours |
| **TOTAL** | **COMPLETE CLEANUP** | **~50 files** | **MEDIUM** | **2-3 days** |

---

## 🎯 RECOMMENDATION

**Đề xuất thực hiện theo thứ tự**:
1. ✅ **Phase 8.1 + 8.2** (LOW RISK) - Có thể làm ngay, không ảnh hưởng DB
2. ⏸️ **Phase 8.3** (HIGH RISK) - Cần testing kỹ trên development trước
3. ✅ **Phase 8.4** (MEDIUM) - Làm sau khi models ổn định
4. ✅ **Phase 8.5** (LOW-MEDIUM) - Làm song song với 8.4
5. ✅ **Phase 8.6** (MEDIUM) - Làm cuối cùng khi mọi thứ ổn định

**Priority**:
- **HIGH PRIORITY**: 8.1 + 8.2 (cleanup URLs, redirects)
- **MEDIUM PRIORITY**: 8.3 (move models - quan trọng nhất)
- **LOW PRIORITY**: 8.4 + 8.5 + 8.6 (cosmetic cleanup)

---

**Generated**: 2026-03-30
**Author**: Spa ANA Team
**Phase**: 8 - CONSOLIDATION & CLEANUP PLAN (NO CODE CHANGES)
**Status**: 📋 PLANNING COMPLETE - READY FOR EXECUTION
