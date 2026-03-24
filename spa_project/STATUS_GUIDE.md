# 🎯 GIẢI QUYẾT STATUS CHO LỊCH HẸN

## 📊 TRẠNG THÁI LỊCH HẸN (Appointment Status)

| Status Code | Display Name | Mô tả | Ai được set? |
|-------------|--------------|-------|--------------|
| `pending` | Chờ xác nhận | Khách VỪA đặt lịch | Backend (auto) |
| `not_arrived` | Chưa đến | Admin đã xác nhận, khách chưa đến | Admin (khi xác nhận) |
| `arrived` | Đã đến | Khách đã đến spa | Admin/Nhân viên |
| `completed` | Đã hoàn thành | Dịch vụ đã xong | Admin/Nhân viên |
| `cancelled` | Đã hủy | Khách hủy hoặc spa hủy | Khách/Admin |

---

## 🔄 FLOW TRẠNG THÁI

```
KHÁCH ĐẶT LỊCH
      ↓
   pending (Chờ xác nhận)
      ↓
   Admin xác nhận + Gán phòng
      ↓
   not_arrived (Chưa đến)
      ↓
   Khách đến spa
      ↓
   arrived (Đã đến)
      ↓
   Thực hiện dịch vụ
      ↓
   completed (Đã hoàn thành)

Có thể hủy → cancelled (từ bất kỳ trạng thái nào)
```

---

## ✅ ĐÃ SỬA TRONG TEMPLATE

### Trước (SAI):
```html
<!-- ❌ KHÔNG KHỚP -->
<a href="?status=confirmed">Đã xác nhận</a>
{% if appointment.status == 'confirmed' or appointment.status == 'pending' %}
```

### Sau (ĐÚNG):
```html
<!-- ✅ KHỚP MODEL -->
<a href="?status=not_arrived">Đã xác nhận</a>
{% if appointment.status == 'not_arrived' or appointment.status == 'pending' %}
```

---

## 🔗 URL TEST

Truy cập các URL sau để test từng trạng thái:

| Tab | URL | Status |
|-----|-----|--------|
| Tất cả | `/lich-hen-cua-toi/?status=all` | - |
| Chờ xác nhận | `/lich-hen-cua-toi/?status=pending` | pending |
| ✅ Đã xác nhận | `/lich-hen-cua-toi/?status=not_arrived` | not_arrived |
| Đã hoàn thành | `/lich-hen-cua-toi/?status=completed` | completed |
| Đã hủy | `/lich-hen-cua-toi/?status=cancelled` | cancelled |

---

## 💡 LƯU Ý KHI DÙNG TRONG CODE

### ❌ SAI (deprecated):
```python
# status='confirmed' không còn tồn tại
if appointment.status == 'confirmed':
    pass
```

### ✅ ĐÚNG:
```python
# Dùng not_arrived thay thế
if appointment.status == 'not_arrived':
    pass

# Hoặc check nhiều status
if appointment.status in ['pending', 'not_arrived']:
    pass
```

### JavaScript (admin-appointments.js):
```javascript
function statusClass(s){
  if(s==="not_arrived") return "status-not_arrived";  // ✅
  if(s==="arrived") return "status-arrived";
  if(s==="completed") return "status-completed";
  if(s==="cancelled") return "status-cancelled";
  return "status-pending";
}

function statusLabel(s){
  if(s==="pending") return "Chờ xác nhận";
  if(s==="not_arrived") return "Chưa đến";  // ✅
  if(s==="arrived") return "Đã đến";
  if(s==="completed") return "Hoàn thành";
  if(s==="cancelled") return "Đã hủy";
  return s;
}
```

---

## 🚀 TEST NGAY

1. **Tạo booking mới (khách):**
   - Vào /booking/
   - Đặt lịch → Status: `pending`

2. **Admin xác nhận:**
   - Vào /manage/appointments/
   - Tab "Yêu cầu đặt lịch"
   - Click "Xác nhận" → Chọn phòng → "Lưu"
   - Status chuyển: `pending` → `not_arrived`

3. **Khách check lại:**
   - Vào /lich-hen-cua-toi/
   - Click tab "Đã xác nhận"
   - Thấy booking với status "Chưa đến"

---

## 📌 TÓM TẮT CÁC THAY ĐỔI

| File | Thay đổi | Line |
|------|----------|------|
| my_appointments.html | `confirmed` → `not_arrived` | 150-156 |
| my_appointments.html | CSS: `.status-confirmed` → `.status-not_arrived` | 91-94 |
| my_appointments.html | CSS: Thêm `.status-arrived` | - |
| my_appointments.html | Condition: `status == 'confirmed'` → `status == 'not_arrived'` | 208 |

---

## ⚠️ CẦN UPDATE NỮA (TODO)

- [ ] Cập nhật ERD (chạy lại `python manage.py graph_models`)
- [ ] Update documentation (README, wiki)
- [ ] Update test cases
- [ ] Check JavaScript admin-appointments.js có dùng 'confirmed' không
- [ ] Check API responses có trả về đúng status không
