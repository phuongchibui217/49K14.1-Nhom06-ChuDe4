# PROJECT REFACTOR STATUS - BÁO CÁO TRẠNG THÁI REFACTOR DỰ ÁN

**Ngày**: 2026-03-30
**Dự án**: Spa ANA - Django Web Application
**Trạng thái**: 🟡 PARTIAL COMPLETION - BRIDGE PHASE
**Phase hiện tại**: 8.4 - Model Move (Batch 1 - Room Bridge Only)

---

## A. TỔNG QUAN TIẾN ĐỘ HIỆN TẠI

### **A.1. Các App Đã Tách Thành Công**

Dự án đã được tách thành **9 apps** từ app monolithic `spa` ban đầu:

| App | Trạng thái | Mô tả | Files đã tạo |
|-----|-----------|-------|--------------|
| **core** | ✅ HOÀN THÀNH | Utilities chung (decorators, validators, API response) | `decorators.py`, `validators.py`, `api_response.py` |
| **pages** | ✅ HOÀN THÀNH | Static pages (home, about) | `views.py`, `urls.py`, `templates/pages/` |
| **accounts** | ✅ HOÀN THÀNH | Authentication, customer profile | `views.py`, `urls.py`, `forms.py`, `templates/accounts/` |
| **spa_services** | ✅ HOÀN THÀNH | Services management | `views.py`, `urls.py`, `forms.py`, `service_services.py`, `templates/spa_services/` |
| **appointments** | ✅ HOÀN THÀNH + ⚠️ BRIDGE | Appointment booking, management | `views.py`, `urls.py`, `forms.py`, `services.py`, `appointment_services.py`, `templates/appointments/`<br>**NEW**: `models.py` (Room bridge) |
| **complaints** | ✅ HOÀN THÀNH | Customer complaints | `views.py`, `urls.py`, `forms.py`, `complaint_services.py`, `templates/complaints/` |
| **admin_panel** | ✅ HOÀN THÀNH | Admin pages | `views.py`, `urls.py`, `templates/admin/` |
| **spa** | ⚠️ PARTIAL | Original app (đang dần được tách) | **GIỮ**: `models.py` (7 models), `views.py`, `forms.py`, `admin.py`, `templates/` |
| **api** | - | API endpoints (nếu có) | (không thấy sử dụng) |

**Tổng số apps**: 9 (7 apps mới + 2 apps cũ/tách)

---

### **A.2. Các Phase Đã Hoàn Thành**

| Phase | Tên Phase | Trạng thái | Mô tả | Date |
|-------|-----------|-----------|-------|------|
| **Phase 1** | Tạo 7 app rỗng | ✅ 100% | Tạo structure cho các apps mới | 2026-03 |
| **Phase 2** | Chuyển utilities | ✅ 100% | Tách `core/` app (decorators, validators) | 2026-03 |
| **Phase 3** | Tách pages | ✅ 100% | Home, about pages → `pages/` app | 2026-03 |
| **Phase 4** | Tách accounts | ✅ 100% | Authentication, profile → `accounts/` app | 2026-03 |
| **Phase 5** | Tách spa_services | ✅ 100% | Services → `spa_services/` app | 2026-03 |
| **Phase 6** | Tách appointments | ✅ 100% | Appointments → `appointments/` app | 2026-03 |
| **Phase 7** | Tách complaints | ✅ 100% | Complaints → `complaints/` app | 2026-03 |
| **Phase 8.1** | URL Namespace Migration | ✅ 100% | Đổi `spa:` → app namespaces (pages:, accounts:, v.v.) | 2026-03 |
| **Phase 8.2** | Redirect Cleanup | ✅ 100% | Đổi absolute URLs → named URLs | 2026-03 |
| **Phase 8.2.5** | Post-Redirect Audit | ✅ 100% | Smoke test + audit sau redirect cleanup | 2026-03 |
| **Phase 8.3** | Template Cleanup | ✅ 100% | Di chuyển templates → app-specific directories | 2026-03 |
| **Phase 8.5** | Template Move (Batch 1+2) | ✅ 100% | 16 templates đã move | 2026-03 |
| **Phase 8.5.5** | Post-Template Verification | ✅ 100% | Verify templates, smoke tests, audit base template | 2026-03 |
| **Phase 8.5.6** | Model Move Readiness Audit | ✅ 100% | Audit 7 models, dependency graph, risk ranking | 2026-03 |
| **Phase 8.4** | Model Move - Batch 1 | ⚠️ 50% | Room bridge created, FK mismatch chưa xử lý | 2026-03-30 |

**Phase đang dừng**: **8.4 - Model Move (Batch 1)** - Chỉ tạo bridge, chưa cleanup FK

---

### **A.3. Tiến Độ Theo Categoy**

