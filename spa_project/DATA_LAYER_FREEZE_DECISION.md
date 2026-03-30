# DATA LAYER FREEZE DECISION - QUYẾT ĐỊNH TẠM DỪNG DATA-LAYER REFACTOR

**Ngày quyết định**: 2026-03-30
**Trạng thái**: 🧊 **FROZEN - TẠM ĐÓNG BĂNG**
**Loại quyết định**: Dừng refactoring data-layer, giữ nguyên hiện trạng
**Thời hạn**: Không thời hạn (cho đến khi có quyết định mới)
**Người duyệt**: Spa ANA Project Owner

---

## A. QUYẾT ĐỊNH CHÍNH THỨC: TẠM DỪNG DATA-LAYER REFACTOR

### **A.1. Quyết Định**

**Ngày 30 tháng 3 năm 2026, Spa ANA project quyết định**:

✅ **TẠM DỪNG MỌI HOẠT ĐỘNG LIÊN QUAN ĐẾN DATA-LAYER REFACTOR**

**Scope của quyết định này**:
- ❌ KHÔNG tạo bridge model mới (Service, CustomerProfile, v.v.)
- ❌ KHÔNG migration model thật (có migration file)
- ❌ KHÔNG cleanup ForeignKey (update FK paths)
- ❌ KHÔNG xóa model cũ khỏi `spa/models.py`
- ❌ KHÔNG xóa `spa/views.py`, `spa/forms.py`, `spa/admin.py`
- ❌ KHÔNG cleanup base template (`spa/base.html`)

**Lý do chính**:
1. **Data-layer refactoring đã đủ**: 75% dự án đã refactor (app, views, forms, templates, URLs)
2. **Room bridge đã cho thấy**: Bridge approach hoạt động NHƯNG có giới hạn (FK type mismatch, technical debt)
3. **Service, CustomerProfile phức tạp hơn**: Không nên tiếp tục bridge
4. **Business priority**: Cần focus vào features, bug fixes, customer satisfaction
5. **Team readiness**: Chưa có đủ expertise migration để làm ngay

---

### **A.2. Phạm Vi Quyết Định**

**ĐÁP DỤNG CHO**:
- ✅ Tất cả thay đổi liên quan đến **database schema** (models, migrations, FKs)
- ✅ Tất cả thay đổi liên quan đến **data-layer architecture** (model moves, FK updates)

**KHÔNG ĐÁP DỤNG CHO**:
- ✅ Feature development (thêm features mới)
- ✅ Bug fixes (sửa lỗi)
- ✅ Code-level refactors (tổ chức code, cleanup imports, v.v.)
- ✅ Performance improvements (không liên quan schema)
- ✅ Documentation (cập nhật docs, thêm comments)
- ✅ Testing (viết tests, fix tests)
- ✅ Small cleanups (formatting, rename variables, v.v.)

---

### **A.3. Từ Này ("FREEZE PERIOD")**

**Từ ngày 30-03-2026 đến khi có quyết định mới**:

**KHÔNG được phép**:
```
❌ Tạo model mới trong app-specific models.py (ngoại trừ Room bridge)
❌ Chạy makemigrations cho models
❌ Chạy migrate cho model changes
❌ Update ForeignKey paths (Appointment.room, Appointment.service, v.v.)
❌ Xóa model khỏi spa/models.py
❌ Xóa views/forms/admin khỏi spa/
❌ Cleanup base template spa/base.html
❌ Bất kỳ thay đổi nào liên quan đến database schema
```

**Được phép**:
```
✅ Thêm features mới (business logic, UI, UX)
✅ Sửa bugs
✅ Code organization (tổ chức imports, thêm comments, v.v.)
✅ Performance optimization (queries, caching, indexes - không schema)
✅ Documentation
✅ Testing
✅ Deployment (production)
✅ Maintenance tasks
```

---

## B. NHỮNG GÌ ĐÃ HOÀN THÀNH VÀ CÓ THỂ SỬ DỤNG ỔN ĐỊNH

### **B.1. ✅ App Structure - 100% HOÀN THÀNH**

**Đã tách**:
- ✅ 9 apps (7 apps mới + 2 apps cũ/tách)
- ✅ `core` - utilities (decorators, validators, api_response)
- ✅ `pages` - static pages (home, about)
- ✅ `accounts` - authentication, customer profile
- ✅ `spa_services` - services management
- ✅ `appointments` - appointment booking, management
- ✅ `complaints` - customer complaints
- ✅ `admin_panel` - admin pages

**Trạng thái**: **ỔN ĐỊNH - SỬ DỤNG TIN CẬY**

---

