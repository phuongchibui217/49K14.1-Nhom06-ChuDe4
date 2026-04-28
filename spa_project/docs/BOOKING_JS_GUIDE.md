# 📘 HƯỚNG DẪN CÁC HÀM JAVASCRIPT TRONG BOOKING PAGE

> **File**: `templates/appointments/booking.html`  
> **Mục đích**: Giải thích cách hoạt động của các hàm JavaScript xử lý form đặt lịch

---

## 🎯 TỔNG QUAN

Trang booking có **6 hàm chính** + **3 constants** + **5 event listeners**:

```
1. updateVariants()        - Cập nhật danh sách gói khi chọn dịch vụ
2. getSelectedDuration()   - Lấy thời lượng của gói đã chọn
3. validateEndTime()       - Kiểm tra giờ kết thúc không vượt 21h
4. updateServiceInfo()     - Hiển thị info box (thời lượng + giá)
5. updateSummary()         - Hiển thị summary box (tóm tắt booking)
6. Event Listeners         - Lắng nghe sự kiện user (click, change...)
```

---

## 📋 CHI TIẾT TỪNG HÀM

### 1️⃣ `updateVariants()` - Cập nhật danh sách gói dịch vụ

**Khi chạy**: User thay đổi dropdown "Chọn dịch vụ"

**Công việc**:
```
User chọn "Massage" 
  → updateVariants() chạy
  → Xóa options cũ trong dropdown gói
  → Load gói Massage từ servicesVariantsData
  → Tạo options mới (60 phút, 90 phút, 120 phút...)
  → Tự động chọn nếu chỉ có 1 gói
  → Cập nhật info box và summary
```

**Code**:
```javascript
function updateVariants() {
  if (!serviceSelect || !variantSelect) return;
  
  // Lấy variants của dịch vụ đã chọn
  const variants = servicesVariantsData[serviceSelect.value] || [];
  
  // Xóa options cũ
  variantSelect.innerHTML = '<option value="">— Chọn gói dịch vụ —</option>';
  
  // Tạo options mới
  variants.forEach(function (v) {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = v.label + ' — ' + v.price.toLocaleString('vi-VN') + ' VNĐ (' + v.duration_minutes + ' phút)';
    
    // Lưu vào data-attributes để dùng sau
    opt.dataset.duration = v.duration_minutes;  // 60, 90, 120...
    opt.dataset.price    = v.price;             // 300000, 450000...
    opt.dataset.label    = v.label;             // "Gói 60 phút"
    
    variantSelect.appendChild(opt);
  });
  
  // Auto-select nếu có 1 variant hoặc có variant_id từ URL
  if (variantIdFromUrl) {
    variantSelect.value = variantIdFromUrl;
  } else if (variants.length === 1) {
    variantSelect.value = variants[0].id;
  }
  
  // Cập nhật UI
  updateServiceInfo();
  updateSummary();
}
```

---

### 2️⃣ `getSelectedDuration()` - Lấy thời lượng gói đã chọn

**Khi chạy**: Các hàm khác cần biết thời lượng

**Trả về**: Số phút (60, 90, 120...) hoặc 60 mặc định

**Logic**:
```javascript
function getSelectedDuration() {
  if (!variantSelect) return DEFAULT_DURATION;  // 60 phút
  
  const opt = variantSelect.options[variantSelect.selectedIndex];
  
  // Nếu có chọn và có data-duration → Trả về duration
  // Ngược lại → Trả về 60 mặc định
  return (opt && opt.value && opt.dataset.duration)
    ? parseInt(opt.dataset.duration)
    : DEFAULT_DURATION;
}
```

**Ví dụ**:
```
User chọn "Gói 90 phút" 
  → getSelectedDuration() trả về 90
  
User chưa chọn gói
  → getSelectedDuration() trả về 60 (mặc định)
```

---

### 3️⃣ `validateEndTime()` - Kiểm tra giờ không vượt 21h

**Khi chạy**: User chọn giờ hoặc đổi gói

**Mục đích**: Đảm bảo giờ kết thúc ≤ 21:00 (giờ đóng cửa)

**Logic tính toán**:
```
Giờ kết thúc = Giờ bắt đầu + Thời lượng gói

Ví dụ:
  Giờ bắt đầu: 19:30
  Thời lượng: 90 phút
  → Giờ kết thúc: 19:30 + 90 phút = 21:00 ✅ OK

Ví dụ VI PHẠM:
  Giờ bắt đầu: 20:00
  Thời lượng: 90 phút
  → Giờ kết thúc: 20:00 + 90 phút = 21:30 ❌ QUÁ GIỜ
```

