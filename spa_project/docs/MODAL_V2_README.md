# 📋 HƯỚNG DẪN SỬ DỤNG MODAL V2

## 🎯 TỔNG QUAN

Modal V2 là phiên bản cải tiến của form Tạo/Sửa/Đặt lại lịch hẹn với:
- ✅ **Giao diện đơn giản, dễ hiểu**
- ✅ **3 khối rõ ràng**: Người đặt → Lịch hẹn → Trạng thái
- ✅ **Code sạch, dễ maintain**
- ✅ **Không dùng framework phức tạp**

---

## 📦 CẤU TRÚC FILE

```
spa_project/
├── static/
│   └── css/
│       └── admin-appointments-modal-v2.css    # CSS cho modal V2
└── templates/
    └── manage/
        └── includes/
            └── appointment_modal_v2.html       # Modal V2 template
```

---

## 🚀 CÁCH TÍCH HỢP

### Bước 1: Thêm CSS vào trang quản lý

Mở file: `templates/manage/pages/admin_appointments.html`

Thêm vào block `{% block extra_css %}`:

```django
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/admin-appointments-modal-v2.css' %}?v={% now 'Ymd' %}">
{% endblock %}
```

### Bước 2: Include modal vào trang

Thêm ở cuối file, trước `{% endblock %}`:

```django
{% include "manage/includes/appointment_modal_v2.html" %}
```

### Bước 3: Sử dụng modal từ JavaScript

```javascript
// Mở modal tạo lịch hẹn mới
AppointmentModalV2.openCreate();

// Mở modal sửa lịch hẹn
AppointmentModalV2.openEdit('appointment_id');

// Đóng modal
AppointmentModalV2.close();

// Thêm guest card
AppointmentModalV2.addGuest({
  name: 'Nguyễn Văn A',
  phone: '0123456789',
  serviceId: 1,
  variantId: 2
});
```

---

## 🎨 GIAO DIỆN

### Bố cục 3 khối:

```
┌─────────────────────────────────────────┐
│  HEADER: Tạo lịch hẹn                    │
├─────────────────────────────────────────┤
│  KHỐC 1: Thông tin người đặt            │
│  ┌───────────────────────────────────┐  │
│  │ Họ tên * | SĐT * | Email          │  │
│  │ Nguồn | Ghi chú                   │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  KHỐC 2: Thông tin lịch hẹn             │
│  ┌───────────────────────────────────┐  │
│  │ [Áp dụng tất cả] [Thêm khách]     │  │
│  │                                   │  │
│  │ ┌─────────────────────────────┐   │  │
│  │ │ 1. Khách hàng              │   │  │
│  │ │ Họ tên | SĐT | Dịch vụ | Gói │   │  │
│  │ └─────────────────────────────┘   │  │
│  │                                   │  │
│  │ ┌─────────────────────────────┐   │  │
│  │ │ 2. Khách hàng              │   │  │
│  │ │ ...                       │   │  │
│  │ └─────────────────────────────┘   │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  KHỐC 3: Trạng thái & Thanh toán       │
│  ┌───────────────────────────────────┐  │
│  │ Trạng thái | Thanh toán          │  │
│  │ Phương thức | Số tiền đã trả     │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  FOOTER: [Xóa] [Hủy] [Đặt lại] [Lưu]   │
└─────────────────────────────────────────┘
```

---

## 🔧 CÁC CHỨC NĂNG

### 1. Tạo lịch hẹn mới

```javascript
// Click nút "Tạo lịch hên" trên trang
document.getElementById('btnCreateAppointment').addEventListener('click', function() {
  AppointmentModalV2.openCreate();
});
```

**Flow:**
1. Reset form về mặc định
2. Hiện nút "Thêm khách" và "Áp dụng tất cả"
3. Ẩn nút "Xóa" và "Đặt lại"
4. Focus vào field "Họ tên"

### 2. Sửa lịch hẹn

```javascript
// Click nút "Sửa" trên một appointment
function editAppointment(appointmentId) {
  // TODO: Load dữ liệu từ API
  fetch(`/api/appointments/${appointmentId}/`)
    .then(res => res.json())
    .then(data => {
      // Fill form với dữ liệu
      document.getElementById('bookerNameV2').value = data.booker_name;
      document.getElementById('bookerPhoneV2').value = data.booker_phone;
      // ... fill các field khác

      // Mở modal
      AppointmentModalV2.openEdit(appointmentId);
    });
}
```

### 3. Đặt lại lịch hẹn (Rebook)

```javascript
// Click nút "Đặt lại" cho appointment đã hủy/từ chối
function rebookAppointment(appointmentId) {
  fetch(`/api/appointments/${appointmentId}/`)
    .then(res => res.json())
    .then(data => {
      // Open modal ở chế độ rebook
      document.getElementById('modalTitleV2').textContent = 'Đặt lại lịch hẹn';
      document.getElementById('btnSaveTextV2').textContent = 'Đặt lại';

      // Pre-fill thông tin
      document.getElementById('bookerNameV2').value = data.booker_name;
      // ... fill các field khác

      // Ẩn nút "Thêm khách" (chỉ có 1 khách)
      document.getElementById('applyAllBarV2').style.display = 'none';

      // Mở modal
      AppointmentModalV2.openCreate();
    });
}
```

### 4. Xóa lịch hẹn

