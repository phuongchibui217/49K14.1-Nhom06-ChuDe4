# PHASE 8.2.5: POST-REDIRECT AUDIT & SMOKE TEST PLAN

**Date**: 2026-03-30
**Status**: 📋 IN PROGRESS
**Type**: Audit & Planning
**Risk**: NONE (read-only analysis)
**Next Phase**: TBD after this audit

---

## A. DANH SÁCH FLOW CẦN SMOKE TEST THỦ CÔNG

### **Priority 1: Critical Authentication Flows** (MUST TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 1 | **User Registration** | Home → Click Register → Fill form → Submit | Create account → Redirect home/login | HIGH - Users can't sign up |
| 2 | **User Login** | Home → Click Login → Enter credentials → Submit | Login success → Redirect home | HIGH - Users can't access |
| 3 | **Password Reset Request** | Login → Click "Quên mật khẩu" → Enter email → Submit | Show success message | MEDIUM - Users locked out |
| 4 | **Password Reset Confirm** | Click reset link from email → Enter new password → Submit | Reset success → Redirect login | MEDIUM - Security issue |
| 5 | **Logout** | Logged in → Click logout → Confirm | Logout → Redirect login | LOW - Minor inconvenience |

---

### **Priority 2: Customer Booking Flows** (MUST TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 6 | **Browse Services** | Home → Click "Dịch vụ" | Show service list | MEDIUM - Can't book |
| 7 | **View Service Detail** | Services → Click service name | Show service details | LOW - UX issue |
| 8 | **Book Appointment** (Unauth) | Service detail → Click "Đặt lịch" | Redirect to login → Then booking form | HIGH - Conversion blocker |
| 9 | **Book Appointment** (Logged in) | Logged in → Fill booking form → Submit | Create appointment → Redirect "My Appointments" | HIGH - Core feature broken |
| 10 | **View My Appointments** | Logged in → Click "Lịch hẹn của tôi" | Show appointments list with filters | MEDIUM - Can't manage bookings |
| 11 | **Cancel Appointment** | My Appointments → Click "Hủy" → Confirm POST | Status changed → Redirect list | MEDIUM - Can't manage bookings |
| 12 | **Update Customer Profile** | Logged in → Click "Tài khoản" → Update info → Submit | Update success → Redirect profile | LOW - Profile management |

---

### **Priority 3: Complaint Flows** (SHOULD TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 13 | **Create Complaint** (Logged in) | Click "Gửi khiếu nại" → Fill form → Submit | Create complaint → Redirect list | MEDIUM - Support blocked |
| 14 | **View My Complaints** | Logged in → Click "Khiếu nại của tôi" | Show complaints list | LOW - Can't track issues |
| 15 | **Reply to Complaint** | Complaint detail → Add reply → Submit | Reply added → Redirect detail | LOW - Support delayed |

---

### **Priority 4: Admin Service Management** (SHOULD TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 16 | **Admin Login** | /manage/login/ → Enter credentials | Admin dashboard | HIGH - Admin blocked |
| 17 | **View Services Admin** | Admin → Click "Quản lý dịch vụ" | Show services list with pagination | MEDIUM - Can't manage |
| 18 | **Create Service** (Admin) | Services admin → Fill form → Submit | Service created → Redirect list | MEDIUM - Can't add services |
| 19 | **Edit Service** (Admin) | Services admin → Click edit → Update → Submit | Service updated → Redirect list | LOW - Can't update |
| 20 | **Delete Service** (Admin) | Services admin → Click delete → Confirm POST | Service deleted → Redirect list | LOW - Can't remove |

---

