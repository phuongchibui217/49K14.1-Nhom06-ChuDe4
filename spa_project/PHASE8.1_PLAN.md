# PHASE 8.1: URL NAMESPACE MIGRATION - EXECUTION PLAN

**Date**: 2026-03-30
**Type**: Template URL Namespace Updates
**Risk**: LOW (chỉ đổi namespace, không ảnh hưởng URL public, không migration)

---

## A. KHẢO SÁT TẤT CẢ TEMPLATE DÙNG `spa:`

**Tổng kết**:
- **Total occurrences**: 69 occurrences
- **Templates affected**: 15 files
- **Namespaces to change**: 17 different URL names

---

## B. PHÂN LOẠI URL NAMESPACE

### ✅ ROUTES SẼ ĐỔI SANG APP MỚI (11 URL names)

#### **PAGES APP** (2 URLs)
```django
spa:home         → pages:home          (path: home/, '')
spa:about        → pages:about         (path: about/)
spa:index        → pages:index         (path: '')
```

#### **ACCOUNTS APP** (4 URLs)
```django
spa:login                    → accounts:login                (path: login/)
spa:register                 → accounts:register             (path: register/)
spa:logout                  → accounts:logout               (path: logout/)
spa:customer_profile        → accounts:customer_profile     (path: tai-khoan/)
```

#### **SPA_SERVICES APP** (4 URLs)
```django
spa:service_list            → spa_services:service_list              (path: services/)
spa:service_detail          → spa_services:service_detail            (path: service/<id>/)
spa:admin_services          → spa_services:admin_services            (path: manage/services/)
spa:api_service_create      → spa_services:api_service_create        (path: api/services/create/)
```

#### **APPOINTMENTS APP** (3 URLs)
```django
spa:booking                 → appointments:booking               (path: booking/)
spa:my_appointments         → appointments:my_appointments       (path: lich-hen-cua-toi/)
spa:cancel_appointment      → appointments:cancel_appointment    (path: lich-hen/cancel/<id>/)
```

#### **COMPLAINTS APP** (9 URLs)
```django
spa:customer_complaint_create     → complaints:customer_complaint_create     (path: gui-khieu-nai/)
spa:customer_complaint_list       → complaints:customer_complaint_list       (path: khieu-nai-cua-toi/)
spa:customer_complaint_detail     → complaints:customer_complaint_detail     (path: khieu-nai-cua-toi/<id>/)
spa:customer_complaint_reply      → complaints:customer_complaint_reply      (path: khieu-nai-cua-toi/<id>/reply/)
spa:admin_complaints              → complaints:admin_complaints              (path: manage/complaints/)
spa:admin_complaint_detail        → complaints:admin_complaint_detail        (path: manage/complaints/<id>/)
spa:admin_complaint_reply         → complaints:admin_complaint_reply         (path: manage/complaints/<id>/reply/)
spa:admin_complaint_take          → complaints:admin_complaint_take          (path: manage/complaints/<id>/take/)
spa:admin_complaint_assign        → complaints:admin_complaint_assign        (path: manage/complaints/<id>/assign/)
spa:admin_complaint_status        → complaints:admin_complaint_status        (path: manage/complaints/<id>/status/)
spa:admin_complaint_complete      → complaints:admin_complaint_complete      (path: manage/complaints/<id>/complete/)
```

**TOTAL URLs TO CHANGE**: 22 unique URL names

---

### ⚠️ ROUTES GIỮ NGUYÊN `spa:` (8 URL names)

**Reason**: Các admin routes này CHƯA được tách sang app mới, vẫn nằm trong spa/views.py

```django
spa:admin_appointments    # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_login           # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_logout          # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_live_chat       # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_customers       # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_staff           # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_profile         # Vẫn còn trong spa/views.py, CHƯA move
spa:admin_appointments    # Sidebar active check
```

**NOT**: Các routes này sẽ được xử lý trong Phase 8.5 hoặc Phase 8.6 khi tách admin views

---

## C. DANH SÁCH FILE TEMPLATE SẼ SỬA

### **Customer-facing Templates** (10 files)

