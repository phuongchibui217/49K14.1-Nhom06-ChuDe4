# PHÂN TÍCH MISMATCH TOÀN DIỆN - CODE HIỆN TẠI VS BÁO CÁO

**Ngày phân tích**: 2026-03-20
**File báo cáo**: BÁO CÁO TIẾN ĐỘ LẦN 2.md (2.3MB)
**Tổng số use case trong báo cáo**: 30+
**Tổng số màn hình trong báo cáo**: 25+

---

## TÓM TẮT EXECUTIVE SUMMARY

### ❌ CRITICAL MISMATCHES (Phải sửa ngay):

| # | Vấn đề | Hiện tại (AS-IS) | Báo cáo (TO-BE) | Priority |
|---|--------|------------------|-----------------|----------|
| 1 | **Auth System** | Customer login/register bắt buộc | KHÔNG có customer auth. Chỉ admin/staff | **P0** |
| 2 | **Booking Flow** | Tạo Appointment trực tiếp | Booking Request → Staff xử lý → Appointment | **P0** |
| 3 | **User Types** | Chỉ có CustomerProfile | Thiếu Staff/Employee model | **P0** |
| 4 | **Dashboard** | Không có | Dashboard cho Chủ Spa | **P1** |
| 5 | **Quản lý nhân viên** | Không có | CRUD nhân viên nội bộ | **P1** |
| 6 | **Quản lý khách hàng** | Chỉ customer profile | CRUD khách hàng cho lễ tân | **P1** |
| 7 | **Appointment Management** | Chỉ "my_appointments" | Calendar view, check-in/out | **P1** |
| 8 | **Chat/Tư vấn** | Placeholder | Chat system 2 chiều | **P2** |
| 9 | **Quên mật khẩu** | Không có | Có chức năng | **P2** |
| 10 | **Ticket System** | Có nhưng sai flow | Ticket system với bàn giao ca | **P1** |

---

## PHẦN 1: ÁNH XẠ CHỨC NĂNG - MẪN HÌNH

### A. PUBLIC WEBSITE (Khách hàng vãng lai)

| STT | Chức năng (Báo cáo) | File/View hiện tại | Mức độ khớp | Ghi chú |
|-----|---------------------|-------------------|-------------|---------|
| A1 | Trang chủ | [home.html](spa_project/templates/spa/pages/home.html) - `home()` | ✅ 90% | Cần review lại content |
| A2 | Về Spa ANA | [about.html](spa_project/templates/spa/pages/about.html) - `about()` | ✅ 100% | Khớp báo cáo |
| A3 | Xem danh sách dịch vụ | [services.html](spa_project/templates/spa/pages/services.html) - `service_list()` | ✅ 85% | Thiết kế cần điều chỉnh |
| A4 | Xem chi tiết dịch vụ | [service_detail.html](spa_project/templates/spa/pages/service_detail.html) - `service_detail()` | ✅ 90% | Cần thêm info |
| A5 | **Đặt lịch trực tuyến** | [booking.html](spa_project/templates/spa/pages/booking.html) - `booking()` | ❌ 30% | **SAI FLOW** - Phần B |
| A6 | Chat/Gửi tin nhắn | [chat_widget.html](spa_project/templates/spa/includes/chat_widget.html) | ❌ 10% | Chỉ placeholder |
| A7 | Floating buttons | [floating_buttons.html](spa_project/templates/spa/includes/floating_buttons.html) | ✅ 100% | Khớp báo cáo |
| A8 | Đăng ký tài khoản | [register.html](spa_project/templates/spa/pages/register.html) - `register()` | ❌ 100% | **KHÔNG CÓ TRONG BÁO CÁO** |
| A9 | Đăng nhập | [login.html](spa_project/templates/spa/pages/login.html) - `login_view()` | ❌ 100% | **KHÔNG CÓ TRONG BÁO CÁO** |

### B. ADMIN SYSTEM (Lễ tân/Chủ Spa)

