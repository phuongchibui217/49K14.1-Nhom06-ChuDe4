# BRIDGE STATUS SUMMARY - TÌNH TRẠNG BRIDGE MODEL

**Ngày tạo**: 2026-03-30
**Batch**: 8.4 - Batch 1 (Room Bridge Adoption)
**Trạng thái**: ✅ BRIDGE HOẠT ĐỘNG (NHƯNG CÓ GIỚI HẠN)
**Scope**: Chỉ dành cho model `Room`

---

## A. MODEL NÀO ĐÃ CÓ BRIDGE

### **Model**: `Room`

**Vị trí hiện tại**:
```
spa/models.py (lines 341-376)
└── class Room (managed=True)
    └── db_table = 'spa_room'

appointments/models.py (TOÀN BỘ FILE)
└── class Room (managed=False) ← BRIDGE MỚI
    └── db_table = 'spa_room' (REUSE TABLE CŨ)
```

**Đã cập nhật imports** (4 files):
- ✅ `appointments/views.py` → Import từ `.models.Room`
- ✅ `appointments/services.py` → Import từ `.models.Room`
- ✅ `appointments/appointment_services.py` → Import từ `.models.Room`
- ⚠️ `spa/models.py` → GIỮ NGUYÊN (chưa xóa)

**ChƯA cập nhật** (theo phạm vi Batch 1):
- ❌ Chưa tạo `RoomAdmin` trong `appointments/admin.py`
- ❌ Chưa xóa `RoomAdmin` trong `spa/admin.py`
- ❌ Chưa update `Appointment.room` ForeignKey

---

## B. BRIDGE ĐANG HOẠT ĐỘNG Ở MỨC NÀO

### **B.1. ✅ HOẠT ĐỘNG TỐT**

| Chức năng | Trạng thái | Chi tiết |
|-----------|-----------|----------|
| **Import Room từ appointments.models** | ✅ HOẠT ĐỘNG | `from appointments.models import Room` - OK |
| **Query danh sách tất cả rooms** | ✅ HOẠT ĐỘNG | `Room.objects.all()` - trả về 5 rooms |
| **Query rooms theo điều kiện** | ✅ HOẠT ĐỘNG | `Room.objects.filter(is_active=True)` - OK |
| **Lấy room theo ID** | ✅ HOẠT ĐỘNG | `Room.objects.first()` - OK |
| **Đọc thuộc tính room** | ✅ HOẠT ĐỘNG | `room.code`, `room.name`, `room.capacity` - OK |
| **Gọi methods của room** | ✅ HOẠT ĐỘNG | `room.__str__()`, `room.get_active_rooms()` - OK |
| **Tạo room mới** | ✅ HOẠT ĐỘNG | `Room.objects.create(...)` - OK (test only) |
| **Cập nhật room** | ✅ HOẠT ĐỘNG | `room.save()` - OK (test only) |
| **Xóa room** | ✅ HOẠT ĐỘNG | `room.delete()` - OK (test only) |
| **Django system check** | ✅ HOẠT ĐỘNG | `python manage.py check` - 0 issues |

**Kết luận**: Bridge hoạt động hoàn hảo cho **các thao tác CRUD trực tiếp trên Room model**.

---

### **B.2. ⚠️ HOẠT ĐỘNG CÓ GIỚI HẠN**

| Chức năng | Trạng thái | Chi tiết |
|-----------|-----------|----------|
| **Query Appointment qua Room** | ❌ KHÔNG HOẠT ĐỘNG | `Appointment.objects.filter(room=room)` - LỖI FK type mismatch |
| **Service layer dùng Room trong Appointment context** | ❌ KHÔNG HOẠT ĐỘNG | `check_room_availability()` - LỖI khi filter Appointment |
| **Admin quản lý Room qua appointments app** | ⚠️ CHƯA CÓ | Chưa tạo RoomAdmin trong appointments/admin.py |