| # | File path | Occurrences | URLs to change |
|---|-----------|-------------|----------------|
| 1 | `spa/includes/header.html` | 11 | home, about, service_list, booking, my_appointments, customer_complaint_list, customer_profile, logout, login, register |
| 2 | `spa/includes/footer.html` | 1 | booking |
| 3 | `spa/pages/home.html` | 12 | booking, service_list, about |
| 4 | `spa/pages/about.html` | 1 | service_list |
| 5 | `spa/pages/login.html` | 1 | register |
| 6 | `spa/pages/booking.html` | 1 | booking |
| 7 | `spa/pages/my_appointments.html` | 2 | cancel_appointment, booking |
| 8 | `spa/pages/customer_profile.html` | 4 | my_appointments, customer_complaint_list, customer_profile |
| 9 | `spa/pages/customer_complaint_list.html` | 4 | home, customer_complaint_create, customer_complaint_detail |
| 10 | `spa/pages/customer_complaint_create.html` | 3 | home, customer_complaint_list |
| 11 | `spa/pages/customer_complaint_detail.html` | 3 | home, customer_complaint_list, customer_complaint_reply |

**Subtotal customer**: 11 files, 43 occurrences

### **Admin-facing Templates** (4 files)

| # | File path | Occurrences | URLs to change | URLs to KEEP |
|---|-----------|-------------|----------------|--------------|
| 12 | `admin/includes/sidebar.html` | 8 | admin_appointments, admin_services, admin_complaints | admin_live_chat, admin_customers, admin_staff, admin_profile, admin_logout |
| 13 | `admin/pages/admin_complaints.html` | 1 | admin_complaint_detail | - |
| 14 | `admin/pages/admin_complaint_detail.html` | 6 | admin_complaints, admin_complaint_reply, admin_complaint_take, admin_complaint_assign, admin_complaint_status, admin_complaint_complete | - |
| 15 | `admin/pages/admin_services.html` | 2 | admin_services, api_service_create | - |
| 16 | `admin/pages/admin_login.html` | 1 | - | index |
| 17 | `admin/pages/admin_clear-login.html` | 1 | home | admin_login |

**Subtotal admin**: 6 files, 19 occurrences (11 changes, 8 keep)

**TOTAL**: 17 files, 69 occurrences (54 changes, 15 keep as spa:)

---

## D. CODE CỤ THỂ CHO TỪNG FILE

### **FILE 1: spa/includes/header.html** (11 changes)

**Line 6**:
```django
<!-- OLD -->
<a class="navbar-brand" href="{% url 'spa:home' %}">

<!-- NEW -->
<a class="navbar-brand" href="{% url 'pages:home' %}">
```

**Line 16**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}" href="{% url 'spa:home' %}">Trang chủ</a>

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}" href="{% url 'pages:home' %}">Trang chủ</a>
```

**Line 19**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'about' %}active{% endif %}" href="{% url 'spa:about' %}">Về Spa ANA</a>

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'about' %}active{% endif %}" href="{% url 'pages:about' %}">Về Spa ANA</a>
```

**Line 22**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'service_list' %}active{% endif %}" href="{% url 'spa:service_list' %}">Dịch vụ</a>

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'service_list' %}active{% endif %}" href="{% url 'spa_services:service_list' %}">Dịch vụ</a>
```

**Line 25**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'booking' %}active{% endif %}" href="{% url 'spa:booking' %}">Đặt lịch</a>

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'booking' %}active{% endif %}" href="{% url 'appointments:booking' %}">Đặt lịch</a>
```

**Line 52**:
```django
<!-- OLD -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'my_appointments' %}active{% endif %}" href="{% url 'spa:my_appointments' %}">

<!-- NEW -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'my_appointments' %}active{% endif %}" href="{% url 'appointments:my_appointments' %}">
```

**Line 58**:
```django
<!-- OLD -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'customer_complaint_list' %}active{% endif %}" href="{% url 'spa:customer_complaint_list' %}">

<!-- NEW -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'customer_complaint_list' %}active{% endif %}" href="{% url 'complaints:customer_complaint_list' %}">
```