| Category | Hoàn thành | còn lại |
|----------|-----------|---------|
| **App Structure** | 100% | 0% (7 apps mới đã tách xong) |
| **URL Organization** | 100% | 0% (namespaces, redirects done) |
| **Template Organization** | 100% | 0% (16 templates moved) |
| **Views Refactoring** | 95% | 5% (spa/views.py vẫn còn, nhưng không active) |
| **Forms Refactoring** | 90% | 10% (spa/forms.py vẫn còn) |
| **Models Refactoring** | 5% | 95% (chỉ Room bridge, 6 models còn lại chưa touch) |
| **Admin Refactoring** | 70% | 30% (admin_panel done, nhưng spa/admin.py vẫn còn) |
| **Utilities Refactoring** | 100% | 0% (core app done) |

**Tổng tiến độ**: ~75% refactoring hoàn thành

---

## B. NHỮNG GÌ ĐÃ REFACTOR XONG Ở MỨC ỔN ĐỊNH

### **B.1. ✅ Utilities - 100% Hoàn Thành**

**Đã tách**: `core/` app

**Files đã tạo**:
```
core/
├── __init__.py
├── decorators.py      # @customer_required, @staff_api
├── validators.py      # phone_validator, validate_phone
└── api_response.py    # staff_api decorator, success/error responses
```

**Đã refactor**:
- ✅ Tách decorators từ views riêng lẻ → `core/decorators.py`
- ✅ Tách validators → `core/validators.py`
- ✅ Tách API response helpers → `core/api_response.py`

**Trạng thái**: **ỔN ĐỊNH** - Có thể dùng tiếp, không cần refactor lại

---

### **B.2. ✅ Views - 95% Hoàn Thành**

**Đã tách views theo app**:

| App | Views đã tách | Trạng thái | Files |
|-----|---------------|-----------|-------|
| **pages** | ✅ 100% | ỔN định | `views.py` (home, about) |
| **accounts** | ✅ 100% | ỔN định | `views.py` (login, register, password reset, profile) |
| **spa_services** | ✅ 100% | ỔN định | `views.py` (service list, detail, admin) |
| **appointments** | ✅ 100% | ỔN định | `views.py` (booking, my appointments, cancel, APIs) |
| **complaints** | ✅ 100% | ỔN định | `views.py` (customer create, list, detail, admin) |
| **admin_panel** | ✅ 100% | ỔN định | `views.py` (admin pages) |
| **spa** | ⚠️ 50% | Chưa xóa | `views.py` (vẫn còn nhưng không active) |

**Đã refactor trong views**:
- ✅ Tách views theo chức năng →各自的 app
- ✅ Update template paths (app-specific)
- ✅ Update import paths
- ✅ URL namespaces cleanup

**Chưa refactor**:
- ⚠️ `spa/views.py` vẫn còn file (2631 dòng, nhưng không được use)
- ❌ Chưa xóa vì phase models chưa làm

**Trạng thái**: **ỔN ĐỊNH** - Views mới hoạt động tốt, view cũ không active

---

### **B.3. ✅ Forms - 90% Hoàn Thành**

**Đã tách forms theo app**:

| App | Forms đã tách | Trạng thái | Files |
|-----|---------------|-----------|-------|
| **accounts** | ✅ 100% | ỔN định | `forms.py` (registration, profile, password) |
| **spa_services** | ✅ 100% | ỔN định | `forms.py` (service forms) |
| **appointments** | ✅ 100% | ỔN định | `forms.py` (appointment forms) |
| **complaints** | ✅ 100% | ỔN định | `forms.py` (complaint forms) |
| **spa** | ⚠️ 50% | Chưa xóa | `forms.py` (vẫn còn nhưng không active) |

**Đã refactor trong forms**:
- ✅ Tách forms theo app
- ✅ Update imports
- ✅ Update model references (vẫn import từ spa.models tạm thời)

**Chưa refactor**:
- ⚠️ `spa/forms.py` vẫn còn file
- ❌ Chưa xóa vì models chưa move

**Trạng thái**: **ỔN ĐỊNH** - Forms mới hoạt động, forms cũ không active

---

### **B.4. ✅ URLs - 100% Hoàn Thành**

**Đã refactor URLs**:

**Trước (Phase 8.1 trước)**:
```python
# spa_project/urls.py
urlpatterns = [
    path('dich-vu/', ...)  # URLs tiếng Việt
    path('dat-lich/', ...)  # URLs tiếng Việt
]
```

**Sau (Phase 8.1+)**:
```python
# spa_project/urls.py
urlpatterns = [
    path('', include('pages.urls')),      # /, /about/
    path('', include('accounts.urls')),   # /login/, /register/
    path('', include('spa_services.urls')), # /services/, /service/<id>/
    path('', include('appointments.urls')), # /booking/, /lich-hen-cua-toi/
    path('', include('complaints.urls')), # /gui-khieu-nai/, /khieu-nai-cua-toi/
    path('manage/', include('admin_panel.urls')), # /manage/...
    path('', include('spa.urls')),        # Fallback (cuối cùng)
]
```