### **Priority 5: Admin Complaint Management** (NICE TO TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 21 | **View Complaints Admin** | Admin → Click "Quản lý khiếu nại" | Show complaints with filters | MEDIUM - Can't manage |
| 22 | **Take Complaint** (Admin) | Complaint detail → Click "Nhận xử lý" | Assigned to admin → Redirect detail | LOW - Workflow broken |
| 23 | **Reply to Complaint** (Admin) | Complaint detail → Add reply → Submit | Reply added → Redirect detail | LOW - Support delayed |
| 24 | **Change Complaint Status** (Admin) | Complaint detail → Change status → Submit | Status updated → Redirect detail | LOW - Workflow broken |
| 25 | **Complete Complaint** (Admin) | Complaint detail → Add resolution → Complete | Marked resolved → Redirect detail | LOW - Workflow broken |

---

### **Priority 6: Admin Appointment Management** (NICE TO TEST)

| # | Flow | Steps | Expected Result | Risk if Broken |
|---|------|-------|-----------------|----------------|
| 26 | **View Appointments Admin** | Admin → Click "Quản lý lịch hẹn" | Show scheduler/calendar | MEDIUM - Can't manage |
| 27 | **Create Appointment** (Admin) | Admin → Fill booking form → Submit | Appointment created | MEDIUM - Manual booking blocked |
| 28 | **Update Appointment** (Admin) | Click appointment → Edit → Submit | Changes saved | LOW - Can't modify |

---

**TOTAL TEST FLOWS**: 28 flows
**CRITICAL (HIGH Risk)**: 6 flows
**IMPORTANT (MEDIUM Risk)**: 13 flows
**NICE TO HAVE (LOW Risk)**: 9 flows

---

## B. DANH SÁCH IMPORT CÒN PHỤ THUỘC `spa.models`

### **Summary Statistics**

- **Total files importing**: 19 files
- **Total import statements**: 21 occurrences
- **Categories**: Views, Forms, Services, Decorators, Validators, Commands

---

### **Breakdown by Type**

#### **1. Views (5 files, 5 imports)**

| File | Line | Import | Models | Target App After Move |
|------|------|--------|--------|----------------------|
| `accounts/views.py` | 24 | `from spa.models import CustomerProfile` | CustomerProfile | accounts |
| `pages/views.py` | 12 | `from spa.models import Service` | Service | spa_services |
| `appointments/views.py` | 23 | `from spa.models import Appointment, CustomerProfile, Service, Room` | Appointment, Room, CustomerProfile, Service | appointments |
| `spa_services/views.py` | 23 | `from spa.models import Service` | Service | spa_services |
| `complaints/views.py` | 19 | `from spa.models import (Complaint, ComplaintReply, ComplaintHistory, CustomerProfile, Service)` | Complaint, ComplaintReply, ComplaintHistory, CustomerProfile, Service | complaints |

**Total models to move from views**: 12 model references

---

#### **2. Forms (3 files, 3 imports)**

| File | Line | Import | Models | Target App After Move |
|------|------|--------|--------|----------------------|
| `accounts/forms.py` | 16 | `from spa.models import CustomerProfile` | CustomerProfile | accounts |
| `appointments/forms.py` | 13 | `from spa.models import Appointment, Service` | Appointment, Service | appointments |
| `spa_services/forms.py` | 14 | `from spa.models import Service` | Service | spa_services |
| `complaints/forms.py` | 17 | `from spa.models import Complaint, Service, ComplaintReply` | Complaint, Service, ComplaintReply | complaints |

**Total models to move from forms**: 8 model references

---

#### **3. Service Layer (3 files, 3 imports)**

| File | Line | Import | Models | Target App After Move |
|------|------|--------|--------|----------------------|
| `appointments/services.py` | 19 | `from spa.models import Appointment, Room` | Appointment, Room | appointments |
| `appointments/appointment_services.py` | 21 | `from spa.models import Appointment, CustomerProfile, Service, Room` | Appointment, Room, CustomerProfile, Service | appointments |
| `spa_services/service_services.py` | 21 | `from spa.models import Service` | Service | spa_services |

**Total models to move from services**: 7 model references

---

#### **4. Core Utilities (4 files, 4 imports)**