**Code**:
```javascript
function validateEndTime() {
  if (!timeInput || !timeInput.value) return;  // Chưa chọn giờ → thoát
  
  // Lấy giờ user chọn (ví dụ "19:30" → {h: 19, m: 30})
  const [h, m] = timeInput.value.split(':').map(Number);
  
  // Lấy thời lượng
  const duration = getSelectedDuration();  // 90 phút
  
  // Tính phút từ 0h
  const startMins = h * 60 + m;      // 19:30 → 1170 phút
  const endMins   = startMins + duration;  // 1170 + 90 = 1260 phút
  const closeMins = 21 * 60 + 0;       // 21:00 → 1260 phút
  
  // Tính giờ trễ nhất có thể chọn
  const latestStartMins = closeMins - duration;  // 1260 - 90 = 1170
  const latestStr = `${String(latestH).padStart(2,'0')}:${String(latestM).padStart(2,'0')}`;
  // → "19:30"
  
  // Set max cho input time
  timeInput.setAttribute('max', latestStr);
  
  // Hiển thị lỗi nếu quá giờ
  let errEl = document.getElementById('timeEndError');
  if (endMins > closeMins) {
    errEl.textContent = `Spa đóng cửa lúc 21:00. Với gói ${duration} phút, giờ bắt đầu trễ nhất là ${latestStr}.`;
    errEl.style.display = 'block';
    return false;  // FAIL
  } else {
    errEl.style.display = 'none';
    return true;  // OK
  }
}
```

**Kết quả**:
- ✅ `true`  → Giờ hợp lệ, cho phép submit
- ❌ `false` → Giờ không hợp lệ, chặn submit

---

### 4️⃣ `updateServiceInfo()` - Cập nhật Info Box

**Khi chạy**: User chọn gói dịch vụ

**Hiển thị**:
```
┌─────────────────────────────┐
│ 📊 Thời lượng: 60 phút      │
│ 💰 Giá dự kiến: 300.000 VNĐ │
└─────────────────────────────┘
```

**Code**:
```javascript
function updateServiceInfo() {
  if (!variantSelect) return;
  
  const opt = variantSelect.options[variantSelect.selectedIndex];
  
  // Nếu đã chọn gói → Hiển thị info
  if (opt && opt.value) {
    // Hiển thị: "60 phút"
    if (durationSpan) durationSpan.textContent = opt.dataset.duration + ' phút';
    
    // Hiển thị: "300.000 VNĐ"
    if (priceSpan) priceSpan.textContent = parseFloat(opt.dataset.price).toLocaleString('vi-VN') + ' VNĐ';
  }
  // Nếu chưa chọn → Hiển thị dash
  else {
    if (durationSpan) durationSpan.textContent = '—';
    if (priceSpan)    priceSpan.textContent    = '—';
  }
}
```

---

### 5️⃣ `updateSummary()` - Cập nhật Summary Box

**Khi chạy**: User thay đổi bất kỳ field nào (dịch vụ, gói, ngày, giờ)

**Hiển thị** (khi đủ thông tin):
```
┌─────────────────────────────────────────┐
│ 📋 TÓM TẮT LỊCH HẸN                   │
├─────────────────────────────────────────┤
│ Dịch vụ: Massage toàn thân              │
│ Gói: Gói 90 phút                        │
│ Ngày: Thứ Ba, 28/04/2026                │
│ Giờ: 14:30                              │
│ ──────────────────────────────────────── │
│ Tổng tiền: 450.000 VNĐ                   │
└─────────────────────────────────────────┘
```

**Logic**:
```javascript
function updateSummary() {
  if (!summaryBox) return;
  
  // Lấy tất cả thông tin user đã chọn
  const svcOpt   = serviceSelect.options[serviceSelect.selectedIndex];
  const varOpt   = variantSelect.options[variantSelect.selectedIndex];
  const dateVal   = dateInput.value;
  const timeVal   = timeInput.value;
  
  // Nếu ĐÃ CHỌN ĐỦ → Hiển thị summary
  if (svcOpt && svcOpt.value && varOpt && varOpt.value && dateVal && timeVal) {
    summaryBox.style.display = 'block';  // Hiện box
    
    // Hiển thị từng dòng
    if (sumService) sumService.textContent = svcOpt.textContent;
    if (sumVariant) sumVariant.textContent = varOpt.dataset.label || varOpt.textContent.split('—')[0].trim();
    if (sumDate) {
      const d = new Date(dateVal + 'T00:00:00');
      sumDate.textContent = d.toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
    if (sumTime) sumTime.textContent = timeVal;
    if (sumTotal) sumTotal.textContent = parseFloat(varOpt.dataset.price).toLocaleString('vi-VN') + ' VNĐ';
  }
  // Nếu CHƯA ĐỦ → Ẩn summary
  else {
    summaryBox.style.display = 'none';
  }
}
```

---

## 🔗 EVENT LISTENERS - LẮNG NGHE SỰ KIỆN