| STT | Chức năng (Báo cáo) | File/View hiện tại | Mức độ khớp | Action |
|-----|---------------------|-------------------|-------------|--------|
| B1 | **Đăng nhập Admin** (Lễ tân/Chủ Spa) | `login.html` - nhưng là customer login | ❌ 0% | **PHẢI LÀM LẠI** |
| B2 | **Quên mật khẩu** | Không có | ❌ 0% | **PHẢI THÊM** |
| B3 | Đăng xuất | `logout_view()` | ✅ 100% | OK |
| B4 | Tài khoản cá nhân | Không có riêng | ❌ 0% | **PHẢI THÊM** |
| B5 | **Quản lý nhân viên** | Không có | ❌ 0% | **PHẢI THÊM** |
| B6 | **Quản lý dịch vụ** | Có trong admin.py | ⚠️ 50% | Cần UI riêng |
| B7 | **Quản lý yêu cầu hỗ trợ/tư vấn** | `consultation.html`, `complaint.html` | ❌ 40% | **SAI FLOW** |
| B8 | **Quản lý lịch hẹn** | `my_appointments.html` | ❌ 30% | **SAI SCOPE** |
| B9 | **Quản lý khách hàng** | Không có | ❌ 0% | **PHẢI THÊM** |
| B10 | **Chat tư vấn** | `chat_widget.html` | ❌ 10% | **PHẢI LÀM** |
| B11 | **Dashboard** | Không có | ❌ 0% | **PHẢI THÊM** |

---

## PHẦN 2: MISMATCH CHI TIẾT THEO CATEGORY

### 2.1 AUTHENTICATION & AUTHORIZATION ❌ CRITICAL

#### Báo cáo yêu cầu:
- **Chỉ có Admin/Staff login**: Lễ tân và Chủ Spa đăng nhập vào backend
- **KHÔNG có customer login/register**: Khách hàng đặt lịch mà không cần tài khoản
- **Vai trò**:
  - Lễ tân: Xử lý booking, quản lý dịch vụ, khách hàng, ticket
  - Chủ Spa: Tất cả + Quản lý nhân viên + Dashboard

#### Code hiện tại:
```python
# models.py
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, ...)
    # Chỉ có customer, KHÔNG có staff model

# views.py
def login_view(request):
    # Login cho KHÁCH HÀNG (customer)
    # Username = phone

def register(request):
    # ĐĂNG KÝ khách hàng mới
```

#### Vấn đề:
1. ❌ **Sai hoàn toàn**: Báo cáo KHÔNG yêu cầu customer login
2. ❌ **Thiếu Staff model**: Không có model cho nhân viên nội bộ
3. ❌ **Thiếu role-based access**: Không có phân quyền lễ tân vs chủ spa
4. ❌ **Thiếu admin authentication**: Không có login riêng cho admin

#### Action required:
- [ ] Xóa/Disable customer login/register
- [ ] Tạo Staff/Employee model
- [ ] Tạo admin login system
- [ ] Implement role-based permissions

---

### 2.2 BOOKING FLOW ❌ CRITICAL

#### Báo cáo yêu cầu (Use case UC4):
```
FLOW CHÍNH XÁC:
1. Khách hàng (KHÔNG CẦN ĐĂNG NHẬP) → Điền form đặt lịch
2. Hệ thống → Lưu "YÊU CẦU ĐẶT LỊCH" (BookingRequest) với status = "pending"
3. Lễ tân → Xem danh sách yêu cầu đặt lịch
4. Lễ tân → Xác nhận hoặc từ chối
5. Nếu xác nhận → Tạo APPOINTMENT chính thức
6. Nếu từ chối → Cập nhật status = "rejected"
```

#### Code hiện tại:
```python
# views.py
def booking(request):
    # YÊU CẦU ĐĂNG NHẬP ❌ SAI
    if not request.user.is_authenticated:
        return redirect('login')

    # TẠO APPOINTMENT TRỰC TIẾP ❌ SAI
    form = AppointmentForm(request.POST)
    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.customer = customer_profile
        appointment.save()  # Lưu thẳng Appointment ❌
```

#### Vấn đề:
1. ❌ **Yêu cầu login**: Báo cáo nói "KHÔNG CẦN ĐĂNG NHẬP"
2. ❌ **Tạo Appointment trực tiếp**: Báo cáo yêu cầu tạo BookingRequest trước
3. ❌ **Thiếu bước xử lý của lễ tân**: Không có màn hình "xử lý yêu cầu đặt lịch"

#### Action required:
- [ ] Tạo BookingRequest model
- [ ] Đổi booking flow: Tạo BookingRequest thay vì Appointment
- [ ] Bỏ require login cho booking
- [ ] Tạo admin screen: "Xử lý yêu cầu đặt lịch"
- [ ] Tạo flow: BookingRequest → Appointment

---

### 2.3 TICKET / SUPPORT SYSTEM ❌ CRITICAL

#### Báo cáo yêu cầu (Use case UC9):
```
TICKET SYSTEM VỚI BÀN GIAO CA:
- Tạo ticket với các trường:
  * Tiêu đề, Loại yêu cầu, Độ ưu tiên
  * Thông tin khách hàng
  * Nhân viên phụ trách
  * Trạng thái: Mới, Đang xử lý, Chờ phản hồi, Đã đóng
  * Ghi chú nội bộ

- BÀN GIAO CA:
  * Ticket chưa xử lý xong → Bàn giao cho ca sau
  * Theo dõi trạng thái ticket qua các ca

- CRUD đầy đủ: Create, Read, Update, Delete
```