**Kết luận**: Bridge **KHÔNG THỂ** dùng được trong **query thông qua ForeignKey của Appointment**.

---

## C. GIỚI HẠN HIỆN TẠI CỦA BRIDGE

### **C.1. ❌ FK TYPE MISMATCH (VẤN ĐỀ CHÍNH)**

**Mô tả**:
```python
from appointments.models import Room as NewRoom
room = NewRoom.objects.first()  # <appointments.models.Room instance>

# Điều này KHÔNG hoạt động:
Appointment.objects.filter(room=room)
# ValueError: Cannot query "P01 - 1": Must be "Room" instance.
```

**Nguyên nhân**:
- `Appointment.room` ForeignKey đang trỏ về `spa.models.Room` (model cũ)
- `appointments.models.Room` là class Python KHÁC
- Django's ForeignKey kiểm tra **Python type**, không chỉ database table
- Type mismatch → Query bị reject

**Hệ quả**:
- ❌ Không thể dùng `appointments.models.Room` instance trong bất kỳ query nào qua `Appointment.room`
- ❌ Service layer functions như `check_room_availability()` sẽ lỗi nếu nhận `appointments.models.Room`
- ❌ Tất cả code paths involve `Appointment.objects.filter(room=...)` đều bị ảnh hưởng

---

### **C.2. ⚠️ MIGRATION STATE DIRTY**

**Vấn đề**:
```bash
python manage.py makemigrations appointments
# Output:
# Migrations for 'appointments':
#   appointments/migrations/0001_initial.py
#     - Create model Room
```

**Nguyên nhân**:
- Django phát hiện model mới trong `appointments/models.py`
- Lệnh `makemigrations` KHÔNG tôn trọng `managed = False`
- Django liên tục muốn tạo migration

**Giải pháp tạm thời**:
- Xóa migration file khi Django tạo ra
- Không áp dụng migration
- Django check vẫn pass

**Rủi ro**:
- State của Django "bẩn" (model tồn tại nhưng không có migration)
- Có thể gây confuse cho developer khác
- Cần xử lý trong batch sau

---

### **C.3. ⚠️ DUAL MODEL DEFINITIONS**

**Hiện tại**:
- 2 file Python cùng định nghĩa class `Room`
- Cả hai đều trỏ vào bảng `spa_room`
- Phải maintain code ở 2 nơi

**Rủi ro**:
- Code duplication
- Phải giữ sync nếu schema thay đổi
- Khó hiểu: import từ đâu?

---

## D. NHỮNG CODE PATH ĐƯỢC DÙNG BRIDGE

### **D.1. ✅ ĐƯỢC DÙNG TỰ DO**

**Pattern**: Các thao tác **trực tiếp** trên Room model, KHÔNG qua Appointment FK

**Ví dụ được phép**:

```python
# ✅ OK - Import từ appointments.models
from appointments.models import Room

# ✅ OK - Query tất cả rooms
rooms = Room.objects.all()

# ✅ OK - Filter rooms
active_rooms = Room.objects.filter(is_active=True)

# ✅ OK - Lấy room theo ID
room = Room.objects.get(code='P001')

# ✅ OK - Đọc thông tin room
print(room.code, room.name, room.capacity)

# ✅ OK - Tạo room mới (test)
new_room = Room.objects.create(
    code='P999',
    name='Test Room',
    capacity=2
)

# ✅ OK - Cập nhật room
room.name = 'Updated Name'
room.save()

# ✅ OK - Xóa room
room.delete()

# ✅ OK - Dùng trong context KHÔNG liên quan Appointment
# Ví dụ: API endpoint chỉ trả về danh sách rooms
def api_rooms_list(request):
    rooms = Room.objects.filter(is_active=True)
    return JsonResponse({'rooms': list(rooms.values())})
```

