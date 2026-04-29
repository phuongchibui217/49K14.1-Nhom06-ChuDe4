# Hướng Dẫn Xây Dựng Giao Diện "Lịch Hẹn Của Tôi"

## Tài liệu hướng dẫn chi tiết cho người mới bắt đầu

---

## 📋 Mục Lục

1. [Tổng quan về giao diện](#tổng-quan)
2. [Cấu trúc file HTML](#cấu-trúc-html)
3. [Cấu trúc file CSS](#cấu-trúc-css)
4. [Chi tiết từng thành phần](#chi-tiết-thành-phần)
5. [JavaScript xử lý tương tác](#javascript)
6. [Responsive Design](#responsive)
7. [Best Practices](#best-practices)

---

## 📱 Tổng quan về giao diện {#tổng-quan}

Giao diện **"Lịch Hẹn Của Tôi"** là trang cho phép khách hàng:
- Xem danh sách các lịch hẹn đã đặt
- Lọc lịch hẹn theo trạng thái (Tất cả, Chờ xác nhận, Đã xác nhận, Hoàn thành, Đã hủy, Đã từ chối)
- Hủy lịch hẹn khi còn ở trạng thái "Chờ xác nhận" hoặc "Chưa đến"
- Xem chi tiết thông tin mỗi lịch hẹn

### Công nghệ sử dụng:
- **HTML5**: Cấu trúc trang
- **Django Template Language**: Render dữ liệu động từ backend
- **CSS3**: Styling giao diện với design hiện đại
- **JavaScript (Vanilla)**: Xử lý tương tác người dùng
- **Bootstrap 5**: Grid system và utility classes

---

## 🏗️ Cấu trúc file HTML {#cấu-trúc-html}

### 1. Template Inheritance (Kế thừa template)

```django
{% extends 'spa/base.html' %}
```

**Giải thích:**
- Dòng này cho biết trang này kế thừa từ `base.html`
- `base.html` chứa các thành phần chung: header, footer, navigation
- Chỉ cần viết nội dung riêng của trang "Lịch hẹn"

### 2. Load Static Files

```django
{% load static %}
```

**Giải thích:**
- Django cần dòng này để sử dụng `{% static %}`
- Giúp load CSS, JS, images từ thư mục `static/`

### 3. Đặt Title cho trang

```django
{% block title %}Lịch hẹn của tôi - Spa ANA{% endblock %}
```

**Giải thích:**
- Override block `title` từ `base.html`
- Hiển thị trên tab trình duyệt
- Tốt cho SEO

### 4. Load CSS riêng cho trang

```django
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/my-appointments.css' %}?v={% now 'Ymd' %}">
{% endblock %}
```

**Giải thích:**
- `?v={% now 'Ymd' %}`: Thêm ngày tháng vào URL CSS
- **Mục đích**: Tránh browser cache CSS cũ
- Ví dụ: `my-appointments.css?v=20260429`

---

## 🎨 Cấu trúc file CSS {#cấu-trúc-css}

File CSS được tổ chức theo các phần rõ ràng:

### 1. Namespace - Tránh xung đột CSS

```css
.my-appointments-page .page-header { ... }
```

**Giải thích:**
- `.my-appointments-page` là container chính
- Tất cả CSS đều bắt đầu với namespace này
- **Lợi ích**: Không ảnh hưởng CSS các trang khác

### 2. Chia section rõ ràng

```css
/* ═══════════════════════════════════════════════════════════
   1. PAGE HEADER - Tiêu đề trang
   ═══════════════════════════════════════════════════════════ */
```

**Giải thích:**
- Dùng line comment để đánh dấu section
- Dễ dàng tìm kiếm và maintain code

---

## 🧩 Chi tiết từng thành phần {#chi-tiết-thành-phần}

### PHẦN 1: PAGE HEADER - Tiêu đề trang

#### HTML:

```django
<section class="page-header">
  <div class="container">
    <h1>Lịch Hẹn Của Tôi</h1>
    <p class="subtitle mb-0">Quản lý và theo dõi các lịch hẹn đặt tại Spa ANA</p>
  </div>
</section>
```

**Giải thích:**

| Element | Công dụng |
|---------|----------|
| `<section>` | Thẻ semantic HTML5 cho một section |
| `.container` | Class Bootstrap để căn giữa nội dung |
| `<h1>` | Tiêu đề chính (SEO quan trọng) |
| `.subtitle` | Mô tả phụ, font nhỏ hơn |
| `.mb-0` | Bootstrap utility: margin-bottom = 0 |

#### CSS:

```css
.my-appointments-page .page-header {
  margin-bottom: 2rem;
}
```

---

### PHẦN 2: FILTER TABS - Thanh lọc theo trạng thái

Đây là **pill-style filter bar** với 6 trạng thái khác nhau.

#### HTML:

```django
<div class="filter-bar">
  <a href="?status=all" class="filter-pill {% if status_filter == 'all' %}active{% endif %}">
    Tất cả
    {% if status_counts.all > 0 %}<span class="pill-count">{{ status_counts.all }}</span>{% endif %}
  </a>
  <!-- Các filter khác tương tự -->
</div>
```

**Giải thích chi tiết:**

1. **URL Parameter**:
   ```django
   href="?status=all"
   ```
   - Khi click, thêm `?status=all` vào URL
   - Django sẽ đọc parameter này và lọc data

2. **Conditional Active Class**:
   ```django
   {% if status_filter == 'all' %}active{% endif %}
   ```
   - Nếu đang lọc "all", thêm class `active`
   - CSS sẽ style khác cho active tab

3. **Count Badge**:
   ```django
   {% if status_counts.all > 0 %}<span class="pill-count">{{ status_counts.all }}</span>{% endif %}
   ```
   - Hiển thị số lượng lịch hẹn mỗi trạng thái
   - Chỉ hiển thị nếu > 0

#### CSS - Design System:

```css
.my-appointments-page .filter-bar {
  background: #f1f5f9;           /* Màu xám nhạt */
  border-radius: 14px;           /* Bo góc 14px */
  padding: 6px;                  /* Khoảng cách trong */
  display: inline-flex;          /* Flexbox ngang */
  flex-wrap: wrap;               /* Wrap xuống dòng nếu quá dài */
  gap: 4px;                      /* Khoảng cách giữa các pill */
  margin-bottom: 2rem;
}
```

**Màu sắc sử dụng:**
- Background: `#f1f5f9` (Slate-100 từ Tailwind)
- Active: `#1e3a5f` (Xanh đậm brand color)
- Hover: `white` với border

**Transition effect:**
```css
.my-appointments-page .filter-pill {
  transition: all 0.2s ease;     /* Mượt mà khi hover */
}

.my-appointments-page .filter-pill:hover {
  background: white;
  color: #1e3a5f;
  border-color: #cbd5e1;
}
```

---

### PHẦN 3: APPOINTMENT CARD - Card hiển thị lịch hẹn

Đây là **thành phần quan trọng nhất** của trang.

#### HTML Structure:

```django
<div class="appointment-card">
  
  <!-- 1. Header: Tên dịch vụ + Mã + Trạng thái -->
  <div class="card-header-section">
    <div class="service-info">
      <h5>Tên dịch vụ — Biến thể</h5>
      <div class="code">#MÃ_LỊCH_HẸN</div>
    </div>
    <span class="status-badge status-pending">Chờ xác nhận</span>
  </div>

  <!-- 2. Body: Ngày/Giờ/Đặt lúc -->
  <div class="card-details">
    <div class="detail-item">
      <i class="far fa-calendar"></i>
      <span>Ngày hẹn:</span>
      <span class="value">29/04/2026</span>
    </div>
    <!-- ... -->
  </div>

  <!-- 3. Notes: Ghi chú (nếu có) -->
  <div class="card-notes">
    Ghi chú từ khách hàng
  </div>

  <!-- 4. Footer: Nút hủy (điều kiện hiển thị) -->
  <div class="card-action-footer">
    <form method="post" action="...">
      <button type="submit">Hủy lịch</button>
    </form>
  </div>

</div>
```

#### CSS - Card Design:

**1. Card Container:**

```css
.my-appointments-page .appointment-card {
  background: white;                    /* Nền trắng */
  border-radius: 16px;                  /* Bo góc 16px - hiện đại */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);  /* Shadow nhẹ */
  padding: 18px 20px;                   /* Padding bên trong */
  margin-bottom: 1rem;                  /* Khoảng cách giữa cards */
  border: 1px solid #f1f5f9;           /* Viền mờ */
  transition: all 0.2s ease;           /* Hiệu ứng hover */
}
```

**2. Hover Effect:**

```css
.my-appointments-page .appointment-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);  /* Shadow đậm hơn */
  transform: translateY(-1px);                 /* Nâng lên 1px */
}
```

**Kỹ thuật sử dụng:**
- `transform: translateY(-1px)`: Tạo cảm giác "nổi"
- `box-shadow`: Tăng độ sâu
- Kết hợp tạo hiệu ứng 3D nhẹ

**3. Card Header:**

```css
.my-appointments-page .card-header-section {
  display: flex;                    /* Flexbox */
  justify-content: space-between;   /* Cách đều 2 đầu */
  align-items: flex-start;          /* Căn đầu */
  margin-bottom: 14px;
}
```

**Layout:**
```
┌─────────────────────────────────────────────┐
│ Tên dịch vụ — Biến thể         [Chờ xác nhận] │
│ #Mã lịch hẹn                            │
└─────────────────────────────────────────────┘
```

**4. Status Badge:**

```css
.my-appointments-page .status-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;          /* Pill shape - bo tròn hoàn toàn */
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;           /* Không wrap text */
}
```

**Color coding cho từng trạng thái:**

| Trạng thái | Background | Color | Ý nghĩa |
|-----------|-----------|-------|---------|
| `pending` | `#fef9ec` (Vàng nhạt) | `#b45309` (Vàng đậm) | Chờ xử lý |
| `confirmed` | `#eff6ff` (Xanh nhạt) | `#1d4ed8` (Xanh đậm) | Đã xác nhận |
| `completed` | `#f0fdf4` (Xanh lá nhạt) | `#15803d` (Xanh lá đậm) | Hoàn thành |
| `cancelled` | `#f3f4f6` (Xám) | `#4b5563` (Xám đậm) | Đã hủy |
| `rejected` | `#fee2e2` (Đỏ nhạt) | `#b91c1c` (Đỏ đậm) | Đã từ chối |

**Kỹ thuật color theory:**
- Dùng pastel colors cho background
- Dùng darker shades cho text
- Tạo contrast dễ đọc nhưng không quá gắt

**5. Card Details:**

```css
.my-appointments-page .card-details {
  display: flex;
  flex-wrap: wrap;               /* Wrap xuống dòng nếu cần */
  gap: 8px 20px;                 /* Row gap 8px, Column gap 20px */
  padding: 12px 0;
  border-top: 1px solid #f1f5f9;  /* Đường kẽ phân cách */
}
```

**Icon styling:**

```css
.my-appointments-page .detail-item i {
  color: #d4a835;                /* Màu vàng gold */
  font-size: 13px;
  width: 14px;                   /* Cố định width để align */
  text-align: center;
}
```

**6. Cancel Button:**

```css
.my-appointments-page .btn-cancel-appt {
  background: #fff1f2;           /* Hồng nhạt */
  color: #be123c;                /* Đỏ hồng */
  border: 1px solid #fecdd3;
  border-radius: 10px;
  padding: 6px 16px;
  cursor: pointer;
  transition: all 0.2s;
}
```

**Design rationale:**
- Màu đỏ = hành động hủy/b nguy hiểm
- Background nhạt để không quá "scary"
- Border để định hình rõ button

---

### PHẦN 4: EMPTY STATE - Trạng thái rỗng

Khi không có lịch hẹn, hiển thị giao diện thân thiện.

#### HTML:

```django
<div class="empty-state">
  <i class="fas fa-calendar-times fa-4x mb-3"></i>
  <h3>Không tìm thấy lịch hẹn nào</h3>
  <p class="text-muted mb-4">
    {% if status_filter != 'all' %}
      Không có lịch hẹn nào ở trạng thái này.
    {% else %}
      Bạn chưa đặt lịch hẹn nào. Hãy trải nghiệm dịch vụ của chúng tôi!
    {% endif %}
  </p>
  <a href="{% url 'appointments:booking' %}" class="btn-appt-cta">
    <i class="fas fa-calendar-check"></i> Đặt lịch ngay
  </a>
</div>
```

**Giải thích:**

1. **Conditional messaging:**
   ```django
   {% if status_filter != 'all' %}
     Không có lịch hẹn nào ở trạng thái này.
   {% else %}
     Bạn chưa đặt lịch hẹn nào...
   {% endif %}
   ```
   - Nếu đang filter: "Không có ở trạng thái này"
   - Nếu filter "Tất cả": "Bạn chưa đặt lịch"

2. **CTA Button:**
   - Dẫn đến trang đặt lịch
   - Màu vàng gold (`#dab987`)
   - Uppercase, letter-spacing để nổi bật

#### CSS:

```css
.my-appointments-page .empty-state {
  text-align: center;             /* Căn giữa */
  padding: 3rem 2rem;              /* Khoảng cách lớn */
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
}
```

---

## 🔧 JavaScript xử lý tương tác {#javascript}

### Confirm Dialog khi hủy lịch:

```javascript
document.addEventListener('submit', async function (event) {
    // 1. Tìm form cancel
    const form = event.target.closest('.cancel-appointment-form');
    if (!form || form.dataset.confirmed === '1') return;

    // 2. Ngăn submit mặc định
    event.preventDefault();

    // 3. Hiển thị confirm dialog
    const ok = await window.showConfirm(
        form.dataset.confirmMessage || 'Bạn có chắc muốn hủy lịch hẹn này?',
        {
            title: 'Xác nhận hủy lịch',
            confirmText: 'Xác nhận',
            cancelText: 'Hủy'
        }
    );

    // 4. Nếu người dùng OK, submit form
    if (!ok) return;
    form.dataset.confirmed = '1';
    form.submit();
});
```

**Giải thích:**

1. **Event Delegation:**
   - Lắng nghe trên `document` thay vì từng form
   - Hiệu năng tốt hơn

2. **Double-submit prevention:**
   ```javascript
   form.dataset.confirmed = '1';
   ```
   - Đánh dấu đã confirm
   - Tránh hỏi lại khi submit thật

3. **Custom confirm dialog:**
   - Dùng `window.showConfirm()` (được define trong base.html)
   - Thay vì `window.confirm()` mặc định xấu

---

## 📱 Responsive Design {#responsive}

### Tablet (≤768px):

```css
@media (max-width: 768px) {
  .my-appointments-page .card-details {
    flex-direction: column;      /* Stack thay vì row */
    gap: 8px;
  }

  .my-appointments-page .filter-bar {
    width: 100%;                 /* Full width */
    justify-content: center;     /* Căn giữa */
  }
}
```

**Thay đổi:**
- Card details từ horizontal → vertical
- Filter bar full width, centered

### Mobile (≤576px):

```css
@media (max-width: 576px) {
  .my-appointments-page .filter-bar {
    width: 100%;
    justify-content: center;
  }

  .my-appointments-page .filter-pill {
    font-size: 0.8rem;          /* Font nhỏ hơn */
    padding: 0.4rem 0.75rem;     /* Padding ít hơn */
  }
}
```

**Mobile-first approach:**
- Base CSS viết cho desktop
- Media query viết cho mobile
- Dễ maintain hơn

---

## ✨ Best Practices {#best-practices}

### 1. Django Template Best Practices

**✅ Tốt:**
```django
{% if appointment.notes %}
  <div class="card-notes">
    <i class="far fa-sticky-note me-1"></i>{{ appointment.notes }}
  </div>
{% endif %}
```
- Chỉ render khi có data
- Không render thẻ rỗng

**❌ Không tốt:**
```django
<div class="card-notes">
  {% if appointment.notes %}{{ appointment.notes }}{% endif %}
</div>
```
- Vẫn render div rỗng
- Vô nghĩa

### 2. CSS Organization

**✅ Tốt:**
```css
/* 1. PAGE HEADER */
.my-appointments-page .page-header { }

/* 2. FILTER TABS */
.my-appointments-page .filter-bar { }
```

**❌ Không tốt:**
```css
.page-header { }
.filter-bar { }
```
- Không có namespace
- Có thể xung đột

### 3. Accessibility

**✅ Tốt:**
```django
<a href="?status=all" class="filter-pill" aria-label="Tất cả lịch hẹn">
```
- Thêm `aria-label` cho screen reader

**✅ Tốt:**
```django
<button type="submit" aria-label="Hủy lịch hên này">
```

### 4. Performance

**CSS Cache Busting:**
```django
?v={% now 'Ymd' %}
```
- Force reload CSS mỗi ngày
- Tránh hiển thị giao diện cũ

**Efficient Selectors:**
```css
.my-appointments-page .appointment-card { }
```
- Tốt hơn: `.appointment-card` (trong namespace)
- Tránh: `div.card.appointment-card` (quá specific)

### 5. User Experience

**✅ Micro-interactions:**
- Hover effects
- Smooth transitions
- Loading states

**✅ Clear Feedback:**
- Confirm dialogs
- Success/error messages
- Empty states với CTA

---

## 🎓 Kết Luận

Giao diện này được xây dựng với các nguyên tắc:

1. **Component-based**: Mỗi phần (header, filter, card) độc lập
2. **Responsive**: Hoạt động tốt trên mọi thiết bị
3. **User-centric**: Dễ sử dụng, feedback rõ ràng
4. **Maintainable**: Code có tổ chức, dễ đọc
5. **Performance**: CSS gọn, JavaScript hiệu quả

### Các kỹ thuật chính đã dùng:

- **Django Template**: Conditional rendering, loops, filters
- **Flexbox**: Layout modern, responsive
- **CSS Transitions**: Micro-interactions
- **Event Delegation**: JavaScript performance
- **Media Queries**: Mobile-first design
- **Namespace CSS**: Tránh xung đột
- **Color Theory**: Semantic coloring cho status

---

## 📚 Tài liệu tham khảo

- [Django Template Language](https://docs.djangoproject.com/en/4.2/topics/templates/)
- [CSS Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)

---

**Author:** Spa ANA Development Team
**Last Updated:** 2026-04-29
**Version:** 1.0
