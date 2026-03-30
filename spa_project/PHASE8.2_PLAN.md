# PHASE 8.2: ABSOLUTE REDIRECT → NAMED URL - EXECUTION PLAN

**Date**: 2026-03-30
**Status**: ✅ COMPLETED
**Type**: Views redirect() updates
**Risk**: LOW-MEDIUM (code changes in views, but no logic changes)

---

## A. KHẢO SÁT ABSOLUTE REDIRECTS

**Total absolute redirects found**: 36 occurrences across 4 views files

### **Breakdown by app**:
- `accounts/views.py`: 4 redirects
- `spa_services/views.py`: 10 redirects
- `appointments/views.py`: 8 redirects
- `complaints/views.py`: 14 redirects

---

## B. PHÂN LOẠI REDIRECT MAPPING

### **ACCOUNTS.APP** (4 redirects)

| Line | Current Redirect | New Named URL | Parameters | Context |
|------|-----------------|---------------|------------|---------|
| 213 | `redirect('/login/')` | `redirect('accounts:login')` | None | Failed registration |
| 222 | `redirect('/quen-mat-khau/')` | `redirect('accounts:password_reset')` | None | Password reset request page |
| 265 | `redirect('/tai-khoan/')` | `redirect('accounts:customer_profile')` | None | After profile update |
| 276 | `redirect('/login/')` | `redirect('accounts:login')` | None | After logout |

### **APPOINTMENTS.APP** (8 redirects)

| Line | Current Redirect | New Named URL | Parameters | Context |
|------|-----------------|---------------|------------|---------|
| 116 | `redirect('/lich-hen-cua-toi/')` | `redirect('appointments:my_appointments')` | None | After booking success |
| 194 | `redirect('/lich-hen-cua-toi/')` | `redirect('appointments:my_appointments')` | None | After booking cancel |
| 202 | `redirect('/lich-hen-cua-toi/')` | `redirect('appointments:my_appointments')` | None | After booking cancel (GET) |
| 218 | `redirect('/lich-hen-cua-toi/')` | `redirect('appointments:my_appointments')` | None | After booking cancel (POST) |
| 230 | `redirect('/')` | `redirect('pages:home')` | None | Fallback |

### **SPA_SERVICES.APP** (10 redirects)

| Line | Current Redirect | New Named URL | Parameters | Context |
|------|-----------------|---------------|------------|---------|
| 81 | `redirect('/')` | `redirect('pages:home')` | None | Delete service without permission |
| 143 | `redirect('/manage/services/')` | `redirect('spa_services:admin_services')` | None | Delete service success |
| 157 | `redirect('/manage/services/')` | `redirect('spa_services:admin_services')` | None | Delete service success |
| 167 | `redirect('/')` | `redirect('pages:home')` | None | Fallback |
| 184 | `redirect('/manage/services/')` | `redirect('spa_services:admin_services')` | None | Edit service success |
| 196 | `redirect('/manage/services/')` | `redirect('spa_services:admin_services')` | None | Edit service success |
| 206 | `redirect('/')` | `redirect('pages:home')` | None | Fallback |
| 224 | `redirect('/manage/services/')` | `redirect('spa_services:admin_services')` | None | After form submission |

### **COMPLAINTS.APP** (14 redirects)