### 1️⃣ Service Change Event
```javascript
// Khi user chọn dịch vụ khác
serviceSelect.addEventListener('change', updateVariants);
```

**Flow**:
```
User chọn "Massage" → change event → updateVariants() → Load gói Massage
User chọn "Facial" → change event → updateVariants() → Load gói Facial
```

---

### 2️⃣ Variant Change Event
```javascript
// Khi user chọn gói khác
variantSelect.addEventListener('change', function () {
  updateServiceInfo();  // Cập nhật info box
  updateSummary();       // Cập nhật summary
  validateEndTime();     // Validate giờ
});
```

**Flow**:
```
User chọn "Gói 90 phút" 
  → updateServiceInfo() → Hiển thị "90 phút", "450.000 VNĐ"
  → updateSummary() → Hiển thị summary với giá 450.000
  → validateEndTime() → Kiểm tra giờ có hợp lệ không
```

---

### 3️⃣ Date Change Event
```javascript
// Khi user đổi ngày
dateInput.addEventListener('change', updateSummary);
```

**Flow**:
```
User đổi ngày → updateSummary() → Cập nhật ngày trong summary
```

---

### 4️⃣ Time Change Event
```javascript
// Khi user chọn giờ
timeInput.addEventListener('change', function() {
  updateSummary();    // Cập nhật summary
  validateEndTime();  // Validate giờ
});
```

**Flow**:
```
User chọn 14:30 
  → updateSummary() → Hiển thị "14:30" trong summary
  → validateEndTime() → Kiểm tra 14:30 + duration có ≤ 21:00 không
```

---

### 5️⃣ Form Submit Event
```javascript
// Khi user click "Xác nhận đặt lịch"
bookingForm.addEventListener('submit', function(e) {
  if (!validateEndTime()) {
    e.preventDefault();  // CHẠN submit
    timeInput.focus();   // Focus vào input giờ
  }
});
```

**Flow**:
```
User click "Xác nhận đặt lịch"
  → validateEndTime() chạy
  → Nếu FAIL → Chặn submit, focus vào input giờ
  → Nếu OK → Cho phép submit form
```

---

## 🎛️ CONSTANTS - HẰNG SỐ

```javascript
const SPA_CLOSE_HOUR = 21;       // Spa đóng cửa lúc 21h
const SPA_CLOSE_MINUTES = 0;     // 0 phút
const DEFAULT_DURATION = 60;     // Thời lượng mặc định 60 phút
```

**Công dụng**:
- `validateEndTime()` dùng để tính giờ đóng cửa
- `getSelectedDuration()` trả về 60 nếu chưa chọn gói

---

## 🔄 FLOW ĐẦY BỘ TOÀN VỌN

### Scenario 1: User đặt lịch bình thường

```
1. Trang load
   → DOMContentLoaded fires
   → Khởi tạo các biến (dateInput, timeInput, serviceSelect...)
   → Set ngày hôm nay cho dateInput
   → setTimeout(updateVariants, 50) // Load variants
   → setTimeout(updateSummary, 100) // Update summary
   → setTimeout(validateEndTime, 150) // Validate giờ

2. User chọn dịch vụ "Massage"
   → serviceSelect 'change' event fires
   → updateVariants() runs
   → Load gói Massage vào dropdown
   → Auto-select nếu 1 gói
   → updateServiceInfo()
   → updateSummary()

3. User chọn gói "90 phút"
   → variantSelect 'change' event fires
   → updateServiceInfo() → Hiển thị "90 phút", "450.000 VNĐ"
   → updateSummary() → Hiển thị summary với giá 450.000
   → validateEndTime() → Set max = "19:30" (21h - 90 phút)

4. User chọn ngày "28/04/2026"
   → dateInput 'change' event fires
   → updateSummary() → Cập nhật ngày trong summary

5. User chọn giờ "14:00"
   → timeInput 'change' event fires
   → updateSummary() → Cập nhật giờ trong summary
   → validateEndTime() → Check: 14:00 + 90 = 15:30 ≤ 21:00 ✅ OK

6. User click "Xác nhận đặt lịch"
   → bookingForm 'submit' event fires
   → validateEndTime() → returns true
   → Form submit thành công → Redirect đến "Lịch hẹn của tôi"
```

---

### Scenario 2: User chọn giờ quá late

```
... (bước 1-4 như trên)

5. User chọn giờ "20:00"
   → timeInput 'change' event fires
   → updateSummary() → Cập nhật giờ "20:00"
   → validateEndTime() → Check: 20:00 + 90 = 21:30 > 21:00 ❌ FAIL
   → Hiển thị lỗi: "Spa đóng cửa lúc 21:00. Với gói 90 phút, giờ bắt đầu trễ nhất là 19:30."
   → Set max attribute = "19:30"
   → return false

6. User cố chọn "20:30"
   → Browser BLOCK (do max="19:30")
   → User buộc phải chọn ≤ 19:30

7. User chọn "19:00"
   → validateEndTime() → Check: 19:00 + 90 = 20:30 ≤ 21:00 ✅ OK
   → Ẩn lỗi

8. User click "Xác nhận đặt lịch"
   → validateEndTime() → returns true
   → Form submit thành công
```

