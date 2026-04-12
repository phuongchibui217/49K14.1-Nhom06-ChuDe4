# 📅 Hướng Dẫn Trang Quản Lý Lịch Hẹn (Appointments Scheduler)

## 🌐 Đường Dẫn Truy Cập

### **Local Development**
```
http://127.0.0.1:8000/manage/appointments/
```

### **Production**
```
https://your-domain.com/manage/appointments/
```

---

## 🔐 Quyền Truy Cập

Trang này **chỉ dành cho**:
- ✅ Staff (`is_staff = True`)
- ✅ Superuser (`is_superuser = True`)

### Cách Login:
1. Truy cập: `http://127.0.0.1:8000/login/`
2. Chọn tab **[Nhân viên]**
3. Nhập thông tin:
   - Username: `letan01`
   - Password: `letan123`
4. Click **[Đăng nhập]** → Auto redirect về `/manage/appointments/`

---

## 📂 Cấu Trúc Files

```
spa_project/
│
├── appointments/                    # Django App
│   ├── views.py                     # Backend logic
│   ├── urls.py                      # URL routes
│   ├── models.py                    # Appointment, Room
│   ├── services.py                  # Business logic
│   └── appointment_services.py      # CRUD operations
│
├── templates/
│   └── manage/
│       ├── base.html                # Base template
│       └── pages/
│           └── admin_appointments.html  # Main UI ✅
│
├── static/
│   ├── css/
│   │   └── admin-appointments.css   # Styles ✅
│   └── js/
│       └── admin-appointments.js    # Frontend Logic ✅
│
└── manage.py                        # Django management
```

---

## 🎯 Tính Năng Chính

### **1. Lịch Theo Phòng (Room Scheduler)**
- Grid layout dạng ô (card-based)
- Trục tung: Danh sách phòng (P01, P02, P03...)
- Trục hoành: Khung giờ (9:00 - 22:00)
- Mỗi 30 phút = 1 ô ngang
- Click ô trống → Tạo lịch hẹn mới
- Click lịch hẹn → Sửa/Xóa

### **2. Yêu Cầu Đặt Lịch (Web Requests)**
- Table layout: Danh sách book từ web
- Hiển thị: Mã, Khách, SĐT, Dịch vụ, Ngày/Giờ, Trạng thái
- Actions: Xác nhận, Hủy, Sửa

### **3. Tìm Kiếm & Lọc**
- Search: Tên, SĐT, Dịch vụ, Mã lịch
- Date picker: Chọn ngày cụ thể
- Navigate: Ngày trước/sau/Hôm nay

---

## 🗺️ URL Routes

### **Main Pages**
```python
# Trang quản lý lịch hẹn
/manage/appointments/           → admin_appointments (View)

# Booking page (public)
/booking/                       → booking (View)
/my-appointments/               → my_appointments (Customer view)
```

### **API Endpoints**
```python
# Rooms
GET  /api/rooms/                → api_rooms_list
# Response: {success: true, rooms: [{id, name, capacity}]}

# Appointments
GET  /api/appointments/         → api_appointments_list
# Query params: ?date=2024-01-15&status=pending&q=search
# Response: {success: true, appointments: [...]}

GET  /api/appointments/<code>/  → api_appointment_detail
# Response: {success: true, appointment: {...}}

POST /api/appointments/create/  → api_appointment_create
# Body: {customerName, phone, serviceId, roomId, date, time, duration}
# Response: {success: true, message: "...", appointment: {...}}

PUT  /api/appointments/<code>/  → api_appointment_update
# Body: {customerName, phone, serviceId, ...}
# Response: {success: true, message: "..."}

POST /api/appointments/<code>/status/ → api_appointment_status
# Body: {status: "confirmed"}
# Response: {success: true, message: "..."}

DELETE /api/appointments/<code>/   → api_appointment_delete
# Response: {success: true, message: "..."}

# Web Booking Requests
GET  /api/booking-requests/    → api_booking_requests
# Response: {success: true, appointments: [...]}
```

---

## 🎨 Layout Structure

### **Grid System**
```
┌─────────────────────────────────────────────────────────┐
│  [📅 Lịch theo phòng]  [🌐 Yêu cầu đặt lịch]            │  ← Tabs
├─────────────────────────────────────────────────────────┤
│  🔍 [Search...]  [📅 < Today >]    Click ô trống→Tạo   │  ← Topbar
├──────┬───┬───┬───┬───┬───┬───┬───┬─────────────────────┤
│ Room │ 9 │ 9:30│10 │10:30│11 │11:30│12  │ ...          │  ← Time Header
├──────┼───┼───┼───┼───┼───┼───┼───┼─────────────────────┤
│  P01 │ . │ . │ [Appointment Card] │ . │ . │ ...         │  ← Room 1
├──────┼───┼───┼───┼───┼───┼───┼───┼─────────────────────┤
│  P02 │ . │ . │ . │ . │ . │ . │ . │ ...                 │  ← Room 2
├──────┼───┼───┼───┼───┼───┼───┼───┼─────────────────────┤
│  P03 │ . │ [Another Appointment] │ . │ . │ ...         │  ← Room 3
└──────┴───┴───┴───┴───┴───┴───┴───┴─────────────────────┘
```

### **Appointment Card**
```
┌──────────────────────────────────────┐
│ 👤 Nguyễn Thị A                       │  ← Customer Name
│ 💅 Chăm sóc da                       │  ← Service
│ 🕐 9:30 - 10:30 (60 phút)            │  ← Time & Duration
│ 📞 0901234567                        │  ← Phone
└──────────────────────────────────────┘
```

---