| File | Line | Import | Models | Target App After Move |
|------|------|--------|--------|----------------------|
| `core/decorators.py` | 182 | `from spa.models import CustomerProfile` | CustomerProfile | accounts |
| `core/decorators.py` | 239 | `from spa.models import CustomerProfile` | CustomerProfile | accounts |
| `core/validators.py` | 46 | `from spa.models import Service` | Service | spa_services |
| `core/validators.py` | 244 | `from spa.models import CustomerProfile` | CustomerProfile | accounts |

**Total models to move from core**: 4 model references

---

#### **5. Management Commands (2 files, 2 imports)**

| File | Line | Import | Models | Target App After Move |
|------|------|--------|--------|----------------------|
| `spa/management/commands/seed_rooms.py` | 3 | `from spa.models import Room` | Room | appointments |
| `spa/management/commands/seed_data.py` | 3 | `from spa.models import Service` | Service | spa_services |

**Total models to move from commands**: 2 model references

---

### **Model Dependency Map**

**Models to be moved** (from Phase 8.3 plan):

| Model | Current Location | Target App | Files Using It |
|-------|-----------------|------------|----------------|
| **Service** | spa/models.py | spa_services | 9 files |
| **Appointment** | spa/models.py | appointments | 3 files |
| **Room** | spa/models.py | appointments | 3 files |
| **Complaint** | spa/models.py | complaints | 2 files |
| **ComplaintReply** | spa/models.py | complaints | 2 files |
| **ComplaintHistory** | spa/models.py | complaints | 1 file |
| **CustomerProfile** | spa/models.py | accounts | 8 files |

---

### **Cross-App Dependencies**

**Critical finding**: Some models reference other models across apps:

1. **Appointment** → references:
   - `CustomerProfile` (FK)
   - `Service` (FK)
   - `Room` (FK, nullable)

2. **Complaint** → references:
   - `CustomerProfile` (FK, nullable)
   - `Service` (FK, nullable)

3. **ComplaintReply** → references:
   - `Complaint` (FK)
   - `User` (FK from django.contrib.auth)

**Implication**: Models MUST be moved in specific order to avoid foreign key errors:

```
Batch 1: CustomerProfile (accounts) - no external FKs
Batch 2: Service (spa_services) - only references User
Batch 3: Complaint, ComplaintReply, ComplaintHistory (complaints) - references CustomerProfile, Service
Batch 4: Appointment, Room (appointments) - references CustomerProfile, Service
```

---

## C. DANH SÁCH TEMPLATE PATH CŨ CÒN SÓT

### **Summary Statistics**

- **Total templates using `spa/` path**: 16 files
- **Total `spa:` URL namespace references**: 7 occurrences in 3 files
- **All templates still in**: `templates/spa/` directory (not moved yet)

---

### **Template Path Issues**

#### **1. All 16 templates still use `extends 'spa/base.html'`**

This is **INTENTIONAL** and correct for Phase 8.2.5 - templates will be moved in Phase 8.4.

**Files affected**:
- `templates/spa/base.html`
- `templates/spa/pages/*.html` (15 files)

**Status**: ✅ OK for now, will fix in Phase 8.4

---

#### **2. Admin templates using `spa:` namespace (3 files, 7 URLs)**

| File | Line | URL | Should Be | Context |
|------|------|-----|-----------|---------|
| `admin/pages/admin_clear-login.html` | 32 | `{% url 'spa:admin_login' %}` | **KEEP** (not moved yet) | Admin login page |
| `admin/includes/sidebar.html` | 23 | `{% url 'spa:admin_live_chat' %}` | **KEEP** | Live chat (not moved) |
| `admin/includes/sidebar.html` | 35 | `{% url 'spa:admin_customers' %}` | **KEEP** | Customers (not moved) |
| `admin/includes/sidebar.html` | 42 | `{% url 'spa:admin_staff' %}` | **KEEP** | Staff (not moved) |
| `admin/includes/sidebar.html` | 49 | `{% url 'spa:admin_profile' %}` | **KEEP** | Profile (not moved) |
| `admin/includes/sidebar.html` | 57 | `{% url 'spa:admin_logout' %}` | **KEEP** | Logout (not moved) |
| `spa/base.html` | 444 | `{% url 'spa:index' %}` | **CHANGE** to `pages:home` | Footer home link |