**Các file có thể dùng bridge**:
- ✅ `appointments/views.py` - NHƯNG chỉ cho operations KHÔNG qua Appointment FK
- ✅ `appointments/services.py` - NHƯNG chỉ cho operations trực tiếp trên Room
- ✅ `appointments/appointment_services.py` - NHƯNG chỉ cho operations trực tiếp trên Room

---

### **D.2. ✅ ĐƯỢC DÙNG VỚI CHÚ Ý**

**Pattern**: Code path có dùng Room, NHƯNG phải dùng `spa.models.Room` (model cũ)

**Ví dụ được phép**:

```python
# ✅ OK - Dùng spa.models.Room trong Appointment context
from spa.models import Room as OldRoom
from spa.models import Appointment

# Query Appointment với room (dùng model cũ)
room = OldRoom.objects.first()
appointments = Appointment.objects.filter(room=room)
# HOẠT ĐỘNG - vì room là spa.models.Room instance

# ✅ OK - Service layer functions (chưa chuyển)
def check_room_availability(room_code, ...):
    room = Room.objects.get(code=room_code)  # Room ở đây là spa.models.Room
    appointments = Appointment.objects.filter(room=room)
    # HOẠT ĐỘNG
```

**Quy tắc**:
- Nếu code path involve `Appointment.objects.filter(room=...)` → PHẢI dùng `spa.models.Room`
- Nếu code path chỉ involve Room operations độc lập → CÓ THỂ dùng `appointments.models.Room`

---

## E. NHỮNG CODE PATH CHƯA ĐƯỢC DÙNG BRIDGE

### **E.1. ❌ CHƯA ĐƯỢC DÙNG (SẼ GÂY LỖI)**

**Pattern**: BẤT KỲ code path nào cố dùng `appointments.models.Room` TRONG `Appointment.objects.filter(room=...)`

**Ví dụ KHÔNG được phép**:

```python
from appointments.models import Room as NewRoom
from spa.models import Appointment

# ❌ KHÔNG ĐƯỢC - Dùng NewRoom trong Appointment query
room = NewRoom.objects.first()  # <appointments.models.Room>
appointments = Appointment.objects.filter(room=room)
# LỖI: ValueError: Cannot query "P01 - 1": Must be "Room" instance.

# ❌ KHÔNG ĐƯỢC - Service layer nếu đổi sang NewRoom
def check_room_availability(room_code, ...):
    room = NewRoom.objects.get(code=room_code)  # SAI nếu dùng NewRoom
    appointments = Appointment.objects.filter(room=room)  # LỖI Ở ĐÂY

# ❌ KHÔNG ĐƯỢC - Tạo Appointment với NewRoom
appointment = Appointment.objects.create(
    customer=customer,
    service=service,
    room=new_room_instance,  # SAI nếu là appointments.models.Room
    ...
)
```

**Các function CHƯA ĐƯỢC chuyển sang bridge**:
- ❌ `check_room_availability()` trong `appointments/services.py` - vẫn dùng `spa.models.Room`
- ❌ Tất cả queries involve `Appointment.room` FK

---

### **E.2. ⚠️ CHƯA CÓ (CHƯA TẠO)**

**Chưa tạo trong Batch 1**:
- ❌ `RoomAdmin` trong `appointments/admin.py`
- ❌ API endpoints riêng cho Room trong appointments app (nếu có plan)

**Vẫn dùng cũ**:
- ✅ `RoomAdmin` trong `spa/admin.py` - vẫn hoạt động

---

## F. ĐIỀU KIỆN ĐỂ SAU NÀY MỚI LÀM BƯỚC CLEANUP / FK MIGRATION

### **F.1. Preconditions BẮT BUỘC**

Trước khi làm bất kỳ cleanup hay FK migration:

**1. ✅ Hiểu rõ Django SeparateDatabaseAndState Operation**
   - Document đã giải thích lý thuyết
   - Cần thực hành trên project test
   - Cần write migration template cụ thể

