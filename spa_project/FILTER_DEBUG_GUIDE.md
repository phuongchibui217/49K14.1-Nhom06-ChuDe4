# Hướng dẫn Debug Bộ Lọc Đặt Lịch

## 🧪 CÁCH TEST BỘ LỌC

### **Bước 1: Mở Browser Console**
1. Vào trang: `http://127.0.0.1:8000/manage/appointments/`
2. Click tab "Yêu cầu đặt lịch"
3. Bấm **F12** → **Console** tab

### **Bước 2: Test API Endpoint**

Chạy các lệnh sau trong Console:

```javascript
// Test 1: Kiểm tra filter element
const filterEl = document.getElementById("webStatusFilter");
console.log("Filter element:", filterEl);
console.log("Filter value:", filterEl ? filterEl.value : "NOT FOUND");

// Test 2: Gọi API trực tiếp với status filter
fetch('/api/booking-requests/?status=pending')
  .then(res => res.json())
  .then(data => {
    console.log("API Response (pending):", data);
    console.log("Appointments count:", data.appointments ? data.appointments.length : 0);
  });

// Test 3: Gọi API với status=cancelled
fetch('/api/booking-requests/?status=cancelled')
  .then(res => res.json())
  .then(data => {
    console.log("API Response (cancelled):", data);
    console.log("Appointments count:", data.appointments ? data.appointments.length : 0);
  });

// Test 4: Gọi API với all status (empty parameter)
fetch('/api/booking-requests/')
  .then(res => res.json())
  .then(data => {
    console.log("API Response (all):", data);
    console.log("Appointments count:", data.appointments ? data.appointments.length : 0);
  });
```

### **Bước 3: Test JavaScript Function**

```javascript
// Test renderWebRequests function
if (typeof renderWebRequests === 'function') {
  console.log("✅ renderWebRequests function exists");
  renderWebRequests();
} else {
  console.log("❌ renderWebRequests function NOT found!");
}

// Test loadBookingRequests function
if (typeof loadBookingRequests === 'function') {
  console.log("✅ loadBookingRequests function exists");

  // Test with different filters
  loadBookingRequests('pending').then(rows => {
    console.log("Pending bookings:", rows.length);
  });

  loadBookingRequests('cancelled').then(rows => {
    console.log("Cancelled bookings:", rows.length);
  });

  loadBookingRequests('').then(rows => {
    console.log("All bookings:", rows.length);
  });
} else {
  console.log("❌ loadBookingRequests function NOT found!");
}
```

### **Bước 4: Test Dropdown Change Event**

```javascript
// Manual test - simulate dropdown change
const filterEl = document.getElementById("webStatusFilter");
if (filterEl) {
  console.log("Current filter value:", filterEl.value);

  // Change value programmatically
  filterEl.value = "pending";
  console.log("Set to pending:", filterEl.value);

  // Trigger change event
  filterEl.dispatchEvent(new Event('change'));
} else {
  console.log("❌ Filter element NOT found!");
}
```

---

## 🐛 COMMON ISSUES & SOLUTIONS

### **Issue 1: "Filter element NOT found"**
**Nguyên nhân:** JavaScript chạy trước khi HTML load xong

**Giải pháp:**
```javascript
// Thêm timeout hoặc đợi DOMContentLoaded
setTimeout(() => {
  const filterEl = document.getElementById("webStatusFilter");
  console.log("Filter:", filterEl);
}, 1000);
```

### **Issue 2: API returns empty array**
**Nguyên nhân:**
- Database không có bookings với status đó
- API endpoint bị lỗi

**Giải pháp:**
```bash
# Check database
python manage.py shell

from appointments.models import Appointment
print("Pending:", Appointment.objects.filter(status='pending').count())
print("Cancelled:", Appointment.objects.filter(status='cancelled').count())
print("All:", Appointment.objects.all().count())
```

### **Issue 3: Filter value is empty string**
**Nguyên nhân:** Dropdown không có value cho option

**Giải pháp:** Check HTML template
```html
<!-- ❌ WRONG -->
<option value="">Tất cả</option>

<!-- ✅ CORRECT -->
<option value="">Tất cả trạng thái</option>
<option value="pending">Chờ xác nhận</option>
```

---

## 🔍 EXPECTED BEHAVIOR

### **Console Log Output:**

```
=== renderWebRequests START ===
Search term: (none)
🔍 Status filter element: <select>
🔍 Status filter value: pending
🔍 Status filter value type: string
Calling loadBookingRequests with: pending
Final API URL: /api/booking-requests/?status=pending
API Response: {success: true, appointments: Array(3)}
Appointments count: 3
Sample row: {id: "APP0001", customerName: "Nguyen Van A", apptStatus: "pending"}
Received rows from API: 3
```

---

## ✅ SUCCESS CRITERIA

Bộ lọc hoạt động đúng khi:

1. ✅ **Console không có lỗi** (red text)
2. ✅ **API URL có parameter** `?status=pending`
3. ✅ **API trả về đúng data** (filter theo status)
4. ✅ **Bảng hiển thị đúng rows** sau khi filter
5. ✅ **Badge count cập nhật** đúng số lượng

---

## 🚨 IF STILL NOT WORKING

### **Check 1: JavaScript File Loading**
```javascript
// In console, check:
console.log(window.renderWebRequests); // Should show function code, not undefined
console.log(window.loadBookingRequests); // Should show function code, not undefined
```

### **Check 2: Template Syntax**
```bash
# Restart Django server
python manage.py runserver

# Clear browser cache (Ctrl+Shift+Delete)
# Reload page with Ctrl+F5 (hard refresh)
```

### **Check 3: Database Data**
```python
# Create test data
python manage.py shell

from appointments.models import Appointment
from spa_services.models import Service
from accounts.models import CustomerProfile
from datetime import date, time

service = Service.objects.first()
customer = CustomerProfile.objects.first()

# Create pending booking
Appointment.objects.create(
    customer=customer,
    service=service,
    appointment_date=date.today(),
    appointment_time=time(14, 0),
    status='pending',
    source='web'
)

# Create cancelled booking
Appointment.objects.create(
    customer=customer,
    service=service,
    appointment_date=date.today(),
    appointment_time=time(15, 0),
    status='cancelled',
    source='web'
)
```

---

## 📞 NEXT STEPS

1. **Copy test commands** từ trên
2. **Paste vào browser console**
3. **Chạy từng test** và báo kết quả
4. **Gửi console output** để tôi debug tiếp

Nếu vẫn không được, hãy:
- Chụp ảnh console log
- Chụp ảnh network tab (F12 → Network)
- Gửi database query results

Tôi sẽ fix ngay! 🔧