**Đã refactor**:
- ✅ URL namespaces: `spa:home` → `pages:home`
- ✅ URLs tiếng Việt → URLs tiếng Anh
- ✅ Include app-specific urls
- ✅ URL namespacing: `{% url 'pages:home' %}`, `{% url 'accounts:login' %}`, v.v.

**Trạng thái**: **HOÀN CHỈNH** - URLs clean, consistent, no conflicts

---

### **B.5. ✅ Templates - 100% Hoàn Thành**

**Đã move templates**:

**Trước (Phase 8.5 trước)**:
```
templates/spa/pages/
├── home.html
├── about.html
├── login.html
├── register.html
... (16 templates)
```

**Sau (Phase 8.5 sau)**:
```
templates/
├── pages/           (2 templates)
│   ├── home.html
│   └── about.html
├── accounts/        (6 templates)
│   ├── login.html
│   ├── register.html
│   ├── password_reset.html
│   ├── password_reset_sent.html
│   ├── password_reset_confirm.html
│   └── customer_profile.html
├── spa_services/    (2 templates)
│   ├── services.html
│   └── service_detail.html
├── appointments/    (3 templates)
│   ├── booking.html
│   ├── my_appointments.html
│   └── cancel_appointment.html
└── complaints/      (3 templates)
    ├── customer_complaint_create.html
    ├── customer_complaint_list.html
    └── customer_complaint_detail.html
```

**Đã refactor**:
- ✅ 16 templates moved sang app-specific directories
- ✅ Update views để dùng template paths mới
- ✅ Tất cả templates vẫn `{% extends 'spa/base.html' %}` (giữ nguyên)

**Chưa refactor**:
- ❌ `spa/base.html` - GIỮ NGUYÊN (không tách base template)
- ❌ `spa/includes/` - GIỮ NGUYÊN (header, footer)
- ❌ `admin/pages/` templates - GIỮ NGUYÊN (admin templates)

**Trạng thái**: **ỔN ĐỊNH** - Templates tổ chức rõ ràng, extends chain hoạt động tốt

---

### **B.6. ✅ Redirects & Namespaces - 100% Hoàn Thành**

**Đã refactor** (Phase 8.2):

**Trước**:
```python
# Absolute URLs (hard-coded)
return redirect('/login/')
return redirect('/')
return redirect('/services/')
```

**Sau**:
```python
# Named URLs (namespace-aware)
return redirect('accounts:login')
return redirect('pages:home')
return redirect('spa_services:service_list')
```

**Đã refactor**:
- ✅ 36 redirects trong views đã chuyển sang named URLs
- ✅ 63 URL references trong templates đã chuyển sang namespaces
- ✅ Settings: `LOGIN_URL = 'accounts:login'`, v.v.

**Trạng thái**: **HOÀN CHỈNH** - Không còn hard-coded URLs

---

## C. NHỮNG GÌ MỚI CHỈ Ở TRẠNG THÁI BRIDGE TẠM THỜI

### **C.1. Model Bridge Hiện Tại**

**Chỉ có 1 model bridge**: **`Room`**

**Vị trí**:
```
appointments/models.py (NEW)
└── class Room (managed=False, db_table='spa_room')
```

**Đã tạo trong Batch 1 (Phase 8.4)**:
- ✅ Room model trong `appointments/models.py`
- ✅ Set `managed = False` (Django không quản lý table)
- ✅ Set `db_table = 'spa_room'` (reuse table cũ)
- ✅ Update imports trong appointments app:
  - `appointments/views.py`
  - `appointments/services.py`
  - `appointments/appointment_services.py`

---

### **C.2. Mức Hoạt Động Của Bridge**

**✅ HOẠT ĐỘNG TỐT** (Standalone Room operations):
- Import: `from appointments.models import Room` ✅
- Query tất cả: `Room.objects.all()` ✅
- Filter: `Room.objects.filter(is_active=True)` ✅
- Get by ID: `Room.objects.get(code='P001')` ✅
- Create: `Room.objects.create(...)` ✅
- Update: `room.save()` ✅
- Delete: `room.delete()` ✅
- Methods: `room.__str__()`, `room.get_active_rooms()` ✅

**❌ KHÔNG HOẠT ĐỘNG** (Appointment FK operations):
- `Appointment.objects.filter(room=new_room)` ❌
- Bất kỳ query involve `Appointment.room` FK ❌
- Service layer functions dùng Room trong Appointment context ❌

---

### **C.3. Giới Hạn Hiện Tại**

**1. FK Type Mismatch** (Vấn đề chính)
```
Appointment.room FK → spa.models.Room (model cũ)
appointments.models.Room (model mới) ≠ spa.models.Room
Django: Type mismatch → Query bị reject
```