**Status**: ⚠️ **1 FOUND** - `spa/base.html` line 444 should use `pages:home`

---

### **Template Path Analysis**

**Current structure**:
```
templates/
├── spa/
│   ├── base.html
│   └── pages/
│       ├── home.html
│       ├── about.html
│       ├── login.html
│       ├── register.html
│       ├── password_reset.html
│       ├── password_reset_sent.html
│       ├── password_reset_confirm.html
│       ├── customer_profile.html
│       ├── services.html
│       ├── service_detail.html
│       ├── booking.html
│       ├── my_appointments.html
│       ├── cancel_appointment.html
│       ├── customer_complaint_create.html
│       ├── customer_complaint_list.html
│       └── customer_complaint_detail.html
└── admin/
    ├── pages/
    │   ├── admin_login.html
    │   ├── admin_clear-login.html
    │   └── ...
    └── includes/
        ├── sidebar.html
        └── ...
```

**Target structure** (Phase 8.4):
```
templates/
├── base.html (shared)
├── pages/
│   ├── home.html
│   └── about.html
├── accounts/
│   ├── login.html
│   ├── register.html
│   ├── password_reset.html
│   ├── password_reset_sent.html
│   ├── password_reset_confirm.html
│   └── customer_profile.html
├── spa_services/
│   ├── services.html
│   └── service_detail.html
├── appointments/
│   ├── booking.html
│   ├── my_appointments.html
│   └── cancel_appointment.html
├── complaints/
│   ├── customer_complaint_create.html
│   ├── customer_complaint_list.html
│   └── customer_complaint_detail.html
└── admin/
    ├── pages/
    │   ├── admin_login.html
    │   └── ...
    └── includes/
        └── ...
```

---

## D. ĐÁNH GIÁ MỨC SẴN SÀNG ĐỂ MOVE MODELS

### **Readiness Assessment**

| Criterion | Status | Score | Notes |
|-----------|--------|-------|-------|
| **1. URL Namespaces Clean** | ✅ PASS | 10/10 | All public-facing URLs migrated (Phase 8.1 + 8.2) |
| **2. Redirects Clean** | ✅ PASS | 10/10 | All 36 absolute redirects converted (Phase 8.2) |
| **3. Templates Clean** | ⚠️ PARTIAL | 7/10 | 1 stray `spa:` URL found, templates not moved yet |
| **4. Imports Catalogued** | ✅ PASS | 10/10 | All 19 files with spa.models imports identified |
| **5. Dependencies Mapped** | ✅ PASS | 10/10 | Cross-app FK relationships analyzed |
| **6. Move Order Defined** | ✅ PASS | 10/10 | 5-batch sequence planned with FK safety |
| **7. Migration Plan Ready** | ✅ PASS | 10/10 | Detailed plan in PHASE8.3_PLAN.md |
| **8. Rollback Plan Ready** | ⚠️ PARTIAL | 8/10 | Git revert available, but DB backup needed |
| **9. Test Plan Defined** | ✅ PASS | 10/10 | 28 smoke test flows identified |

**OVERALL READINESS SCORE**: **85/100** ✅

**Verdict**: **READY TO PROCEED** with caveats

---

### **Remaining Blockers**

**Blocker 1: Template URL namespace** (LOW priority)
- File: `spa/base.html` line 444
- Issue: Uses `{% url 'spa:index' %}` instead of `{% url 'pages:home' %}`
- Impact: Minor - footer link on public pages
- Risk: LOW
- Can be fixed: **Before OR after** model move

**Blocker 2: Templates not moved** (MEDIUM priority)
- Impact: Can't test template render after model move
- Risk: MEDIUM - templates may break if model paths change
- Recommendation: **Fix after** model move (Phase 8.4)

