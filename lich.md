# Hướng dẫn Test Admin Appointments Scheduler

## 1. Chuẩn bị môi trường

### 1.1. Chạy Django Server
```bash
cd spa_project
python manage.py runserver
```

Server sẽ chạy tại: `http://127.0.0.1:8000`

### 1.2. Tạo tài khoản Admin (nếu chưa có)
```bash
python manage.py createsuperuser
# Nhập username, email, password
```

---

## 2. Đăng nhập Admin

1. Truy cập: `http://127.0.0.1:8000/manage/login/`
2. Đăng nhập với tài khoản admin (is_staff=True)

---

## 3. Test các chức năng

### 3.1. Xem lịch hẹn (Scheduler)

**Bước 1:** Vào trang Appointments
- URL: `http://127.0.0.1:8000/manage/appointments/`
- Hoặc click menu sidebar **"Lịch hẹn"**

**Bước 2:** Quan sát giao diện
- **Header thời gian:** Hiển thị các khung giờ từ 9:00 - 22:00
- **Danh sách phòng:** 5 phòng (1, 2, 3, 4, 5) hiển thị theo hàng ngang
- **Các block lịch hẹn:** Hiển thị với màu sắc theo trạng thái:
  - 🔵 Xanh dương: Chưa đến (not_arrived)
  - 🟢 Xanh lá: Đã đến (arrived)
  - 🟣 Tím: Hoàn thành (completed)
  - 🔴 Đỏ: Đã hủy (cancelled)
  - 🟡 Vàng: Chờ xác nhận (pending)

### 3.2. Tạo lịch hẹn mới

**Cách 1: Click vào vùng trống trên lịch**
1. Click vào bất kỳ ô trống nào trên timeline
2. Modal "Tạo lịch hẹn" sẽ hiện ra với thời gian đã được điền sẵn

**Cách 2: Click nút "Thêm lịch hẹn"**
1. Click nút **"Thêm lịch hẹn"** ở góc trên bên phải
2. Điền thông tin vào form:

| Trường | Mô tả | Ví dụ |
|--------|-------|-------|
| Họ tên khách hàng | Bắt buộc | Nguyễn Văn A |
| Số điện thoại | 10 số | 0901234567 |
| Email | Tùy chọn | test@email.com |
| Dịch vụ | Chọn từ dropdown | Chăm sóc da mặt |
| Phòng | Chọn từ dropdown | Phòng 1 |
| Số khách | Số nguyên > 0 | 2 |
| Ngày | Định dạng YYYY-MM-DD | 2026-03-24 |
| Giờ | Định dạng HH:MM | 10:00 |
| Thời lượng | Số phút | 60 |
| Trạng thái | Dropdown | Chưa đến |
| Thanh toán | Dropdown | Chưa thanh toán |
| Ghi chú | Tùy chọn | Khách hàng VIP |

3. Click **"Lưu"** để tạo

**Kết quả mong đợi:**
- Toast thông báo "Tạo lịch hẹn thành công! Mã: APxxxxx"
- Block lịch hẹn mới xuất hiện trên timeline
- Lịch hẹn được lưu vào database

### 3.3. Sửa lịch hẹn

**Bước 1:** Click vào block lịch hẹn trên timeline
- Modal "Chỉnh sửa • APxxxxx" hiện ra

**Bước 2:** Thay đổi thông tin cần thiết
- Có thể sửa tất cả các trường
- Có thể đổi phòng, giờ, ngày

**Bước 3:** Click **"Lưu"**

**Kết quả mong đợi:**
- Toast thông báo "Cập nhật lịch hẹn thành công"
- Block lịch hẹn cập nhật vị trí/thông tin trên timeline

### 3.4. Xóa/Hủy lịch hẹn

**Bước 1:** Click vào block lịch hẹn cần xóa

**Bước 2:** Click nút **"Xóa"** (màu đỏ)

**Bước 3:** Xác nhận trong dialog
- Click **"OK"** để xác nhận

**Kết quả mong đợi:**
- Toast thông báo "Đã hủy lịch hẹn APxxxxx"
- Block lịch hẹn chuyển sang màu đỏ (cancelled) hoặc biến mất

### 3.5. Điều hướng ngày

- **DatePicker:** Click vào ô ngày để chọn ngày cụ thể
- **Nút "<":** Lùi 1 ngày
- **Nút ">":** Tới 1 ngày
- **Nút "Hôm nay":** Về ngày hiện tại

### 3.6. Tìm kiếm

**Bước 1:** Nhập từ khóa vào ô tìm kiếm
- Có thể tìm theo: Tên khách, SĐT, Dịch vụ, Mã lịch hẹn

**Bước 2:** Kết quả được lọc realtime
- Timeline chỉ hiển thị các lịch hẹn khớp từ khóa
- Bảng yêu cầu web cũng được lọc

---

## 4. Test Yêu cầu đặt lịch từ Web (UC4)

### 4.1. Tạo yêu cầu từ trang customer

**Bước 1:** Đăng nhập tài khoản customer
- URL: `http://127.0.0.1:8000/login/`

**Bước 2:** Vào trang đặt lịch
- URL: `http://127.0.0.1:8000/booking/`

**Bước 3:** Điền form và submit
- Chọn dịch vụ, ngày, giờ
- Click **"Đặt lịch"**