**2. ✅ Hiểu rõ tác động của FK update**
   - Mọi query `Appointment.objects.filter(room=...)` sẽ bị ảnh hưởng
   - Cần test ALL code paths involve Appointment.room
   - Cần regression test toàn diện

**3. ✅ Database backup**
   ```bash
   python manage.py dumpdata > backup_pre_cleanup.json
   cp db.sqlite3 db.sqlite3.backup
   ```

**4. ✅ Git commit + tag**
   ```bash
   git add .
   git commit -m "Bridge state before cleanup"
   git tag bridge-state-before-cleanup
   ```

**5. ✅ Test suite đầy đủ**
   - Tất cả tests hiện tại phải pass
   - Viết thêm tests cho Appointment queries
   - Document test results

---

### **F.2. Batch Cleanup Plan (TƯƠNG LAI)**

**Khi đủ điều kiện, cleanup có thể làm theo 3 batch nhỏ:

**Batch 1.x: SeparateDatabaseAndState Migration**
- Tạo migration: state_operations = CreateModel, database_operations = [] (empty)
- Áp dụng migration để Django biết về model
- KHÔNG update FK yet

**Batch 1.y: FK Migration**
- Update `Appointment.room` FK → `appointments.models.Room`
- Test tất cả Appointment queries
- Verify service layer functions

**Batch 1.z: Final Cleanup**
- Xóa `spa.models.Room`
- Xóa `RoomAdmin` trong `spa/admin.py`
- (Optional) Rename table: `spa_room` → `appointments_room`

**Timeline**: 3-6 giờ (research + execution + testing)

---

### **F.3. Rollback Plan (Cho Cleanup)**

Nếu cleanup fail:

```bash
# Option 1: Git reset
git reset --hard bridge-state-before-cleanup
python manage.py migrate

# Option 2: Database restore
rm db.sqlite3
cp db.sqlite3.backup db.sqlite3
git reset --hard HEAD

# Option 3: Manual revert
# Delete migration files
# Revert FK change in models
# Re-import spa.models.Room
```

---

### **F.4. Decision Criteria**

**NÊN làm cleanup khi**:
- ✅ Đã có 2-3 model bridges khác (Service, CustomerProfile)
- ✅ Pattern đã rõ ràng, repeatable
- ✅ Có đủ thời gian (3-6 giờ) để test kỹ
- ✅ Team đồng ý với rủi ro migration

**KHÔNG NÊN làm cleanup khi**:
- ❌ Chỉ có 1 model bridge (Room)
- ❌ Time window ngắn (< 2 giờ)
- ❌ Chưa test migration operation trên project test
- ❌ Team chưa đồng ý

---

## TÓM TẮT

**Hiện tại**:
- ✅ Bridge model `appointments.models.Room` hoạt động ở mức CRUD cơ bản
- ❌ KHÔNG dùng được trong Appointment queries (FK mismatch)
- ⚠️ State tạm thời, chấp nhận được

**Được phép**:
- ✅ Dùng `appointments.models.Room` cho standalone Room operations
- ✅ Dùng `spa.models.Room` cho Appointment-related queries

**Không được phép**:
- ❌ Dùng `appointments.models.Room` trong `Appointment.objects.filter(room=...)`
- ❌ Migration thêm trong phase này
- ❌ Cleanup thêm trong phase này

**Bước tiếp theo**:
- ⏸️ Dừng ở bridge cho Room
- 🔄 Áp dụng pattern bridge cho models khác (Service, CustomerProfile, v.v.)
- 📋 Review tất cả bridges, rồi quyết định cleanup cùng lúc

---

**Người tạo**: Spa ANA Team
**Ngày**: 2026-03-30
**Batch**: 8.4 - Batch 1 (Room Bridge)
**Trạng thái**: ✅ BRIDGE ACTIVE (WITH KNOWN LIMITATIONS)
**Next Phase**: PENDING USER CONFIRMATION