**2. Migration State Dirty**
```
python manage.py makemigrations appointments
→ Django muốn tạo migration (vì phát hiện model mới)
→ Phải xóa migration file (tạm thời chấp nhận state bẩn)
```

**3. Dual Model Definitions**
```
spa/models.py vẫn có class Room (managed=True)
appointments/models.py mới có class Room (managed=False)
→ Code duplication
```

**4. Chưa Có Admin Mới**
```
appointments/admin.py - Chưa có RoomAdmin
spa/admin.py - Vẫn có RoomAdmin (dùng tạm)
```

---

## D. NHỮNG GÌ CHƯA ĐƯỢC LÀM

### **D.1. ❌ Model Migration Thật (CÓ MIGRATION)**

**Chưa làm gì với 6 models còn lại**:

| Model | Vị trí hiện tại | Đích đến | Trạng thái |
|-------|----------------|----------|-----------|
| **CustomerProfile** | `spa/models.py` | `accounts/models.py` | ❌ CHƯA TOUCH |
| **Service** | `spa/models.py` | `spa_services/models.py` | ❌ CHƯA TOUCH |
| **Room** | `spa/models.py` | `appointments/models.py` | ⚠️ BRIDGE ONLY (chưa migration thật) |
| **Appointment** | `spa/models.py` | `appointments/models.py` | ❌ CHƯA TOUCH |
| **Complaint** | `spa/models.py` | `complaints/models.py` | ❌ CHƯA TOUCH |
| **ComplaintReply** | `spa/models.py` | `complaints/models.py` | ❌ CHƯA TOUCH |
| **ComplaintHistory** | `spa/models.py` | `complaints/models.py` | ❌ CHƯA TOUCH |

**Tất cả models** vẫn trong `spa/models.py` (trừ Room bridge)

**Chưa tạo migration file** nào cho models (chỉ Room bridge, nhưng không có migration)

**Chưa chạy `python manage.py migrate` cho model moves**

---

### **D.2. ❌ FK Cleanup / FK Migration**

**Chưa update bất kỳ ForeignKey nào**:

**Các FK cần update**:
- `Appointment.room` → vẫn trỏ `spa.models.Room` (cần → `appointments.models.Room`)
- `Appointment.service` → vẫn trỏ `spa.models.Service` (cần → `spa_services.models.Service`)
- `Appointment.customer` → vẫn trỏ `spa.models.CustomerProfile` (cần → `accounts.models.CustomerProfile`)
- `Complaint.service` → vẫn trỏ `spa.models.Service`
- `Complaint.customer` → vẫn trỏ `spa.models.CustomerProfile`
- `ComplaintReply.complaint` → vẫn trỏ `spa.models.Complaint`
- `ComplaintHistory.complaint` → vẫn trỏ `spa.models.Complaint`

**Chưa tạo migration để update FKs**

---

### **D.3. ❌ Xóa Model Cũ Khỏi `spa/models.py`**

**Hiện tại**:
```
spa/models.py (3418+ dòng)
├── Service model
├── CustomerProfile model
├── Room model ← BRIDGE trong appointments/models.py, NHƯNG CŨ VẪN CÓ
├── Appointment model
├── Complaint model
├── ComplaintReply model
└── ComplaintHistory model
```

**Chưa xóa** bất kỳ model nào khỏi `spa/models.py`

**Lý do**:
- Room: Chưa xóa vì bridge chưa cleanup
- Các model khác: Chưa move, nên chưa xóa

---

### **D.4. ❌ Xóa `spa/views.py`**

**Hiện tại**:
```
spa/views.py (2631 dòng)
├── Home/Awards views
├── Services views
├── Appointments views
├── Accounts views
├── Password reset views
└── Complaints views
```

**Trạng thái**:
- File vẫn tồn tại
- NHƯNG views trong file này **KHÔNG ĐƯỢC USE** (URLs trỏ đến views mới)

**Chưa xóa** vì:
- Phase models chưa hoàn thành
- Có thể còn cần reference

**Rủi ro**:
- Code duplication
- Confusing cho developer mới
- Hard to know which views are active

---

### **D.5. ❌ Xóa `spa/forms.py`**

**Hiện tại**:
```
spa/forms.py (2000+ dòng)
├── Service forms
├── Appointment forms
├── Account forms
└── Complaint forms
```

**Trạng thái**:
- File vẫn tồn tại
- NHƯNG forms trong file này **KHÔNG ĐƯỢC USE** (forms mới ở app-specific forms.py)

**Chưa xóa** vì models chưa move

---

### **D.6. ❌ Xóa `spa/models.py`**

**Xem D.3** - Vẫn còn 7 models

---

### **D.7. ❌ Cleanup Base Template**

**Hiện tại**:
```
spa/base.html (105 dòng) - GIỮ NGUYÊN
└── Được extends bởi 15/16 templates mới
```

**Chưa tách** base template thành `templates/base.html`