#### Code hiện tại:
```python
# models.py
class ConsultationRequest(models.Model):
    # Yêu cầu tư vấn - form công khai
    full_name, phone, email, request_type, content...

class SupportRequest(models.Model):
    # Góp ý/Khiếu nại - form công khai
    full_name, phone, email, support_type, content...
```

#### Vấn đề:
1. ❌ **Tên không khớp**: Báo cáo gọi là "Ticket", code dùng "ConsultationRequest/SupportRequest"
2. ❌ **Thiếu các trường quan trọng**:
   - Không có ticket_code (mã ticket)
   - Không có assigned_staff (nhân viên phụ trách)
   - Không có priority (độ ưu tiên)
   - Không có internal_notes (ghi chú nội bộ)
3. ❌ **Thiếu CRUD**: Chỉ có create, không có update/delete cho admin
4. ❌ **Thiếu bàn giao ca**: Không có feature theo dõi qua các ca

#### Action required:
- [ ] Refactor model: Tạo Ticket model mới hoặc rename
- [ ] Thêm các trường thiếu
- [ ] Tạo CRUD views cho admin
- [ ] Implement bàn giao ca feature

---

### 2.4 APPOINTMENT MANAGEMENT ❌ CRITICAL

#### Báo cáo yêu cầu (Use case UC10):
```
QUẢN LÝ LỊCH HẸN (CHO LỄ TÂN):
1. XEM LỊCH TỔNG QUÁT:
   - Calendar view: Phòng × Khung giờ
   - Hiển thị các lịch hẹn dưới dạng card
   - Có thể thấy lịch trùng giờ

2. TẠO LỊCH HẸN:
   - Tạo lịch hẹn nội bộ (khách walk-in)
   - Chọn phòng, khách, dịch vụ, ngày, giờ
   - Check sức chứa phòng

3. XỬ LÝ YÊU CẦU ĐẶT LỊCH:
   - Xem danh sách booking requests
   - Xác nhận → Tạo appointment
   - Từ chối → Update status

4. SỬA LỊCH HẸN:
   - Chỉnh sửa thông tin
   - Check trùng giờ/phòng

5. XÓA LỊCH HẸN:
   - Xóa lịch (không phải soft delete)
   - Không xóa lịch đã hoàn thành

6. CHECK-IN / CHECK-OUT:
   - Check-in: Khách đến
   - Check-out: Khách làm xong dịch vụ
```

#### Code hiện tại:
```python
# views.py
@login_required
def my_appointments(request):
    # CHỈ XEM LỊCH CỦA CUSTOMER HIỆN TẠI ❌
    customer_profile = request.user.customer_profile
    appointments = customer_profile.appointments.all()

# models.py
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
        ('no_show', 'Không đến'),
    ]
    # KHÔNG CÓ:
    # - check_in_time
    # - check_out_time
    # - payment_status
    # - room
    # - staff_assigned
```

#### Vấn đề:
1. ❌ **Sai scope**: "my_appointments" chỉ cho customer, báo cáo cần cho admin xem TẤT CẢ
2. ❌ **Thiếu calendar view**: Không có view dạng lịch phòng × giờ
3. ❌ **Thiếu check-in/out**: Không có thời gian check-in, check-out
4. ❌ **Thiếu payment status**: Không có trạng thái thanh toán
5. ❌ **Thiếu room management**: Không có phòng
6. ❌ **Thiếu staff assignment**: Không có nhân viên phụ trách

#### Action required:
- [ ] Tạo admin view: Xem tất cả appointments
- [ ] Tạo calendar view (phòng × khung giờ)
- [ ] Thêm check_in_time, check_out_time fields
- [ ] Thêm payment_status field
- [ ] Thêm room model và room selection
- [ ] Thêm staff_assigned field

---

### 2.5 STAFF / EMPLOYEE MANAGEMENT ❌ CRITICAL

#### Báo cáo yêu cầu (Use case UC6):
```
QUẢN LÝ TÀI KHOẢN NHÂN VIÊN (CHỦ SPA):
1. Tạo tài khoản nhân viên:
   - Tên đăng nhập, mật khẩu
   - Họ tên, SĐT, email
   - Vai trò (Lễ tân / Chuyên viên / Khác)

2. Xem thông tin nhân viên:
   - Danh sách nhân viên
   - Chi tiết từng nhân viên

3. Khóa tài khoản:
   - Vô hiệu hóa tài khoản
   - Không thể đăng nhập
```