### **B.2. ✅ URLs & Namespaces - 100% HOÀN THÀNH**

**Đã refactor**:
- ✅ URL namespaces: `spa:home` → `pages:home`, v.v.
- ✅ URLs tiếng Việt → URLs tiếng Anh
- ✅ App-specific urls.py files
- ✅ Named URLs trong views và templates

**Trạng thái**: **ỔN ĐỊNH - SỬ DỤNG TIN CẬY**

**Ví dụ**:
```python
# Trong templates:
{% url 'pages:home' %}
{% url 'accounts:login' %}
{% url 'spa_services:service_list' %}

# Trong views:
return redirect('pages:home')
return redirect('accounts:customer_profile')
```

---

### **B.3. ✅ Templates - 100% HOÀN THÀNH**

**Đã move**:
- ✅ 16 templates sang app-specific directories
  - `templates/pages/` (2 templates)
  - `templates/accounts/` (6 templates)
  - `templates/spa_services/` (2 templates)
  - `templates/appointments/` (3 templates)
  - `templates/complaints/` (3 templates)

**Trạng thái**: **ỔN ĐỊNH - SỬ DỤNG TIN CẬY**

**Extends chain**:
```
templates/pages/home.html
templates/accounts/login.html
templates/spa_services/services.html
...
└── {% extends 'spa/base.html' %} (giữ nguyên)
```

---

### **B.4. ✅ Views - 95% HOÀN THÀNH**

**Đã tách**:
- ✅ `pages/views.py` - home, about
- ✅ `accounts/views.py` - login, register, profile
- ✅ `spa_services/views.py` - service list, detail
- ✅ `appointments/views.py` - booking, appointments
- ✅ `complaints/views.py` - complaints
- ✅ `admin_panel/views.py` - admin pages

**Chưa tách** (nhưng không active):
- ⚠️ `spa/views.py` - vẫn còn file nhưng không được use

**Trạng thái**: **ỔN ĐỊNH - VIEWS MỚI HOẠT ĐỘNG TỐT, VIEW CŨ KHÔNG ACTIVE**

---

### **B.5. ✅ Forms - 90% HOÀN THÀNH**

**Đã tách**:
- ✅ `accounts/forms.py` - registration, profile, password
- ✅ `spa_services/forms.py` - service forms
- ✅ `appointments/forms.py` - appointment forms
- ✅ `complaints/forms.py` - complaint forms

**Chưa tách** (nhưng không active):
- ⚠️ `spa/forms.py` - vẫn còn file nhưng không được use

**Trạng thái**: **ỔN ĐỊNH - FORMS MỚI HOẠT ĐỘNG TỐT, FORM CŨ KHÔNG ACTIVE**

---

### **B.6. ✅ Utilities - 100% HOÀN THÀNH**

**Đã tách**:
- ✅ `core/decorators.py` - @customer_required, @staff_api
- ✅ `core/validators.py` - phone_validator
- ✅ `core/api_response.py` - API response helpers

**Trạng thái**: **ỔN ĐỊNH - SỬ DỤNG TIN CẬY, KHÔNG CẦN THAY ĐỔI**

---

### **B.7. ✅ Redirects - 100% HOÀN THÀNH**

**Đã refactor**:
- ✅ 36 redirect statements: absolute URLs → named URLs
- ✅ Settings: `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`
- ✅ 63 URL references trong templates: `spa:url_name` → `app:url_name`

**Trạng thái**: **ỔN ĐỊNH - KHÔNG CÒN HARD-CODED URLs, ALL CLEAN**

---

## C. NHỮNG GÌ ĐANG Ở TRẠNG THÁI BRIDGE TẠM (`ROOM`)

### **C.1. `Room` Model Bridge**

**Vị trí hiện tại**:
```python
# File: appointments/models.py
class Room(models.Model):
    ...
    class Meta:
        db_table = 'spa_room'     # Reuse existing table
        managed = False             # Django không quản lý
        ...

# File: spa/models.py (VẪN CÒN)
class Room(models.Model):
    ...
    class Meta:
        db_table = 'spa_room'     # Cùng bảng
        managed = True              # Django quản lý
        ...
```

**Trạng thái**: **BRIDGE TẠM THỜI - NHƯNG CÓ GIỚI HẠN**

---

### **C.2. Những Gì Hoạt Động Với Room Bridge**

**✅ HOẠT ĐỘNG TỐT**:
- Import: `from appointments.models import Room` ✅
- Query tất cả: `Room.objects.all()` ✅
- Filter: `Room.objects.filter(is_active=True)` ✅
- CRUD: Create, Read, Update, Delete ✅
- Methods: `room.__str__()`, `room.get_active_rooms()` ✅