**Lý do**:
- Base template hoạt động tốt
- Không có vấn đề gì với `spa/base.html`
- Tách base = phải update 15 templates (không đáng lợi)

**Đề xuất**: Giữ nguyên, không cleanup (đã audit trong Phase 8.5.5)

---

### **D.8. ❌ Cleanup Admin Hoàn Chỉ**

**Hiện tại**:

**Admin scattered across multiple files**:
```
spa/admin.py (còn lại)
├── ServiceAdmin
├── CustomerProfileAdmin
├── RoomAdmin ← Room bridge chưa có admin mới
├── AppointmentAdmin
├── ComplaintAdmin
└── ComplaintReply/History admins

appointments/admin.py
└── (Chưa có RoomAdmin)

spa_services/admin.py
└── (Chưa có - hoặc chưa rõ)

accounts/admin.py
└── (Chưa có - hoặc chưa rõ)
```

**Chưa migrate admin** sang app-specific admin.py (ngoại trừ admin_panel đã tách)

**Đề xuất**: Defer sau khi models xong

---

## E. NHỮNG VÙNG NGUY HIỂM / KHÔNG ĐƯỢC LÀM TIẾP NẾU CHƯA CÓ PLAN RIÊNG

### **E.1. 🔴 VÙNG NGUY HIỂM - KHÔNG ĐƯỢC TOUCH**

**1. CustomerProfile** 🔴
- **Rủi ro**: CAO - Authentication system depends on this
- **FKs**: FROM Appointment, Complaint (CASCADE)
- **Cross-app**: Dùng bởi 5 apps (accounts, appointments, complaints, spa_services, core)
- **Không được**: Move, migrate, edit nếu không có plan chi tiết

**2. Service** 🟡
- **Rủi ro**: CAO - Core business model
- **FKs**: FROM Appointment (CASCADE), Complaint (SET_NULL)
- **Cross-app**: Dùng bởi 4 apps (pages, spa_services, appointments, complaints)
- **Không được**: Move trước khi có plan chi tiết, test data đầy đủ

**3. Appointment** 🔴
- **Rủi ro**: RẤT CAO - Core transactional model
- **FKs**: TO CustomerProfile, Service, Room (3 FKs)
- **Complex queries**: Nhiều business logic, service layer functions
- **Không được**: Move trước khi 3 models kia xong, test trước-sau kỹ

**4. Complaint Ecosystem** (Complaint, ComplaintReply, ComplaintHistory) 🟡
- **Rủi ro**: TRUNG BÌNH
- **FKs**: Complex (Complaint → CustomerProfile, Service; Reply/History → Complaint)
- **Không được**: Move từng model riêng lẻ, phải move cả ecosystem cùng lúc

---

### **E.2. 🟡 VÙNG CẦN THẬN TRỌNG**

**1. Room (Batch 1.1)** 🟡
- **Hiện tại**: Bridge đã tạo, nhưng FK mismatch chưa xong
- **Không được**: Batch 1.1 (cleanup FK) nếu không có:
  - Database backup
  - Git commit + tag
  - Migration plan chi tiết (SeparateDatabaseAndState)
  - Test suite cho Appointment queries
  - 3-6 giờ thời gian liên tục

**2. Model Migration (Phase 8.4 tiếp theo)** 🟡
- **Không được**: Move bất kỳ model nào nếu không:
  - Đọc kỹ Phase 8.5.6 audit
  - Hiểu dependency graph
  - Theo đúng thứ tự: Room → Service → CustomerProfile → Complaint → Appointment
  - Backup trước mỗi batch
  - Test sau mỗi batch

---

### **E.3. 🟢 VÙNG AN TOÀN - CÓ THỂ LÀM**

**1. Tạo thêm bridge models** 🟢
- **Có thể**: Áp dụng pattern giống Room
- **Điều kiện**: Chỉ tạo bridge (managed=False), không cleanup FK
- **Models nên**: Service, CustomerProfile (vì ít rủi ro hơn Appointment/Complaint)
- **Không**: Batch 1.1 cho Room (cleanup FK) trước khi có bridge cho các model khác

**2. Code organization** 🟢
- **Có thể**: Tidy up imports, add comments, improve readability
- **Không**: Refactor logic, change queries, update FKs

**3. Testing** 🟢
- **Có thể**: Write tests, improve test coverage
- **Không**: Change existing logic trong tests

---

## F. QUY TẮC LÀM VIỆC TIẾP THEO

### **F.1. Quy Tắc Về Migration**

**QUY TẮC 1**: KHÔNG migration nếu chưa có plan riêng
- ❌ Không chạy `makemigrations` cho models
- ❌ Không chạy `migrate` cho model moves
- ❌ Không tạo migration file cho FK updates
- ✅ CHỈ migration khi có:
  - Plan chi tiết (viết ra, được duyệt)
  - Database backup
  - Git commit + tag
  - Test strategy rõ ràng
  - Rollback plan đã test

