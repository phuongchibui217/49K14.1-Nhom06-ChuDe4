# 📖 Hướng dẫn chi tiết file `booking.html` — Dành cho người mới học

> **File:** `spa_project/templates/appointments/booking.html`  
> **Chức năng:** Trang đặt lịch hẹn spa cho khách hàng  
> **Framework:** Django Templates + Bootstrap 5 + JavaScript thuần

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Phần 1: Template Inheritance — Kế thừa template](#2-phần-1-template-inheritance--kế-thừa-template)
3. [Phần 2: Block extra_css — CSS tùy chỉnh](#3-phần-2-block-extra_css--css-tùy-chỉnh)
4. [Phần 3: Block content — Giao diện chính](#4-phần-3-block-content--giao-diện-chính)
5. [Phần 4: Block extra_js — JavaScript xử lý logic](#5-phần-4-block-extra_js--javascript-xử-lý-logic)
6. [Phần 5: Django View tương ứng](#6-phần-5-django-view-tương-ứng)
7. [Tóm tắt kiến thức đã học](#7-tóm-tắt-kiến-thức-đã-học)

---

## 1. Tổng quan kiến trúc

File `booking.html` được chia thành **4 phần chính**:

```
booking.html
├── {% extends 'spa/base.html' %}        ← Kế thừa template cha
├── {% block extra_css %}...{% endblock %} ← CSS riêng của trang này
├── {% block content %}...{% endblock %}   ← HTML giao diện chính
└── {% block extra_js %}...{% endblock %}  ← JavaScript xử lý logic
```

**Luồng hoạt động:**

```
Người dùng truy cập /appointments/booking/
        ↓
Django View (views.py → hàm booking()) xử lý request
        ↓
View render template booking.html + truyền dữ liệu (form, services, customer_profile)
        ↓
Template kế thừa base.html → ghép CSS + HTML + JS → trả về trang web hoàn chỉnh
```

---

## 2. Phần 1: Template Inheritance — Kế thừa template

```html
{% extends 'spa/base.html' %}
{% block title %}Đặt lịch hẹn - Spa ANA{% endblock %}
```

### Giải thích:

| Cú pháp | Ý nghĩa |
|---------|----------|
| `{% extends 'spa/base.html' %}` | Kế thừa template cha `base.html`. Điều này có nghĩa là booking.html sẽ **tái sử dụng** toàn bộ cấu trúc của `base.html` (header, footer, navigation, CSS/JS chung). |
| `{% block title %}...{% endblock %}` | Ghi đè (override) block `title` trong `base.html` để đặt tiêu đề trang riêng. |

### Cách hoạt động của Template Inheritance:

Trong `base.html` có định nghĩa các "lỗ" (blocks):
```html
<!-- base.html -->
<title>{% block title %}Spa ANA{% endblock %}</title>
{% block extra_css %}{% endblock %}
<main>{% block content %}{% endblock %}</main>
{% block extra_js %}{% endblock %}
```

Khi `booking.html` dùng `{% extends %}`, nó sẽ **đổ nội dung** vào các "lỗ" đó:

```
base.html (khung)
├── <head>
│   ├── Bootstrap CSS (chung)
│   ├── Font Awesome (chung)
│   ├── style.css (chung)
│   └── {% block extra_css %} ← booking.html đổ CSS vào đây
├── <body>
│   ├── Header (chung)
│   ├── {% block content %}  ← booking.html đổ HTML vào đây
│   ├── Footer (chung)
│   ├── Bootstrap JS (chung)
│   └── {% block extra_js %} ← booking.html đổ JS vào đây
```

> 💡 **Lợi ích:** Không cần viết lại header, footer, CSS/JS chung cho mỗi trang. Chỉ cần viết phần riêng.

---

## 3. Phần 2: Block extra_css — CSS tùy chỉnh

```html
{% block extra_css %}
<style>
  /* Toàn bộ CSS cho trang booking */
</style>
{% endblock %}
```

### Các kỹ thuật CSS được sử dụng:

### 3.1 CSS Variables (Biến CSS)

```css
.bk-card {
  border: 1px solid var(--border);      /* Dùng biến CSS */
  border-radius: var(--r-lg);           /* Border radius lớn */
  box-shadow: var(--shadow-sm);         /* Shadow nhỏ */
}
```

> **Biến CSS** được định nghĩa trong file `style.css` chung (ví dụ: `--gold`, `--border`, `--r-lg`, `--shadow-sm`). Giúp **đồng bộ giao diện** trên toàn bộ website — thay 1 chỗ thì tất cả đều đổi theo.

### 3.2 CSS Grid Layout — Bố cục 2 cột

```css
.booking-grid {
  display: grid;
  grid-template-columns: 360px 1fr;   /* Cột trái 360px, cột phải chiếm phần còn lại */
  gap: 2rem;                           /* Khoảng cách giữa 2 cột */
  align-items: start;                  /* Căn trên */
}
```

Kết quả:
```
┌──────────────────┬────────────────────────────────────┐
│  Sidebar (360px) │  Main Content (1fr = flexible)     │
│  - Thông tin KH  │  - Dịch vụ & Thời gian             │
│                  │  - Ghi chú                          │
│                  │  - Nút đặt lịch                     │
└──────────────────┴────────────────────────────────────┘
```

### 3.3 Sticky Position — Thanh bên cố định

```css
.customer-sidebar {
  position: sticky;    /* Cố định sidebar khi cuộn */
  top: 2rem;           /* Cách top 2rem khi bắt đầu dính */
}
```

> Khi người dùng cuộn trang, sidebar sẽ **"dính"** lại trên màn hình, luôn hiển thị thông tin khách hàng trong khi cuộn phần bên phải.

### 3.4 CSS Transitions — Hiệu ứng chuyển đổi

```css
.bk-card {
  transition: box-shadow .2s ease;    /* Hiệu ứng đổi bóng mượt trong 0.2s */
}
.bk-card:hover {
  box-shadow: var(--shadow-md);       /* Bóng lớn hơn khi hover */
}
```

```css
.btn-book {
  transition: all .3s ease;           /* Tất cả thuộc tính đều có transition */
}
.btn-book:hover {
  transform: translateY(-2px);        /* Nâng nút lên 2px khi hover */
  box-shadow: 0 6px 22px rgba(201,169,110,.38);  /* Bóng đổ đậm hơn */
}
```

### 3.5 CSS Gradient — Nền chuyển màu

```css
.btn-book {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-hover) 100%);
  /* Gradient từ góc 135°, màu gold → gold-hover */
}
```

### 3.6 Responsive Design — Thiết kế đáp ứng

```css
@media (max-width: 991px) {
  /* Khi màn hình ≤ 991px (tablet) */
  .booking-grid {
    grid-template-columns: 1fr;   /* Chuyển sang 1 cột */
  }
  .customer-sidebar {
    position: static;              /* Bỏ sticky */
  }
}

@media (max-width: 768px) {
  /* Khi màn hình ≤ 768px (mobile) */
  .booking-wrap { padding: 0 1rem 2.5rem; }
  .bk-card { padding: 1.4rem; }         /* Giảm padding */
  .btn-book { padding: .875rem 1.5rem; font-size: 1rem; }
}
```

> 💡 **Nguyên tắc Mobile-First:** Thiết kế cho desktop trước, rồi dùng `@media` để điều chỉnh cho tablet/mobile.

### 3.7 BEM-like Naming Convention — Quy tắc đặt tên CSS

File này dùng quy tắc đặt tên theo pattern: `bk-` (viết tắt của booking):

```css
.bk-card          /* Card container */
.bk-field         /* Form field wrapper */
.bk-label         /* Label của field */
.bk-input         /* Input field */
.bk-select        /* Select dropdown */
.bk-textarea      /* Textarea */
.bk-error         /* Thông báo lỗi */
.bk-section-title /* Tiêu đề section */
```

> 💡 **Lợi ích:** Tránh trùng lặp CSS class với các trang khác. Tìm kiếm và bảo trì dễ hơn.

---

## 4. Phần 3: Block content — Giao diện chính

### 4.1 Hiển thị lỗi form (Form Error Handling)

```html
{# Lỗi toàn form (non-field errors) #}
{% if form.non_field_errors %}
<div class="alert-danger-ana">
  <i class="fas fa-exclamation-circle"></i>
  <span>{% for e in form.non_field_errors %}{{ e }}{% endfor %}</span>
</div>
{% endif %}

{# Lỗi từng field #}
{% if form.errors %}
<div class="alert-danger-ana">
  <span>
    Vui lòng kiểm tra lại thông tin:
    {% for field in form %}
      {% for e in field.errors %}{{ field.label }}: {{ e }} {% endfor %}
    {% endfor %}
  </span>
</div>
{% endif %}
```

**Cách hoạt động:**
- `form.non_field_errors` → Lỗi **không thuộc** field cụ thể nào (ví dụ: "Lịch hẹn bị trùng giờ")
- `form.errors` → Lỗi của **từng field** (ví dụ: "Vui lòng chọn dịch vụ")
- Dùng `{% if %}` để **chỉ hiển thị khi có lỗi**

### 4.2 Form HTML & CSRF Protection

```html
<form method="post" action="{% url 'appointments:booking' %}" id="bookingForm" novalidate>
  {% csrf_token %}
```

| Thuộc tính | Ý nghĩa |
|-----------|----------|
| `method="post"` | Gửi dữ liệu bằng phương thức POST (bảo mật hơn GET cho dữ liệu form) |
| `action="{% url 'appointments:booking' %}"` | Gửi đến URL được định nghĩa trong `urls.py` với name `booking` |
| `novalidate` | Tắt validation mặc định của trình duyệt → Tự viết validation bằng JS |
| `{% csrf_token %}` | **BẮT BUỘC** — Token bảo mật chống tấn công CSRF (Cross-Site Request Forgery) |

> ⚠️ **CSRF là gì?** Là tấn công mà hacker có thể gửi form giả mạo từ trang web khác. Django tạo một token ngẫu nhiên để xác nhận form được gửi từ chính trang web của mình.

### 4.3 Hidden Fields — Trường ẩn

```html
{# booker = người đang đăng nhập — hidden, không cho sửa #}
{{ form.booker_name }}
{{ form.booker_phone }}
```

- `{{ form.booker_name }}` và `{{ form.booker_phone }}` là **hidden inputs** (ẩn)
- Chứa thông tin của người đang đăng nhập (người đặt lịch)
- Khách hàng không thấy và không sửa được các trường này

### 4.4 HTML Structure — Cấu trúc HTML

Trang được chia thành **2 cột** trong `.booking-grid`:

```
booking-grid
├── customer-sidebar (CỘT TRÁI)
│   └── bk-card
│       ├── Tiêu đề: "Thông tin khách sử dụng dịch vụ"
│       ├── Input: Họ và tên *
│       ├── Input: Số điện thoại
│       └── Input: Email
│
└── booking-main (CỘT PHẢI)
    ├── bk-card: Dịch vụ & Thời gian
    │   ├── Row (Bootstrap grid col-md-6)
    │   │   ├── Cột trái: Chọn dịch vụ + Gói dịch vụ + Service Info
    │   │   └── Cột phải: Ngày hẹn + Giờ hẹn + Booking Summary
    │   │
    ├── bk-card: Ghi chú thêm
    │   └── Textarea
    │
    └── Button: "Xác nhận đặt lịch"
```

### 4.5 Django Template Variables — Biến trong template

```html
value="{{ customer_profile.full_name|default:request.user.get_full_name|default:request.user.username }}"
```

**Giải thích từng bước:**

| Phần | Ý nghĩa |
|------|----------|
| `customer_profile.full_name` | Lấy tên đầy đủ từ hồ sơ khách hàng |
| `\|default:` | **Filter** — Nếu giá trị trước đó rỗng/None, dùng giá trị mặc định phía sau |
| `request.user.get_full_name` | Nếu không có hồ sơ, lấy tên đầy đủ từ tài khoản đăng nhập |
| `\|default:request.user.username` | Nếu vẫn rỗng, lấy username |

> 💡 Đây là **chuỗi fallback** (dự phòng): A → không có → B → không có → C

### 4.6 Django Form Rendering

```html
{{ form.service }}           <!-- Render dropdown chọn dịch vụ -->
{{ form.service_variant }}   <!-- Render dropdown chọn gói dịch vụ -->
{{ form.appointment_date }}  <!-- Render input chọn ngày -->
{{ form.appointment_time }}  <!-- Render input chọn giờ -->
{{ form.notes }}             <!-- Render textarea ghi chú -->
```

Django tự động render HTML `<select>` hoặc `<input>` dựa trên loại field được định nghĩa trong `forms.py`.

### 4.7 Field-level Error Display

```html
{% for e in form.service.errors %}
  <div class="bk-error">{{ e }}</div>
{% endfor %}
```

- Duyệt qua tất cả lỗi của field `service`
- Hiển thị mỗi lỗi trong 1 div `.bk-error`
- CSS `.bk-error::before { content: "⚠"; }` tự động thêm icon cảnh báo

### 4.8 Service Info Box — Hiển thị thông tin dịch vụ

```html
<div class="service-info-box">
  <div class="service-info-item">
    <i class="far fa-clock"></i>           <!-- Icon đồng hồ -->
    <span>Thời lượng</span>
    <span class="value" id="serviceDuration">—</span>  <!-- JS sẽ cập nhật -->
  </div>
  <div class="service-info-item">
    <i class="fas fa-tag"></i>             <!-- Icon giá -->
    <span>Giá dự kiến</span>
    <span class="value" id="servicePrice">—</span>     <!-- JS sẽ cập nhật -->
  </div>
</div>
```

- Ban đầu hiển thị `—` (chưa chọn dịch vụ)
- Khi người dùng chọn gói dịch vụ → JavaScript sẽ cập nhật thời lượng và giá

### 4.9 Booking Summary — Tóm tắt lịch hẹn

```html
<div class="booking-summary" id="bookingSummary" style="display:none;">
```

- `style="display:none;"` → **Ẩn mặc định**, chỉ hiện khi đủ thông tin
- JavaScript sẽ kiểm tra: nếu đã chọn dịch vụ + gói + ngày + giờ → hiện summary

```
┌─────────────────────────────┐
│ 📋 Tóm tắt lịch hẹn         │
├─────────────────────────────┤
│ Dịch vụ      Massage Thái   │
│ Gói          60 phút        │
│ Ngày         Thứ Hai, ...   │
│ Giờ          14:00          │
├─────────────────────────────┤
│ TỔNG TIỀN    350.000 VNĐ    │
└─────────────────────────────┘
```

---

## 5. Phần 4: Block extra_js — JavaScript xử lý logic

### 5.1 Nhận dữ liệu từ Django sang JavaScript

```javascript
const servicesVariantsData = {{ services_variants_json|safe }};
```

**Cách hoạt động:**
1. Django view truyền biến `services_variants_json` (chuỗi JSON)
2. Filter `|safe` báo Django **không escape** HTML (vì đây là JSON hợp lệ)
3. Kết quả: JavaScript nhận được 1 Object

**Ví dụ dữ liệu:**
```javascript
{
  "1": [                          // Service ID = 1
    {
      "id": 10,                   // Variant ID
      "label": "60 phút",        // Tên gói
      "duration_minutes": 60,    // Thời lượng
      "price": 350000            // Giá tiền
    },
    {
      "id": 11,
      "label": "90 phút",
      "duration_minutes": 90,
      "price": 500000
    }
  ],
  "2": [ ... ]                    // Service ID = 2
}
```

> 💡 **Kỹ thuật này** cho phép truyền dữ liệu động từ database (Python) sang JavaScript mà không cần gọi API riêng.

### 5.2 DOMContentLoaded — Chờ trang load xong

```javascript
document.addEventListener('DOMContentLoaded', function () {
  // Toàn bộ code nằm trong này
  // → Chỉ chạy SAU KHI HTML đã render xong
});
```

> ⚠️ **Tại sao cần?** Nếu chạy code ngay, các element (input, select) chưa tồn tại → lỗi `null`.

### 5.3 Setup ngày tháng

```javascript
const dateInput = document.getElementById('{{ form.appointment_date.id_for_label }}');
const today = new Date().toISOString().split('T')[0];   // "2026-04-28"
if (dateInput) {
  dateInput.setAttribute('min', today);   // Không cho chọn ngày trong quá khứ
  dateInput.value = today;                // Mặc định chọn hôm nay
}
```

**Giải thích:**
- `{{ form.appointment_date.id_for_label }}` → Django render ra ID của input (ví dụ: `id_appointment_date`)
- `new Date().toISOString().split('T')[0]` → Lấy ngày hiện tại dạng `YYYY-MM-DD`
- `setAttribute('min', today)` → Đặt ngày tối thiểu = hôm nay (không cho chọn ngày quá khứ)

### 5.4 Đọc tham số URL — Pre-select từ trang khác

```javascript
const urlParams = new URLSearchParams(window.location.search);
const serviceIdFromUrl = urlParams.get('service_id') || urlParams.get('service');
const variantIdFromUrl = urlParams.get('variant');
if (serviceIdFromUrl && serviceSelect) serviceSelect.value = serviceIdFromUrl;
```

**Ví dụ:** Nếu người dùng đến từ URL `/booking/?service=2&variant=5`
- `serviceIdFromUrl` = `"2"` → Tự động chọn dịch vụ có ID = 2
- `variantIdFromUrl` = `"5"` → Tự động chọn gói có ID = 5

> 💡 **Trường hợp sử dụng:** Khách hàng xem trang danh sách dịch vụ → click "Đặt lịch" trên dịch vụ cụ thể → chuyển sang trang booking với dịch vụ đã được chọn sẵn.

### 5.5 Hàm updateVariants() — Cập nhật dropdown gói dịch vụ

```javascript
function updateVariants() {
  if (!serviceSelect || !variantSelect) return;

  // 1. Lấy danh sách gói dịch vụ của dịch vụ đang chọn
  const variants = servicesVariantsData[serviceSelect.value] || [];

  // 2. Xóa tất cả option cũ, thêm option mặc định
  variantSelect.innerHTML = '<option value="">— Chọn gói dịch vụ —</option>';

  // 3. Thêm option mới cho từng gói dịch vụ
  variants.forEach(function (v) {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = v.label + ' — ' + v.price.toLocaleString('vi-VN') + ' VNĐ (' + v.duration_minutes + ' phút)';
    // Lưu dữ liệu vào data attributes để dùng sau
    opt.dataset.duration = v.duration_minutes;
    opt.dataset.price    = v.price;
    opt.dataset.label    = v.label;
    variantSelect.appendChild(opt);
  });

  // 4. Nếu có variant từ URL, chọn nó; nếu chỉ có 1 gói, tự chọn
  if (variantIdFromUrl) {
    variantSelect.value = variantIdFromUrl;
  } else if (variants.length === 1) {
    variantSelect.value = variants[0].id;
  }

  // 5. Cập nhật thông tin và tóm tắt
  updateServiceInfo();
  updateSummary();
}
```

**Sơ đồ hoạt động:**
```
Người dùng chọn dịch vụ "Massage Thái"
        ↓
updateVariants() được gọi
        ↓
Lấy danh sách gói: [{60 phút, 350k}, {90 phút, 500k}]
        ↓
Render dropdown:
  — Chọn gói dịch vụ —
  60 phút — 350.000 VNĐ (60 phút)
  90 phút — 500.000 VNĐ (90 phút)
        ↓
Cập nhật info box + summary
```

> 💡 **Kỹ thuật `dataset`:** `opt.dataset.price = v.price` cho phép lưu dữ liệu tùy chỉnh vào HTML element, sau đó lấy lại bằng `opt.dataset.price`.

### 5.6 Hàm validateEndTime() — Kiểm tra giờ đóng cửa

```javascript
function validateEndTime() {
  if (!timeInput || !timeInput.value) return;

  // 1. Tính tổng phút của giờ bắt đầu
  const [h, m] = timeInput.value.split(':').map(Number);  // "14:30" → [14, 30]
  const startMins = h * 60 + m;                            // 14*60 + 30 = 870 phút

  // 2. Lấy thời lượng dịch vụ
  const duration = getSelectedDuration();                   // ví dụ: 90 phút

  // 3. Tính phút kết thúc
  const endMins = startMins + duration;                     // 870 + 90 = 960 phút (= 16:00)

  // 4. Phút đóng cửa: 21:00 = 1260 phút
  const closeMins = SPA_CLOSE_HOUR * 60 + SPA_CLOSE_MINUTES; // 21*60 = 1260

  // 5. Kiểm tra: giờ kết thúc có vượt giờ đóng cửa không?
  if (endMins > closeMins) {
    // → Hiển thị lỗi
    errEl.textContent = `Spa đóng cửa lúc 21:00. Với gói ${duration} phút, giờ bắt đầu trễ nhất là ${latestStr}.`;
    return false;
  } else {
    // → Hủy lỗi
    errEl.style.display = 'none';
    return true;
  }
}
```

**Ví dụ:**
- Chọn gói 90 phút + giờ 20:30 → Kết thúc 22:00 → **LỖI** (qua 21:00)
- Chọn gói 90 phút + giờ 19:00 → Kết thúc 20:30 → **HỢP LỆ** ✓

### 5.7 Hàm updateSummary() — Cập nhật tóm tắt

```javascript
function updateSummary() {
  // Lấy giá trị từ các input
  const svcOpt = serviceSelect.options[serviceSelect.selectedIndex];
  const varOpt = variantSelect.options[variantSelect.selectedIndex];
  const dateVal = dateInput ? dateInput.value : '';
  const timeVal = timeInput ? timeInput.value : '';

  // Chỉ hiện summary khi ĐỦ thông tin
  if (svcOpt && svcOpt.value && varOpt && varOpt.value && dateVal && timeVal) {
    summaryBox.style.display = 'block';           // Hiện summary

    sumService.textContent = svcOpt.textContent;   // Tên dịch vụ
    sumVariant.textContent = varOpt.dataset.label; // Tên gói
    sumDate.textContent = d.toLocaleDateString('vi-VN', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });  // Format: "Thứ Hai, 28 tháng 4, 2026"
    sumTime.textContent = timeVal;                 // Giờ
    sumTotal.textContent = parseFloat(varOpt.dataset.price).toLocaleString('vi-VN') + ' VNĐ';
    // Format giá: "350.000 VNĐ"
  } else {
    summaryBox.style.display = 'none';             // Ẩn nếu chưa đủ thông tin
  }
}
```

### 5.8 Event Listeners — Lắng nghe sự kiện

```javascript
// Khi đổi dịch vụ → cập nhật danh sách gói
serviceSelect.addEventListener('change', updateVariants);

// Khi đổi gói dịch vụ → cập nhật info + summary + validate giờ
variantSelect.addEventListener('change', function () {
  updateServiceInfo();
  updateSummary();
  validateEndTime();
});

// Khi đổi ngày → cập nhật summary
dateInput.addEventListener('change', updateSummary);

// Khi đổi giờ → cập nhật summary + validate
timeInput.addEventListener('change', function() {
  updateSummary();
  validateEndTime();
});
```

### 5.9 Chặn submit nếu lỗi

```javascript
const bookingForm = timeInput ? timeInput.closest('form') : null;
if (bookingForm) {
  bookingForm.addEventListener('submit', function(e) {
    if (!validateEndTime()) {   // Nếu giờ không hợp lệ
      e.preventDefault();       // CHẶN submit form
      timeInput.focus();        // Focus vào trường giờ
    }
  });
}
```

> `e.preventDefault()` → Ngăn hành vi mặc định (gửi form) → Form sẽ không gửi nếu validation thất bại.

### 5.10 setTimeout — Chạy sau khi trang load

```javascript
setTimeout(updateVariants, 50);    // Chạy sau 50ms
setTimeout(updateSummary, 100);    // Chạy sau 100ms
setTimeout(validateEndTime, 150);  // Chạy sau 150ms
```

> **Tại sao dùng setTimeout?** Để đảm bảo các element đã được render hoàn toàn (đặc biệt khi có pre-select từ URL) trước khi chạy các hàm cập nhật.

---

## 6. Phần 5: Django View tương ứng

File `views.py` xử lý request và truyền dữ liệu cho template:

```python
@customer_required()           # Chỉ khách hàng mới được truy cập
def booking(request):
    customer_profile = request.user.customer_profile   # Lấy hồ sơ khách hàng

    if request.method == 'POST':                       # Khi người dùng submit form
        form = AppointmentForm(request.POST, customer_profile=customer_profile)
        if form.is_valid():
            # ... xử lý dữ liệu, tạo lịch hẹn ...
            appointment.save()
            messages.success(request, 'Đặt lịch thành công!')
            return redirect('appointments:my_appointments')   # Chuyển hướng
    else:                                               # Khi GET (mở trang)
        form = AppointmentForm(customer_profile=customer_profile)

    # Chuẩn bị dữ liệu dịch vụ cho JavaScript
    services = Service.objects.filter(status='ACTIVE').prefetch_related('variants')
    services_with_variants = {
        str(s.id): [
            {'id': v.id, 'label': v.label, 'duration_minutes': v.duration_minutes, 'price': float(v.price)}
            for v in s.variants.order_by('sort_order', 'duration_minutes')
        ]
        for s in services
    }

    # Render template với dữ liệu
    return render(request, 'appointments/booking.html', {
        'form': form,                              # Form Django
        'services': services,                       # Danh sách dịch vụ
        'services_variants_json': json.dumps(services_with_variants),  # JSON cho JS
        'customer_profile': customer_profile,       # Hồ sơ khách hàng
    })
```

**Luồng dữ liệu View → Template:**
```
View (Python)                    Template (HTML)
─────────────                    ───────────────
form                      →  {{ form.service }}, {{ form.appointment_date }}, ...
customer_profile          →  {{ customer_profile.full_name }}, {{ customer_profile.phone }}, ...
services_variants_json    →  {{ services_variants_json|safe }}  → dùng trong <script>
```

---

## 7. Tóm tắt kiến thức đã học

### Django Templates
| Kỹ thuật | Ví dụ | Mô tả |
|----------|-------|-------|
| Template Inheritance | `{% extends 'spa/base.html' %}` | Kế thừa template cha |
| Block override | `{% block content %}...{% endblock %}` | Ghi đè nội dung block |
| Variables | `{{ customer_profile.full_name }}` | Hiển thị biến |
| Filters | `\|default:` , `\|safe` | Xử lý dữ liệu trước khi hiển thị |
| Tags | `{% if %}`, `{% for %}`, `{% url %}` | Logic điều khiển |
| CSRF | `{% csrf_token %}` | Bảo mật form |
| Form rendering | `{{ form.service }}` | Django tự tạo HTML cho form field |

### CSS
| Kỹ thuật | Ví dụ | Mô tả |
|----------|-------|-------|
| CSS Variables | `var(--gold)` | Biến CSS tái sử dụng |
| Grid Layout | `grid-template-columns: 360px 1fr` | Bố cục 2 cột |
| Sticky | `position: sticky` | Sidebar cố định khi cuộn |
| Transitions | `transition: box-shadow .2s ease` | Hiệu ứng mượt |
| Gradient | `linear-gradient(135deg, ...)` | Nền chuyển màu |
| Responsive | `@media (max-width: 991px)` | Thiết kế đáp ứng |
| Hover effects | `:hover { transform: translateY(-2px) }` | Hiệu ứng khi di chuột |

### JavaScript
| Kỹ thuật | Ví dụ | Mô tả |
|----------|-------|-------|
| DOM Manipulation | `document.getElementById()` | Truy cập element |
| Event Listeners | `addEventListener('change', fn)` | Lắng nghe sự kiện |
| Data Attributes | `opt.dataset.price` | Lưu dữ liệu trong HTML |
| URL Params | `new URLSearchParams()` | Đọc tham số URL |
| Form Validation | `e.preventDefault()` | Chặn submit nếu lỗi |
| Dynamic HTML | `variantSelect.innerHTML = ...` | Thay đổi HTML động |
| Date/Time | `toLocaleDateString('vi-VN')` | Format ngày tháng |
| Number Format | `toLocaleString('vi-VN')` | Format số tiền |

### Thiết kế & UX
| Kỹ thuật | Mô tả |
|----------|-------|
| BEM-like naming | Đặt tên class theo prefix `bk-` |
| Progressive disclosure | Summary chỉ hiện khi đủ thông tin |
| Real-time validation | Kiểm tra ngay khi đổi giá trị |
| Pre-select from URL | Chọn sẵn dịch vụ khi chuyển từ trang khác |
| Error display | Hiện lỗi tại từng field + alert toàn form |

---

> 🎯 **Kết luận:** File `booking.html` là một ví dụ hoàn chỉnh về cách xây dựng trang web với Django Templates, bao gồm: **kế thừa template**, **CSS tùy chỉnh với responsive**, **HTML form với Django Form**, **xử lý logic phía client bằng JavaScript**, và **tương tác dữ liệu giữa Django (Python) và JavaScript**.
</task_progress>
</task_progress>
</write_to_file>