#### Code hiện tại:
```python
# models.py
# KHÔNG CÓ Staff/Employee model ❌

# Chỉ có CustomerProfile cho khách hàng
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, ...)
```

#### Vấn đề:
1. ❌ **Không có model**: Hoàn toàn thiếu Staff/Employee model
2. ❌ **Không có CRUD**: Không có views quản lý nhân viên
3. ❌ **Không có phân vai trò**: Không có role (lễ tân vs chủ spa)

#### Action required:
- [ ] Tạo Staff/Employee model
- [ ] Tạo CRUD views: staff_list, staff_create, staff_update, staff_delete
- [ ] T tạo staff lock/unlock functionality
- [ ] Add role field: RECEPTIONIST, OWNER, SPECIALIST

---

### 2.6 CUSTOMER MANAGEMENT (CHO LỄ TÂN) ❌ IMPORTANT

#### Báo cáo yêu cầu (Use case UC11):
```
QUẢN LÝ THÔNG TIN KHÁCH HÀNG (LỄ TÂN):
1. Thêm khách hàng:
   - Họ tên, SĐT (bắt buộc, unique)
   - Ngày sinh, Kênh liên hệ
   - Dị ứng, Tình trạng da
   - Ghi chú

2. Cập nhật khách hàng:
   - Sửa thông tin
   - Validate SĐT unique

3. Tìm kiếm khách hàng:
   - Theo SĐT, họ tên
```

#### Code hiện tại:
```python
# models.py
class CustomerProfile(models.Model):
    # CÓ các cơ bản fields
    full_name, phone, email, gender, dob, address, notes

    # NHƯNG:
    # - Liên kết với User (dùng cho login) ❌
    # - Không có kênh liên hệ
    # - Không có dị ứng
    # - Không có tình trạng da
```

#### Vấn đề:
1. ⚠️ **Model tồn tại nhưng sai design**:
   - CustomerProfile hiện tại liên kết với User (cho login)
   - Báo cáo KHÔNG cần customer login
2. ❌ **Thiếu fields**:
   - contact_channel (kênh liên hệ: Zalo, Facebook, Phone)
   - allergies (dị ứng)
   - skin_condition (tình trạng da)
3. ❌ **Không có CRUD views cho admin**: Không có screen để lễ tân quản lý khách

#### Action required:
- [ ] Refactor CustomerProfile:
  - Bỏ hoặc tách khỏi User model
  - Thêm các fields thiếu
- [ ] Tạo CRUD views: customer_list, customer_create, customer_update
- [ ] Add search functionality

---

### 2.7 DASHBOARD ❌ IMPORTANT

#### Báo cáo yêu cầu:
```
DASHBOARD (CHỈ CHO CHỦ SPA):
Cards:
- Số lịch hẹn hôm nay
- Số lịch hẹn tháng này
- Số khách mới tháng này
- Số tư vấn chưa xử lý

Table:
- Lịch hẹn gần đây

Quick actions:
- Tạo lịch hẹn
- Thêm khách hàng
- Thêm dịch vụ
```

#### Code hiện tại:
```python
# KHÔNG CÓ Dashboard ❌
```

#### Vấn đề:
1. ❌ **Hoàn toàn thiếu**: Không có dashboard

#### Action required:
- [ ] Tạo dashboard view
- [ ] Add statistics calculations
- [ ] Add recent activities table
- [ ] Add quick action buttons
- [ ] Restrict access: Only CHỦ SPA (Owner role)

---

### 2.8 SERVICE MANAGEMENT ⚠️ PARTIAL

#### Báo cáo yêu cầu (Use case UC8):
```
QUẢN LÝ DỊCH VỤ (LỄ TÂN/CHỦ SPA):
- Thêm dịch vụ
- Xem danh sách (với filter/search)
- Cập nhật dịch vụ
- XÓA = SOFT DELETE (chuyển sang "Ngừng hoạt động")
- Tìm kiếm dịch vụ
```

#### Code hiện tại:
```python
# models.py
class Service(models.Model):
    is_active = models.BooleanField(default=True)  # ✅ Có soft delete

# admin.py
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # ✅ Có trong Django admin
```

#### Vấn đề:
1. ⚠️ **Chỉ có Django admin**: Báo cáo yêu cầu custom UI, không dùng admin
2. ❌ **Thiếu CRUD views**: Không có service_list, service_create, service_update views
3. ❌ **Thiếu search/filter views**: Không có màn hình search với filter