**Ứng dụng**:
- Dùng cho standalone Room operations
- Dùng trong appointments app (nhưng không qua Appointment FK)

---

### **C.3. Những Gì Chưa Hoạt Động Với Room Bridge**

**❌ KHÔNG HOẠT ĐỘNG**:
- `Appointment.objects.filter(room=new_room_instance)` ❌
- Bất kỳ query qua `Appointment.room` ForeignKey ❌
- Service layer functions involve Appointment queries ❌

**Giới hạn**:
- **FK type mismatch**: `Appointment.room` FK vẫn trỏ về `spa.models.Room`
- Dùng `appointments.models.Room` instance trong Appointment queries → Lỗi

**Workaround**:
- Trong appointments app, vẫn dùng `spa.models.Room` cho Appointment queries
- Chỉ dùng `appointments.models.Room` cho standalone Room operations

---

### **C.4. Trạng Thái Bridge Room**

**Được phép**:
- ✅ Giữ nguyên bridge Room như hiện tại
- ✅ Dùng `appointments.models.Room` cho standalone Room operations
- ✅ Dùng `spa.models.Room` cho Appointment queries (workaround)

**Không được phép**:
- ❌ Cleanup Room bridge (Batch 1.1)
- ❌ Update Appointment.room FK → `appointments.models.Room`
- ❌ Xóa `spa.models.Room`
- ❌ Tạo migration cho Room

**Đóng băng**: Room bridge giữ nguyên hiện tại, không thay đổi.

---

## D. NHỮNG GÌ TUYỆT ĐỐI KHÔNG LÀM TIẾP NẾU CHƯA CÓ PLAN RIÊNG

### **D.1. ❌ KHÔNG TẠO BRIDGE MODEL MỚI**

**Không được phép**:
- ❌ Tạo `Service` bridge trong `spa_services/models.py`
- ❌ Tạo `CustomerProfile` bridge trong `accounts/models.py`
- ❌ Tạo `Appointment` bridge trong `appointments/models.py`
- ❌ Tạo `Complaint` bridge trong `complaints/models.py`
- ❌ BẤT KỲ bridge model nào khác

**Lý do**:
- Room bridge đã cho thấy: bridge có giới hạn (FK type mismatch)
- Service, CustomerProfile phức tạp hơn Room nhiều
- Technical debt tăng với mỗi bridge thêm
- Không nên tiếp tục hướng bridge-first

---

### **D.2. ❌ KHÔNG MIGRATION MODEL THẬT**

**Không được phép**:
- ❌ Chạy `makemigrations` cho models
- ❌ Chạy `migrate` cho model changes
- ❌ Tạo migration file cho Service, CustomerProfile, v.v.
- ❌ Update ForeignKey paths (Appointment.room, Appointment.service, v.v.)
- ❌ Di chuyển model từ `spa/models.py` sang app-specific models.py

**Lý do**:
- Migration là **hoạt động rủi ro cao**
- Cần expertise Django migrations (team chưa có)
- Cần planning chi tiết (chưa có)
- Cần thời dedicate (team cần focus business)

---

### **D.3. ❌ KHÔNG CLEANUP CODE CŨ**

**Không được phép**:
- ❌ Xóa `spa/models.py`
- ❌ Xóa `spa/views.py`
- ❌ Xóa `spa/forms.py`
- ❌ Xóa `spa/admin.py`
- ❌ Xóa các templates cũ trong `spa/pages/` (nếu còn)

**Lý do**:
- Models vẫn trong `spa/models.py` (Service, CustomerProfile, Appointment, Complaint, v.v.)
- Xóa file = break code
- Models cần phải migrate TRƯỚ khi cleanup

**Vẫn giữ nguyên**:
- ✅ `spa/models.py` - 7 models vẫn còn (trừ Room bridge)
- ✅ `spa/views.py` - vẫn còn nhưng không active
- ✅ `spa/forms.py` - vẫn còn nhưng không active
- ✅ `spa/admin.py` - vẫn active (admin cho các models)

---

### **D.4. ❌ KHÔNG CLEANUP BASE TEMPLATE**

**Không được phép**:
- ❌ Tách `spa/base.html` thành `templates/base.html`
- ❌ Tách `spa/includes/` (header, footer) thành templates riêng
- ❌ Update extends clauses trong templates (15+ templates)

**Lý do**:
- `spa/base.html` hoạt động tốt
- Không có vấn đề gì với base template hiện tại
- Tách base = update 15+ templates = nhiều rủi ro
- Benefit không đáng lợi với effort cần thiết

