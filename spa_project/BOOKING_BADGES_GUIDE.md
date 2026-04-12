# 🎯 HỆ THỐNG BADGES - THÔNG BÁO ĐẶT LỊCH

## 📊 OVERVIEW

Hệ thống có **2 badges** để hiển thị số lượng yêu cầu đặt lịch:

---

## 🔵 BADGE #1: TAB HEADER BADGE

**Vị trí:** Tab "Yêu cầu đặt lịch" trong admin appointments page

**HTML:** [`templates/manage/pages/admin_appointments.html:31`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\templates\manage\pages\admin_appointments.html#L31)

```html
<span class="badge badge-soft ms-2" id="webCount">0</span>
```

**CSS:** [`static/css/admin-appointments.css:224-260`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\static\css\admin-appointments.css)

**Features:**
- ✅ Màu đỏ gradient (#ff6b6b → #ff8787)
- ✅ Hiển thị số lượng bookings TRONG TAB HIỆN TẠI
- ✅ Auto-hide khi count = 0
- ✅ Pulse animation khi thay đổi
- ✅ Box shadow để nổi bật

**Update Logic:** [`static/js/admin-appointments.js:406`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\static\js\admin-appointments.js#L406)

```javascript
// Cập nhật trong renderWebRequests()
webCount.textContent = String(rows.length);
```

---

## 🔴 BADGE #2: SIDEBAR BADGE

**Vị trí:** Sidebar "Quản lý lịch hẹn"

**HTML:** [`templates/manage/includes/sidebar.html:14`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\templates\manage\includes\sidebar.html#L14)

```html
<span class="sidebar-booking-badge d-none" id="adminSidebarBookingBadge">
    0
</span>
```

**CSS:** [`static/css/admin.css:177-217`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\static\css\admin.css)

**Features:**
- ✅ Real-time updates qua SSE stream (10s interval)
- ✅ Chỉ đếm bookings với `status='pending'` (chờ xác nhận)
- ✅ Auto-reconnect khi mất kết nối
- ✅ Fallback to polling nếu SSE fails
- ✅ Pulse animation khi thay đổi

**Update Logic:** [`static/js/admin-sidebar-booking-badge.js`](d:\2_HOC_KI\6_SEMESTER\2.Lap_trinh_web\REFACTOR_SPA\LTW_Spa_Ana\spa_project\static\js\admin-sidebar-booking-badge.js)

```javascript
// Auto-update qua SSE stream
eventSource.addEventListener("message", function (event) {
    const data = JSON.parse(event.data);
    renderBadge(data.count);  // Update badge real-time
});
```

---

## 🔍 SỰ KHÁC BIỆT GIỮA 2 BADGES:

| Tính năng | Tab Header Badge | Sidebar Badge |
|----------|-----------------|---------------|
| **Vị trí** | Trong tab "Yêu cầu đặt lịch" | Sidebar "Quản lý lịch hẹn" |
| **Đếm gì** | **TẤT CẢ** bookings (trong tab hiện tại) | **CHỈ** pending bookings |
| **Update khi** | Filter/tab change | Real-time (SSE, 10s) |
| **Auto-hide** | ✅ Khi count = 0 | ✅ Khi count = 0 |
| **Animation** | ✅ Pulse khi thay đổi | ✅ Pulse khi thay đổi |
| **Color** | Đỏ gradient | Đỏ solid (#ff6b6b) |

---

## 🧪 TEST BADGES:

### **Test 1: Tab Header Badge**

```javascript
// F12 Console
console.log("Tab header badge:", document.getElementById("webCount").textContent);

// Test manual update
document.getElementById("webCount").textContent = "5";

// Test animation
document.getElementById("webCount").classList.add("badge-update");
setTimeout(() => {
  document.getElementById("webCount").classList.remove("badge-update");
}, 500);
```

### **Test 2: Sidebar Badge**

```javascript
// F12 Console
console.log("Sidebar badge:", document.getElementById("adminSidebarBookingBadge")?.textContent);

// Test manual update
const badge = document.getElementById("adminSidebarBookingBadge");
if (badge) {
  badge.textContent = "3";
  badge.classList.remove("d-none");
}
```

### **Test 3: Cả 2 Badges Sync**

```javascript
// Test function update
window.testBadgeUpdate = function(count) {
  // Update tab header badge
  const tabBadge = document.getElementById("webCount");
  if (tabBadge) {
    tabBadge.textContent = String(count);
    tabBadge.classList.add('badge-update');
    setTimeout(() => tabBadge.classList.remove('badge-update'), 500);
  }

  // Update sidebar badge
  const sidebarBadge = document.getElementById("adminSidebarBookingBadge");
  if (sidebarBadge) {
    sidebarBadge.textContent = String(count);
    sidebarBadge.classList.remove("d-none");
  }

  console.log(`✅ Updated both badges: ${count}`);
};

// Test
testBadgeUpdate(5);  // Should show "5" in both badges
testBadgeUpdate(0);  // Should hide both badges
```

---

## 🎨 CSS STYLING:

### **Tab Header Badge:**
```css
#webCount {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4) !important;
  min-width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

#webCount[data-count="0"] {
  display: none !important;  /* Hide khi 0 */
}
```

### **Sidebar Badge:**
```css
.sidebar-booking-badge {
  background: #ff6b6b;
  color: #ffffff;
  border-radius: 999px;
  box-shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
  transition: all 0.3s ease;
}
```

---

## 🔄 UPDATE FLOW:

### **Tab Header Badge:**
```
User filter/change → renderWebRequests()
    → loadBookingRequests(statusFilter)
    → API returns filtered data
    → updateBookingBadges(rows.length)
    → webCount.textContent = String(count)
    → Animation: badge-update class
```

### **Sidebar Badge:**
```
Backend creates pending booking
    → API stream sends update
    → SSE message listener
    → renderBadge(count)
    → adminSidebarBookingBadge.textContent = count
    → Animation: badge-pulse class
```

---

## ✅ EXPECTED BEHAVIOR:

### **Có 5 pending bookings:**

**Tab Header Badge:**
- Hiển thị: **"5"**
- Màu: Đỏ gradient
- Animation: Pulse khi filter thay đổi

**Sidebar Badge:**
- Hiển thị: **"5"**
- Màu: Đỏ solid
- Animation: Pulse khi có new booking

### **Có 0 pending bookings:**

**Tab Header Badge:**
- Ẩn hoàn toàn (`display: none`)
- Không chiếm chỗ

**Sidebar Badge:**
- Ẩn hoàn toàn (`d-none` class)
- Không chiếm chỗ

---

## 🚨 TROUBLESHOOTING:

### **Badge không hiển thị:**

**Tab Header Badge:**
```javascript
// Check element exists
console.log("webCount element:", document.getElementById("webCount"));

// Check visibility
const badge = document.getElementById("webCount");
console.log("Display:", window.getComputedStyle(badge).display);
console.log("Content:", badge.textContent);
```

**Sidebar Badge:**
```javascript
// Check element exists
console.log("Sidebar badge:", document.getElementById("adminSidebarBookingBadge"));

// Check visibility
const sidebarBadge = document.getElementById("adminSidebarBookingBadge");
console.log("Classes:", sidebarBadge?.className);
```

### **Badge không update:**

```javascript
// Test manual update
updateBookingBadges(999);  // Should show 999

// Check renderWebRequests() called
console.log("renderWebRequests function:", typeof renderWebRequests);
renderWebRequests();  // Manual trigger
```

### **Sidebar Badge SSE không hoạt động:**

```javascript
// Check SSE connection
const config = window.adminSidebarBookingBadgeConfig;
console.log("Badge config:", config);

// Test API manually
fetch('/api/booking/pending-count/')
  .then(r => r.json())
  .then(d => console.log("Pending count:", d.count));
```

---

## 📱 TEST NGAY BÂY GIỜ:

### **Bước 1: Restart Server**
```bash
cd spa_project
python manage.py runserver
```

### **Bước 2: Vào Admin Page**
```
http://127.0.0.1:8000/manage/appointments/
```

### **Bước 3: Open Console**
```
F12 → Console tab
```

### **Bước 4: Test Badges**

**Test Tab Header Badge:**
```javascript
// In console
testBadgeUpdate(3);
// Expected: Tab badge shows "3"
```

**Test Sidebar Badge:**
```javascript
// In console
fetch('/api/booking/pending-count/')
  .then(r => r.json())
  .then(d => console.log("Sidebar should show:", d.count));
```

### **Bước 5: Create Test Data**
```python
# Django shell
python manage.py shell

from appointments.models import Appointment
from spa_services.models import Service
from accounts.models import CustomerProfile
from datetime import date, time

service = Service.objects.first()
customer = CustomerProfile.objects.first()

# Create 3 pending bookings
for i in range(1, 4):
    Appointment.objects.create(
        customer=customer,
        service=service,
        appointment_date=date.today(),
        appointment_time=time(9 + i, 0),
        status='pending',
        source='web'
    )

print("✅ Created 3 pending bookings")
print("Tab badge should show: 3")
print("Sidebar badge should show: 3")
```

---

## 🎯 KEY BENEFITS:

### **Tab Header Badge:**
- ✅ **Contextual** - Hiển thị số bookings trong tab hiện tại
- ✅ **Fast** - Update ngay khi filter/tab change
- ✅ **Visible** - Nổi bật với gradient đỏ

### **Sidebar Badge:**
- ✅ **Real-time** - Update tự động mỗi 10s
- ✅ **Always visible** - Luôn thấy từ mọi page
- ✅ **Pending only** - Chỉ đếm bookings cần action

---

## 📊 COMPARISON:

| Use Case | Tab Header Badge | Sidebar Badge |
|----------|-----------------|---------------|
| **Check total bookings** | ✅ | ❌ (Only pending) |
| **Quick overview** | ✅ (Trong tab) | ✅ (Mọi page) |
| **Real-time updates** | ❌ (Manual refresh) | ✅ (SSE auto) |
| **Filter aware** | ✅ | ❌ (Show total pending) |

---

## 🚀 READY TO TEST!

**Cả 2 badges đã sẵn sàng!**

1. **Tab Header Badge:** Hiển thị số bookings sau khi filter
2. **Sidebar Badge:** Hiển thị số pending bookings real-time

**Test ngay và báo kết quả!** 🎉