## ⚙️ Configuration

### **Time Settings** (static/js/admin-appointments.js)
```javascript
const START_HOUR = 9;    // Giờ mở cửa: 9:00 SA
const END_HOUR = 22;     // Giờ đóng cửa: 22:00 (10 PM)
const SLOT_MIN = 30;     // 1 ô = 30 phút
```

### **CSS Grid Dimensions** (static/css/admin-appointments.css)
```css
:root {
  --slotW: 52px;         /* Width mỗi ô ngang */
  --rowH: 66px;          /* Height mỗi hàng phòng */
  --totalSlots: 24;      /* Số ô ngang (tính từ START-END) */
}
```

### **Status Colors**
```javascript
// Appointment Status
pending    → 🟡 Chờ xác nhận (vàng)
not_arrived→ 🔴 Chưa đến (đỏ)
arrived    → 🔵 Đã đến (xanh)
completed  → 🟢 Hoàn thành (xanh lá)
cancelled  → ⚫ Đã hủy (xám)

// Payment Status
unpaid     → 💳 Chưa thanh toán
partial    → 💵 Thanh toán một phần
paid       → ✅ Đã thanh toán
```

---

## 🔄 User Flow

### **Tạo Lịch Hẹn Mới**
```
1. Click ô trống trong grid
   ↓
2. Modal "Tạo lịch hẹn" mở
   ↓
3. Điền form:
   - Họ tên khách hàng *
   - Số điện thoại *
   - Email
   - Dịch vụ *
   - Phòng *
   - Số khách *
   - Ngày hẹn *
   - Giờ hẹn *
   - Thời lượng (30/60/90/120 phút)
   - Trạng thái lịch hẹn
   - Trạng thái thanh toán
   - Ghi chú
   ↓
4. Click [Lưu lịch hẹn]
   ↓
5. API: POST /api/appointments/create/
   ↓
6. Re-render Grid với appointment mới
```

### **Sửa Lịch Hẹn**
```
1. Click vào appointment card
   ↓
2. Modal "Cập nhật lịch hẹn" mở
   ↓
3. Edit thông tin
   ↓
4. Click [Lưu lịch hẹn]
   ↓
5. API: PUT /api/appointments/<code>/
   ↓
6. Re-render Grid
```

### **Xóa Lịch Hẹn**
```
1. Click appointment card
   ↓
2. Modal mở → Click [Xóa] (nút đỏ)
   ↓
3. Confirm dialog: "Bạn có chắc?"
   ↓
4. API: DELETE /api/appointments/<code>/
   ↓
5. Xóa vĩnh viễn khỏi database
```

---

## 🔧 Debug

### **Check Permissions**
```python
# Python shell
python manage.py shell

>>> from django.contrib.auth.models import User
>>> u = User.objects.get(username='letan01')
>>> print(f"is_staff: {u.is_staff}")  # Should be True
>>> print(f"is_superuser: {u.is_superuser}")  # Should be False/True
```

### **Check URL Routing**
```bash
# List all URLs
python manage.py show_urls | grep appointment
```

### **Browser Console**
```javascript
// Check API calls
console.log('Rooms:', ROOMS);
console.log('Appointments:', APPOINTMENTS);

// Re-render grid
renderGrid();

// Force refresh
loadAppointments();
```

---

## 📱 Responsive Design

### **Desktop (> 1024px)**
- Full grid with scroll
- 2-column tabs
- Modal size: Large

### **Tablet (768px - 1024px)**
- Horizontal scroll for grid
- Stacked tabs
- Modal size: Medium

### **Mobile (< 768px)**
- List view instead of grid
- Single column tabs
- Full-screen modal
- Simplified search bar

---

## 🚀 Deployment Checklist

- [ ] Update `ALLOWED_HOSTS` in settings.py
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up CSRF protection
- [ ] Enable HTTPS
- [ ] Configure CDN for static files (optional)
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Test with real users

---

## 📞 Support

### **Common Issues**

**Issue: Redirect to /home/ instead of /manage/appointments/**
- **Solution**: Check `is_staff` flag in User model
- **Debug**: See [DEBUG_REDIRECT.md](DEBUG_REDIRECT.md)

**Issue: Grid not rendering**
- **Solution**: Check browser console for JS errors
- **Verify**: API endpoints returning data

**Issue: Cannot create appointment**
- **Solution**: Check CSRF token in request headers
- **Debug**: Network tab in DevTools

---

## 📚 Related Files

- [appointments/views.py](appointments/views.py) - Backend views
- [appointments/urls.py](appointments/urls.py) - URL configuration
- [templates/manage/pages/admin_appointments.html](templates/manage/pages/admin_appointments.html) - Main template
- [static/css/admin-appointments.css](static/css/admin-appointments.css) - Styles
- [static/js/admin-appointments.js](static/js/admin-appointments.js) - Frontend logic
- [DEBUG_REDIRECT.md](DEBUG_REDIRECT.md) - Debug login redirects
- [PERMISSION_GUIDE.md](PERMISSION_GUIDE.md) - Permission system

---

## 🎓 Quick Reference

| Tính năng | Keyboard Shortcut |
|-----------|-------------------|
| Tạo lịch hẹn | Click ô trống |
| Sửa lịch hẹn | Click appointment |
| Xóa lịch hên | Click → Nút Xóa |
| Ngày trước | `Alt + ←` |
| Ngày sau | `Alt + →` |
| Hôm nay | `Alt + T` |
| Search | `Ctrl + F` |
| Close modal | `Esc` |

---

**Last Updated:** 2026-04-11
**Version:** 1.0.0
**Author:** Spa ANA Development Team
