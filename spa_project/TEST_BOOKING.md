# HƯỚNG DẪN TEST CHỨC NĂNG ĐẶT LỊCH

## 📋 VẤN ĐỀ ĐÃ TÌM THẤY VÀ SỬA

### ❌ VẤN ĐỀ GỐC:
Khi khách hàng đặt lịch thành công và ở trạng thái "chờ xác nhận", giao diện quản lý (admin) **KHÔNG NHẬN** thông tin.

### 🔍 NGUYÊN NHÂN:
1. **Khách đặt lịch KHÔNG chọn phòng**:
   - `AppointmentForm` không có field `room`
   - Khi lưu: `room = NULL`

2. **Method `get_end_time_display()` thiếu fallback**:
   - Nếu `duration_minutes = NULL` → return rỗng
   - Không fallback vào `service.duration_minutes`

3. **Tab "Lịch theo phòng" filter theo roomId**:
   - `APPOINTMENTS.filter(a => a.roomId === r.id)`
   - Appointments KHÔNG CÓ room bị loại bỏ

### ✅ GIẢI PHÁP ĐÃ ÁP DỤNG:

1. **Sửa `get_end_time_display()` trong models.py**:
   ```python
   # Fallback vào service duration nếu appointment không có duration_minutes
   duration = self.duration_minutes
   if duration is None and hasattr(self, 'service'):
       duration = self.service.duration_minutes
   ```

2. **Thêm debug log vào JavaScript**:
   - Console.log chi tiết web bookings
   - Kiểm tra roomId, status

3. **Đảm bảo API trả về đúng dữ liệu**:
   - `api_booking_requests()` filter đúng `source='web'`
   - Trả về cả appointments KHÔNG CÓ room

---

## 🧪 HƯỚNG DẪN TEST

### Bước 1: Chạy server và login admin

```bash
cd D:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\5.GIT_HUB\TD_3\LTW_Spa_Ana\spa_project
python manage.py runserver
```

Truy cập:
- Admin: http://127.0.0.1:8000/manage/login/
- Đăng nhập với tài khoản staff

### Bước 2: Mở Browser Console (F12)

Chuyển sang tab **Console** để xem debug logs.

### Bước 3: Đặt lịch từ khách hàng

1. Logout (nếu đang login admin)
2. Vào http://127.0.0.1:8000/booking/
3. Chọn dịch vụ, ngày, giờ
4. Bấm "Xác nhận đặt lịch"
5. Xem thông báo thành công

### Bước 4: Kiểm tra Admin - Tab "Yêu cầu đặt lịch"

1. Login lại admin
2. Vào http://127.0.0.1:8000/manage/appointments/
3. Click tab **"Yêu cầu đặt lịch"**
4. Xem Console log:
   ```
   Rendering web requests, rows: X
   - APP202603230001 | Nguyễn Văn A | roomId: | status: pending
   ```

### Bước 5: Xác nhận booking (Admin)

1. Click button **"Xác nhận"** của booking
2. Chọn phòng (P01-P05)
3. Bấm **"Lưu lịch hẹn"**
4. Booking chuyển từ tab "Yêu cầu đặt lịch" sang tab "Lịch theo phòng"

---

## 🔧 CÁC FILE ĐÃ SỬA

### 1. `spa/models.py` - Line 453-466
```python
def get_end_time_display(self):
    """Get end time as string"""
    if self.end_time:
        return self.end_time.strftime('%H:%M')

    # Get duration - fallback to service duration if not set
    duration = self.duration_minutes
    if duration is None and hasattr(self, 'service'):
        duration = self.service.duration_minutes

    # Calculate from duration
    if self.appointment_time and duration:
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), self.appointment_time)
        end_dt = start_dt + timedelta(minutes=duration)
        return end_dt.strftime('%H:%M')
    return ''
```

### 2. `static/js/admin-appointments.js` - Line 257-272
```javascript
async function renderWebRequests(){
  const searchTerm = searchInput.value.toLowerCase().trim();
  let rows = await loadBookingRequests();
  console.log('Rendering web requests, rows:', rows.length);

  // Debug: log chi tiết từng row
  rows.forEach(r => console.log('  -', r.id, r.customerName, 'roomId:', r.roomId, 'status:', r.apptStatus));

  // ... render logic
}
```