#### Action required:
- [ ] Tạo service CRUD views (outside admin)
- [ ] Tạo service list view với filters
- [ ] Tạo service search functionality

---

### 2.9 CHAT SYSTEM ❌ MISSING

#### Báo cáo yêu cầu:
```
CHAT TƯ VẤN TRỰC TUYẾN:
Public:
- Khách gửi tin nhắn

Admin:
- Xem danh sách hội thoại
- Phản hồi khách hàng
- Chat 2 chiều
```

#### Code hiện tại:
```html
<!-- chat_widget.html -->
<!-- Chỉ placeholder, không có functionality ❌ -->
```

#### Vấn đề:
1. ❌ **Chỉ UI placeholder**: Không có backend
2. ❌ **Không có Chat model**: Không lưu tin nhắn
3. ❌ **Không có realtime**: Không có WebSocket hoặc polling

#### Action required:
- [ ] Tạo ChatMessage/Conversation models
- [ ] Tạo chat API endpoint
- [ ] Implement frontend chat functionality
- [ ] Hoặc tích hợp Zalo API (đơn giản hơn)

---

### 2.10 FORGOT PASSWORD ❌ MISSING

#### Báo cáo yêu cầu (Use case UC3):
```
QUÊN MẬT KHẨU:
1. Nhập email/username
2. Hệ thống gửi mã xác thực
3. Nhập mã + mật khẩu mới
4. Cập nhật mật khẩu
```

#### Code hiện tại:
```python
# KHÔNG CÓ ❌
```

#### Vấn đề:
1. ❌ **Hoàn toàn thiếu**: Không có forgot password

#### Action required:
- [ ] Implement Django password reset view
- [ ] Tạo forgot password template
- [ ] Configure email backend

---

## PHẦN 3: MAPPING DATABASE MODELS

### 3.1 MODELS CÓ TRONG CODE (CẦN SỬA)

| Model hiện tại | Báo cáo yêu cầu | Action |
|----------------|-----------------|--------|
| **CustomerProfile** | ✅ CẦN GIỮ nhưng sửa | Refactor |
| `user = OneToOneField(User)` | ❌ KHÔNG CẦN User | Tách riêng hoặc bỏ |
| `full_name, phone, email` | ✅ Giữ | Giữ nguyên |
| `gender, dob, address` | ✅ Giữ | Giữ nguyên |
| `notes` | ✅ Giữ | Giữ nguyên |
| **Thiếu**: `contact_channel` | ❌ Thiếu | Thêm field |
| **Thiếu**: `allergies` | ❌ Thiếu | Thêm field |
| **Thiếu**: `skin_condition` | ❌ Thiếu | Thêm field |

| Model hiện tại | Báo cáo yêu cầu | Action |
|----------------|-----------------|--------|
| **Service** | ✅ CÓ - Giữ | OK |
| **Appointment** | ⚠️ CÓ nhưng thiếu fields | Sửa lại |
| `appointment_code` | ✅ Giữ | OK |
| `customer = FK(CustomerProfile)` | ⚠️ Cần review | Có thể optional |
| `service = FK(Service)` | ✅ Giữ | OK |
| `appointment_date, appointment_time` | ✅ Giữ | OK |
| `status` | ✅ Giữ | OK |
| `notes, staff_notes` | ✅ Giữ | OK |
| **Thiếu**: `room` | ❌ Cần | Thêm FK to Room |
| **Thiếu**: `staff_assigned` | ❌ Cần | Thêm FK to Staff |
| **Thiếu**: `check_in_time` | ❌ Cần | Thêm DateTimeField |
| **Thiếu**: `check_out_time` | ❌ Cần | Thêm DateTimeField |
| **Thiếu**: `payment_status` | ❌ Cần | Thêm CharField |
| **Thiếu**: `num_guests` | ❌ Cần | Thêm PositiveIntegerField |

| Model hiện tại | Báo cáo yêu cầu | Action |
|----------------|-----------------|--------|
| **ConsultationRequest** | ❌ SAI tên, thiếu fields | Refactor thành Ticket |
| **SupportRequest** | ❌ SAI tên, thiếu fields | Merge vào Ticket |

### 3.2 MODELS THIẾU (PHẢI TẠO MỚI)

| Model | Fields | Priority |
|-------|--------|----------|
| **Staff/Employee** | user (FK), staff_code, full_name, phone, email, role, is_active, date_created | **P0** |
| **BookingRequest** | booking_code, customer_name, customer_phone, customer_email, service, preferred_date, preferred_time, notes, status, created_at | **P0** |
| **Ticket** | ticket_code, title, ticket_type, priority, customer_name, customer_phone, customer_email, service_concerned, assigned_staff, status, description, internal_notes, created_at, updated_at | **P1** |
| **Room** | room_code, name, capacity, is_active | **P1** |
| **ChatMessage** | conversation_id, sender (staff/customer), message, sent_at, is_read | **P2** |
| **ChatConversation** | conversation_code, customer_name, customer_phone, assigned_staff, status, created_at | **P2** |