**Giữ nguyên**:
- ✅ `spa/base.html` - base template
- ✅ `spa/includes/header.html` - header component
- ✅ `spa/includes/footer.html` - footer component
- ✅ Tất cả templates vẫn `{% extends 'spa/base.html' %}`

---

### **D.5. ❌ KHÔNG CLEANUP ADMIN**

**Không được phép**:
- ❌ Di chuyển `ServiceAdmin` từ `spa/admin.py` sang `spa_services/admin.py`
- ❌ Di chuyển `CustomerProfileAdmin` sang `accounts/admin.py`
- ❌ Di chuyển `RoomAdmin` sang `appointments/admin.py`
- ❌ Di chuyển `AppointmentAdmin` sang `appointments/admin.py`

**Lý do**:
- Admin vẫn hoạt động tốt trong `spa/admin.py`
- Models chưa move → admin chưa thể move
- Migration admin = rủi ro cao

**Giữ nguyên**:
- ✅ `spa/admin.py` - vẫn quản lý tất cả models
- ✅ Admin panel hoạt động tốt

---

### **D.6. ❌ KHÔNG BẤT KỲ THAY ĐỔI SCHEMA

**Không được phép**:
- ❌ Thêm field mới vào models
- ❌ Xóa field khỏi models
- ❌ Thay đổi field types
- ❌ Thay đổi field names
- ❌ Thêm index, unique constraint (trừ khi an toàn tuyệt đối)
- ❌ Drop table, rename table
- ❌ Bất kỳ thay đổi nào liên quan đến database schema

**Lý do**:
- **TẤT CẢ database schema changes ĐƯỢC ĐÓNG BĂNG**
- Thay đổi schema = cần migration
- Migration = rủi ro cao
- Không có kế hoạch migration → không được làm

**Được phép** (nếu an toàn):
- ✅ Add comments vào models
- ✅ Add methods vào models (business logic)
- ✅ Add properties (calculated fields)
- ✅ Thay đổi `verbose_name`, `help_text` (metadata only, không schema)

---

### **D.7. ❌ KHÔNG XÓA FILE CŨ (CHƯA THỜI ĐIỀU KỲ)

**Không được phép**:
- ❌ Xóa `spa/models.py` (vẫn còn 6 models)
- ❌ Xóa `spa/views.py` (vẫn còn nhưng không active)
- ❌ Xóa `spa/forms.py` (vẫn còn nhưng không active)
- ❌ Xóa `spa/admin.py` (vẫn active)

**Lý do**:
- Models vẫn còn → không thể xóa
- Views/forms cũ không active → nhưng tồn tại để reference
- Xóa = break code, hard to recover

---

## E. NHỮNG LOẠI THAY ĐỔI VẪN ĐƯỢC PHÉP TRONG GIAI ĐOẠN ĐÓNG BĂNG

### **E.1. ✅ FEATURE DEVELOPMENT (ĐƯỢC KHUYẾN KHÍCH)**

**Được phép**:
- ✅ Thêm features mới cho customers
  - Booking enhancements
  - Payment integration
  - Email notifications
  - SMS notifications
  - Customer dashboard improvements
  - Review/rating system
- ✅ Thêm features cho admin
  - Dashboard improvements
  - Reporting features
  - Data export features
  - Admin workflow enhancements
- ✅ Thêm features cho staff
  - Appointment scheduling
  - Staff management
  - Room management enhancements

**Quy tắc**:
- Feature development **THƯỜNG BUSINESS LOGIC**, KHÔNG data schema
- Nếu feature cần thay đổi schema → feature request phải defer đến sau freeze period

---

### **E.2. ✅ BUG FIXES (ĐƯỢC KHUYẾN KHÍCH)**

**Được phép**:
- ✅ Sửa bugs trong views
- ✅ Sửa bugs trong forms
- ✅ Sửa bugs trong templates
- ✅ Sửa bugs trong business logic
- ✅ Sửa bugs trong queries
- ✅ Sửa bugs trong validators
- ✅ Sửa bugs trong decorators

**Quy tắc**:
- Bug fixes **THƯỜNG CODE LOGIC**, KHÔNG schema
- Nếu bug cần schema change → phải defer

---

### **E.3. ✅ CODE ORGANIZATION (MỨC ĐỘ AN TOÀN)**

**Được phép**:
- ✅ Tổ chức imports (đã tốt)
- ✅ Thêm comments vào code
- ✅ Format code (Prettier, Black, v.v.)
- ✅ Rename variables (cẩn thận)
- ✅ Extract functions/methods (refactor code structure)
- ✅ Add docstrings
- ✅ Remove dead code (nếu chắc chắn không dùng)

**Quy tắc**:
- Code organization KHÔNG ảnh hưởng database
- Chỉ improve code readability, maintainability