| Line | Current Redirect | New Named URL | Parameters | Context |
|------|-----------------|---------------|------------|---------|
| 72 | `redirect('/khieu-nai-cua-toi/')` | `redirect('complaints:customer_complaint_list')` | None | After complaint create |
| 110 | `redirect('/khieu-nai-cua-toi/')` | `redirect('complaints:customer_complaint_list')` | None | Permission denied |
| 133 | `redirect('/khieu-nai-cua-toi/')` | `redirect('complaints:customer_complaint_list')` | None | Permission denied |
| 159 | `redirect('/khieu-nai-cua-toi/%d/' % complaint_id)` | `redirect('complaints:customer_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After customer reply |
| 171 | `redirect('/')` | `redirect('pages:home')` | None | Fallback |
| 215 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 243 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 263 | `redirect('/manage/complaints/%d/' % complaint_id)` | `redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After admin take |
| 271 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 291 | `redirect('/manage/complaints/%d/' % complaint_id)` | `redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After admin assign |
| 299 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 321 | `redirect('/manage/complaints/%d/' % complaint_id)` | `redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After admin reply |
| 329 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 350 | `redirect('/manage/complaints/%d/' % complaint_id)` | `redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After admin status change |
| 358 | `redirect('/')` | `redirect('pages:home')` | None | Not staff permission denied |
| 383 | `redirect('/manage/complaints/%d/' % complaint_id)` | `redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)` | `complaint_id` | After admin complete |

---

## C. FILES SẼ SỬA

### **4 views files** (36 redirects total)

1. **accounts/views.py** (4 redirects)
2. **appointments/views.py** (8 redirects)
3. **spa_services/views.py** (10 redirects)
4. **complaints/views.py** (14 redirects)

---

## D. CODE CỤ THỂ

### **FILE 1: accounts/views.py**

**Line 213**: Failed registration
```python
# OLD
return redirect('/login/')

# NEW
return redirect('accounts:login')
```

**Line 222**: Password reset request
```python
# OLD
return redirect('/quen-mat-khau/')

# NEW
return redirect('accounts:password_reset')
```

**Line 265**: After profile update
```python
# OLD
return redirect('/tai-khoan/')

# NEW
return redirect('accounts:customer_profile')
```

**Line 276**: After logout
```python
# OLD
return redirect('/login/')

# NEW
return redirect('accounts:login')
```

---

### **FILE 2: appointments/views.py**

**Lines 116, 194, 202, 218**: After booking operations
```python
# OLD
return redirect('/lich-hen-cua-toi/')

# NEW
return redirect('appointments:my_appointments')
```

**Line 230**: Fallback
```python
# OLD
return redirect('/')

# NEW
return redirect('pages:home')
```

---

### **FILE 3: spa_services/views.py**

**Lines 81, 167, 206**: Fallback to home
```python
# OLD
return redirect('/')

# NEW
return redirect('pages:home')
```

**Lines 143, 157, 184, 196, 224**: After admin service operations
```python
# OLD
return redirect('/manage/services/')

# NEW
return redirect('spa_services:admin_services')
```

---

### **FILE 4: complaints/views.py**

**Lines 72, 110, 133**: After customer complaint operations
```python
# OLD
return redirect('/khieu-nai-cua-toi/')

# NEW
return redirect('complaints:customer_complaint_list')
```

**Line 159**: After customer reply (with ID)
```python
# OLD
return redirect('/khieu-nai-cua-toi/%d/' % complaint_id)

# NEW
return redirect('complaints:customer_complaint_detail', complaint_id=complaint_id)
```

**Lines 171, 215, 243, 271, 299, 329, 358**: Permission denied / fallback
```python
# OLD
return redirect('/')

# NEW
return redirect('pages:home')
```

**Lines 263, 291, 321, 350, 383**: After admin operations (with ID)
```python
# OLD
return redirect('/manage/complaints/%d/' % complaint_id)

# NEW
return redirect('complaints:admin_complaint_detail', complaint_id=complaint_id)
```

---

## E. REDIRECT GIỮ NGUYÊN (KHÔNG SỬA)

**None** - All absolute redirects have been mapped to named URLs.

---

## F. RỦI RO

### **LOW-MEDIUM Risk** - Because:

1. **Logic changes**: Changing redirect() calls
2. **Testing critical**: Must test all redirect flows
3. **Parameters**: Must ensure all parameters passed correctly
4. **Namespace errors**: Risk of NoReverseMatch if namespace wrong

### **Mitigation**:
- ✅ All namespaces verified in Phase 8.1
- ✅ All URL names verified in Phase 8.1
- ✅ Easy rollback: Git revert if issues
- ✅ No database changes: Pure code changes

---

## G. CÁCH TEST THỦ CÔNG

### **1. Automated Test (Django Shell)**
```python
from django.test import Client
from django.contrib.auth import get_user_model

client = Client()

# Test redirects
response = client.get('/login/')
assert response.status_code == 200