---

## PHẦN 4: MAPPING VIEWS/URLS

### 4.1 PUBLIC VIEWS (KHÁCH HÀNG)

| URL hiện tại | View hiện tại | Báo cáo yêu cầu | Action |
|--------------|---------------|-----------------|--------|
| `/` | `home()` | ✅ Trang chủ | Giữ |
| `/about/` | `about()` | ✅ Về Spa ANA | Giữ |
| `/services/` | `service_list()` | ✅ Danh sách dịch vụ | Giữ |
| `/services/<id>/` | `service_detail()` | ✅ Chi tiết dịch vụ | Giữ |
| `/booking/` | `booking()` | ⚠️ Đặt lịch | **PHẢI SỬA** |
| `/consultation/` | `consultation()` | ❌ Không yêu cầu riêng | Xóa hoặc gộp |
| `/complaint/` | `complaint()` | ❌ Không yêu cầu riêng | Xóa hoặc gộp |
| `/login/` | `login_view()` | ❌ KHÔNG CÓ customer login | **XÓA** |
| `/register/` | `register()` | ❌ KHÔNG CÓ customer register | **XÓA** |
| `/my-appointments/` | `my_appointments()` | ❌ KHÔNG CÓ cho khách | **XÓA** |
| `/cancel-appointment/<id>/` | `cancel_appointment()` | ❌ KHÔNG CÓ cho khách | **XÓA** |

### 4.2 ADMIN VIEWS (LỄ TÂN/CHỦ SPA)

| URL cần tạo | View cần tạo | Functionality | Priority |
|------------|--------------|---------------|----------|
| `/admin/login/` | `admin_login()` | Đăng nhập admin/staff | **P0** |
| `/admin/forgot-password/` | `forgot_password()` | Quên mật khẩu | **P2** |
| `/admin/logout/` | `admin_logout()` | Đăng xuất | **P0** |
| `/admin/dashboard/` | `dashboard()` | Dashboard (Chủ Spa) | **P1** |
| `/admin/profile/` | `admin_profile()` | Tài khoản cá nhân | **P1** |
| `/admin/staff/` | `staff_list()` | Danh sách nhân viên | **P1** |
| `/admin/staff/add/` | `staff_create()` | Thêm nhân viên | **P1** |
| `/admin/staff/<id>/` | `staff_detail()` | Chi tiết nhân viên | **P1** |
| `/admin/staff/<id>/edit/` | `staff_update()` | Sửa nhân viên | **P1** |
| `/admin/staff/<id>/lock/` | `staff_lock()` | Khóa tài khoản | **P1** |
| `/admin/customers/` | `customer_list()` | Danh sách khách hàng | **P1** |
| `/admin/customers/add/` | `customer_create()` | Thêm khách hàng | **P1** |
| `/admin/customers/<id>/` | `customer_detail()` | Chi tiết khách | **P1** |
| `/admin/customers/<id>/edit/` | `customer_update()` | Sửa khách hàng | **P1** |
| `/admin/services/` | `service_list()` | Danh sách dịch vụ | **P1** |
| `/admin/services/add/` | `service_create()` | Thêm dịch vụ | **P1** |
| `/admin/services/<id>/edit/` | `service_update()` | Sửa dịch vụ | **P1** |
| `/admin/services/<id>/delete/` | `service_delete()` | Xóa dịch vụ (soft) | **P1** |
| `/admin/bookings/requests/` | `booking_requests_list()` | Yêu cầu đặt lịch | **P0** |
| `/admin/bookings/requests/<id>/approve/` | `approve_booking_request()` | Xác nhận yêu cầu | **P0** |
| `/admin/bookings/requests/<id>/reject/` | `reject_booking_request()` | Từ chối yêu cầu | **P0** |
| `/admin/appointments/calendar/` | `appointment_calendar()` | Lịch tổng quát | **P1** |
| `/admin/appointments/add/` | `appointment_create()` | Tạo lịch hẹn | **P1** |
| `/admin/appointments/<id>/` | `appointment_detail()` | Chi tiết lịch | **P1** |
| `/admin/appointments/<id>/edit/` | `appointment_update()` | Sửa lịch hẹn | **P1** |
| `/admin/appointments/<id>/delete/` | `appointment_delete()` | Xóa lịch hẹn | **P1** |
| `/admin/appointments/<id>/check-in/` | `appointment_check_in()` | Check-in khách | **P1** |
| `/admin/appointments/<id>/check-out/` | `appointment_check_out()` | Check-out khách | **P1** |
| `/admin/tickets/` | `ticket_list()` | Danh sách ticket | **P1** |
| `/admin/tickets/add/` | `ticket_create()` | Tạo ticket | **P1** |
| `/admin/tickets/<id>/` | `ticket_detail()` | Chi tiết ticket | **P1** |
| `/admin/tickets/<id>/edit/` | `ticket_update()` | Cập nhật ticket | **P1** |
| `/admin/tickets/<id>/delete/` | `ticket_delete()` | Xóa ticket | **P1** |
| `/admin/chat/` | `chat_list()` | Danh sách chat | **P2** |