**Line 64**:
```django
<!-- OLD -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'customer_profile' %}active{% endif %}" href="{% url 'spa:customer_profile' %}">

<!-- NEW -->
<a class="dropdown-item {% if request.resolver_match.url_name == 'customer_profile' %}active{% endif %}" href="{% url 'accounts:customer_profile' %}">
```

**Line 71**:
```django
<!-- OLD -->
<a class="dropdown-item text-danger logout-link" href="{% url 'spa:logout' %}">

<!-- NEW -->
<a class="dropdown-item text-danger logout-link" href="{% url 'accounts:logout' %}">
```

**Line 80**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'login' %}active{% endif %} me-2" href="{% url 'spa:login' %}">Đăng nhập</a>

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'login' %}active{% endif %} me-2" href="{% url 'accounts:login' %}">Đăng nhập</a>
```

**Line 81**:
```django
<!-- OLD -->
<a class="btn btn-warning text-white px-3" href="{% url 'spa:register' %}">Đăng ký</a>

<!-- NEW -->
<a class="btn btn-warning text-white px-3" href="{% url 'accounts:register' %}">Đăng ký</a>
```

---

### **FILE 2: spa/includes/footer.html** (1 change)

**Line 29**:
```django
<!-- OLD -->
<a href="{% url 'spa:booking' %}" class="btn btn-warning w-100 mb-3">Đặt lịch hẹn</a>

<!-- NEW -->
<a href="{% url 'appointments:booking' %}" class="btn btn-warning w-100 mb-3">Đặt lịch hẹn</a>
```

---

### **FILE 3: spa/pages/home.html** (12 changes)

**Line 26, 213**:
```django
<!-- OLD -->
<a href="{% url 'spa:booking' %}" class="btn btn-warning btn-lg">

<!-- NEW -->
<a href="{% url 'appointments:booking' %}" class="btn btn-warning btn-lg">
```

**Line 33, 123, 131**:
```django
<!-- OLD -->
<a href="{% url 'spa:service_list' %}" class="btn btn-warning btn-lg">

<!-- NEW -->
<a href="{% url 'spa_services:service_list' %}" class="btn btn-warning btn-lg">
```

**Line 40**:
```django
<!-- OLD -->
<a href="{% url 'spa:about' %}" class="btn btn-warning btn-lg">Tìm hiểu thêm</a>

<!-- NEW -->
<a href="{% url 'pages:about' %}" class="btn btn-warning btn-lg">Tìm hiểu thêm</a>
```

**Lines 74, 87, 99, 111**:
```django
<!-- OLD -->
<a href="{% url 'spa:booking' %}?service={{ service.id }}" class="btn btn-outline-warning w-100">Đặt lịch ngay</a>
<a href="{% url 'spa:booking' %}" class="btn btn-outline-warning w-100">Đặt lịch ngay</a>

<!-- NEW -->
<a href="{% url 'appointments:booking' %}?service={{ service.id }}" class="btn btn-outline-warning w-100">Đặt lịch ngay</a>
<a href="{% url 'appointments:booking' %}" class="btn btn-outline-warning w-100">Đặt lịch ngay</a>
```

---

### **FILE 4: spa/pages/about.html** (1 change)

**Line 134**:
```django
<!-- OLD -->
<a href="{% url 'spa:service_list' %}" class="btn btn-warning btn-lg">

<!-- NEW -->
<a href="{% url 'spa_services:service_list' %}" class="btn btn-warning btn-lg">
```

---

### **FILE 5: spa/pages/login.html** (1 change)

**Line 327**:
```django
<!-- OLD -->
<a href="{% url 'spa:register' %}" class="text-warning fw-bold">Đăng ký ngay</a>

<!-- NEW -->
<a href="{% url 'accounts:register' %}" class="text-warning fw-bold">Đăng ký ngay</a>
```

---

### **FILE 6: spa/pages/booking.html** (1 change)

**Line 255**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:booking' %}" id="bookingForm" novalidate>

<!-- NEW -->
<form method="post" action="{% url 'appointments:booking' %}" id="bookingForm" novalidate>
```