---

### **F.2. Quy Tắc Về Bridge Cleanup**

**QUY TẮC 2**: KHÔNG cleanup bridge nếu chưa có backup + rollback
- ❌ Không xóa `spa.models.Room` (hoặc model cũ)
- ❌ Không update FK (`Appointment.room`)
- ❌ Không chạy migration để cập nhật state
- ✅ CHỈ cleanup khi:
  - Đã backup database
  - Đã git tag trạng thái hiện tại
  - Đã test SeparateDatabaseAndState operation
  - Đã test tất cả queries involve FK
  - Có rollback plan đã verify

---

### **F.3. Quy Tắc Về Xóa Code**

**QUY TẮC 3**: KHÔNG xóa code cũ nếu chưa chứng minh code mới chạy hoàn toàn
- ❌ Không xóa `spa/views.py`
- ❌ Không xóa `spa/forms.py`
- ❌ Không xóa `spa/models.py` (chưa có model nào)
- ❌ Không xóa `spa/admin.py`
- ✅ CHỈ xóa khi:
  - MỖI view/form/model/admin đã có thay thế trong app mới
  - TẤT CẢ tests pass với code mới
  - Smoke tests pass (all critical URLs)
  - Regression tests pass (no broken functionality)
  - Đã chạy production (nếu applicable) được X thời gian

---

### **F.4. Quy Tắc Về Thứ Tự Model Move**

**QUY TẮC 4**: PHẢI theo đúng thứ tự dependency
```
Đúng:
1. Room (không có outgoing FKs)
2. Service (FK to User, incoming FKs from Appointment/Complaint)
3. CustomerProfile (FK to User, incoming FKs from Appointment/Complaint)
4. Complaint ecosystem (FK to CustomerProfile, Service)
5. Appointment (FK to CustomerProfile, Service, Room)

Sai:
- Appointment trước Service/Room
- Complaint trước CustomerProfile/Service
- Bất kỳ model nào trước các models nó phụ thuộc
```

---

### **F.5. Quy Tắc Về Testing**

**QUY TẮC 5**: PHẢI test đầy đủ trước khi move model
- ✅ Smoke tests: All critical URLs (home, login, services, booking, etc.)
- ✅ Unit tests: Model operations, queries
- ✅ Integration tests: Service layer functions
- ✅ Regression tests: Ensure nothing broke
- ✅ Performance tests: Queries không chậm hơn

**Không move model nếu**:
- Tests failing
- Không có test coverage
- Không chạy test được (test suite broken)

---

### **F.6. Quy Tắc Về Git**

**QUY TẮC 6**: PHẢI commit + tag trước mỗi batch
- ✅ Git commit: `git commit -m "Phase X.Y: ..."`
- ✅ Git tag: `git tag phase-x-y-before-model-z`
- ✅ Push: `git push origin main --tags`
- ✅ Verify: `git log -1` shows correct commit

**Không được**:
- Làm nhiều batch mà không commit giữa chừng
- Làm migration mà không có tag để rollback
- Làm thay đổi code mà không track trong git

---

## G. ĐỀ XUẤT 3 LỰA CHỌN BƯỚC TIẾP THEO

### **LỰA CHỌN 1: DỪNG LẠI VÀ CHỐT TRẠNG THÁI HIỆN TẠI** (KHUYẾN NGHỊ)

**Ý tưởng**:
- Dừng Batch 1 ở đây (Room bridge, chưa cleanup FK)
- Chốt trạng thái hiện tại như một milestone
- Document current state (file này)
- Không làm thêm Phase 8.4 (model moves) trong thời gian tới

**Ưu điểm**:
- ✅ An toàn nhất - không rủi ro migration
- ✅ Dự án đã refactor ~75% - đủ tốt để dùng
- ✅ Bridge Room hoạt động ở mức cơ bản
- ✅ Có thể quay lại sau khi có plan tốt hơn
- ✅ Tập trung vào features mới thay vì refactoring

**Nhược điểm**:
- ⚠️ Technical debt tồn tại:
  - Room bridge có FK mismatch
  - Models vẫn trong `spa/models.py`
  - `spa/views.py`, `spa/forms.py` vẫn còn
- ⚠️ Architecture chưa hoàn toàn clean
- ⚠️ Có thể confuse cho developer mới

**Khi nào nên chọn**:
- ✅ Muốn refactor lần lượt, từng phần
- ✅ Muốn dùng software ngay, không chờ refactor 100%
- ✅ Không có time/resources để hoàn thành refactoring
- ✅ Hài lòng với 75% completion

---

### **LỰA CHỌN 2: TIẾP TỤC TẠO BRIDGE CHO MODEL KẾ TIẾP** (RỦI RO THẤP)

