# 🚀 Quick Start - Hệ Thống Đăng Nhập

> **Hướng dẫn sử dụng nhanh** cho hệ thống Login với UI Toggle

---

## ✅ ĐÃ HOÀN THÀNH

### 1️⃣ Backend (Django)
- ✅ Login View với role handling
- ✅ Validation cho Customer (phone) và Staff (username)
- ✅ Redirect theo role
- ✅ Error messages rõ ràng

### 2️⃣ Frontend (HTML/CSS/JS)
- ✅ UI Toggle: 2 buttons chọn role
- ✅ Form Khách hàng: Phone + Password
- ✅ Form Nhân viên: Username + Password
- ✅ CSS đẹp, animation mượt
- ✅ JavaScript switch form

### 3️⃣ Tài liệu
- ✅ [login_system_design.md](./login_system_design.md) - Đầy đủ, chi tiết

---

## 🧪 CÁCH TEST

### Bước 1: Tạo dữ liệu test

Chạy script tạo user test:

```bash
cd /d/2_HOC_KI/6_SEMESTER/2.Lap_trinh_web/REFACTOR_SPA/LTW_Spa_Ana/spa_project
python create_test_users.py
```

Hoặc tạo bằng tay:

```bash
# Tạo Superuser (Admin/Chủ Spa)
python manage.py createsuperuser

Username: Chu  
Email: admin@spasana.vn
Password: chu123
```

### Bước 2: Chạy server

```bash
python manage.py runserver
```

### Bước 3: Test Login

Mở browser: `http://localhost:8000/login/`

#### Test Khách hàng:
1. Click button **[Khách hàng]**
2. Nhập:
   - Số điện thoại: `0382434901'
   - Mật khẩu: `123456'
3. Click **Đăng nhập**
4. ✅ Should redirect về trang chủ
--

## 📋 THÔNG TIN ĐĂNG NHẬP TEST

### Khách hàng (Customer)
| Phone | Password | Full Name |
|-------|----------|-----------|
| 0912345678 | customer123 | Nguyễn Thị An |

### Nhân viên (Staff)
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser (Chủ Spa) |
| letan01 | letan123 | Lễ tân |

---

## 🎯 CÁC TRANG QUAN TRỌNG

| Trang | URL | Mô tả |
|------|-----|-------|
| Login | `/login/` | Trang đăng nhập (UI Toggle) |
| Register | `/register/` | Đăng ký khách hàng mới |
| Customer Profile | `/tai-khoan/` | Thông tin khách hàng |
| Admin Dashboard | `/manage/appointments/` | Quản lý lịch hẹn (Staff) |
| Django Admin | `/admin/` | Quản lý User, Database |

---

## ⚠️ CÁC LỖI THƯỜNG GẶP

### 1. Lỗi: "Số điện thoại chưa được đăng ký"
**Nguyên nhân:** Chưa có CustomerProfile với phone này
**Fix:** Đăng ký khách hàng mới tại `/register/`

### 2. Lỗi: "Tài khoản này không có quyền truy cập"
**Nguyên nhân:** Staff account nhưng `is_staff=False`
**Fix:** Vào `/admin/`, set `is_staff=True`

### 3. Lỗi: "Tên đăng nhập hoặc mật khẩu không đúng"
**Nguyên nhân:** Sai username/password
**Fix:** Kiểm tra lại hoặc reset password trong Django Admin

---

## 🔧 TẠO USER MỚI

### Cách 1: Qua Django Admin (Khuyên dùng)
1. Vào `http://localhost:8000/admin/`
2. Login với superuser
3. Vào **Users** → **Add user**
4. Set permissions:
   - Khách hàng: Không cần tick gì cả
   - Nhân viên: Tick **Staff status**
   - Admin: Tick **Superuser status**

### Cách 2: Qua Python Shell
```python
from django.contrib.auth.models import User
from accounts.models import CustomerProfile

# Tạo khách hàng
user = User.objects.create_user(username='0912345678', password='pass123')
CustomerProfile.objects.create(user=user, phone='0912345678', full_name='Nguyễn Văn A')

# Tạo nhân viên
staff = User.objects.create_user(username='nhanvien01', password='pass123', is_staff=True)
```