---

## PHẦN 5: BUSINESS RULES MISMATCH

### 5.1 BOOKING BUSINESS RULES

| Rule | Báo cáo | Code hiện tại | Match? |
|------|---------|---------------|-------|
| BR1 | KHÔNG cần login để đặt lịch | BẮT BUỘC login | ❌ |
| BR2 | Tạo BookingRequest (pending) | Tạo Appointment trực tiếp | ❌ |
| BR3 | Lễ tân xử lý yêu cầu | Không có bước xử lý | ❌ |
| BR4 | Check trùng lịch trước khi xác nhận | Không có check | ❌ |
| BR5 | Check sức chứa phòng | Không có phòng | ❌ |

### 5.2 APPOINTMENT BUSINESS RULES

| Rule | Báo cáo | Code hiện tại | Match? |
|------|---------|---------------|-------|
| BR1 | Check-in/Check-out time | Không có | ❌ |
| BR2 | Payment status | Không có | ❌ |
| BR3 | Staff assignment | Không có | ❌ |
| BR4 | Room capacity | Không có | ❌ |
| BR5 | Calendar view | Chỉ list view | ❌ |

### 5.3 CUSTOMER BUSINESS RULES

| Rule | Báo cáo | Code hiện tại | Match? |
|------|---------|---------------|-------|
| BR1 | KHÔNG cần đăng ký | Có đăng ký | ❌ |
| BR2 | SĐT unique | Có (đúng) | ✅ |
| BR3 | Lễ tân quản lý khách | Chỉ customer tự quản lý | ❌ |

---

## PHẦN 6: ƯU TIÊN FIX THEO PHASE

### PHASE 0 - SETUP (1 ngày)
1. Backup code hiện tại
2. Tạo branch mới cho refactor
3. Setup git flow

### PHASE 1 - CẤU TRÚC DATABASE (2-3 ngày) **CRITICAL**
1. ✅ Tạo `Staff/Employee` model
2. ✅ Tạo `BookingRequest` model
3. ✅ Tạo `Ticket` model (refactor from ConsultationRequest/SupportRequest)
4. ✅ Tạo `Room` model
5. ✅ Sửa `Appointment` model:
   - Add: room, staff_assigned, check_in_time, check_out_time, payment_status, num_guests
6. ✅ Sửa `CustomerProfile` model:
   - Remove user dependency (hoặc tách riêng)
   - Add: contact_channel, allergies, skin_condition
7. ✅ Create and run migrations
8. ✅ Update admin.py

### PHASE 2 - AUTH SYSTEM (2 ngày) **CRITICAL**
1. ✅ Xóa/disable customer login/register
2. ✅ Tạo admin login system
3. ✅ Tạo role-based permissions:
   - RECEPTIONIST (Lễ tân)
   - OWNER (Chủ Spa)
   - SPECIALIST (Chuyên viên)
4. ✅ Tạo login_required decorator cho admin
5. ✅ Tạo forgot password views

### PHASE 3 - BOOKING FLOW (2-3 ngày) **CRITICAL**
1. ✅ Sửa `booking()` view:
   - Bỏ require login
   - Tạo BookingRequest thay vì Appointment
2. ✅ Tạo `booking_requests_list()` admin view
3. ✅ Tạo `approve_booking_request()` view
4. ✅ Tạo `reject_booking_request()` view
5. ✅ Update booking.html template

### PHASE 4 - ADMIN VIEWS - NHÂN VIÊN & KHÁCH (2-3 ngày) **IMPORTANT**
1. ✅ Tạo CRUD Staff:
   - staff_list, staff_create, staff_update, staff_detail, staff_lock
2. ✅ Tạo CRUD Customer:
   - customer_list, customer_create, customer_update, customer_detail
3. ✅ Tạo search/filter functionality