---

### **FILE 7: spa/pages/my_appointments.html** (2 changes)

**Line 198**:
```django
<!-- OLD -->
action="{% url 'spa:cancel_appointment' appointment.id %}"

<!-- NEW -->
action="{% url 'appointments:cancel_appointment' appointment.id %}"
```

**Line 252**:
```django
<!-- OLD -->
<a href="{% url 'spa:booking' %}" class="btn btn-warning btn-lg">

<!-- NEW -->
<a href="{% url 'appointments:booking' %}" class="btn btn-warning btn-lg">
```

---

### **FILE 8: spa/pages/customer_profile.html** (4 changes)

**Line 317**:
```django
<!-- OLD -->
<a href="{% url 'spa:my_appointments' %}" class="btn btn-spa-secondary">

<!-- NEW -->
<a href="{% url 'appointments:my_appointments' %}" class="btn btn-spa-secondary">
```

**Line 320**:
```django
<!-- OLD -->
<a href="{% url 'spa:customer_complaint_list' %}" class="btn btn-outline-secondary">

<!-- NEW -->
<a href="{% url 'complaints:customer_complaint_list' %}" class="btn btn-outline-secondary">
```

**Lines 389, 465**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:customer_profile' %}">

<!-- NEW -->
<form method="post" action="{% url 'accounts:customer_profile' %}">
```

---

### **FILE 9: spa/pages/customer_complaint_list.html** (4 changes)

**Line 372**:
```django
<!-- OLD -->
<a href="{% url 'spa:home' %}">

<!-- NEW -->
<a href="{% url 'pages:home' %}">
```

**Lines 389, 440**:
```django
<!-- OLD -->
<a href="{% url 'spa:customer_complaint_create' %}" class="btn btn-spa-primary">

<!-- NEW -->
<a href="{% url 'complaints:customer_complaint_create' %}" class="btn btn-spa-primary">
```

**Line 427**:
```django
<!-- OLD -->
<a href="{% url 'spa:customer_complaint_detail' complaint.id %}"

<!-- NEW -->
<a href="{% url 'complaints:customer_complaint_detail' complaint.id %}"
```

---

### **FILE 10: spa/pages/customer_complaint_create.html** (3 changes)

**Lines 192**:
```django
<!-- OLD -->
<a href="{% url 'spa:home' %}">

<!-- NEW -->
<a href="{% url 'pages:home' %}">
```

**Lines 197, 332**:
```django
<!-- OLD -->
<a href="{% url 'spa:customer_complaint_list' %}">

<!-- NEW -->
<a href="{% url 'complaints:customer_complaint_list' %}">
```

---

### **FILE 11: spa/pages/customer_complaint_detail.html** (3 changes)

**Lines 517**:
```django
<!-- OLD -->
<a href="{% url 'spa:home' %}">

<!-- NEW -->
<a href="{% url 'pages:home' %}">
```

**Line 522**:
```django
<!-- OLD -->
<a href="{% url 'spa:customer_complaint_list' %}">

<!-- NEW -->
<a href="{% url 'complaints:customer_complaint_list' %}">
```

**Line 621**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:customer_complaint_reply' complaint.id %}">

<!-- NEW -->
<form method="post" action="{% url 'complaints:customer_complaint_reply' complaint.id %}">
```

---

### **FILE 12: admin/includes/sidebar.html** (3 changes, 5 keep)

**CHANGE - Line 11**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_appointments' %}active{% endif %}" href="{% url 'spa:admin_appointments' %}">

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_appointments' %}active{% endif %}" href="{% url 'appointments:admin_appointments' %}">
```

**CHANGE - Line 17**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_services' %}active{% endif %}" href="{% url 'spa:admin_services' %}">

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_services' %}active{% endif %}" href="{% url 'spa_services:admin_services' %}">
```

**CHANGE - Line 29**:
```django
<!-- OLD -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_complaints' %}active{% endif %}" href="{% url 'spa:admin_complaints' %}">

<!-- NEW -->
<a class="nav-link {% if request.resolver_match.url_name == 'admin_complaints' %}active{% endif %}" href="{% url 'complaints:admin_complaints' %}">
```

