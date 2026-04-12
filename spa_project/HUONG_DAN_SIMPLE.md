# 📘 HƯỚNG DẪN: REFACTOR ĐƠN GIẢN HÓA CODE

## 🎯 MỤC TIÊU

Chuyển logic phức tạp từ **JavaScript → Python (Django Backend)**
- JS chỉ còn: Show/hide modal, gọi API, hiển thị kết quả
- Python lo: Validate, tính toán trùng lịch, render HTML

---

## 📊 SO SÁNH TRƯỚC - SAU

### ❌ TRƯỚC (JS PHỨC TẠP):
```javascript
// JS làm 3 việc:
1. Render UI (vẽ lưới, tính toán lane)
2. Validate (kiểm tra SĐT, trùng lịch)
3. Business logic (overlap detection, capacity check)

→ 600+ dòng code JS
→ Khó hiểu, khó maintain
```

### ✅ SAU (JS ĐƠN GIẢN):
```javascript
// JS chỉ làm 2 việc:
1. Render UI (gọi API, hiển thị HTML)
2. Gửi form data (không validate)

→ 300 dòng code JS (giảm 50%)
→ Dễ hiểu, dễ maintain
→ Backend lo validate, logic phức tạp
```

---

## 🔄 CÁCH SỬ DỤNG

### BƯỚC 1: Thay file JS

**Trước:** Dùng file cũ
```html
<script src="{% static 'js/admin-appointments.js' %}"></script>
```

**Sau:** Dùng file mới
```html
<script src="{% static 'js/admin-appointments-simple.js' %}"></script>
```

---

### BƯỚC 2: Thêm file Backend Logic

Copy file `backend_logic.py` vào thư mục `appointments/`:
```
spa_project/appointments/backend_logic.py
```

---

### BƯỚC 3: Thêm URL Endpoint

Mở file `appointments/urls.py`, thêm:
```python
from . import backend_logic

urlpatterns = [
    # ... các URL cũ ...

    # API render lưới lịch (backend xử lý logic)
    path('api/appointments/render-grid/', backend_logic.api_render_grid),
]
```

---

### BƯỚC 4: Kiểm tra hoạt động

1. **Mở trình duyệt:**
   ```
   http://localhost:8000/manage/appointments/
   ```

2. **F12 Console → Kiểm tra lỗi:**
   - Nếu có lỗi → Xem Network tab, check API endpoint
   - Nếu không có lỗi → Test chức năng

3. **Test các chức năng:**
   - ✅ Click ô trống → Mở modal tạo lịch
   - ✅ Điền form → Bấm "Lưu" → Backend validate
   - ✅ Click block lịch → Mở modal sửa
   - ✅ Bấm "Xóa" → Modal xác nhận

---

## 📝 GIẢI THÍCH CODE

### File JS Mới (`admin-appointments-simple.js`)

**Khác biệt chính:**
```javascript
// ===== TRƯỚC (JS cũ) =====
// Validate ở frontend
if (!isValidPhone(phoneVal)) {
  modalError.textContent = "SĐT không hợp lệ";
  return;
}

if (!capacityOK(...)) {
  modalError.textContent = "Phòng đã đủ chỗ";
  return;
}

// ===== SAU (JS mới) =====
// KHÔNG validate ở frontend
// Chỉ thu thập data và gửi lên backend
const payload = {
  phone: phone.value.trim(),
  room: room.value,
  // ...
};

// Backend sẽ lo validate
const result = await apiPost('/api/appointments/create/', payload);

// Nếu backend trả về lỗi → Hiển thị
if (!result.success) {
  modalError.textContent = result.error;
}
```

---

### File Backend (`backend_logic.py`)

**Chức năng chính:**

1. **Validate Logic:**
```python
def validate_phone_number(phone):
    """Kiểm tra SĐT đúng 10 số"""
    cleaned_phone = re.sub(r'\D', '', str(phone))
    if not re.match(r'^\d{10}$', cleaned_phone):
        return False, cleaned_phone, "SĐT phải có 10 chữ số"
    return True, cleaned_phone, None
```

2. **Business Logic:**
```python
def check_room_capacity(room_id, date, start_time, end_time, new_guests):
    """Kiểm tra phòng có đủ chỗ không"""
    overlapping = check_appointment_overlap(room_id, date, start_time, end_time)
    current_guests = sum(apt.guests for apt in overlapping)

    if current_guests + new_guests > capacity:
        return False, f"Phòng đã đủ chỗ ({current_guests}/{capacity})"

    return True, current_guests, capacity, None
```

3. **Lane Allocation:**
```python
def allocate_lanes_for_room(room_id, date, appointments):
    """Phân bổ lane cho từng lịch hẹn"""
    # Algorithm tìm lane trống
    # Trả về: {capacity: 3, placements: [...]}
```

4. **Render HTML:**
```python
def api_render_grid(request):
    """API endpoint: Render lưới lịch"""
    # Tính toán lane allocation
    # Render HTML
    return JsonResponse({'success': True, 'html': html})
```

---

## 🎓 LỢI ÍCH KHI THUYẾT TRÌNH

### ✅ 1. Code Đơn Giản Hơn

**Nói với giáo viên:**
> "Em đã refactor code để JS chỉ làm giao diện, logic phức tạp chuyển sang Python.
> - JS cũ: 600 dòng → JS mới: 300 dòng
> - Dễ hiểu hơn: JavaScript chỉ call API, show kết quả
> - Backend lo validate, tính toán trùng lịch"