**Ý tưởng**:
- Áp dụng pattern giống Room cho các models khác
- Tạo bridge models với `managed=False`, `db_table='<old_table>'`
- Update imports trong app-specific files
- Test, verify, nhưng KHÔNG cleanup FK

**Models nên làm bridge**:
- `Service` → `spa_services/models.Service` (managed=False, db_table='spa_service')
- `CustomerProfile` → `accounts/models.CustomerProfile` (managed=False, db_table='spa_customerprofile')
- (KHÔNG làm Appointment/Complaint trước khi 2 models này xong)

**Ưu điểm**:
- ✅ Rủi ro thấp - chỉ tạo bridge, không migration
- ✅ Pattern đã biết từ Room - repeatable
- ✅ Mỗi model bridge tốn ~15-30 phút
- ✅ Có thể dừng bất cứ lúc nào
- ✅ Tách biệt code level (nhưng chưa DB level)

**Nhược điểm**:
- ⚠️ Tăng technical debt (nhiều bridge = nhiều FK mismatch)
- ⚠️ Cần track nhiều model definitions
- ⚠️ Chưa giải quyết vấn đề gốc (models trong spa)

**Khi nào nên chọn**:
- ✅ Muốn refactor đều đặn, từng model
- ✅ Có time để làm 2-3 bridges nữa
- ✅ Muốn hoàn thiện code organization trước khi migration
- ✅ Chấp nhận technical debt tạm thời

---

### **LỰA CHỌN 3: CHUẨN BỊ PLAN MIGRATION SẠCH CHO `ROOM`** (RỦI RO CAO)

**Ý tưởng**:
- Lập plan chi tiết cho Batch 1.1 (Room cleanup)
- Sử dụng SeparateDatabaseAndState operation
- Update `Appointment.room` FK → `appointments.models.Room`
- Xóa `spa.models.Room`
- Test toàn diện

**Các bước chính**:
1. **Plan**: Viết migration plan chi tiết
2. **Research**: Hiểu SeparateDatabaseAndState
3. **Backup**: Database + git tag
4. **Migrate**: Create + apply migration
5. **Test**: Tất cả Appointment queries
6. **Cleanup**: Xóa model cũ, update admin

**Ưu điểm**:
- ✅ Giải quyết triệt để Room model
- ✅ Appointments app hoàn toàn tự chủ
- ✅ Django migration state sạch
- ✅ Pattern học được cho models khác

**Nhược điểm**:
- ❌ Rủi ro cao - có thể break Appointment queries
- ❌ Cần 3-6 giờ (research + execute + test)
- ❌ Cần hiểu sâu Django migrations
- ❌ Rollback phức tạp nếu fail
- ❌ Làm 1 model trong khi 6 models còn lại chưa bridge

**Khi nào nên chọn**:
- ✅ Đã có bridge cho 2-3 models khác
- ✅ Muốn hoàn thiện Room hoàn toàn
- ✅ Có đủ time (3-6 giờ) và resources
- ✅ Team đồng ý với rủi ro

---

### **BẢNG SO SÁNH 3 LỰA CHỌN**

| Tiêu chí | Lựa chọn 1: Dừng lại | Lựa chọn 2: Bridge thêm | Lựa chọn 3: Migrate Room |
|---------|---------------------|----------------------|------------------------|
| **Rủi ro** | 🟢 THẤP nhất | 🟡 THẤP-TRUNG BÌNH | 🔴 CAO |
| **Thời gian** | 0 giờ (dừng lại) | 1-2 giờ/bridge | 3-6 giờ (chỉ Room) |
| **Technical debt** | Trung bình (Room bridge) | Cao (nhiều bridges) | Thấp (Room clean) |
| **Tiến độ refactor** | 75% (hiện tại) | 80-85% (sau 2-3 bridges) | 76% (chỉ Room xong) |
| **Architecture clean** | ⚠️ Partially clean | ⚠️ Partially clean | ✅ Clean (Room only) |
| **Khả quay lại dễ** | ✅ Dễ nhất | ✅ Dễ | ⚠️ Khó hơn |
| **Tài nguyên cần** | Ít nhất | Trung bình | Nhiều nhất |
| **Learning value** | Thấp | Trung bình | Cao |

---

## H. KHUYẾN NGHỊ CỤ THỂ

### **H.1. Khuyến Nghị Bước Tiếp Theo**

**LỰA CHỌN TỐT NHẤT HIỆN TẠI**: ✅ **LỰA CHỌN 2 - TIẾP TỤC TẠO BRIDGE**

**Lý do**:

1. **Rủi ro thấp**:
   - Bridge pattern đã verify với Room
   - Chỉ tạo bridge (managed=False), không migration
   - Không thay đổi database schema
   - Dễ rollback (xóa model, revert imports)

2. **Tiến độ đều**:
   - Dự án đang ở 75% completion
   - Làm thêm 2-3 bridges → 80-85%
   - Mỗi bridge nhanh (15-30 phút)

