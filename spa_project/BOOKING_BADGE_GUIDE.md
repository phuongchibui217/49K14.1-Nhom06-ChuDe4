# Notification Badge Implementation Guide
## Yêu cầu đặt lịch chờ xác nhận

---

## ✅ IMPLEMENTATION COMPLETED

### **1. Backend API (Django)**

**File:** `appointments/api.py`

**New Endpoints:**
```python
# GET /api/booking/pending-count/
@require_http_methods(["GET"])
def api_booking_pending_count(request)
# Returns: {"success": true, "count": 5, "timestamp": "2026-04-12T10:30:00"}

# GET /api/booking/pending-count/stream/
def api_booking_pending_count_stream(request)
# SSE Stream: data: {"count": 5, "timestamp": "2026-04-12T10:30:00"}
```

**URL Configuration:** `appointments/urls.py`
```python
path('api/booking/pending-count/', api.api_booking_pending_count, name='api_booking_pending_count'),
path('api/booking/pending-count/stream/', api.api_booking_pending_count_stream, name='api_booking_pending_count_stream'),
```

---

### **2. Frontend JavaScript**

**File:** `static/js/admin-sidebar-booking-badge.js`

**Features:**
- ✅ Auto-fetch initial count on page load
- ✅ Real-time updates via SSE stream (10s interval)
- ✅ Auto-reconnection on connection loss (3s delay)
- ✅ Graceful fallback to polling if EventSource not supported
- ✅ Badge animation on count change
- ✅ Format: Shows "99+" for counts > 99

**Configuration:** `templates/manage/base.html`
```javascript
window.adminSidebarBookingBadgeConfig = {
    countUrl: "{% url 'appointments:api_booking_pending_count' %}",
    countStreamUrl: "{% url 'appointments:api_booking_pending_count_stream' %}"
};
```

---

### **3. UI Components**

**Sidebar Badge HTML:** `templates/manage/includes/sidebar.html`
```html
<span class="sidebar-booking-badge d-none" id="adminSidebarBookingBadge"
      aria-live="polite" aria-label="Số yêu cầu đặt lịch chờ xác nhận">0</span>
```

**CSS Styling:** `static/css/admin.css`
```css
.sidebar-booking-badge {
    background: #ff6b6b;  /* Red color for urgency */
    color: #ffffff;
    /* Badge pulse animation on count change */
}
```

---

## 🧪 TESTING STEPS

### **Step 1: Test API Endpoints**

```bash
# 1. Start Django server
cd spa_project
python manage.py runserver

# 2. Login as admin/staff user
# 3. Test API endpoint
curl http://127.0.0.1:8000/api/booking/pending-count/
# Expected: {"success": true, "count": 0, "timestamp": "..."}

# 4. Test SSE stream
curl http://127.0.0.1:8000/api/booking/pending-count/stream/
# Expected: SSE stream with data updates every 10s
```

### **Step 2: Test Badge UI**

1. **Create test booking requests:**
   ```python
   # In Django shell: python manage.py shell
   from appointments.models import Appointment
   from spa_services.models import Service
   from accounts.models import CustomerProfile
   from datetime import date, time

   # Create 3 test pending bookings
   service = Service.objects.first()
   customer = CustomerProfile.objects.first()

   for i in range(3):
       Appointment.objects.create(
           customer=customer,
           service=service,
           appointment_date=date.today(),
           appointment_time=time(14, 0),
           status='pending',
           source='web'
       )
   ```

2. **Check badge display:**
   - Go to: `http://127.0.0.1:8000/manage/appointments/`
   - Look at sidebar: "Quản lý lịch hẹn"
   - Expected: Red badge showing "3"

3. **Test real-time updates:**
   - Create new booking via web interface
   - Badge should auto-update within 10 seconds
   - Badge will pulse animation when count changes

4. **Test badge hide/show:**
   - Approve all pending bookings
   - Badge should disappear (count = 0)
   - Create new booking → Badge reappears

### **Step 3: Test Error Handling**

1. **Connection loss:**
   - Stop Django server
   - Badge should attempt reconnect every 3s
   - Restart server → Badge should reconnect

2. **Invalid API response:**
   - Badge should keep showing current count
   - No UI errors shown to user

---

## 🎨 CUSTOMIZATION

### **Change Badge Color:**
```css
/* static/css/admin.css */
.sidebar-booking-badge {
    background: #YOUR_COLOR;  /* Change red to preferred color */
}
```

### **Change Update Interval:**
```python
# appointments/api.py - _booking_count_stream_generator()
time.sleep(10)  # Change 10 to preferred seconds
```

### **Change Badge Position:**
```html
<!-- templates/manage/includes/sidebar.html -->
<!-- Move badge inside or outside link as needed -->
```

---

## 🔧 TROUBLESHOOTING

**Badge not showing:**
1. Check browser console for errors
2. Verify API endpoint works: `/api/booking/pending-count/`
3. Check user permissions (must be staff/superuser)
4. Clear browser cache

**Badge not updating:**
1. Check SSE stream is working
2. Look for JavaScript errors in console
3. Verify network tab for SSE connection
4. Check EventSource support in browser

**Count incorrect:**
1. Check database for appointments with `status='pending'` and `source='web'`
2. Run query: `Appointment.objects.filter(status='pending', source='web').count()`
3. Verify API returns correct count

---

## 📊 PERFORMANCE NOTES

- **SSE Stream:** Maintains persistent connection (minimal overhead)
- **Polling Fallback:** Only used if EventSource not supported (30s interval)
- **Database Query:** Optimized with `.count()` (fast)
- **Browser Compatibility:** Works in all modern browsers

---

## 🚀 FUTURE ENHANCEMENTS

1. **Sound notification:** Play sound when new booking arrives
2. **Desktop notification:** Browser push notifications
3. **Multiple filters:** Show badges for different statuses
4. **Historical data:** Track booking trends over time
5. **WebSocket upgrade:** For true real-time updates

---

**Last Updated:** 2026-04-12
**Status:** ✅ Ready for Production
**Tested:** Django 4.2+, Python 3.12+