### 4.2. Duyệt yêu cầu từ Admin

**Bước 1:** Vào tab **"Yêu cầu từ web"** trên trang Appointments

**Bước 2:** Quan sát danh sách yêu cầu
- Các yêu cầu mới có trạng thái "Chờ xác nhận"
- Hiển thị: Mã, Tên, SĐT, Email, Dịch vụ, Ngày, Giờ, Ghi chú

**Bước 3:** Duyệt hoặc từ chối

**Duyệt:**
1. Click nút **"Xác nhận"** (vàng)
2. Modal chỉnh sửa hiện ra
3. Kiểm tra/chỉnh sửa thông tin (đặc biệt là Phòng)
4. Đổi trạng thái thành "Chưa đến"
5. Click **"Lưu"**

**Từ chối:**
1. Click nút **"Từ chối"** (đỏ)
2. Xác nhận trong dialog
3. Yêu cầu bị hủy, trạng thái chuyển sang "Đã hủy"

---

## 5. Test API trực tiếp (Postman/Browser)

### 5.1. Lấy danh sách phòng
```
GET http://127.0.0.1:8000/api/rooms/
```

Response:
```json
{
  "success": true,
  "rooms": [
    {"id": "P01", "name": "1", "capacity": 3},
    {"id": "P02", "name": "2", "capacity": 2},
    ...
  ]
}
```

### 5.2. Lấy danh sách lịch hẹn
```
GET http://127.0.0.1:8000/api/appointments/?date=2026-03-24
```

### 5.3. Tạo lịch hẹn
```
POST http://127.0.0.1:8000/api/appointments/create/
Content-Type: application/json
X-CSRFToken: <csrf_token>

{
  "customerName": "Nguyễn Văn Test",
  "phone": "0901234567",
  "serviceId": 1,
  "roomId": "P01",
  "guests": 2,
  "date": "2026-03-24",
  "time": "10:00",
  "duration": 60
}
```

### 5.4. Cập nhật lịch hẹn
```
POST http://127.0.0.1:8000/api/appointments/AP00001/update/
Content-Type: application/json
X-CSRFToken: <csrf_token>

{
  "apptStatus": "arrived"
}
```

---

## 6. Checklist Test

| STT | Chức năng | Pass | Fail | Ghi chú |
|-----|-----------|------|------|---------|
| 1 | Xem timeline lịch hẹn | ☐ | ☐ | |
| 2 | Tạo lịch hẹn bằng click vào ô trống | ☐ | ☐ | |
| 3 | Tạo lịch hẹn bằng nút Thêm | ☐ | ☐ | |
| 4 | Sửa thông tin lịch hẹn | ☐ | ☐ | |
| 5 | Xóa/Hủy lịch hẹn | ☐ | ☐ | |
| 6 | Điều hướng ngày (prev/next/today) | ☐ | ☐ | |
| 7 | Tìm kiếm lịch hẹn | ☐ | ☐ | |
| 8 | Xem danh sách yêu cầu từ web | ☐ | ☐ | |
| 9 | Duyệt yêu cầu đặt lịch | ☐ | ☐ | |
| 10 | Từ chối yêu cầu đặt lịch | ☐ | ☐ | |
| 11 | Validate số điện thoại (10 số) | ☐ | ☐ | |
| 12 | Validate sức chứa phòng | ☐ | ☐ | |
| 13 | Validate giờ làm việc (9-22h) | ☐ | ☐ | |
| 14 | Toast notification hoạt động | ☐ | ☐ | |
| 15 | Responsive trên mobile | ☐ | ☐ | |

---

## 7. Troubleshooting

### Lỗi: Không load được dữ liệu
- Kiểm tra console browser (F12) xem có lỗi JS không
- Kiểm tra network tab xem API có trả về lỗi không
- Đảm bảo đã đăng nhập admin

### Lỗi: CSRF token missing
- Đảm bảo đã đăng nhập
- Clear cookie và đăng nhập lại

### Lỗi: Không tạo được lịch hẹn
- Kiểm tra validation (SĐT 10 số, chọn dịch vụ, chọn phòng)
- Kiểm tra sức chứa phòng trong khung giờ

### Lỗi: Migration conflict
```bash
python manage.py migrate --fake
python manage.py migrate
```

---

## 8. Dữ liệu test mẫu

### Tạo customer test
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from spa.models import CustomerProfile, Service

# Tạo user
user = User.objects.create_user(username='0901234567', password='test123456')

# Tạo customer profile
customer = CustomerProfile.objects.create(user=user, phone='0901234567', full_name='Khách Hàng Test')

# Lấy service đầu tiên
service = Service.objects.first()
print(f"Service: {service.name}")
```

### Tạo lịch hẹn test qua shell
```python
from spa.models import CustomerProfile, Service, Room, Appointment
from datetime import date, time

customer = CustomerProfile.objects.get(phone='0901234567')
service = Service.objects.first()
room = Room.objects.get(code='P01')

appt = Appointment.objects.create(
    customer=customer,
    service=service,
    room=room,
    appointment_date=date.today(),
    appointment_time=time(10, 0),
    duration_minutes=60,
    guests=2,
    status='not_arrived',
    source='admin'
)
print(f"Created: {appt.appointment_code}")
```

---

*Tài liệu này được tạo để hướng dẫn test chức năng Admin Appointments Scheduler của Spa ANA*