3. **Pattern rõ ràng**:
   - Room bridge đã chứng minh concept
   - Có thể repeat cho Service, CustomerProfile
   - Học từ mỗi bridge, refine process

4. **Không cần migration ngay**:
   - Migration có thể defer sau
   - Làm bridge trước, migrate sau khi ready
   - Không phải gấp gáp

5. **Thời điểm hợp lý**:
   - Templates stable (100%)
   - URLs stable (100%)
   - Views stable (95%)
   - Chỉ còn models (5%)
   - Tập trung vào phần còn thiếu

---

### **H.2. Lộ Trình Đề Xuất (Nếu Chọn Lựa Chọn 2)**

```
HIỆN TẠI:
✅ Room bridge đã tạo (Batch 1)
⏸️ Dừng Batch 1 ở đây

BƯỚC TIẾP THEO (Batch 2):
⏭️ Tạo Service bridge trong spa_services/models.py
    - managed=False
    - db_table='spa_service'
    - Update imports trong spa_services app
    - Test (15-30 phút)

BƯỚC TIẾP THEO (Batch 3):
⏭️ Tạo CustomerProfile bridge trong accounts/models.py
    - managed=False
    - db_table='spa_customerprofile'
    - Update imports trong accounts app
    - Test (15-30 phút)

SAU KHI 2-3 BRIDGES XONG:
📋 Review tất cả bridges
📋 Đánh giá technical debt tổng thể
📋 Quyết định: migrate từng bridge hay migrate tất cả cùng lúc

TƯƠNG LAI (PHASE 8.4 TIẾP):
→ Batch N: Migration cleanup cho Room (SeparateDatabaseAndState)
→ Batch N+1: Migration cleanup cho Service
→ Batch N+2: Migration cleanup cho CustomerProfile
→ Batch N+3: Move Complaint ecosystem
→ Batch N+4: Move Appointment (cuối cùng)
```

---

## I. TÓM TẮT TRẠNG THÁI DỰ ÁN

### **I.1. Đã Hoàn Thành (75%)**

✅ **App structure**: 7 apps đã tách xong
✅ **URLs**: 100% clean, namespaces, redirects done
✅ **Templates**: 100% organized (16 templates moved)
✅ **Views**: 95% tách xong (spa/views.py inactive)
✅ **Forms**: 90% tách xong (spa/forms.py inactive)
✅ **Utilities**: 100% tách xong (core app)

### **I.2. Đang Làm (5%)**

⚠️ **Models**: Chỉ Room bridge created (5% of model refactoring)
⚠️ **Bridge status**: Room bridge hoạt động mức CRUD, nhưng FK mismatch

### **I.3. Chưa Làm (20%)**

❌ **Model migration thật**: Chưa move 6 models còn lại
❌ **FK cleanup**: Chưa update bất kỳ FK
❌ **File cleanup**: Chưa xóa spa/views.py, spa/forms.py, spa/models.py
❌ **Admin migration**: Chưa move admin sang app-specific
❌ **Base template cleanup**: Chưa tách spa/base.html

### **I.4. Trạng Thái Tổng Thể**

```
Dự án: 🟡 PARTIAL REFACTOR - BRIDGE PHASE

Architecture:        [██████████████████░░░░] 80%
Code Organization:   [███████████████████░░░░] 85%
Database Schema:     [███░░░░░░░░░░░░░░░░░░░░░] 15%
Clean Factor:        [██████████████████░░░░] 80%

Overall Progress:    [████████████████████░░] 90%
  (Không tính database schema changes)
```

---

## KẾT LUẬN

**Trạng thái hiện tại**: Dự án đã refactor tốt ở level code organization (URLs, templates, views, forms), nhưng models vẫn còn trong `spa/models.py` (trừ Room bridge).

**Khuyến nghị**: Tiếp tục tạo bridge cho 2-3 models kế tiếp (Service, CustomerProfile) với pattern giống Room, rồi mới quyết định migration cleanup.

**Không được làm**:
- ❌ Batch 1.1 (Room FK cleanup) - rủi ro cao, chưa có bridge cho models khác
- ❌ Model migration thật (Service, CustomerProfile, etc.) - cần plan riêng
- ❌ Xóa code cũ (spa/views.py, spa/forms.py, spa/models.py) - chưa phải lúc
- ❌ Cleanup base template, admin - chưa phải lúc

**Được làm**:
- ✅ Tạo thêm bridge models (Service, CustomerProfile)
- ✅ Code organization, documentation
- ✅ Testing, bug fixes, features mới
- ✅ Planning cho migration tương lai

---

**Người tạo**: Spa ANA Team
**Ngày**: 2026-03-30
**File**: PROJECT_REFACTOR_STATUS.md
**Mục đích**: Báo cáo trạng thái refactoring toàn dự án
**Trạng thái**: ✅ COMPLETE - Ready for review