---

### **E.4. ✅ PERFORMANCE OPTIMIZATIONS (KHÔNG SCHEMA)**

**Được phép**:
- ✅ Optimize queries (select_related, prefetch_related)
- ✅ Add caching (Redis, Memcached)
- ✅ Optimize templates (fragment caching, template optimization)
- ✅ Add indexes (CẦN THẬN TRỌNG - indexes không phải schema change)
- ✅ Query optimization (remove N+1 queries)

**Quy tắc**:
- Performance improvements KHÔNG liên quan schema changes
- Cần test kỹ trước khi deploy

---

### **E.5. ✅ DOCUMENTATION**

**Được phép**:
- ✅ Cập nhật README files
- ✅ Thêm comments vào code
- ✅ Viết API documentation
- ✅ Viết developer guides
- ✅ Update architecture diagrams

---

### **E.6. ✅ TESTING**

**Được phép**:
- ✅ Viết unit tests
- ✅ Viết integration tests
- ✅ Viết E2E tests
- ✅ Fix broken tests
- ✅ Improve test coverage

---

### **E.7. ✅ DEPLOYMENT & MAINTENANCE**

**Được phép**:
- ✅ Deploy lên production
- ✅ Database backups (regular)
- ✅ Server maintenance
- ✅ Dependency updates (pip packages)
- ✅ Security patches

---

### **E.8. ✅ SMALL CLEANUPS (AN TOÀN)**

**Được phép**:
- ✅ Remove unused imports
- ✅ Remove dead code (functions không được gọi)
- ✅ Format code consistently
- ✅ Lint fixes
- ✅ Type hints additions
- ✅ Variable renames (local scope)

---

## F. ĐIỀU KIỀN ĐỂ TRONG TƯƠNG MỞ LẠI MIGRATION MODEL

### **F.1. Khi Nào Có Thể Mở Lại Data-Layer Refactor?**

**NGUYÊN NHẤT THỦ (CÓ THỂ XEM XÉT LẠI)**:

**Option 1**: **Khi dự án đã STABLE**
- Business features hoàn thiện
- Revenue ổn định
- Team size tăng
- Need better scalability

**Option 2**: **Khi TEAM CÓ EXPERTISE**
- Team member(s) đã học Django migrations
- Có kinh nghiệm production migrations
- Confident với risk management

**Option 3**: **Khi CÓ NGÂN BỘ, TÀI NGUYÊN**
- Stakeholder approve budget cho refactoring
- Timeline rõ ràng (3-6 tháng dedicate)
- Resources充足的 (time, people)

**Option 4**: **Khi có TECHNICAL DEBT BLOCKING FEATURES**
- Không thể add features vì schema constraints
- Performance issues do schema badly designed
- Hard to maintain due to schema complexity

---

### **F.2. Điều Kiện BẮT BUỘC TRƯỚC MỞ LẠI**

**Trước khi mở lại data-layer refactor**:

**1. ✅ COMPREHENSIVE AUDIT**
- Audit lại toàn bộ models
- Audit lại toàn bộ FK relationships
- Audit lại toàn bộ queries involve models
- Document current state (update PROJECT_REFACTOR_STATUS.md)

**2. ✅ MIGRATION PLAN CHI TIẾT**
- Plan từng model: Service → CustomerProfile → Complaint → Appointment
- Document từng bước migration
- Document rollback strategy cho từng bước
- Timeline rõ ràng

**3. ✅ TEAM READINESS**
- Team đã học Django migrations
- Team đã practice migration trên test project
- Team confident với risk
- Team allocate đủ time (3-6 tháng)

**4. ✅ ENVIRONMENT READINESS**
- Staging environment sẵn sàng
- Backup strategy rõ ràng
- Test suite comprehensive
- Monitoring/logging đầy đủ

**5. ✅ STAKEHOLDER BUY-IN**
- Management/leadership approve plan
- Business stakeholders understand impact
- Timeline communicated clearly
- Risk accepted by all parties

---

### **F.3. QUY TRÌNH MỞ LẠI SAU KHI MỞ CÁI**

**QUY TRÌNH 1: MIGRATION-FIRST APPROACH**
```
KHÔNG bridge thêm models
Migrate trực tiếp models:
- Tạo migration file (SeparateDatabaseAndState)
- Apply migration
- Update FKs
- Delete old model
→ Clean architecture ngay
```

**QUY TRÌNH 2: MODELS MIGRATE ORDER**
```
Thứ tự (phải tuân thủ):
1. Room (cleanup existing bridge, delete old model)
2. Service (migrate từ spa → spa_services)
3. CustomerProfile (migrate từ spa → accounts)
4. Complaint ecosystem (migrate từ spa → complaints)
5. Appointment (migrate từ spa → appointments, CUỐI CÙNG)
```

