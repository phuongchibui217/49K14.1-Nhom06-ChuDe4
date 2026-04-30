# Appointments API Documentation

## Overview

Django REST API cho quản lý lịch hẹn (appointments) trong hệ thống Spa ANA.

**Base URL:** `/api/`

**Authentication:** Yêu cầu user đã đăng nhập và có quyền staff/admin.

**Response Format:** JSON

```json
{
  "success": true/false,
  "data": { ... },
  "error": "Error message (if success=false)"
}
```

---

## 📋 Table of Contents

- [Appointments](#appointments)
  - [List Appointments](#1-get-apiappointments---danh-sách-lịch-hẹn)
  - [Search Appointments](#2-get-apiappointmentssearch---tìm-lịch-hẹn-toàn-hệ-thống)
  - [Appointment Detail](#3-get-apiappointmentscode---chi-tiết-lịch-hẹn)
  - [Create Appointment (Batch)](#4-post-apiappointmentscreate-batch---tạo-nhiều-lịch-hẹn)
  - [Update Appointment](#5-post-apiappointmentscodeupdate---cập-nhật-lịch-hẹn)
  - [Change Status](#6-post-apiappointmentscodestatus---đổi-trạng-thái)
  - [Delete Appointment](#7-post-apiappointmentscodedelete---xóa-lịch-hẹn)
  - [Rebook Appointment](#8-getpost-apiappointmentscoderebook---đặt-lại-lịch-hẹn)
- [Booking Requests](#booking-requests)
  - [List Booking Requests](#9-get-apibooking-requests---xem-yêu-cầu-đặt-lịch)
  - [Pending Count](#10-get-apibookingpending-count---số-lượng-pending)
- [Rooms](#rooms)
  - [List Rooms](#11-get-apirooms---danh-sách-phòng)
- [Customers](#customers)
  - [Search Customer](#12-get-apicustomerssearch---tìm-khách-hàng)

---

## Appointments

### 1. GET /api/appointments/ - Danh sách lịch hẹn

Lấy danh sách lịch hẹn có filter.

**Endpoint:** `GET /api/appointments/`

**Permission:** Staff/Admin

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | string | Filter theo ngày (YYYY-MM-DD) | `?date=2026-04-30` |
| `status` | string | Filter theo trạng thái | `?status=NOT_ARRIVED` |
| `source` | string | Filter theo nguồn (ONLINE, DIRECT) | `?source=ONLINE` |
| `service` | int | Filter theo service ID | `?service=3` |
| `q` | string | Tìm kiếm tự do | `?q=Nguyen Van A` |

**Status Values:** `PENDING`, `NOT_ARRIVED`, `ARRIVED`, `COMPLETED`, `CANCELLED`, `REJECTED`

**Response:**

```json
{
  "success": true,
  "appointments": [
    {
      "code": "APT-20260430-001",
      "status": "NOT_ARRIVED",
      "source": "ONLINE",
      "customerName": "Nguyễn Văn A",
      "customerPhone": "0123456789",
      "serviceName": "Massage toàn thân",
      "variantName": "Gói 90 phút",
      "roomName": "Phòng VIP",
      "date": "2026-04-30",
      "time": "14:00",
      "duration": 90,
      "price": "900000",
      "paymentStatus": "UNPAID"
    }
  ]
}
```

---

### 2. GET /api/appointments/search/ - Tìm lịch hẹn toàn hệ thống

Tìm kiếm linh hoạt với nhiều điều kiện.

**Endpoint:** `GET /api/appointments/search/`

**Permission:** Staff/Admin

**Query Parameters:** (Bắt buộc ít nhất 1 parameter)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Tìm kiếm tổng hợp | `?q=0987654321` |
| `name` | string | Tìm theo tên khách | `?name=Nguyen Van A` |
| `code` | string | Mã lịch hẹn | `?code=APT-001` |
| `phone` | string | Số điện thoại | `?phone=0987654321` |
| `email` | string | Email | `?email=test@example.com` |
| `status` | string | Trạng thái | `?status=CANCELLED` |
| `source` | string | Nguồn | `?source=ONLINE` |
| `service` | int | Service ID | `?service=3` |
| `room` | string | Mã phòng | `?room=VIP` |
| `date_from` | string | Từ ngày (YYYY-MM-DD) | `?date_from=2026-04-01` |
| `date_to` | string | Đến ngày (YYYY-MM-DD) | `?date_to=2026-04-30` |

**Response:** (Giống GET /api/appointments/)

**Max Results:** 100 records

---

### 3. GET /api/appointments/<code>/ - Chi tiết lịch hẹn

Lấy chi tiết 1 lịch hẹn theo mã.

**Endpoint:** `GET /api/appointments/<code>/`

**Permission:** Staff/Admin

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Mã lịch hẹn (ví dụ: `APT-20260430-001`) |

**Response:**

```json
{
  "success": true,
  "appointment": {
    "code": "APT-20260430-001",
    "status": "NOT_ARRIVED",
    "source": "ONLINE",
    "customerName": "Nguyễn Văn A",
    "customerPhone": "0123456789",
    "customerEmail": "email@example.com",
    "bookerName": "Nguyễn Văn A",
    "bookerPhone": "0123456789",
    "bookerEmail": "email@example.com",
    "serviceName": "Massage toàn thân",
    "variantName": "Gói 90 phút",
    "variantId": 5,
    "roomId": "VIP",
    "roomName": "Phòng VIP",
    "roomCapacity": 1,
    "date": "2026-04-30",
    "time": "14:00",
    "duration": 90,
    "endTime": "15:30",
    "price": "900000",
    "paymentStatus": "UNPAID",
    "notes": "Khách bị dị ứng hương lavender",
    "staffNotes": "Đã chuẩn bị phòng",
    "createdAt": "2026-04-29T10:30:00",
    "createdBy": {
      "id": 1,
      "username": "admin",
      "fullName": "Admin User"
    }
  }
}
```

**Error Response (404):**

```json
{
  "success": false,
  "error": "Không tìm thấy lịch hẹn"
}
```

---

### 4. POST /api/appointments/create-batch/ - Tạo nhiều lịch hẹn

Tạo nhiều lịch hẹn cùng lúc (1 người đặt, nhiều khách).

**Endpoint:** `POST /api/appointments/create-batch/`

**Permission:** Staff/Admin

**Request Body:**

```json
{
  "booker": {
    "name": "Nguyễn Văn A",
    "phone": "0123456789",
    "email": "email@example.com",
    "source": "DIRECT"
  },
  "guests": [
    {
      "customerId": 45,
      "name": "Nguyễn Văn A",
      "phone": "0123456789",
      "email": "email@example.com",
      "variantId": 5,
      "roomId": "VIP",
      "date": "2026-04-30",
      "time": "14:00",
      "note": "Khách VIP",
      "staffNote": "Chuẩn bị phòng",
      "apptStatus": "NOT_ARRIVED",
      "payStatus": "PAID",
      "paymentMethod": "CARD",
      "paymentAmount": 900000,
      "paymentRecordedNo": "TXN123456",
      "paymentNote": "Thanh toán qua thẻ"
    },
    {
      "name": "Nguyễn Văn B",
      "phone": "0987654321",
      "variantId": 3,
      "roomId": "MASSAGE-1",
      "date": "2026-04-30",
      "time": "14:30",
      "apptStatus": "NOT_ARRIVED",
      "payStatus": "UNPAID"
    }
  ]
}
```

**Field Descriptions:**

**booker object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ Yes | Tên người đặt |
| `phone` | string | ✅ Yes | SĐT người đặt (chỉ digits) |
| `email` | string | No | Email người đặt |
| `source` | string | No | Nguồn (ONLINE, DIRECT) - default: DIRECT |

**guests array items:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customerId` | int | No | ID khách hàng (nếu đã tồn tại) |
| `name` | string | ✅ Yes | Tên khách |
| `phone` | string | No | SĐT khách |
| `email` | string | No | Email khách |
| `variantId` | int | ✅ Yes | ID gói dịch vụ |
| `roomId` | string | ✅ Yes | Mã phòng |
| `date` | string | ✅ Yes | Ngày hẹn (YYYY-MM-DD) |
| `time` | string | ✅ Yes | Giờ hẹn (HH:MM) |
| `note` | string | No | Ghi chú công khai |
| `staffNote` | string | No | Ghi chú nội bộ |
| `apptStatus` | string | No | Trạng thái (default: NOT_ARRIVED) |
| `payStatus` | string | No | Trạng thái thanh toán (default: UNPAID) |
| `paymentMethod` | string | No* | Phương thức (CASH, CARD, BANK_TRANSFER, E_WALLET) |
| `paymentAmount` | decimal | No* | Số tiền thanh toán |
| `paymentRecordedNo` | string | No | Mã giao dịch |
| `paymentNote` | string | No | Ghi chú thanh toán |

*Required nếu `payStatus` != UNPAID

**Appointment Status Values:** `PENDING`, `NOT_ARRIVED`, `ARRIVED`, `COMPLETED`, `CANCELLED`, `REJECTED`

**Payment Status Values:** `UNPAID`, `PARTIAL`, `PAID`, `REFUNDED`

**Response:**

```json
{
  "success": true,
  "message": "Đã tạo 2 lịch hẹn",
  "appointments": [
    { /* appointment object 1 */ },
    { /* appointment object 2 */ }
  ],
  "errors": []
}
```

**Partial Success Response:**

```json
{
  "success": true,
  "message": "Đã tạo 1 lịch hẹn (1 lỗi)",
  "appointments": [
    { /* appointment object */ }
  ],
  "errors": [
    "Khách 2: Phòng đã đầy vào khung giờ này"
  ]
}
```

**Validation Checks:**
- ✅ Ngày không quá khứ (trừ khi staff confirm)
- ✅ Giờ trong 9:00 - 21:00
- ✅ Giờ kết thúc không vượt 21:00
- ✅ Phòng còn trống (check capacity)
- ✅ Gói dịch vụ tồn tại
- ✅ Phòng tồn tại
- ✅ Payment data valid (nếu có)

---

### 5. POST /api/appointments/<code>/update/ - Cập nhật lịch hẹn

Cập nhật thông tin lịch hẹn.

**Endpoint:** `POST /api/appointments/<code>/update/`

**Permission:** Staff/Admin

**Request Body:** (All fields optional)

```json
{
  "bookerName": "Nguyễn Văn A (Updated)",
  "bookerPhone": "0123456789",
  "bookerEmail": "newemail@example.com",
  "customerName": "Nguyễn Văn A",
  "phone": "0123456789",
  "email": "email@example.com",
  "variantId": 7,
  "roomId": "DELUXE",
  "date": "2026-05-01",
  "time": "15:00",
  "note": "Updated note",
  "staffNote": "Updated staff note",
  "apptStatus": "ARRIVED",
  "payStatus": "PAID",
  "paymentData": {
    "payment_method": "CARD",
    "amount": 900000,
    "recorded_no": "TXN789",
    "note": "Paid at counter"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Cập nhật lịch hẹn APT-20260430-001 thành công",
  "appointment": { /* updated appointment object */ }
}
```

**Validation:**
- Nếu đổi ngày/giờ/phòng/variant → Re-validate conflicts
- Không thể sửa lịch đã CANCELLED/REJECTED (dùng rebook)

**Error Response (400):**

```json
{
  "success": false,
  "error": "Phòng đã đầy vào khung giờ này"
}
```

---

### 6. POST /api/appointments/<code>/status/ - Đổi trạng thái

Đổi trạng thái lịch hẹn nhanh.

**Endpoint:** `POST /api/appointments/<code>/status/`

**Permission:** Staff/Admin

**Request Body:**

```json
{
  "status": "NOT_ARRIVED"
}
```

**Valid Status Values:**
- `PENDING` - Chờ xác nhận
- `NOT_ARRIVED` - Đã xác nhận, chưa đến
- `ARRIVED` - Khách đã đến
- `COMPLETED` - Hoàn thành
- `CANCELLED` - Đã hủy
- `REJECTED` - Từ chối

**Response:**

```json
{
  "success": true,
  "message": "Đã cập nhật trạng thái: Chưa đến"
}
```

**Auto Behavior:**
- Nếu `status=CANCELLED` → `cancelled_by=admin`

---

### 7. POST /api/appointments/<code>/delete/ - Xóa lịch hẹn

Xóa mềm lịch hẹn (soft delete).

**Endpoint:** `POST /api/appointments/<code>/delete/`

**Permission:** Staff/Admin

**Response:**

```json
{
  "success": true,
  "message": "Đã xóa lịch hẹn APT-20260430-001",
  "deleted_id": 123,
  "customer_name": "Nguyễn Văn A"
}
```

**Database Changes:**
- Sets `deleted_at = NOW()`
- Sets `deleted_by_user = current_user`
- Record vẫn tồn tại nhưng không hiển thị trong queries thường

---

### 8. GET/POST /api/appointments/<code>/rebook/ - Đặt lại lịch hẹn

Xử lý lịch hẹn đã hủy/từ chối.

**Endpoint:** `GET/POST /api/appointments/<code>/rebook/`

**Permission:** Staff/Admin

**GET Response:** (Trả về thông tin để pre-fill form)

```json
{
  "success": true,
  "rebook": {
    "bookerName": "Nguyễn Văn A",
    "bookerPhone": "0123456789",
    "bookerEmail": "email@example.com",
    "customerName": "Nguyễn Văn A",
    "customerPhone": "0123456789",
    "customerEmail": "email@example.com",
    "serviceId": 3,
    "variantId": 5,
    "notes": "Old notes",
    "source": "ONLINE",
    "variantWarning": null
  }
}
```

**POST Request Body:** (Empty body)

**POST Response:** (Re-activate appointment)

```json
{
  "success": true,
  "message": "Đã đặt lại lịch hẹn APT-20260430-001 về trạng thái chờ xác nhận.",
  "appointment": { /* appointment object */ }
}
```

**Conditions:**
- Chỉ dùng cho appointments có status `CANCELLED` hoặc `REJECTED`
- GET: Trả về data để pre-fill form tạo mới
- POST: Set status về `PENDING` (tái kích hoạt appointment cũ)

**Error Response (400):**

```json
{
  "success": false,
  "error": "Chỉ có thể đặt lại lịch đã hủy hoặc đã từ chối.",
  "currentStatus": "NOT_ARRIVED"
}
```

---

## Booking Requests

### 9. GET /api/booking-requests/ - Xem yêu cầu đặt lịch

Lấy danh sách booking requests (PENDING/CANCELLED/REJECTED).

**Endpoint:** `GET /api/booking-requests/`

**Permission:** Staff/Admin

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string | Filter theo ngày |
| `status` | string | Filter theo status |
| `q` | string | Tìm kiếm (code, name, phone) |
| `service` | int | Filter theo service ID |

**Special Behavior:**
- `PENDING` / `CANCELLED`: Chỉ lấy `source='ONLINE'`
- `REJECTED`: Lấy tất cả sources
- Sort ưu tiên: `PENDING` → `CANCELLED`/`REJECTED`

**Response:** (Giống GET /api/appointments/)

---

### 10. GET /api/booking/pending-count/ - Số lượng pending

Lấy số lượng booking pending (để hiển thị badge).

**Endpoint:** `GET /api/booking/pending-count/`

**Permission:** Staff/Admin

**Response:**

```json
{
  "success": true,
  "count": 5,
  "timestamp": "2026-04-30T10:30:00+07:00"
}
```

**Usage:** Polling mỗi 30s để update badge notification

---

## Rooms

### 11. GET /api/rooms/ - Danh sách phòng

Lấy danh sách phòng active.

**Endpoint:** `GET /api/rooms/`

**Permission:** Staff/Admin

**Response:**

```json
{
  "success": true,
  "rooms": [
    {
      "id": "VIP",
      "name": "Phòng VIP",
      "capacity": 1
    },
    {
      "id": "DOUBLE",
      "name": "Phòng đôi",
      "capacity": 2
    }
  ]
}
```

---

## Customers

### 12. GET /api/customers/search/ - Tìm khách hàng

Tìm khách hàng theo tên/SĐT/email.

**Endpoint:** `GET /api/customers/search/?q=<query>`

**Permission:** Staff/Admin

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ✅ Yes | Query string (min 2 chars) |

**Response:**

```json
{
  "success": true,
  "customers": [
    {
      "id": 45,
      "fullName": "Nguyễn Văn A",
      "phone": "0123456789",
      "email": "email@example.com"
    },
    {
      "id": 67,
      "fullName": "Nguyễn Văn B",
      "phone": "0987654321",
      "email": "vanb@example.com"
    }
  ]
}
```

**Max Results:** 10 customers

**Search Fields:**
- `full_name` (icontains)
- `phone` (icontains)
- `user.email` (icontains)

---

## Error Codes

| HTTP Code | Description | Example Response |
|-----------|-------------|------------------|
| 200 | Success | `{"success": true, ...}` |
| 400 | Bad Request / Validation Error | `{"success": false, "error": "Phòng đã đầy..."}` |
| 403 | Forbidden (Not staff) | `{"success": false, "error": "Không có quyền truy cập"}` |
| 404 | Not Found | `{"success": false, "error": "Không tìm thấy lịch hẹn"}` |
| 500 | Server Error | `{"success": false, "error": "Lỗi: ..."}` |

---

## Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Ngày hẹn không được nhỏ hơn ngày hôm nay` | Booking ngày quá khứ | Chọn ngày hôm nay hoặc tương lai |
| `Giờ làm việc từ 09:00 đến 21:00` | Giờ ngoài giờ làm việc | Chọn giờ 9-21h |
| `Gói 90 phút sẽ kết thúc sau 21:00. Giờ trễ nhất có thể đặt: 19:30` | Giờ kết thúc > 21h | Chọn giờ sớm hơn hoặc gói ngắn hơn |
| `Giờ hẹn phải sau giờ hiện tại (14:30)` | Booking giờ đã qua | Chọn giờ sau hiện tại |
| `Phòng đã đầy vào khung giờ này` | Phòng hết capacity | Chọn phòng khác hoặc giờ khác |
| `Vui lòng chọn gói dịch vụ` | Thiếu variantId | Chọn gói dịch vụ |
| `Phòng XYZ không tồn tại` | Room code không hợp lệ | Chọn phòng khác |
| `Gói dịch vụ không tồn tại` | VariantId không hợp lệ | Chọn gói dịch vụ khác |

---

## Rate Limiting (Optional)

Đề xuất implement:
- Public endpoints: 100 req/hour
- Authenticated endpoints: 1000 req/hour
- Staff endpoints: No limit

---

## Versioning

**Current Version:** v1.0

**API Stability:** Production

**Changelog:**
- v1.0 (2026-04-30): Initial release

---

## Support

**Developer:** Spa ANA Team
**Last Updated:** 2026-04-30
**Documentation Version:** 1.0

---

## Quick Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List appointments | GET | `/api/appointments/` |
| Search appointments | GET | `/api/appointments/search/` |
| Get appointment detail | GET | `/api/appointments/<code>/` |
| Create appointment(s) | POST | `/api/appointments/create-batch/` |
| Update appointment | POST | `/api/appointments/<code>/update/` |
| Change status | POST | `/api/appointments/<code>/status/` |
| Delete appointment | POST | `/api/appointments/<code>/delete/` |
| Rebook appointment | GET/POST | `/api/appointments/<code>/rebook/` |
| List booking requests | GET | `/api/booking-requests/` |
| Pending count | GET | `/api/booking/pending-count/` |
| List rooms | GET | `/api/rooms/` |
| Search customers | GET | `/api/customers/search/` |