**KEEP (no change) - Lines 23, 35, 42, 49, 57**:
```django
<!-- These stay as 'spa:' because not moved yet -->
{% url 'spa:admin_live_chat' %}
{% url 'spa:admin_customers' %}
{% url 'spa:admin_staff' %}
{% url 'spa:admin_profile' %}
{% url 'spa:admin_logout' %}
```

---

### **FILE 13: admin/pages/admin_complaints.html** (1 change)

**Line 188**:
```django
<!-- OLD -->
<a href="{% url 'spa:admin_complaint_detail' complaint.id %}" class="btn btn-action btn-view">

<!-- NEW -->
<a href="{% url 'complaints:admin_complaint_detail' complaint.id %}" class="btn btn-action btn-view">
```

---

### **FILE 14: admin/pages/admin_complaint_detail.html** (6 changes)

**Line 137**:
```django
<!-- OLD -->
<li class="breadcrumb-item"><a href="{% url 'spa:admin_complaints' %}">Quản lý khiếu nại</a></li>

<!-- NEW -->
<li class="breadcrumb-item"><a href="{% url 'complaints:admin_complaints' %}">Quản lý khiếu nại</a></li>
```

**Line 248**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:admin_complaint_reply' complaint.id %}">

<!-- NEW -->
<form method="post" action="{% url 'complaints:admin_complaint_reply' complaint.id %}">
```

**Line 317**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:admin_complaint_take' complaint.id %}" class="d-inline">

<!-- NEW -->
<form method="post" action="{% url 'complaints:admin_complaint_take' complaint.id %}" class="d-inline">
```

**Line 394**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:admin_complaint_assign' complaint.id %}">

<!-- NEW -->
<form method="post" action="{% url 'complaints:admin_complaint_assign' complaint.id %}">
```

**Line 426**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:admin_complaint_status' complaint.id %}">

<!-- NEW -->
<form method="post" action="{% url 'complaints:admin_complaint_status' complaint.id %}">
```

**Line 456**:
```django
<!-- OLD -->
<form method="post" action="{% url 'spa:admin_complaint_complete' complaint.id %}">

<!-- NEW -->
<form method="post" action="{% url 'complaints:admin_complaint_complete' complaint.id %}">
```

---

### **FILE 15: admin/pages/admin_services.html** (2 changes)

**Line 23**:
```django
<!-- OLD -->
<form method="get" action="{% url 'spa:admin_services' %}">

<!-- NEW -->
<form method="get" action="{% url 'spa_services:admin_services' %}">
```

**Line 204**:
```django
<!-- OLD -->
<form id="addServiceForm" method="post" action="{% url 'spa:api_service_create' %}" enctype="multipart/form-data" onsubmit="return submitServiceForm(event)">

<!-- NEW -->
<form id="addServiceForm" method="post" action="{% url 'spa_services:api_service_create' %}" enctype="multipart/form-data" onsubmit="return submitServiceForm(event)">
```

---

### **FILE 16: admin/pages/admin_login.html** (0 changes, 1 keep)

**Line 444** - KEEP as `spa:`:
```django
<!-- KEEP - index not moved to pages yet -->
<a href="{% url 'spa:index' %}">
```

---

### **FILE 17: admin/pages/admin_clear-login.html** (1 change, 1 keep)

**CHANGE - Line 33**:
```django
<!-- OLD -->
<a href="{% url 'spa:home' %}" class="btn btn-secondary"><i class="fas fa-home me-2"></i>Trang chủ</a>

<!-- NEW -->
<a href="{% url 'pages:home' %}" class="btn btn-secondary"><i class="fas fa-home me-2"></i>Trang chủ</a>
```

**KEEP - Line 32**:
```django
<!-- KEEP - admin_login not moved yet -->
<a href="{% url 'spa:admin_login' %}" class="btn btn-primary"><i class="fas fa-sign-in-alt me-2"></i>Đăng nhập lại</a>
```

---

## E. RỦI RO