**QUY TRÌNH 3: TEST DRIVEN**
```
Trước khi migrate model:
- Write tests cho model
- Test queries involve FKs
- Test service layer functions
- Test admin operations
- Test ALL code paths
→ Tests pass → Migrate
```

**QUY TRÌNH 4: INCREMENTAL MIGRATION**
```
Migrate từng model:
- Batch 1: Room migration
- Test → Verify → Deploy
- Batch 2: Service migration
- Test → Verify → Deploy
- ...
→ Mỗi batch independent, rollback được nếu cần
```

---

### **F.4. Checklist Trước Khi Mở Lại**

**Checklist phải complete**:
- [ ] Comprehensive audit done
- [ ] Migration plan written
- [ ] Team trained on migrations
- [ ] Team practiced on test project
- [ ] Stakeholder approval obtained
- [ ] Timeline committed (3-6 tháng)
- [ ] Resources allocated
- [ ] Staging environment ready
- [ ] Backup strategy documented
- [ ] Rollback strategy tested
- [ ] Test suite comprehensive
- [ ] All conditions above satisfied

**Nếu ANY condition not met**:
→ KHÔNG mở lại data-layer refactor
→ Continue freeze period

---

## G. KHUYẾN NGHĨ CHO DEVELOPER KHÁC KHI ĐỌC CODEBASE HIỆN TẠI

### **G.1. HIỂU THỤ NGUYÊN: DỰ ÁN BỀ CODEBASE HIỆN TẠI**

**Người mới vào project sẽ thấy**:
```
spa_project/
├── accounts/          ✅ App tách riêng, clean
├── admin_panel/       ✅ App tách riêng, clean
├── appointments/      ✅ App tách riêng, clean
│   └── models.py    ⚠️ Room bridge (managed=False)
├── complaints/        ✅ App tách riêng, clean
├── core/              ✅ App tách riêng, clean
├── pages/             ✅ App tách riêng, clean
├── spa_services/      ✅ App tách riêng, clean
└── spa/               ⚠️ App cũ, chứa models
    ├── models.py     ⚠️ 7 models (Service, CustomerProfile, etc.)
    ├── views.py       ⚠️ Views cũ (không active)
    ├── forms.py       ⚠️ Forms cũ (không active)
    └── admin.py       ⚠️ Admin cũ (vẫn active)
```

**Confusion points**:
- "Tại sao có 2 models Room?" (spa.models.Room, appointments.models.Room)
- "Tại sao models vẫn trong spa/models.py?" (Service, CustomerProfile, etc.)
- "Tại sao views/forms cũ vẫn còn?" (không active nhưng tồn tại)
- "Tại sao không xóa spa/app?" (chưa migrate models)

---

### **G.2. GIẢI THÍCH TRẠNG THÁI CHO DEVELOPER MỚI**

**Gợi ý cho lead dev/senior dev**:

**1. EXPLAIN ARCHITECTURE**
```
"Chào [Tên],

Dự án đã refactor một phần, nhưng data-layer (models, database) đang tạm đóng băng.

ĐÃ refactor (75%):
- App structure: 9 apps, tách theo chức năng
- URLs: Clean, namespaces
- Templates: Organized theo app
- Views/Forms: Tách theo app, views/forms cũ không active

Chưa refactor (25%):
- Models: Vẫn trong spa/models.py (6 models)
- Room: Có bridge tạm trong appointments/models.py
- Database schema: Không thay đổi

TẠM DỪNG: Focus business features, database schema giữ nguyên."
```

**2. DOCUMENT FILE STRUCTURE**
```markdown
# FILE STRUCTURE GUIDE

## Apps tách riêng (7 apps)
- accounts/ - Authentication, customer profile
- admin_panel/ - Admin pages
- appointments/ - Booking, appointments management
- ...
- Khi làm features liên quan accounts → dùng accounts app
- Khi làm features liên quan appointments → dùng appointments app

## App cũ (spa/)
- ChứA models: Service, CustomerProfile, Appointment, Complaint, etc.
- CHỨ XÓA models.py/views.py/forms.py
- Dùng khi: Cần reference models cũ, hoặc legacy queries
```

**3. WORKFLOW GUIDE**
```
LÀM FEATURE MỚI:
1. Xác định feature thuộc app nào (accounts, appointments, etc.)
2. Vào app đó, tạo views/forms/templates
3. Nếu cần models → dùng spa.models (tạm thời)
4. KHÔNG tạo models mới trong app-specific models.py
5. KHÔNG migrate models

VÍ DỤ:
- Feature "thêm review cho appointment" → appointments app
- Feature "thêm notification cho complaint" → complaints app
- Feature "thêm field vào Service model" → KHÔNG LÀM (schema change)
```