---

## 📊 BIỂU ĐỒI THỜI GIAN TRONG VIỆC

### Bước 1: User Action
```
User click/select → Event fires
```

### Bước 2: Event Listener
```
addEventListener('change', function_name)
```

### Bước 3: Function Execution
```
function_name() → Update DOM
```

### Bước 4: UI Update
```
Info box, Summary box, Error message
```

---

## 🎨 GỢI Ý QUAN TRỌNG

### 1. **Info Box** (Thời lượng + Giá)
- Cập nhật **NGAY LẬP TỨC** khi user chọn gói
- Hiển thị "—" nếu chưa chọn

### 2. **Summary Box** (Tóm tắt)
- Chỉ hiện khi **ĐÃ CHỌN ĐỦ 4 THÔNG TIN**:
  - ✅ Dịch vụ
  - ✅ Gói dịch vụ  
  - ✅ Ngày
  - ✅ Giờ
- Nếu thiếu 1 → Ẩn đi

### 3. **Validate Giờ**
- Chạy mỗi khi user chọn giờ hoặc đổi gói
- Tính **giờ trễ nhất** = 21:00 - duration
- Set `max` attribute cho input time
- Hiển thị lỗi nếu quá giờ

### 4. **Form Submit**
- Validate TRƯỚC KHI submit
- Nếu FAIL → `e.preventDefault()` chặn submit
- Focus vào input time để user sửa

---

## 💡 TIPS & TRICKS

### Tip 1: Data Attributes
```javascript
opt.dataset.duration = v.duration_minutes;  // Lưu để dùng sau
opt.dataset.price    = v.price;
opt.dataset.label    = v.label;
```
→ Không cần query lại database, lấy từ DOM luôn.

### Tip 2: Template Literals
```javascript
const latestStr = `${String(latestH).padStart(2,'0')}:${String(latestM).padStart(2,'0')}`;
```
→ Format giờ "HH:MM" dễ dàng.

### Tip 3: Optional Chaining
```javascript
if (!serviceSelect || !variantSelect) return;
```
→ Tránh crash nếu element không tồn tại.

### Tip 4: Early Return
```javascript
if (!timeInput || !timeInput.value) return;
```
→ Thoát sớm nếu điều kiện không thỏa, code gọn hơn.

---

## 🐛 COMMON BUGS & FIXES

### Bug 1: Summary không hiện
**Nguyên nhân**: Chưa chọn ĐỦ thông tin  
**Fix**: Kiểm tra tất cả 4 fields đã có value chưa

### Bug 2: Validate không hoạt động
**Nguyên nhân**: Quên bind event listener  
**Fix**: Kiểm tra `addEventListener('submit', ...)` đã có chưa

### Bug 3: Giờ vẫn chọn được sau 21h
**Nguyên nhân**: Quên set `max` attribute  
**Fix**: Kiểm tra `timeInput.setAttribute('max', latestStr)` đã chạy chưa

### Bug 4: Info box hiển thị sai giá
**Nguyên nhân**: `data-price` chưa set  
**Fix**: Kiểm tra `opt.dataset.price` có giá trị đúng không

---

## 📝 SUMMARY

| Hàm | Mục đích | Khi chạy | Trả về |
|------|----------|-----------|--------|
| `updateVariants()` | Load gói theo dịch vụ | Change service | void |
| `getSelectedDuration()` | Lấy thời lượng gói | Cần duration | number (phút) |
| `validateEndTime()` | Check giờ ≤ 21h | Change time/variant | boolean |
| `updateServiceInfo()` | Hiển thị info box | Change variant | void |
| `updateSummary()` | Hiển thị summary | Change bất kỳ | void |

---

## 🎓 HỌC CÁCH DỌC DỄ THEO DÕI

1. **Debug**: Dùng `console.log()` để xem giá trị biến
2. **Breakpoint**: Set breakpoint trong DevTools để chạy từng bước
3. **Watch**: Theo dõi giá trị biến khi thay đổi
4. **Test**: Test tất cả scenarios (hợp lệ, không hợp lệ)

---

## 📚 LIÊN KẾT

- [MDN - JavaScript Events](https://developer.mozilla.org/en-US/docs/Web/Events)
- [MDN - DOM Manipulation](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)
- [JavaScript DOM Cheatsheet](https://overapi.com/javascript-dom-cheatsheet/)

---

**Author**: Spa ANA Team  
**Last Updated**: 2026-04-28