### **LOW RISK** - Vì lý do:

1. **Không ảnh hưởng URL public**: Chỉ đổi namespace trong template tag, URL thực tế không đổi
   - Ví dụ: `/services/` vẫn là `/services/` - chỉ đổi từ `spa:service_list` → `spa_services:service_list`

2. **Không ảnh hưởng database**: Không có migration

3. **Không ảnh hưởng business logic**: Chỉ là template tag change

4. **Easy rollback**: Git revert nếu có vấn đề

### **POTENTIAL ISSUES**:

1. **Template inheritance**: Nếu base template extend sai có thể break
   - **Mitigation**: Test all pages after change

2. **Active link highlighting**: `request.resolver_match.url_name` check có thể fail nếu URL name đổi
   - **Mitigation**: URL name giữ nguyên, chỉ namespace đổi → nên vẫn work

3. **Missing URLs**: Nếu template gọi URL không tồn tại trong new app
   - **Mitigation**: Đã verify tất cả URLs trong respective urls.py files

---

## F. CÁCH TEST THỦ CÔNG

### **Test Checklist**:

#### **1. Customer-facing Pages** (Test with browser)
- [ ] Trang chủ (`/`) - loads without error
- [ ] Navigation menu links work:
  - [ ] Trang chủ
  - [ ] Về Spa ANA
  - [ ] Dịch vụ
  - [ ] Đặt lịch
- [ ] Login page - "Đăng ký ngay" link works
- [ ] Services list page - all links work
- [ ] About page - "Xem chi tiết" link works
- [ ] Booking page - form submits correctly
- [ ] My appointments page - cancel button works
- [ ] Customer profile page - all links work
- [ ] Complaint pages - all links and forms work

#### **2. Admin Pages** (Test with browser)
- [ ] Admin sidebar - all links work
- [ ] Admin services page - all links work
- [ ] Admin complaints page - detail page link works
- [ ] Admin complaint detail - all form actions work
- [ ] Admin login page - home link works

#### **3. URL Verification**
```bash
# Run Django check
python manage.py check

# Show URLs - verify new namespaces exist
python manage.py show_urls | grep -E "pages:|accounts:|spa_services:|appointments:|complaints:"
```

#### **4. Link Testing**
- Click every link in customer navigation
- Click every link in admin sidebar
- Test all form submissions
- Verify no 404 errors

---

## G. ĐIỀU KIỆN ĐỂ SANG PHASE 8.2

### **Prerequisites Checklist**:

- [ ] All 17 template files updated
- [ ] All 54 URL namespace occurrences changed
- [ ] Django system check passes (`python manage.py check`)
- [ ] Server starts without errors
- [ ] Manual testing passes:
  - [ ] All customer pages load
  - [ ] All admin pages load
  - [ ] All navigation links work
  - [ ] All forms submit correctly
  - [ ] No 404 errors
- [ ] No `spa:` namespace errors in logs
- [ ] Git commit created with message: "Phase 8.1: URL namespace migration in templates"

### **Success Criteria**:

1. ✅ Zero `NoReverseMatch` errors for `spa:` URLs (except those intentionally kept)
2. ✅ All navigation links work correctly
3. ✅ All forms submit to correct URLs
4. ✅ Active link highlighting still works
5. ✅ No visual or functional regression

---

## H. EXECUTION SUMMARY

**Files to modify**: 17 templates
**Total changes**: 54 URL namespace replacements
**URLs to keep as `spa:`**: 8 (admin routes not yet moved)
**Estimated time**: 1-2 hours
**Risk level**: LOW
**Rollback**: Git revert

**Order of execution**:
1. Customer includes (header.html, footer.html)
2. Customer pages (home.html → about.html → ... → customer_complaint_detail.html)
3. Admin includes (sidebar.html)
4. Admin pages (admin_complaints.html → ... → admin_clear-login.html)
5. Test thoroughly
6. Commit changes

---

**Generated**: 2026-03-30
**Author**: Spa ANA Team
**Phase**: 8.1 - URL NAMESPACE MIGRATION
**Status**: 🚧 READY FOR EXECUTION