---

### **G.3. QUY TẮC LÀM VIỆC CẦN THẬN

**✅ CÓ THỂ LÀM**:
```python
# 1. Thêm business logic trong views
def booking(request):
    # Logic hiện tại
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Thêm validation logic mới
            if is_peak_hour(request.POST['time']):
                messages.warning('Giờ cao, phí phụ thu')
            # ... rest of logic

# 2. Add service layer functions
def calculate_appointment_cost(service, appointment):
    """Calculate total cost"""
    base_price = service.price
    if appointment.is_weekend:
        return base_price * 1.2
    return base_price

# 3. Add utility functions
def format_currency(amount):
    """Format VND currency"""
    return f"{amount:,.0f} VND"

# 4. Add decorators
def login_required_json(view_func):
    """Custom decorator for JSON login check"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

# 5. Improve queries
# BAD:
services = Service.objects.all()  # N+1 queries
for service in services:
    appointments = service.appointments.all()  # N+1 queries

# GOOD:
services = Service.objects.prefetch_related('appointments')
# No N+1 queries
```

---

### **G.4. NGHIÊM CÁC KHÔNG NÊN LÀM**

**❌ KHÔNG NÊN LÀM**:

**1. Model changes**:
```python
# ❌ KHÔNG
class Service(models.Model):
    new_field = models.CharField(...)  # Schema change
```

**2. ForeignKey changes**:
```python
# ❌ KHÔNG
# In Appointment model
room = models.ForeignKey('appointments.models.Room', ...)  # FK path change
```

**3. Deleting files**:
```python
# ❌ KHÔNG
# Delete spa/models.py
# Delete spa/views.py
# Delete spa/forms.py
```

**4. Creating new models**:
```python
# ❌ KHÔNG
# In spa_services/models.py
class Service(models.Model):  # Create new Service
    ...
```

**5. Migration operations**:
```bash
# ❌ KHÔNG
python manage.py makemigrations  # For model changes
python manage.py migrate            # For model changes
```

---

### **G.5. NẾU CÓ THẮC - HỎI SENIOR DEV**

**NẾU developer mới thắc mắc**:

**Câu hỏi**: "Tại sao có 2 models Room?"

**Trả lời**:
```
"Đây là **bridge tạm thời**:
- appointments.models.Room = model mới trong app riêng
- spa.models.Room = model cũ
- Cả hai trỏ vào cùng bảng database spa_room
- Mục đích: Tách code organization, nhưng chưa migrate database
- Giới hạn: Không dùng appointments.models.Room trong Appointment queries
- Workaround: Dùng spa.models.Room cho Appointment queries
- Future: Khi database được migrate, chỉ còn appointments.models.Room
```

**Câu hỏi**: "Tại sao không xóa spa/models.py?"

**Trả lời**:
```
"spa/models.py vẫn còn 6 models:
- Service, CustomerProfile, Appointment
- Complaint, ComplaintReply, ComplaintHistory
- Không thể xóa vì:
  1. Models chưa migrate sang apps riêng
  2. ForeignKey relationships vẫn trỏ về spa.models
  3. Database schema chưa thay đổi
- Dự án đang tạm dừng data-layer refactor
- Focus vào business features trong thời gian tới
```

**Câu hỏi**: "Tôi có thể thêm field vào Service không?"

**Trả lời**:
```
"KHÔNG - schema changes bị đóng băng.

THẬ TRƯỜC:
- Thêm method vào Service model (business logic)
- Thêm property vào Service model (calculated field)
- Add service layer functions

KHÔNG THỂ TRƯỜC:
- Add/remove field (schema change)
- Change field type (schema change)
- Add/remove FK (schema change)

Nếu CẦN thiết: Hãy thảo luận với team lead."
```

---

### **G.6. THAM KHẢO TÀI LIỆU**

**Documents đã có**:
- ✅ `BRIDGE_STATUS_SUMMARY.md` - Room bridge status
- ✅ `PROJECT_REFACTOR_STATUS.md` - Project refactor status
- ✅ `PHASE 8.4 PLAN ONLY - BATCH 2 (SERVICE)` - Service audit
- ✅ `PHASE 8.6 PLAN ONLY - MIGRATION STRATEGY COMPARISON` - Strategy comparison
- ✅ `DATA_LAYER_FREEZE_DECISION.md` - (file này)