```javascript
// Click nút "Xóa" trong modal (chỉ hiện ở edit mode)
document.getElementById('btnDeleteV2').addEventListener('click', function() {
  if (confirm('Bạn có chắc muốn xóa lịch hẹn này?')) {
    const appointmentId = document.getElementById('apptIdV2').value;

    // TODO: Gọi API xóa
    fetch(`/api/appointments/${appointmentId}/`, {
      method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
      showToast('success', 'Thành công', 'Đã xóa lịch hẹn');
      closeModal();
      // Reload danh sách
      loadAppointments();
    });
  }
});
```

---

## 📝 TODO - Cần tích hợp với backend

### 1. API Integration

```javascript
// ═══════════════════════════════════════════════════════════
// API ENDPOINTS
// ═══════════════════════════════════════════════════════════

const API_BASE = '/api';

// Lấy danh sách dịch vụ
async function loadServices() {
  const res = await fetch(`${API_BASE}/services/`);
  const data = await res.json();
  return data.services;
}

// Lấy variants theo service
async function loadVariants(serviceId) {
  const res = await fetch(`${API_BASE}/services/${serviceId}/variants/`);
  const data = await res.json();
  return data.variants;
}

// Tạo appointment mới
async function createAppointment(formData) {
  const res = await fetch(`${API_BASE}/appointments/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  return await res.json();
}

// Cập nhật appointment
async function updateAppointment(appointmentId, formData) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  return await res.json();
}

// Xóa appointment
async function deleteAppointment(appointmentId) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/`, {
    method: 'DELETE'
  });
  return await res.json();
}
```

### 2. Validation

```javascript
// ═══════════════════════════════════════════════════════════
// SERVER-SIDE VALIDATION
// ═══════════════════════════════════════════════════════════

function validateForm(form) {
  const errors = [];

  // Validate người đặt
  const bookerName = form.querySelector('#bookerNameV2');
  const bookerPhone = form.querySelector('#bookerPhoneV2');

  if (!bookerName.value.trim()) {
    errors.push('Vui lòng nhập họ tên người đặt');
    bookerName.style.borderColor = '#ef4444';
  }

  if (!bookerPhone.value.trim()) {
    errors.push('Vui lòng nhập SĐT người đặt');
    bookerPhone.style.borderColor = '#ef4444';
  }

  // Validate guest cards
  const guestCards = form.querySelectorAll('.guest-card');
  if (guestCards.length === 0) {
    errors.push('Vui lòng thêm ít nhất 1 khách hàng');
  }

  guestCards.forEach((card, index) => {
    const name = card.querySelector('.form-group:nth-child(1) input');
    const variant = card.querySelector('.form-group:nth-child(4) select');

    if (!name.value.trim()) {
      errors.push(`Vui lòng nhập tên khách ${index + 1}`);
      name.style.borderColor = '#ef4444';
    }

    if (!variant.value) {
      errors.push(`Vui lòng chọn gói dịch vụ cho khách ${index + 1}`);
      variant.style.borderColor = '#ef4444';
    }
  });

  return {
    isValid: errors.length === 0,
    errors: errors
  };
}
```

### 3. Toast Notification

```javascript
// ═══════════════════════════════════════════════════════════
// TOAST NOTIFICATION
// ═══════════════════════════════════════════════════════════

function showToast(type, title, message) {
  // Tạo toast element
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-header">
      <i class="fas fa-${getToastIcon(type)} me-2"></i>
      <strong class="me-auto">${title}</strong>
      <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
    </div>
    <div class="toast-body">${message}</div>
  `;

  // Thêm vào container
  const container = document.querySelector('.toast-container');
  if (!container) {
    const newContainer = document.createElement('div');
    newContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(newContainer);
  }
  document.querySelector('.toast-container').appendChild(toast);

  // Hiển thị
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();

  // Xóa sau khi ẩn
  toast.addEventListener('hidden.bs.toast', () => {
    toast.remove();
  });
}

function getToastIcon(type) {
  const icons = {
    success: 'check-circle',
    error: 'exclamation-circle',
    warning: 'exclamation-triangle',
    info: 'info-circle'
  };
  return icons[type] || 'info-circle';
}
```

---

## 🎨 TÙY CHỈNH GIAO DIỆN

### Thay đổi màu sắc

Mở file: `static/css/admin-appointments-modal-v2.css`

```css
/* Màu chính (header, buttons) */
:root {
  --primary-color: #1e3a5f;
  --primary-hover: #2c5282;
}

#apptModal .modal-header {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
}

.btn-primary-custom {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
}
```

### Thay đổi spacing

```css
/* Spacing giữa các section */
.form-section {
  padding: 20px; /* Tăng lên 24px cho thoáng hơn */
}

/* Spacing giữa các field */
.form-grid-2,
.form-grid-3,
.form-grid-4,
.form-grid-5 {
  gap: 16px; /* Tăng lên 20px */
}
```

---

## 🐛 TROUBLESHOOTING

### Modal không mở

**Kiểm tra:**
1. Đã include CSS chưa?
2. Đã include modal template chưa?
3. Có lỗi JavaScript không? (F12 → Console)

### Form không submit

**Kiểm tra:**
1. Các field required đã điền đủ chưa?
2. API endpoint có đúng không?
3. Network request có bị lỗi không? (F12 → Network)

### Style bị vỡ

**Kiểm tra:**
1. CSS file có được load không?
2. Có conflict với CSS khác không?
3. Browser cache đã clear chưa? (Ctrl + F5)

---

## 📚 THAM KHẢO

- [Bootstrap Modal](https://getbootstrap.com/docs/5.0/components/modal/)
- [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

---

## 👨‍💻 AUTHOR

Frontend Team - Spa ANA Project

---

## 📝 LICENSE

MIT