### PHASE 5 - ADMIN VIEWS - DỊCH VỤ & TICKET (2-3 ngày) **IMPORTANT**
1. ✅ Tạo CRUD Service (outside admin):
   - service_list, service_create, service_update, service_delete
2. ✅ Refactor Ticket system:
   - ticket_list, ticket_create, ticket_update, ticket_detail, ticket_delete
3. ✅ Tạo filter/search cho tickets

### PHASE 6 - APPOINTMENT MANAGEMENT (3-4 ngày) **IMPORTANT**
1. ✅ Tạo appointment_calendar() view
2. ✅ Tạo appointment_create() (cho admin)
3. ✅ Tạo appointment_update() (cho admin)
4. ✅ Tạo appointment_delete() (cho admin)
5. ✅ Tạo appointment_check_in() view
6. ✅ Tạo appointment_check_out() view
7. ✅ Tạo calendar template với room × time grid

### PHASE 7 - DASHBOARD (1-2 ngày) **IMPORTANT**
1. ✅ Tạo dashboard() view
2. ✅ Calculate statistics:
   - Today's appointments
   - Monthly appointments
   - New customers
   - Pending tickets
3. ✅ Create dashboard template
4. ✅ Restrict access: Owner only

### PHASE 8 - CHAT (2-3 ngày) **NICE TO HAVE**
1. ✅ Tạo ChatMessage/Conversation models
2. ✅ Tạo chat views
3. ✅ Implement chat UI
4. **HOẶC** tích hợp Zalo API (đơn giản hơn)

### PHASE 9 - CLEANUP (1 ngày)
1. ✅ Xóa customer login/register templates và views
2. ✅ Xóa các file không dùng
3. ✅ Update URLs
4. ✅ Test toàn bộ flow

---

## PHẦN 7: RỦI RO & LƯU Ý

### RỦI RO CAO:
1. ⚠️ **Dữ liệu hiện có**: CustomerProfile liên kết với User - refactor sẽ mất dữ liệu
   - **Giải pháp**: Migration script để preserve data

2. ⚠️ **Booking flow đang hoạt động**: Nếu đang có production users
   - **Giải pháp**: Feature flag hoặc gradual rollout

3. ⚠️ **Khối lượng work lớn**: ~30 views phải tạo/sửa
   - **Giải pháp**: Làm theo phase, priority first

### LƯU Ý QUAN TRỌNG:
1. 📋 **Báo cáo là SOURCE OF TRUTH**: Khi có conflict, theo báo cáo
2. 🚫 **KHÔNG dùng React/SPA**: Dùng Django templates + form POST
3. 🔐 **Security**:
   - Admin phải login
   - Role-based access control
   - CSRF protection
4. 📱 **Mobile responsive**: Templates phải responsive
5. ♻️ **Reuse components**: Dùng template inheritance, includes

---

## PHẦN 8: ƯỚC TÍNH THỜI GIAN

| Phase | Mô tả | Ước tính | Priority |
|-------|-------|----------|----------|
| 0 | Setup | 1 ngày | - |
| 1 | Database refactor | 2-3 ngày | **P0** |
| 2 | Auth system | 2 ngày | **P0** |
| 3 | Booking flow | 2-3 ngày | **P0** |
| 4 | Staff & Customer | 2-3 ngày | **P1** |
| 5 | Service & Ticket | 2-3 ngày | **P1** |
| 6 | Appointment mgmt | 3-4 ngày | **P1** |
| 7 | Dashboard | 1-2 ngày | **P1** |
| 8 | Chat | 2-3 ngày | **P2** |
| 9 | Cleanup | 1 ngày | - |
| **TOTAL** | | **20-27 ngày** | |

---

## PHẦN 9: RECOMMENDATION

### LỘ TRÌNH ĐỀ XUẤT:

**TUẦN 1-2: CRITICAL FOUNDATION**
- Phase 1 (Database)
- Phase 2 (Auth)
- Phase 3 (Booking flow)

**TUẦN 3-4: CORE ADMIN FEATURES**
- Phase 4 (Staff & Customer)
- Phase 5 (Service & Ticket)

**TUẦN 5-6: APPOINTMENT MANAGEMENT**
- Phase 6 (Appointment)

**TUẦN 7: POLISH**
- Phase 7 (Dashboard)
- Phase 9 (Cleanup)

**OPTIONAL (TUẦN 8+):**
- Phase 8 (Chat)

---

**PHÂN TÍCH HOÀN THÀNH**

File này là SOURCE OF TRUTH cho việc refactoring.
Tất cả quyết định technical nên dựa trên analysis này.

Cập nhật lần cuối: 2026-03-20
