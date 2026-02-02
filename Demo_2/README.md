# 🏥 Viện Thẩm Mỹ DIVA - Customer Care System

Hệ thống Chăm sóc khách hàng cho Viện Thẩm Mỹ DIVA - Dự án Web Development

## 📋 Table of Contents
- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cài đặt](#cài-đặt)
- [Sử dụng](#sử-dụng)
- [Database Schema](#database-schema)
- [JavaScript Functions](#javascript-functions)
- [Quy tắc nghiệp vụ](#quy-tắc-nghiệp-vụ)
- [Tài liệu](#tài-liệu)

## 🎯 Giới thiệu

Hệ thống DIVA là một giải pháp web toàn diện giúp quản lý khách hàng, đặt lịch hẹn, tư vấn và xử lý khiếu nại cho Viện Thẩm Mỹ DIVA. Hệ thống bao gồm giao diện khách hàng và trang quản trị viên.

## ✨ Tính năng

### Khách hàng
- 🔐 **Authentication**: Đăng ký, Đăng nhập với validation
- 📅 **Đặt lịch hẹn**: Chọn dịch vụ, ngày giờ, nhân viên
- 📋 **Quản lý lịch hẹn**: Xem danh sách, hủy lịch (quy tắc 24h)
- 💬 **Gửi yêu cầu tư vấn**: Form đăng ký tư vấn
- ⚠️ **Gửi khiếu nại**: Form khiếu nại với loại và nội dung
- 🌐 **Xem thông tin**: Giới thiệu, Dịch vụ, Chi tiết dịch vụ
- 💬 **Chat System**: Chat trực tuyến với nhân viên (demo)

### Quản trị viên
- 📊 **Dashboard**: Thống kê tổng quan
- 📋 **Quản lý Dịch vụ**: CRUD Services, tìm kiếm
- 📅 **Quản lý Lịch hẹn**: Filter theo dịch vụ, trạng thái, ngày tháng
- 📝 **Quản lý Tư vấn & Khiếu nại**: Cập nhật trạng thái
- 💰 **Tích điểm**: Cộng/trừ điểm cho khách hàng
- 👥 **Quản lý Nhân viên**: Danh sách nhân viên

## 🛠 Công nghệ sử dụng

### Frontend
- **HTML5**: Cấu trúc semantic
- **CSS3**: Custom styling với CSS Variables
- **Bootstrap 5**: Framework UI responsive
- **FontAwesome 6.5**: Icons
- **Google Fonts**: Montserrat
- **JavaScript ES6+**: Logic xử lý phía client

### Backend (Future)
- **Django**: Python Web Framework (MTV Architecture)
- **SQLite3**: Database
- **Bootstrap 5**: Template framework

## 📁 Cấu trúc dự án

```
Demo_2/
│
├── index.html                    # Trang chủ
├── about.html                   # Về chúng tôi
├── services.html                 # Danh sách dịch vụ
├── service-detail.html            # Chi tiết dịch vụ
│
├── login.html                   # Đăng nhập
├── register.html                # Đăng ký
│
├── booking.html                 # Đặt lịch hẹn
├── my-appointments.html          # Quản lý lịch hẹn
├── consultation.html             # Yêu cầu tư vấn
├── complaint.html                # Khiếu nại
│
├── css/
│   └── style.css               # Custom CSS styles
│
├── js/
│   └── main.js                # JavaScript logic
│
├── admin/
│   ├── dashboard.html          # Admin dashboard
│   ├── admin-services.html    # Quản lý dịch vụ
│   ├── admin-appointments.html # Quản lý lịch hẹn
│   └── admin-reports.html    # Báo cáo
│
└── database/
    └── schema.sql             # Database schema
```

## 🚀 Cài đặt

### Yêu cầu
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection cho external resources (CDN)

### Cách chạy

1. **Clone hoặc download dự án**
```bash
git clone <repository-url>
cd Demo_2
```

2. **Mở file index.html bằng trình duyệt**
```
Double-click index.html
hoặc
Right-click -> Open with Chrome/Firefox
```

3. **Sử dụng Live Server (VS Code Extension)**
```bash
# Cài đặt Live Server trong VS Code
# Right-click index.html -> Open with Live Server
```

## 💻 Sử dụng

### Đăng nhập Demo
- **Admin**: Username: `admin`, Password: (bất kỳ)
- **Customer**: Username: (bất kỳ), Password: (bất kỳ)

### Quy trình đặt lịch
1. Chọn dịch vụ từ trang Services
2. Click "Đặt lịch"
3. Điền form đặt lịch (ngày không được trong quá khứ)
4. Submit và nhận thông báo thành công

### Hủy lịch hẹn
- Chỉ được hủy trước 24h theo giờ hẹn
- Nếu < 24h: Thông báo lỗi
- Nếu > 24h: Confirm và hủy thành công

### Chat System (Demo)
1. Mở trang với chat container
2. Nhập tin nhắn và gửi
3. Nhân viên phản hồi tự động sau 2 giây
4. Auto scroll xuống tin nhắn mới nhất

## 📊 Database Schema

### Các bảng chính

#### 1. **users**
```sql
- id (PK)
- username (UNIQUE)
- email (UNIQUE)
- password
- first_name, last_name
- is_staff, is_superuser
- is_active
- date_joined, last_login
```

#### 2. **profiles**
```sql
- id (PK)
- user_id (FK -> users)
- full_name
- phone_number
- address, date_of_birth
- loyalty_points
- is_locked, lock_reason
```

#### 3. **services**
```sql
- id (PK)
- code (UNIQUE)
- name, description
- price, duration_minutes
- category
- image_url
```

#### 4. **appointments**
```sql
- id (PK)
- code (UNIQUE)
- customer_id (FK -> users)
- staff_id (FK -> users)
- service_id (FK -> services)
- appointment_date
- status (pending, confirmed, processing, completed, cancelled)
- notes
```

#### 5. **consultations**
```sql
- id (PK)
- code (UNIQUE)
- customer_name, customer_phone, customer_email
- service_id (FK -> services)
- message
- status (pending, processing, completed)
- staff_id (FK -> users)
```

#### 6. **complaints**
```sql
- id (PK)
- code (UNIQUE)
- customer_id (FK -> users)
- customer_name, customer_phone, customer_email
- complaint_type
- related_service_id, related_appointment_id
- content, expected_solution
- incident_date
- status (pending, processing, completed)
- staff_id (FK -> users)
```

#### 7. **conversations** & **messages**
```sql
conversations:
- id (PK)
- customer_id (FK -> users)
- staff_id (FK -> users)
- subject, status

messages:
- id (PK)
- conversation_id (FK -> conversations)
- sender_id (FK -> users)
- content
- is_read
```

## 🔧 JavaScript Functions

### Form Validation
```javascript
// Email validation
validateEmail(email)
// => true/false

// Phone validation (Vietnam format)
validatePhone(phone)
// => true/false

// Password strength
validatePassword(password)
// => { valid: boolean, message: string }
```

### Real-time Validation
- `blur` event: Check khi rời khỏi input
- Inline error display dưới ô input
- Clear error khi user bắt đầu sửa

### Booking Logic
```javascript
// Date constraint
dateInput.min = today;

// Cancel appointment
cancelAppointment(id, dateStr)
// Check if (appointmentDate - now) < 24h
// => Error if < 24h
// => Success if >= 24h
```

### Chat System
```javascript
// Auto scroll to bottom
scrollToBottom()

// Add message
addMessage(content, isUser)

// Auto response after 2s
setTimeout(() => {
    addMessage(randomResponse, false)
}, 2000)
```

### Filter & Search
```javascript
filterAppointments()
// Filter by:
// - Customer name (text search)
// - Service (dropdown)
// - Status (dropdown)
// - Date range (from/to)
```

## 📐 Quy tắc nghiệp vụ

### 1. Hủy lịch hẹn
- **Quy tắc**: Chỉ cho phép hủy trước 24h
- **Logic**: 
  ```
  if (appointmentDate - now < 24 hours) {
      Error: "Không thể hủy! Quá hạn 24h."
  } else {
      Success: "Hủy thành công!"
  }
  ```

### 2. Đặt lịch
- **Quy tắc**: Không chọn ngày trong quá khứ
- **Logic**:
  ```javascript
  if (selectedDate < today) {
      Error: "Vui lòng chọn ngày trong tương lai!"
  }
  ```

### 3. Validation Form
- **Email**: Regex pattern `^[^\s@]+@[^\s@]+\.[^\s@]+$`
- **Phone**: Vietnam format `(84|0[3|5|7|8|9])+([0-9]{8})`
- **Password**: Minimum 6 characters
- **Confirm password**: Must match

### 4. Trạng thái lịch hẹn
- `pending`: Chờ xác nhận
- `confirmed`: Đã xác nhận
- `processing`: Đang xử lý
- `completed`: Hoàn thành
- `cancelled`: Đã hủy

### 5. Trạng thái khiếu nại/tư vấn
- `pending`: Chưa xử lý
- `processing`: Đang xử lý
- `completed`: Hoàn thành

## 📚 Tài liệu

### Bootstrap 5
- [Documentation](https://getbootstrap.com/docs/5.3/)
- [Components](https://getbootstrap.com/docs/5.3/components/)

### FontAwesome
- [Icons](https://fontawesome.com/icons)

### Google Fonts
- [Montserrat](https://fonts.google.com/specimen/Montserrat)

### Django
- [Documentation](https://docs.djangoproject.com/)
- [Tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/)

## 🎨 Design System

### Color Palette
- **Primary (Gold)**: `#f39c12`, `#f1c40f`
- **Dark**: `#2c3e50`
- **Light**: `#ecf0f1`
- **Success**: `#27ae60`
- **Danger**: `#e74c3c`
- **Info**: `#3498db`

### Typography
- **Font Family**: Montserrat
- **Font Size**: 16px (base)
- **Line Height**: 1.6

### Spacing
- **Border Radius**: 10px (cards), 15px (chat)
- **Shadows**: 
  - Small: `0 2px 4px rgba(0,0,0,0.08)`
  - Medium: `0 4px 8px rgba(0,0,0,0.12)`
  - Large: `0 8px 16px rgba(0,0,0,0.15)`

## 🔄 Tính năng mở rộng

### Planned Features
- [ ] Backend API (Django REST Framework)
- [ ] Authentication với JWT
- [ ] Real-time chat (WebSockets)
- [ ] Email notifications
- [ ] SMS notifications
- [ ] Payment integration
- [ ] Review/Rating system
- [ ] Appointment reminder
- [ ] Photo gallery
- [ ] Blog/News section

## 📞 Hỗ trợ

### Contact
- **Hotline**: 1900 1234
- **Email**: support@diva.vn
- **Address**: 123 Nguyễn Huệ, Q.1, TP.HCM

### License
© 2024 Viện Thẩm Mỹ DIVA. All rights reserved.

## 👨‍💻 Development Team

- **Frontend Developer**: HTML/CSS/Bootstrap 5
- **Fullstack Developer**: JavaScript Logic
- **Backend Developer**: Django/SQLite3 (Future)

---

**Được xây dựng với ❤️ cho Viện Thẩm Mỹ DIVA**