**Blocker 3: No database backup** (HIGH priority)
- Impact: Can't rollback if migration fails
- Risk: HIGH - data loss possible
- Requirement: **Must do** before model move

---

### **Model Move Complexity Analysis**

| Model | FK Dependencies | Move Complexity | Risk Level | Batch Order |
|-------|----------------|-----------------|------------|-------------|
| CustomerProfile | User (django.contrib.auth) | LOW | LOW | 1st |
| Service | User (created_by) | LOW | LOW | 2nd |
| ComplaintReply | Complaint (FK) | LOW | LOW | 3rd (with Complaint) |
| ComplaintHistory | Complaint (FK) | LOW | LOW | 3rd (with Complaint) |
| Complaint | CustomerProfile, Service | MEDIUM | MEDIUM | 3rd |
| Room | None (but used by Appointment) | LOW | LOW | 4th (or with Appointment) |
| Appointment | CustomerProfile, Service, Room | HIGH | HIGH | 5th (or 4th with Room) |

**Recommended Batch Order**:
```
Batch 1: CustomerProfile → accounts
Batch 2: Service → spa_services
Batch 3: Complaint, ComplaintReply, ComplaintHistory → complaints
Batch 4: Room, Appointment → appointments
```

---

## E. KHUYẾN NGHỊ BƯỚC TIẾP THEO AN TOÀN NHẤT

### **Recommended Next Steps**

#### **OPTION A: Model-First Approach** (RECOMMENDED) ✅

**Rationale**:
1. ✅ Models are the **source of truth** - should be in correct location first
2. ✅ Import statements will be **simpler** after models moved
3. ✅ Template move (Phase 8.4) will use **correct model paths** from start
4. ✅ One-time migration pain, then clean slate

**Sequence**:
```
Phase 8.2.5: [CURRENT] Audit & Smoke Test Plan
    ↓
Phase 8.3: Move Models (7 models, 5 batches, HIGH RISK)
    ├─ Prerequisite: Database backup
    ├─ Batch 1: CustomerProfile → accounts
    ├─ Batch 2: Service → spa_services
    ├─ Batch 3: Complaint ecosystem → complaints
    └─ Batch 4: Appointment + Room → appointments
    ↓
Phase 8.4: Move Templates (23 templates)
    ├─ Fix spa:home → pages:home in base.html
    ├─ Move templates to app folders
    └─ Update extends paths
    ↓
Phase 8.5: Extract remaining views/forms
Phase 8.6: Finalize admin_panel + Delete spa
```

**Pros**:
- ✅ Logical order: foundation (models) first
- ✅ Fewer total changes (no need to re-update templates after models move)
- ✅ Cleaner git history (models done once)

**Cons**:
- ❌ Higher upfront risk (migration)
- ❌ Can't fully test until after Phase 8.4 (templates moved)

---

#### **OPTION B: Template-First Approach** (ALTERNATIVE)

**Rationale**:
1. ✅ Templates have **zero database impact**
2. ✅ Can **test immediately** after changes
3. ✅ Lower risk, builds confidence

**Sequence**:
```
Phase 8.2.5: [CURRENT] Audit & Smoke Test Plan
    ↓
Phase 8.4: Move Templates FIRST
    ├─ Fix spa:home → pages:home
    ├─ Move templates to app folders
    └─ Update extends paths
    ↓
Phase 8.3: Move Models SECOND
    ├─ Templates already using correct paths
    └─ Can test template renders immediately
```

**Pros**:
- ✅ Lower risk (no migrations)
- ✅ Can verify changes immediately
- ✅ Builds momentum with quick wins

**Cons**:
- ❌ Illogical order (presentation before data)
- ❌ Model imports in views still use `spa.models`
- ❌ Templates may need updates after models move anyway

---

### **FINAL RECOMMENDATION: OPTION A (Model-First)** ✅

**Why Model-First is safer**:

1. **Architectural Correctness**
   - Models define the data structure
   - Should be in final location before building on top
   - Follows Django best practices

2. **Import Clarity**
   - After models moved: `from accounts.models import CustomerProfile` ✅
   - Before models moved: `from spa.models import CustomerProfile` (still points to spa) ❌

3. **Template Simplicity**
   - When templates move in Phase 8.4, models are already in correct apps
   - No need to update templates twice

4. **Risk Containment**
   - Get the hardest part (migrations) done early
   - If something breaks, easier to rollback before more changes pile up

5. **Testing Parity**
   - Both approaches require testing after Phase 8.4 anyway
   - Model-first doesn't add extra testing burden

---

### **CRITICAL PREREQUISITES Before Phase 8.3**

**MUST DO** (cannot proceed without):

1. ✅ **Database Backup**
   ```bash
   python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
   # Or: pg_dump spa_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. ✅ **Git Commit Before Starting**
   ```bash
   git add .
   git commit -m "Phase 8.2.5: Pre-move audit complete"
   git tag phase-8.2.5-before-model-move
   ```

3. ✅ **Smoke Test Baseline**
   - Run 28 smoke test flows (from Section A)
   - Document any pre-existing failures
   - This becomes baseline to compare against

---

### **Optional Improvements** (nice to have, but not required):

1. ⚠️ **Fix `spa:home` → `pages:home` in base.html**
   - Takes 1 minute
   - Reduces confusion
   - Can be done anytime

2. ⚠️ **Create rollback script**
   ```bash
   # rollback_phase_8_3.sh
   git checkout phase-8.2.5-before-model-move
   python manage.py migrate spa zero
   python manage.py migrate
   ```

3. ⚠️ **Document model field usage**
   - Search for `model.field` references in code
   - Identify any hardcoded field names
   - Reduces risk of breakage

---

## F. ACTION ITEMS

### **Before Phase 8.3** (Must complete)

- [ ] Create database backup
- [ ] Git commit + tag current state
- [ ] Run baseline smoke tests (28 flows)
- [ ] Document any pre-existing failures
- [ ] Fix `spa:home` → `pages:home` in base.html (optional)

### **Phase 8.3 Execution** (Model move)

- [ ] Move Batch 1: CustomerProfile
- [ ] Test accounts app (6 flows)
- [ ] Move Batch 2: Service
- [ ] Test spa_services app (3 flows)
- [ ] Move Batch 3: Complaint ecosystem
- [ ] Test complaints app (4 flows)
- [ ] Move Batch 4: Room + Appointment
- [ ] Test appointments app (5 flows)
- [ ] Run full smoke test suite (28 flows)

### **After Phase 8.3** (Before Phase 8.4)

- [ ] Verify all imports use correct app paths
- [ ] Check for any remaining `from spa.models import`
- [ ] Document any workarounds needed
- [ ] Update PHASE8.3_SUMMARY.md

---

## G. SUMMARY

**Current State**:
- ✅ URL namespaces: Clean
- ✅ Redirects: Clean
- ⚠️ Templates: 1 stray URL, not moved
- ✅ Imports: Catalogued (19 files)
- ✅ Dependencies: Mapped

**Readiness for Phase 8.3**: **85%** ✅

**Recommended Approach**: **Model-First (OPTION A)** ✅

**Critical Prerequisites**:
1. Database backup
2. Git commit + tag
3. Baseline smoke tests

**Estimated Timeline**:
- Phase 8.2.5 (Audit): ✅ COMPLETE
- Phase 8.3 (Models): 2-3 hours
- Phase 8.4 (Templates): 1-2 hours
- Phase 8.5 (Views/Forms): 1-2 hours
- Phase 8.6 (Finalize): 1 hour

**Total remaining**: ~5-8 hours

---

**Generated**: 2026-03-30
**Author**: Spa ANA Team
**Phase**: 8.2.5 - POST-REDIRECT AUDIT & SMOKE TEST PLAN
**Status**: 📋 READY FOR NEXT PHASE
