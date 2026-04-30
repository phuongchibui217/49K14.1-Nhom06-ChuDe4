# Booking Flow Documentation

## Overview

Document chi tiết về **luồng đặt lịch (booking flow)** từ khi khách hàng chọn dịch vụ đến khi staff xác nhận và hoàn tất dịch vụ.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Actor Definitions](#actor-definitions)
- [Flow Diagrams](#flow-diagrams)
  - [Flow 1: Customer Booking Online](#flow-1-customer-booking-online)
  - [Flow 2: Staff Confirmation](#flow-2-staff-confirmation)
  - [Flow 3: Staff Direct Booking](#flow-3-staff-direct-booking)
- [File Structure](#file-structure)
- [Database Schema](#database-schema)
- [State Transitions](#state-transitions)
- [API Integration](#api-integration)
- [Frontend Integration](#frontend-integration)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Customer Side          │         Staff Side                │
│  - Django Templates     │         - JavaScript SPA          │
│  - jQuery/Vanilla JS    │         - Fetch API                │
│  - Traditional Forms    │         - Polling                  │
└───────────┬─────────────────────────────┬──────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND LAYER (Django)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   views.py   │ ───▶ │  forms.py    │ ───▶ │services.py│ │
│  │              │      │              │      │           │ │
│  │ HTTP Logic   │      │ Form Validate│      │ Business  │ │
│  │ (Customer)   │      │              │      │ Logic     │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                     api.py                            │ │
│  │              (REST API - Staff)                       │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  - appointments  - customers  - rooms  - service_variants    │
│  - invoices     - payments   - services                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Actor Definitions

| Actor | Description | Access Methods |
|-------|-------------|----------------|
| **Customer** | Khách hàng đặt lịch qua website | Django Templates (HTML Forms) |
| **Staff** | Nhân viên lễ tân/admin quản lý booking | JavaScript SPA (REST API) |
| **System** | Automated processes (cron, tasks) | Backend scripts |

---

## Flow Diagrams

### Flow 1: Customer Booking Online

**Use Case:** Khách hàng tự đặt lịch qua website.

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: KHÁCH CHỌN DỊCH VỤ                                 │
└─────────────────────────────────────────────────────────────┘
     │
     │ URL: /services/massage-toan-than/
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Page: Service Detail                                        │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ [Button: ĐẶT LỊCH]                                  │       │
│ │                                                      │       │
│ │ JavaScript:                                          │       │
│ │ window.location.href = `/booking/?service_id=3`     │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ Redirect: /booking/?service_id=3
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: TRANG ĐẶT LỊCH (BOOKING PAGE)                       │
└─────────────────────────────────────────────────────────────┘
     │
     │ URL: /booking/
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: views.py → booking()                                │
│                                                              │
│ if request.method == 'GET':                                  │
│   selected_service_id = request.GET.get('service')          │
│   form = AppointmentForm()                                   │
│   if selected_service_id:                                    │
│     form.fields['service'].initial = selected_service_id     │
│                                                              │
│   return render(request, 'booking.html', {...})              │
└─────────────────────────────────────────────────────────────┘
     │
     │ Render HTML
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: booking.html                                      │
│                                                              │
│ JavaScript (DOMContentLoaded):                               │
│ ┌────────────────────────────────────────────────────┐       │
│ │ // 1. Đọc URL params                                │       │
│ │ const urlParams = new URLSearchParams(              │       │
│ │   window.location.search                            │       │
│ │ );                                                   │       │
│ │                                                      │       │
│ │ const serviceId = urlParams.get('service_id');       │       │
│ │                                                      │       │
│ │ // 2. Tự động chọn dropdown                         │       │
│ │ if (serviceId) {                                     │       │
│ │   serviceSelect.value = serviceId;  ▼ Auto-select    │       │
│ │ }                                                    │       │
│ │                                                      │       │
│ │ // 3. Validate frontend                             │       │
│ │ dateInput.setAttribute('min', today);  ▼ No past    │       │
│ │ timeInput.setAttribute('min', '09:00');             │       │
│ │ timeInput.setAttribute('max', '21:00');             │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ User điền form:
     │ - Tên khách: "Nguyễn Văn A"
     │ - SĐT: "0123456789"
     │ - Ngày: "2026-04-30"
     │ - Giờ: "14:00"
     │ - Gói dịch vụ: "Gói 90 phút"
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: USER SUBMIT FORM                                    │
└─────────────────────────────────────────────────────────────┘
     │
     │ HTML Form Submit:
     │ <form method="POST" action="/appointments/booking/">
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: views.py → booking()                                │
│                                                              │
│ if request.method == 'POST':                                │
│   form = AppointmentForm(request.POST)                      │
│                                                              │
│   if form.is_valid():  ← ⚠️ IMPORTANT                       │
│     # form.is_valid() trigger forms.py validation            │
└─────────────────────────────────────────────────────────────┘
     │
     │ forms.py → AppointmentForm.is_valid()
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: forms.py → AppointmentForm                          │
│                                                              │
│ class AppointmentForm(forms.ModelForm):                     │
│   ┌──────────────────────────────────────────────────┐      │
│   │ def clean_appointment_date(self):                 │      │
│   │   # Validate ngày không quá khứ                   │      │
│   │   validate_appointment_date(appointment_date)     │      │
│   └──────────────────────────────────────────────────┘      │
│                                                              │
│   ┌──────────────────────────────────────────────────┐      │
│   │ def clean_appointment_time(self):                 │      │
│   │   # Validate giờ 9-21h                            │      │
│   │   validate_appointment_time(appointment_time,    │      │
│   │                          appointment_date)        │      │
│   └──────────────────────────────────────────────────┘      │
│                                                              │
│   ┌──────────────────────────────────────────────────┐      │
│   │ def clean(self):                                  │      │
│   │   # Validate giờ kết thúc không > 21h             │      │
│   │   validate_appointment_time(..., duration_min)    │      │
│   └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     │ forms.py calls services.py
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: services.py                                         │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ def validate_appointment_date(...):                 │       │
│ │   if appointment_date < timezone.now().date():      │       │
│ │     raise ValidationError(                          │       │
│ │       'Ngày hẹn không được nhỏ hơn ngày hôm nay.'   │       │
│ │     )                                               │       │
│ └────────────────────────────────────────────────────┘       │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ def validate_appointment_time(...):                 │       │
│ │   if appointment_time < SPA_OPEN_TIME:              │       │
│ │     raise ValidationError('Giờ làm việc từ...')      │       │
│ │                                                      │       │
│ │   if appointment_time >= SPA_CLOSE_TIME:             │       │
│ │     raise ValidationError('Giờ hẹn phải trước...')   │       │
│ │                                                      │       │
│ │   end_time = _calc_end_time(appointment_time,       │       │
│ │                          duration_minutes)           │       │
│ │   if end_time > SPA_CLOSE_TIME:                      │       │
│ │     raise ValidationError('Gói X phút sẽ kết thúc...')│      │
│ │                                                      │       │
│ │   # Validate không đặt giờ quá khứ                  │       │
│ │   if appointment_date == now.date() and ...          │       │
│ │     raise ValidationError('Giờ hẹn phải sau...')     │       │
│ └────────────────────────────────────────────────────┘       │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ def check_room_availability(...):                   │       │
│ │   # Query existing appointments in same room        │       │
│ │   # Check overlapping time slots                    │       │
│ │   # Compare with room.capacity                      │       │
│ │   if overlapping_count >= room.capacity:             │       │
│ │     return (False, conflict, 'Phòng đã đầy...')     │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ If validation FAIL → Return error to form
     │ If validation PASS → Continue
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: views.py → booking() (continued)                    │
│                                                              │
│ if form.is_valid():                                          │
│   # Tìm hoặc tạo customer                                   │
│   customer = _get_or_create_customer(                        │
│     phone=booker_phone,                                     │
│     customer_name=booker_name                               │
│   )                                                          │
│                                                              │
│   # Gán phòng mặc định                                     │
│   default_room = Room.objects.filter(                        │
│     is_active=True                                           │
│   ).first()                                                  │
│                                                              │
│   # Tạo appointment                                        │
│   appointment = form.save(commit=False)                      │
│   appointment.customer = customer                            │
│   appointment.room = default_room                            │
│   appointment.source = 'ONLINE'                              │
│   appointment.status = 'PENDING'  ← ⚠️ KEY                  │
│   appointment.created_by = request.user                      │
│   appointment.save()                                         │
│                                                              │
│   messages.success(request, 'Đặt lịch thành công!')          │
│   return redirect('appointments:my_appointments')            │
└─────────────────────────────────────────────────────────────┘
     │
     │ Database INSERT
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Database: appointments table                                │
│                                                              │
│ INSERT INTO appointments (                                  │
│   appointment_code = 'APT-20260430-001',                    │
│   status = 'PENDING',         ← Chờ xác nhận                 │
│   source = 'ONLINE',          ← Đặt từ web                  │
│   customer_id = 45,                                        │
│   service_variant_id = 5,                                   │
│   room_id = 1,                                              │
│   appointment_date = '2026-04-30',                           │
│   appointment_time = '14:00',                               │
│   created_at = NOW(),                                       │
│   created_by_id = 2                                         │
│ );                                                           │
└─────────────────────────────────────────────────────────────┘
     │
     │ Redirect to customer view
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: KHÁCH XEM LẠI (MY APPOINTMENTS)                      │
└─────────────────────────────────────────────────────────────┘
     │
     │ URL: /appointments/my-appointments
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: views.py → my_appointments()                        │
│                                                              │
│ appointments = customer_profile.appointments.filter(         │
│   deleted_at__isnull=True                                   │
│ ).order_by('-created_at')                                    │
│                                                              │
│ return render(request, 'my_appointments.html', {            │
│   'appointments': appointments,                              │
│   'status_filter': 'all'                                    │
│ })                                                           │
└─────────────────────────────────────────────────────────────┘
     │
     │ Render template
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: my_appointments.html                              │
│                                                              │
│ Display:                                                     │
│ ┌────────────────────────────────────────────────────┐       │
│ │ Mã: APT-20260430-001                               │       │
│ │ Dịch vụ: Massage toàn thân                         │       │
│ │ Gói: Gói 90 phút                                   │       │
│ │ Ngày: 30/04/2026                                   │       │
│ │ Giờ: 14:00                                         │       │
│ │ Trạng thái: 🟡 Chờ xác nhận (PENDING)              │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**⏱️ Total Time:** ~2-3 seconds

**🔑 Key Points:**
- ✅ Customer KHÔNG gọi API trực tiếp
- ✅ Sử dụng Django Forms (traditional)
- ✅ Frontend validation (JavaScript)
- ✅ Backend validation (services.py)
- ✅ Status = `PENDING` (chờ staff xác nhận)

---

### Flow 2: Staff Confirmation

**Use Case:** Staff xem yêu cầu booking và xác nhận.

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: STAFF MỞ TRANG QUẢN LÝ                              │
└─────────────────────────────────────────────────────────────┘
     │
     │ URL: /manage/admin-appointments
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: admin-appointments.html + admin-appointments.js   │
│                                                              │
│ JavaScript:                                                  │
│ ┌────────────────────────────────────────────────────┐       │
│ │ // Polling: Gọi API mỗi 30s                         │       │
│ │ setInterval(() => {                                 │       │
│ │   fetchPendingAppointments();                       │       │
│ │ }, 30000);                                          │       │
│ │                                                      │       │
│ │ function fetchPendingAppointments() {                │       │
│ │   fetch('/api/booking-requests/?status=PENDING')    │       │
│ │     .then(res => res.json())                         │       │
│ │     .then(data => {                                  │       │
│ │       renderPendingList(data.appointments);          │       │
│ │       updateBadge(data.appointments.length);         │       │
│ │     });                                              │       │
│ │ }                                                    │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ API Call
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: api.py → api_booking_requests()                     │
│                                                              │
│ @require_http_methods(["GET"])                              │
│ def api_booking_requests(request):                           │
│   if not _is_staff(request.user):                            │
│     return _deny()                                           │
│                                                              │
│   appointments = Appointment.objects.filter(                 │
│     status='PENDING',                                        │
│     source='ONLINE'  ← Chỉ lấy booking online               │
│   ).order_by('-created_at')                                  │
│                                                              │
│   return JsonResponse({                                      │
│     'success': True,                                         │
│     'appointments': [                                        │
│       serialize_appointment(a) for a in appointments         │
│     ]                                                        │
│   })                                                         │
└─────────────────────────────────────────────────────────────┘
     │
     │ JSON Response
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: JavaScript render list                            │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ data.appointments.forEach(appt => {                  │       │
│ │   const card = createAppointmentCard(appt);          │       │
│ │   container.appendChild(card);                       │       │
│ │ });                                                   │       │
│ └────────────────────────────────────────────────────┘       │
│                                                              │
│ Display:                                                     │
│ ┌────────────────────────────────────────────────────┐       │
│ │ ┌──────────────────────────────────────────────┐    │       │
│ │ │ Nguyễn Văn A                                  │    │       │
│ │ │ Massage toàn thân - Gói 90 phút              │    │       │
│ │ │ 30/04/2026 14:00                              │    │       │
│ │ │ Phòng: VIP                                    │    │       │
│ │ │                                                │    │       │
│ │ │ [XÁC NHẬN] [TỪ CHỐI] [CHI TIẾT]               │    │       │
│ │ └──────────────────────────────────────────────┘    │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ Staff click [XÁC NHẬN]
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: STAFF XÁC NHẬN BOOKING                             │
└─────────────────────────────────────────────────────────────┘
     │
     │ JavaScript:
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: admin-appointments.js                              │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ function confirmAppointment(code) {                 │       │
│ │   if (!confirm('Xác nhận booking này?')) return;    │       │
│ │                                                      │       │
│ │   fetch(`/api/appointments/${code}/status/`, {       │       │
│ │     method: 'POST',                                  │       │
│ │     headers: {                                        │       │
│ │       'Content-Type': 'application/json'             │       │
│ │     },                                                 │       │
│ │     body: JSON.stringify({                           │       │
│ │       status: 'NOT_ARRIVED'  ← ⚠️ KEY               │       │
│ │     })                                                │       │
│ │   })                                                  │       │
│ │     .then(res => res.json())                         │       │
│ │     .then(data => {                                  │       │
│ │       if (data.success) {                            │       │
│ │         showToast('✅ Đã xác nhận lịch hẹn');         │       │
│ │         refreshList();                               │       │
│ │       } else {                                       │       │
│ │         showToast('❌ ' + data.error);               │       │
│ │       }                                              │       │
│ │     });                                              │       │
│ │ }                                                    │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ API Call: POST /api/appointments/APT-001/status/
     │ Body: {"status": "NOT_ARRIVED"}
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: api.py → api_appointment_status()                   │
│                                                              │
│ @require_http_methods(["POST"])                             │
│ @staff_api                                                   │
│ def api_appointment_status(request, appointment_code):      │
│   appointment = Appointment.objects.get(                     │
│     appointment_code=appointment_code                        │
│   )                                                          │
│                                                              │
│   data = json.loads(request.body)                           │
│   new_status = str(data.get('status', '')).strip().upper()  │
│                                                              │
│   appointment.status = new_status  ← "NOT_ARRIVED"          │
│   appointment.save()                                         │
│                                                              │
│   return JsonResponse({                                      │
│     'success': True,                                         │
│     'message': f'Đã cập nhật trạng thái: ...'                │
│   })                                                         │
└─────────────────────────────────────────────────────────────┘
     │
     │ Database UPDATE
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Database: appointments table                                │
│                                                              │
│ UPDATE appointments                                          │
│ SET status = 'NOT_ARRIVED',    ← Đã xác nhận                 │
│     updated_at = NOW()                                        │
│ WHERE appointment_code = 'APT-20260430-001'                  │
└─────────────────────────────────────────────────────────────┘
     │
     │ API Response
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: JavaScript handle response                        │
│                                                              │
│ if (data.success) {                                          │
│   showToast('✅ Đã xác nhận lịch hẹn');                       │
│   refreshList();  ← Gọi lại API để cập nhật UI              │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
     │
     │ Refresh list
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: Updated UI                                        │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ ┌──────────────────────────────────────────────┐    │       │
│ │ │ Nguyễn Văn A                                  │    │       │
│ │ │ Massage toàn thân - Gói 90 phút              │    │       │
│ │ │ 30/04/2026 14:00                              │    │       │
│ │ │ Trạng thái: 🟢 Đã xác nhận (NOT_ARRIVED)      │    │       │
│ │ │                                                │    │       │
│ │ │ [ĐẾN] [HOÀN THÀNH] [HỦY] [CHI TIẾT]            │    │       │
│ │ └──────────────────────────────────────────────┘    │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**⏱️ Total Time:** ~1-2 seconds

**🔑 Key Points:**
- ✅ Staff gọi API trực tiếp (REST)
- ✅ Sử dụng Fetch API (AJAX)
- ✅ Real-time update (polling 30s)
- ✅ Status thay đổi: `PENDING` → `NOT_ARRIVED`

---

### Flow 3: Staff Direct Booking

**Use Case:** Staff tạo booking trực tiếp (khách gọi điện, đến trực tiếp).

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: STAFF MỞ FORM TẠO BOOKING                          │
└─────────────────────────────────────────────────────────────┘
     │
     │ URL: /manage/admin-appointments
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: admin-appointments.html                           │
│                                                              │
│ Button: [TẠO BOOKING TRỰC TIẾP]                            │
│   ↓                                                          │
│ Modal: Create Booking Form                                   │
└─────────────────────────────────────────────────────────────┘
     │
     │ Staff điền form:
     │ - Booker: Nguyễn Văn A
     │ - Booker Phone: 0123456789
     │
     │ Thêm khách:
     │ - Customer: Nguyễn Văn A
     │ - Variant: Gói 90 phút
     │ - Room: VIP
     │ - Date: 2026-04-30
     │ - Time: 14:00
     │ - Payment: PAID
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: STAFF SUBMIT FORM                                   │
└─────────────────────────────────────────────────────────────┘
     │
     │ JavaScript:
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: admin-appointments.js                              │
│                                                              │
│ ┌────────────────────────────────────────────────────┐       │
│ │ function createBooking() {                          │       │
│ │   const data = {                                    │       │
│ │     booker: {                                       │       │
│ │       name: 'Nguyễn Văn A',                         │       │
│ │       phone: '0123456789',                          │       │
│ │       source: 'DIRECT'  ← ⚠️ KEY                   │       │
│ │     },                                               │       │
│ │     guests: [                                        │       │
│ │       {                                              │       │
│ │         name: 'Nguyễn Văn A',                       │       │
│ │         variantId: 5,                               │       │
│ │         roomId: 'VIP',                              │       │
│ │         date: '2026-04-30',                         │       │
│ │         time: '14:00',                              │       │
│ │         apptStatus: 'NOT_ARRIVED',  ← ⚠️ KEY        │       │
│ │         payStatus: 'PAID'                           │       │
│ │       }                                              │       │
│ │     ]                                                │       │
│ │   };                                                 │       │
│ │                                                      │       │
│ │   fetch('/api/appointments/create-batch/', {        │       │
│ │     method: 'POST',                                  │       │
│ │     headers: {                                        │       │
│ │       'Content-Type': 'application/json'             │       │
│ │     },                                                 │       │
│ │     body: JSON.stringify(data)                       │       │
│ │   })                                                  │       │
│ │     .then(res => res.json())                         │       │
│ │     .then(data => {                                  │       │
│ │       if (data.success) {                            │       │
│ │         showToast('✅ Đã tạo booking');               │       │
│ │         refreshList();                               │       │
│ │       } else {                                       │       │
│ │         showToast('❌ ' + data.error);               │       │
│ │       }                                              │       │
│ │     });                                              │       │
│ │ }                                                    │       │
│ └────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
     │
     │ API Call: POST /api/appointments/create-batch/
     │ Body: {booker: {...}, guests: [{...}]}
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Python: api.py → api_appointment_create_batch()             │
│                                                              │
│ @require_http_methods(["POST"])                             │
│ @staff_api                                                   │
│ def api_appointment_create_batch(request):                  │
│   raw = json.loads(request.body)                            │
│   booker = raw.get('booker', {})                            │
│   guests = raw.get('guests', [])                            │
│                                                              │
│   created = []                                              │
│   errors = []                                               │
│                                                              │
│   for idx, g in enumerate(guests):                          │
│     # 1. Validate data                                      │
│     validation = _validate_appointment_data(data)           │
│     if not validation['valid']:                             │
│       errors.append(f"Khách {idx+1}: {...}")                │
│       continue                                              │
│                                                              │
│     # 2. Resolve customer                                   │
│     customer = _get_or_create_customer(phone, name)         │
│                                                              │
│     # 3. Create appointment                                 │
│     with transaction.atomic():                              │
│       appt = Appointment.objects.create(                    │
│         customer=customer,                                  │
│         service_variant=variant,                            │
│         room=room,                                          │
│         booker_name=booker_name,                            │
│         booker_phone=booker_phone,                          │
│         appointment_date=date,                              │
│         appointment_time=time,                              │
│         status='NOT_ARRIVED',  ← ⚠️ KEY                    │
│         source='DIRECT',        ← ⚠️ KEY                   │
│         payment_status='PAID',                              │
│         created_by=request.user                             │
│       )                                                     │
│                                                              │
│       # 4. Create invoice & payment                         │
│       _create_invoice_and_payment(appt, pay_status, ...)    │
│                                                              │
│       created.append(serialize_appointment(appt))           │
│                                                              │
│   return JsonResponse({                                      │
│     'success': True,                                         │
│     'message': f'Đã tạo {len(created)} lịch hẹn',            │
│     'appointments': created,                                │
│     'errors': errors                                        │
│   })                                                         │
└─────────────────────────────────────────────────────────────┘
     │
     │ Database INSERT (multiple records)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Database: appointments table                                │
│                                                              │
│ INSERT INTO appointments (                                  │
│   appointment_code = 'APT-20260430-002',                    │
│   status = 'NOT_ARRIVED',     ← Đã xác nhận ngay            │
│   source = 'DIRECT',          ← Tạo trực tiếp               │
│   customer_id = 45,                                        │
│   service_variant_id = 5,                                   │
│   room_id = 1,                                              │
│   appointment_date = '2026-04-30',                           │
│   appointment_time = '14:00',                               │
│   payment_status = 'PAID',     ← Đã thanh toán              │
│   created_at = NOW(),                                       │
│   created_by_id = 3                                         │
│ );                                                           │
│                                                              │
│ INSERT INTO invoices (                                       │
│   appointment_id = 456,                                     │
│   subtotal_amount = 900000,                                  │
│   final_amount = 900000,                                    │
│   status = 'PAID'                                           │
│ );                                                           │
│                                                              │
│ INSERT INTO invoice_payments (                               │
│   invoice_id = 789,                                         │
│   amount = 900000,                                          │
│   payment_method = 'CASH',                                  │
│   transaction_status = 'SUCCESS',                           │
│   recorded_by_id = 3                                        │
│ );                                                           │
└─────────────────────────────────────────────────────────────┘
     │
     │ API Response
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: JavaScript handle response                        │
│                                                              │
│ if (data.success) {                                          │
│   showToast(`✅ Đã tạo ${data.appointments.length} booking`); │
│   closeModal();                                              │
│   refreshList();                                            │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
```

**⏱️ Total Time:** ~2-3 seconds

**🔑 Key Points:**
- ✅ Staff tạo booking trực tiếp
- ✅ Status = `NOT_ARRIVED` (không cần confirm)
- ✅ Source = `DIRECT` (không phải online)
- ✅ Có thể tạo nhiều booking cùng lúc (batch)
- ✅ Tạo luôn invoice + payment

---

## File Structure

```
spa_project/appointments/
├── models.py              # Database models
├── views.py               # Customer-facing views (Django templates)
├── forms.py               # Django Forms (validation)
├── services.py            # Business logic
├── api.py                 # REST API endpoints (staff)
├── urls.py                # URL routing
├── serializers.py         # Data serialization
└── templates/appointments/
    ├── booking.html       # Customer booking page
    └── my_appointments.html # Customer appointments list

spa_project/static/js/
├── admin-appointments.js  # Staff appointment management
└── dialog-modal.js        # Modal components

spa_project/templates/manage/
└── pages/
    └── admin_appointments.html # Staff dashboard
```

---

## Database Schema

### appointments table

```sql
CREATE TABLE appointments (
  id INTEGER PRIMARY KEY,
  appointment_code VARCHAR(50) UNIQUE,
  status VARCHAR(20),  -- PENDING, NOT_ARRIVED, ARRIVED, COMPLETED, CANCELLED, REJECTED
  source VARCHAR(20),  -- ONLINE, DIRECT
  customer_id INTEGER,
  service_variant_id INTEGER,
  room_id INTEGER,
  booker_name VARCHAR(100),
  booker_phone VARCHAR(20),
  booker_email VARCHAR(100),
  customer_name_snapshot VARCHAR(100),
  customer_phone_snapshot VARCHAR(20),
  customer_email_snapshot VARCHAR(100),
  appointment_date DATE,
  appointment_time TIME,
  notes TEXT,
  staff_notes TEXT,
  payment_status VARCHAR(20),  -- UNPAID, PARTIAL, PAID, REFUNDED
  created_at TIMESTAMP,
  created_by_id INTEGER,
  updated_at TIMESTAMP,
  cancelled_by VARCHAR(20),
  deleted_at TIMESTAMP,
  deleted_by_user_id INTEGER,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (service_variant_id) REFERENCES service_variants(id),
  FOREIGN KEY (room_id) REFERENCES rooms(id),
  FOREIGN KEY (created_by_id) REFERENCES users(id),
  FOREIGN KEY (deleted_by_user_id) REFERENCES users(id)
);
```

### invoices table

```sql
CREATE TABLE invoices (
  id INTEGER PRIMARY KEY,
  appointment_id INTEGER,
  subtotal_amount DECIMAL(10, 0),
  discount_amount DECIMAL(10, 0),
  final_amount DECIMAL(10, 0),
  status VARCHAR(20),  -- UNPAID, PARTIAL, PAID, REFUNDED
  created_at TIMESTAMP,
  created_by_id INTEGER,
  FOREIGN KEY (appointment_id) REFERENCES appointments(id),
  FOREIGN KEY (created_by_id) REFERENCES users(id)
);
```

### invoice_payments table

```sql
CREATE TABLE invoice_payments (
  id INTEGER PRIMARY KEY,
  invoice_id INTEGER,
  amount DECIMAL(10, 0),
  payment_method VARCHAR(20),  -- CASH, CARD, BANK_TRANSFER, E_WALLET
  transaction_status VARCHAR(20),  -- SUCCESS, FAILED, PENDING
  recorded_no VARCHAR(50),
  note TEXT,
  recorded_at TIMESTAMP,
  recorded_by_id INTEGER,
  FOREIGN KEY (invoice_id) REFERENCES invoices(id),
  FOREIGN KEY (recorded_by_id) REFERENCES users(id)
);
```

---

## State Transitions

### Appointment Status Flow

```
                    ┌─────────────┐
                    │   PENDING   │ ◄── Customer Booking Online
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ NOT_ARRIVED │  │  CANCELLED  │  │  REJECTED   │
    └──────┬──────┘  └─────────────┘  └─────────────┘
           │               ▲               ▲
           │               │               │
           ▼               │               │
    ┌─────────────┐        │               │
    │   ARRIVED   │        │               │
    └──────┬──────┘        │               │
           │               │               │
           ▼               │               │
    ┌─────────────┐        │               │
    │  COMPLETED  │        │               │
    └─────────────┘        └───────────────┴─────┐
                                                 │
                                                 │ Rebook
                                                 │
                                   ┌─────────────┴──────┐
                                   │   PENDING (rebook)  │
                                   └──────────────────────┘
```

### Payment Status Flow

```
┌───────────┐
│  UNPAID   │ ◄── Customer booking (no payment)
└─────┬─────┘
      │
      ├──────────┐
      ▼          ▼
┌───────────┐ ┌───────────┐
│  PARTIAL  │ │   PAID    │ ◄── Staff direct booking
└─────┬─────┘ └───────────┘
      │            │
      └────┬───────┘
           ▼
    ┌───────────┐
    │  REFUNDED │
    └───────────┘
```

---

## API Integration

### Customer Flow (No API)

```
Customer Browser
    ↓
HTTP POST /appointments/booking/
    ↓
views.py → booking()
    ↓
forms.py → AppointmentForm.is_valid()
    ↓
services.py → validate_*()
    ↓
Database INSERT
    ↓
HTTP Redirect → /appointments/my-appointments
    ↓
views.py → my_appointments()
    ↓
Render HTML Template
```

### Staff Flow (REST API)

```
Staff Browser (JavaScript)
    ↓
Fetch API → GET /api/booking-requests/
    ↓
api.py → api_booking_requests()
    ↓
Database SELECT
    ↓
JSON Response → JavaScript
    ↓
Render UI (DOM manipulation)
    ↓
User Action (Confirm button)
    ↓
Fetch API → POST /api/appointments/<code>/status/
    ↓
api.py → api_appointment_status()
    ↓
Database UPDATE
    ↓
JSON Response → JavaScript
    ↓
Refresh UI
```

---

## Frontend Integration

### Customer Side (Django Templates)

**File:** `templates/appointments/booking.html`

```html
<form method="post" action="{% url 'appointments:booking' %}">
  {% csrf_token %}
  {{ form.booker_name }}
  {{ form.booker_phone }}

  <input name="customer_name_snapshot"
         value="{{ customer_profile.full_name }}">

  {{ form.service_variant }}
  {{ form.appointment_date }}
  {{ form.appointment_time }}

  <button type="submit">Xác nhận đặt lịch</button>
</form>
```

**JavaScript:** `booking.html` (inline)

```javascript
// Pre-select from URL params
const urlParams = new URLSearchParams(window.location.search);
const serviceId = urlParams.get('service_id');
if (serviceId) {
  serviceSelect.value = serviceId;
}

// Validate frontend
dateInput.setAttribute('min', today);
timeInput.setAttribute('min', '09:00');
timeInput.setAttribute('max', '21:00');
```

### Staff Side (JavaScript SPA)

**File:** `static/js/admin-appointments.js`

```javascript
// Polling pending bookings
setInterval(() => {
  fetch('/api/booking-requests/?status=PENDING')
    .then(res => res.json())
    .then(data => {
      renderPendingList(data.appointments);
    });
}, 30000);

// Confirm booking
function confirmAppointment(code) {
  fetch(`/api/appointments/${code}/status/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status: 'NOT_ARRIVED'})
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast('✅ Đã xác nhận');
      refreshList();
    }
  });
}
```

---

## Key Differences Summary

| Aspect | Customer Flow | Staff Flow |
|--------|---------------|------------|
| **Interface** | Django Templates (HTML) | JavaScript SPA |
| **Communication** | HTTP POST (Form submit) | Fetch API (AJAX) |
| **Backend** | views.py | api.py |
| **Initial Status** | `PENDING` (chờ confirm) | `NOT_ARRIVED` (đã confirm) |
| **Source** | `ONLINE` | `DIRECT` |
| **Validation** | Frontend + Backend | Backend only |
| **Response** | HTTP Redirect | JSON |
| **Real-time** | No (manual refresh) | Yes (polling 30s) |

---

## Performance Considerations

### Optimization Tips

1. **Database Indexing:**
   ```python
   class Appointment(models.Model):
     status = models.CharField(db_index=True)
     source = models.CharField(db_index=True)
     appointment_date = models.DateField(db_index=True)
     created_at = models.DateTimeField(db_index=True)
   ```

2. **Query Optimization:**
   ```python
   # Bad: N+1 queries
   appointments = Appointment.objects.all()
   for appt in appointments:
     print(appt.customer.full_name)  # Query mỗi lần

   # Good: select_related
   appointments = Appointment.objects.select_related(
     'customer', 'service_variant', 'room'
   ).all()
   ```

3. **Caching:**
   ```python
   # Cache pending count
   from django.core.cache import cache

   def get_pending_count():
     count = cache.get('pending_count')
     if count is None:
       count = Appointment.objects.filter(
         status='PENDING'
       ).count()
       cache.set('pending_count', count, 30)  # 30s
     return count
   ```

4. **Pagination:**
   ```python
   from django.core.paginator import Paginator

   def api_appointments_list(request):
     appointments = Appointment.objects.all()
     paginator = Paginator(appointments, 20)  # 20 per page
     page = request.GET.get('page', 1)
     return paginator.page(page)
   ```

---

## Troubleshooting

### Common Issues

**Issue 1: Booking không hiển thị trong admin**

```
Cause: status != PENDING hoặc source != ONLINE
Fix: Check filter trong api_booking_requests()
```

**Issue 2: Validate báo "Phòng đã đầy" nhưng phòng trống**

```
Cause: overlapping_count tính sai
Fix: Check logic trong check_room_availability()
```

**Issue 3: JavaScript không polling**

```
Cause: setInterval bị block bởi browser
Fix: Check console.log() để debug
```

**Issue 4: Status không update sau khi confirm**

```
Cause: API endpoint bị 403 Forbidden
Fix: Check user.is_staff permission
```

---

## Future Improvements

1. **WebSocket for Real-time Updates**
   - Thay thế polling bằng WebSocket
   - Instant update khi có booking mới

2. **SMS/Email Notifications**
   - Gửi SMS cho customer khi confirm
   - Email reminder trước 1 ngày

3. **Calendar View**
   - Hiển thị booking dạng calendar
   - Drag-drop để reschedule

4. **Mobile App**
   - Customer app để đặt lịch
   - Staff app để quản lý

5. **Analytics Dashboard**
   - Thống kê booking theo ngày/tuần/tháng
   - Doanh thu theo dịch vụ

---

## Conclusion

Hiểu rõ **booking flow** giúp bạn:

1. ✅ Debug vấn đề nhanh hơn
2. ✅ Thêm tính năng dễ dàng
3. ✅ Optimize performance
4. ✅ Maintain code hiệu quả

**Key Takeaways:**
- Customer dùng Django Templates (traditional)
- Staff dùng REST API (modern)
- services.py chứa business logic quan trọng
- Status = `PENDING` là key point giữa 2 flows

---

**Last Updated:** 2026-04-30
**Version:** 1.0
**Author:** Spa ANA Team