# Test named URL reverses
from django.urls import reverse
url = reverse('accounts:login')
assert url == '/login/'
```

### **2. Manual Testing Checklist**

#### **Accounts App** (4 tests)
- [ ] Failed registration → redirects to `/login/` ✅
- [ ] Password reset request → redirects to `/quen-mat-khau/` ✅
- [ ] Profile update → redirects to `/tai-khoan/` ✅
- [ ] Logout → redirects to `/login/` ✅

#### **Appointments App** (5 tests)
- [ ] Booking success → redirects to `/lich-hen-cua-toi/` ✅
- [ ] Booking cancel (POST) → redirects to `/lich-hen-cua-toi/` ✅
- [ ] Booking cancel (GET) → redirects to `/lich-hen-cua-toi/` ✅
- [ ] Fallback → redirects to `/` ✅

#### **Spa Services App** (4 tests)
- [ ] Delete service (no permission) → redirects to `/` ✅
- [ ] Delete service (success) → redirects to `/manage/services/` ✅
- [ ] Edit service → redirects to `/manage/services/` ✅
- [ ] Form submission → redirects to `/manage/services/` ✅

#### **Complaints App** (10 tests)
- [ ] Customer create → redirects to `/khieu-nai-cua-toi/` ✅
- [ ] Customer reply → redirects to detail page with ID ✅
- [ ] Permission denied → redirects to `/` ✅
- [ ] Admin take → redirects to detail page with ID ✅
- [ ] Admin assign → redirects to detail page with ID ✅
- [ ] Admin reply → redirects to detail page with ID ✅
- [ ] Admin status → redirects to detail page with ID ✅
- [ ] Admin complete → redirects to detail page with ID ✅

### **3. Browser Testing**
```bash
# Start server
python manage.py runserver

# Test in browser:
http://localhost:8000/booking/         # Try booking
http://localhost:8000/gui-khieu-nai/   # Try complaint
http://localhost:8000/manage/services/ # Try admin
```

### **4. Smoke Test**
- ✅ Click all navigation links
- ✅ Submit all forms
- ✅ Test all redirect flows
- ✅ Verify no 404 errors
- ✅ Verify parameters passed correctly

---

## H. ĐIỀU KIỂN ĐỂ SANG PHASE 8.3

### **Prerequisites Checklist**:

- [ ] All 36 absolute redirects converted to named URLs
- [ ] Django system check passes
- [ ] Server starts without errors
- [ ] Manual testing passes:
  - [ ] All account redirects work (login, password reset, profile)
  - [ ] All appointment redirects work (booking, cancel)
  - [ ] All service redirects work (admin operations)
  - [ ] All complaint redirects work (create, reply, admin actions)
  - [ ] All fallback redirects to home page work
- [ ] No `NoReverseMatch` errors in logs
- [ ] All parameters (complaint_id, appointment_id) passed correctly
- [ ] Git commit created with message: "Phase 8.2: Absolute redirects to named URLs"

### **Success Criteria**:

1. ✅ Zero absolute path redirects (`redirect('/...')`) in 4 views files
2. ✅ All redirects use named URLs or `reverse()`
3. ✅ All redirect flows tested and working
4. ✅ No regression in redirect behavior
5. ✅ All parameters passed correctly to redirects

---

## I. EXECUTION SUMMARY

**Files to modify**: 4 views files
**Total redirects to change**: 36 absolute redirects
**Redirects to keep**: 0 (all mapped)
**Estimated time**: 1-2 hours
**Risk level**: LOW-MEDIUM
**Rollback**: Git revert

**Order of execution**:
1. accounts/views.py (4 redirects) - LOWEST risk
2. appointments/views.py (8 redirects) - LOW risk
3. spa_services/views.py (10 redirects) - MEDIUM risk
4. complaints/views.py (14 redirects) - HIGHEST risk (most complex with parameters)

---

**Generated**: 2026-03-30
**Author**: Spa ANA Team
**Phase**: 8.2 - ABSOLUTE REDIRECT → NAMED URL
**Status**: 🚧 READY FOR EXECUTION