**Developer nên đọc**:
1. `PROJECT_REFACTOR_STATUS.md` - Hiểu overview
2. `BRIDGE_STATUS_SUMMARY.md` - Hiểu Room bridge
3. File này - Hiểu quy tắc freeze period

---

## H. SUMMARY & FINAL WORDS

### **H.1. TÓM TẮT QUYẾT ĐỊNH**

**QUYẾT ĐỊNH CHÍNH THỨC**:
- **TẠM DỪNG data-layer refactor** (models, migrations, FKs, schema changes)
- **Giữ nguyên hiện trạng** (75% refactored, 25% frozen)
- **Focus business value** (features, bug fixes, customer satisfaction)

**Được phép**:
- ✅ Features, bug fixes, code organization, performance (không schema), docs, tests

**Không được phép**:
- ❌ Bridge model mới
- ❌ Migration model thật
- ❌ Cleanup code cũ (spa/models.py, spa/views.py, spa/forms.py)
- ❌ Schema changes

---

### **H.2. Current State Summary**

**Dự án Spa ANA**:
- **Overall Progress**: 75% refactored
- **Code Organization**: 90% clean (app-level)
- **Database Schema**: 100% frozen
- **Models State**: Room bridge (tạm), others trong spa/models.py
- **Architecture**: Clean enough để continue development

**Trạng thái**: **SẴN SỬ DỤNG TIN CẬY** - Dự án có thể phát triển bình thường.

---

### **H.3. Next Steps** (CHO TƯƠNG LAI)

**KHÔNG có next steps NGAY**.

**Sau 6-12 tháng** (khi có điều kiện):
- Review lại quyết định freeze
- Re-audit project needs
- Decide: Tiếp tục refactor hay giữ nguyên hiện tại mãi mãi?

**Có thể consider**:
- Migrate Room (cleanup FK, delete old model)
- Migrate Service, CustomerProfile
- HOẶC accept 75% refactored as "good enough"

---

### **H.4. LỜI NHẬN TỪ DỰ ÁN BỎ**

**Dự án Spa ANA đã đi rất xa**:
- Từ monolithic app → 9 modular apps
- Từ hard-coded URLs → clean namespaces
- Từ templates lộn xộn → organized structure
- Từ mixed codebase → clean separation

**75% refactoring là THÀNH TỐT**:
- Architecture tốt
- Code maintainable
- Team productivity cao
- Rất đáng tự hào

**25% còn lại (data-layer)**:
- Không cản trở development
- Không phải bottlenecks
- Có thể defer bất cứ lúc nào
- Có thể accept as-is

---

## I. APPROVAL & SIGNATURE

**Quyết định này đã được**:

✅ **REVIEWED** bởi: [Tên Project Owner/Team Lead]
✅ **APPROVED** bởi: [Tên Manager/Stakeholder]
✅ **COMMUNICATED** to: Development Team
✅ **DOCUMENTED** in: `DATA_LAYER_FREEZE_DECISION.md`

**Date**: 2026-03-30
**Status**: 🧊 **ACTIVE - FROZEN**

---

## J. APPENDIX: QUICK REFERENCE

### **J.1. Check-list: Có được phép hay không?**

**Action**: Tôi muốn [action]

**Decision Tree**:
```
Liên quan models/database schema?
├── YES → ❌ KHÔNG được phép (data-layer freeze)
└── NO  → Có thể được phép
```

**Ví dụ**:
```
Action: Thêm field vào Service model
→ Liên quan schema? YES
→ ❌ KHÔNG được phép

Action: Thêm method vào Service model
→ Liên quan schema? NO (methods chỉ là code)
→ ✅ CÓ THỂ được phép

Action: Update FK Appointment.room → appointments.models.Room
→ Liên quan schema? YES
→ ❌ KHÔNG được phép

Action: Optimize query (add select_related)
→ Liên quan schema? NO (chỉ query)
→ ✅ CÓ THỂ được phép
```

---

### **J.2. Emergency Contact**

**Nếu nghi ngờ action có vi phạm freeze**:
1. Read `DATA_LAYER_FREEZE_DECISION.md`
2. Read `PROJECT_REFACTOR_STATUS.md`
3. Ask team lead/senior dev
4. Ask project owner

**Better safe than sorry**:
- Khi nghi ngờ → hỏi trước
- Khi unclear → hỏi trước
- Khi unsure → hỏi trước

---

**Người tạo**: Spa ANA Team
**Ngày**: 2026-03-30
**File**: DATA_LAYER_FREEZE_DECISION.md
**Status**: ✅ COMPLETE - DECISION FINAL
**Next Review**: 6-12 tháng sau (hoặc khi cần)

**Câu hỏi?**: Contact team lead hoặc project owner.