### ✅ 2. Dễ Giải Thích

**Đoạn code dễ nói:**
```python
# Backend logic (Python)
def check_room_capacity(room_id, date, start_time, end_time, guests):
    """Kiểm tra phòng đã đủ chỗ chưa"""
    # 1. Tìm các lịch trùng giờ
    overlapping = find_overlapping_appointments(room_id, date, start_time, end_time)

    # 2. Đếm tổng số khách
    current_guests = sum(apt.guests for apt in overlapping)

    # 3. So sánh với capacity
    if current_guests + guests > capacity:
        return False  # Đủ chỗ rồi

    return True  # Còn chỗ
```

### ✅ 3. Đáp ứng yêu cầu "Thay đổi logic không ảnh hưởng frontend"

**Thay đổi validate:**
```python
# Chỉ sửa ở backend, JS KHÔNG cần đổi
def validate_phone_number(phone):
    # Trước: 10 số
    # if not re.match(r'^\d{10}$', phone):

    # Sau: Bổ sung 11 số
    if not re.match(r'^\d{10,11}$', phone):
        return False, "SĐT phải có 10-11 chữ số"
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Backend PHẢI validate lại

**Tại sao?**
- Frontend có thể bị bypass (user edit HTML, dùng Postman)
- Backend là "bẢO"CƠ cuối cùng

**Ví dụ:**
```python
# views.py - appointments/create
def api_appointment_create(request):
    payload = json.loads(request.body)

    # ===== VALIDATE Ở BACKEND =====
    # 1. Validate SĐT
    is_valid, cleaned_phone, error = validate_phone_number(payload['phone'])
    if not is_valid:
        return JsonResponse({'success': False, 'error': error})

    # 2. Validate giờ
    is_valid, error, end_time = validate_appointment_time(
        payload['date'],
        payload['time'],
        payload['duration']
    )
    if not is_valid:
        return JsonResponse({'success': False, 'error': error})

    # 3. Validate capacity
    has_capacity, current, capacity, error = check_room_capacity(
        payload['roomId'],
        payload['date'],
        payload['time'],
        end_time,
        payload['guests']
    )
    if not has_capacity:
        return JsonResponse({'success': False, 'error': error})

    # ===== Hợp lệ → Lưu vào DB =====
    appointment = Appointment.objects.create(**validated_data)
    return JsonResponse({'success': True})
```

### 2. UX có thể kém hơn

**Vấn đề:**
- Trước: Validate realtime → Báo lỗi ngay
- Sau: Submit mới validate → Chờ server response

**Giải pháp:**
- Thêm loading state
- Toast thông báo rõ ràng
- Không reload trang (dùng AJAX)

### 3. Performance

**Backend render HTML:**
- Ưu: JS đơn giản hơn
- Nhược: Backend phải render HTML (nặng hơn server)

**Giải pháp:**
- Cache HTML nếu có thể
- Chỉ render lại khi cần thiết

---

## 🚀 CÁCH TEST

### Test 1: Validate SĐT

```bash
# Case 1: SĐT đúng
curl -X POST http://localhost:8000/api/appointments/create/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "0123456789", ...}'
# Expected: {"success": true, ...}

# Case 2: SĐT sai
curl -X POST http://localhost:8000/api/appointments/create/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "123", ...}'
# Expected: {"success": false, "error": "SĐT phải có 10 chữ số"}
```

### Test 2: Check Capacity

```bash
# Phòng P01, capacity = 3
# Đã có 2 khách trong khung 10:00-11:00
# User đặt 1 khách → ✅ Thành công
# User đặt 2 khách → ❌ "Phòng đã đủ chỗ (2/3)"
```

### Test 3: Lane Allocation

```python
# Test trong Django shell
python manage.py shell

>>> from appointments.backend_logic import allocate_lanes_for_room
>>> from appointments.models import Appointment

>>> appointments = Appointment.objects.filter(room_id="P01", date="2026-04-11")
>>> result = allocate_lanes_for_room("P01", "2026-04-11", appointments)

>>> print(f"Capacity: {result['capacity']}")
>>> print(f"Placements: {len(result['placements'])}")
>>> for p in result['placements']:
...     print(f"  Lane {p['lane_index']}: {p['appointment'].customerName}")
```

---

## 📚 TÀI LIỆU THAM KHẢO

- [Django Validation](https://docs.djangoproject.com/en/4.0/ref/validators/)
- [Python Regex](https://docs.python.org/3/library/re.html)
- [Django JSON Response](https://docs.djangoproject.com/en/4.0/ref/request-response/#jsonresponse-objects)

---

## ❓ CÂU HỎI THƯỜNG GẶP

### Q1: Tại sao không giữ validate ở frontend?

**A:** Có thể giữ, nhưng:
- Frontend validate = UX tốt hơn (báo lỗi ngay)
- Backend validate = Bắt buộc (bảo mật)
- **Khuyên dùng:** Validate ở cả 2 nơi

### Q2: File JS mới có dùng được không?

**A:** Chưa đầy đủ. Cần:
1. Test kỹ các chức năng
2. Thêm error handling
3. Bổ sung một số helper function

### Q3: Có cần học thêm không?

**A:** Cần nắm:
- Python regex: `re.match()`, `re.sub()`
- Django datetime: `datetime.strptime()`, `timedelta`
- Django ORM: `filter()`, `exclude()`, `Q objects`

---

**Chúc bạn refactor thành công! 🎉**