---

## 📊 LUỒNG DỮ LIỆU (DATA FLOW)

```
KHÁCH HÀNG                        BACKEND                      ADMIN
    |                              |                            |
    |--[POST] /booking/---------->|                            |
    |   - service                 |                            |
    |   - appointment_date        | Save to DB:                 |
    |   - appointment_time        | - source = 'web'            |
    |   (KHÔNG chọn room)          | - room = NULL               |
    |                              | - status = 'pending'         |
    |                              |                            |
    |<-----Success----------------|                            |
    |                              |                            |
    |                              |<--GET /api/bookings---------|
    |                              |   filter: source='web'      |
    |                              |   return: appointments[]    |
    |                              |                            |
    |                              |                            |
    |                        ADMIN VIEW                        |
    |                              |                            |
    |  Tab "Yêu cầu đặt lịch" <----| Web bookings (room=NULL)  |
    |  - Hiển thị pending         | - roomId: ''                |
    |  - Nút "Xác nhận"            | - Có thể chỉnh sửa          |
    |                              |                            |
    |  Admin chọn room ----->------>| Update:                    |
    |  Bấm "Lưu"                   | - room = P01                |
    |                              | - status = 'not_arrived'     |
    |                              |                            |
    |                              |                            |
    |  Tab "Lịch theo phòng" <----| Confirmed appointments     |
    |  - Hiển thị trên lưới        | - roomId: 'P01'             |
    |  - Có thể chỉnh              | - Có thể chuyển phòng       |
```

---

## 🐛 DEBUG TIPS

### Nếu KHÔNG thấy web bookings:

1. **Kiểm tra Console Browser**:
   - Có lỗi API không? (403, 404, 500)
   - Có CSRF token error không?

2. **Kiểm tra Network tab**:
   - Request `/api/booking-requests/` có trả về 200 OK không?
   - Response có `appointments` array không?

3. **Kiểm tra Database**:
   ```python
   python manage.py shell
   >>> from spa.models import Appointment
   >>> Appointment.objects.filter(source='web').count()
   >>> # Phải > 0
   ```

4. **Kiểm tra quyền user**:
   ```python
   >>> from django.contrib.auth.models import User
   >>> user = User.objects.get(username='admin')
   >>> user.is_staff  # Phải là True
   ```

### Nếu bookings KHÔNG hiện trên lưới:

1. **Kiểm tra roomId**:
   ```javascript
   // Mở Console
   console.log(APPOINTMENTS.filter(a => a.roomId === ''));
   // Phải trả về web bookings
   ```

2. **Kiểm tra renderGrid()**:
   - Filter theo `roomId === r.id`
   - Web bookings có `roomId = ''` → bị lọc ra ✓ (đúng)

3. **Xác nhận booking** để gán phòng:
   - Click button "Xác nhận"
   - Chọn phòng P01-P05
   - Bấm "Lưu"
   - Booking chuyển sang tab "Lịch theo phòng"

---

## ✅ CHECKLIST TEST

- [ ] Server đang chạy (python manage.py runserver)
- [ ] Admin user là staff (is_staff=True)
- [ ] Database đã có Rooms (P01-P05)
- [ ] Khách có thể đặt lịch
- [ ] Web bookings hiển thị ở tab "Yêu cầu đặt lịch"
- [ ] Console browser có debug log
- [ ] Có thể xác nhận booking (chọn phòng)
- [ ] Booking chuyển sang tab "Lịch theo phòng" sau khi xác nhận
- [ ] Có thể chỉnh/sửa/xóa booking

---

## 📞 HỖ TRỢ

Nếu vẫn không hoạt động:
1. Chụp ảnh Console Browser (F12 → Console tab)
2. Chụp ảnh Network tab (F12 → Network tab)
3. Chạy: `python manage.py shell -c "from spa.models import Appointment; print(Appointment.objects.filter(source='web').count())"`
4. Gửi lại để hỗ trợ
