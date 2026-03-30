# PHASE 8.3: TEMPLATE CLEANUP PREP

**Date**: 2026-03-30
**Status**: ✅ IN PROGRESS
**Type**: Template cleanup (NO model changes, NO migrations)
**Risk**: LOW (template-only changes)
**Scope**: Fix namespace remnants, audit template structure, plan template move

---

## A. TEMPLATE CÒN SÓT NAMESPACE CŨ

### **Namespace Remnants Found & Fixed**

| File | Line | Old Namespace | New Namespace | Status |
|------|------|---------------|---------------|--------|
| `admin/pages/admin_login.html` | 444 | `{% url 'spa:index' %}` | `{% url 'pages:home' %}` | ✅ FIXED |

### **Admin URLs Still Using `spa:` (INTENTIONAL - Not Moved Yet)**

| File | URLs | Context | Status |
|------|------|---------|--------|
| `admin/includes/sidebar.html` | admin_live_chat, admin_customers, admin_staff, admin_profile, admin_logout | Admin routes NOT moved yet | ✅ CORRECT |
| `admin/pages/admin_clear-login.html` | admin_login | Admin login NOT moved yet | ✅ CORRECT |
| `admin/pages/admin_login.html` | admin_login | Admin login NOT moved yet | ✅ CORRECT (after fix) |

**Note**: These 7 `spa:` URLs in admin area are **intentional** - admin routes have not been moved yet and will be handled in a later phase.

---

## B. DANH SÁCH TEMPLATE PATH HIỆN TẠI

### **Current Template Structure**

```
templates/
├── spa/                          # Public-facing templates
│   ├── base.html                # Main base template (105 lines)
│   ├── includes/
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── floating_buttons.html
│   │   └── chat_widget.html
│   └── pages/                   # 15 page templates
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
│
└── admin/                       # Admin area templates
    ├── base.html               # Admin base template (107 lines)
    ├── includes/
    │   ├── header.html
    │   └── sidebar.html
    └── pages/                  # 9 page templates
        ├── admin_login.html
        ├── admin_clear-login.html
        ├── admin_appointments.html
        ├── admin_services.html
        ├── admin_complaints.html
        ├── admin_complaint_detail.html
        ├── admin_customers.html
        ├── admin_staff.html
        └── profile.html
```

---

### **Template Breakdown by App**

#### **1. PAGES App** (2 templates)
Currently in: `templates/spa/pages/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Home | `spa/pages/home.html` | `spa/base.html` | `pages/home.html` |
| About | `spa/pages/about.html` | `spa/base.html` | `pages/about.html` |

**Move complexity**: LOW
- Only 2 templates
- Both use `spa/base.html`
- Need to extract shared base or create `pages/base.html`

---

#### **2. ACCOUNTS App** (6 templates)
Currently in: `templates/spa/pages/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Login | `spa/pages/login.html` | `spa/base.html` | `accounts/login.html` |
| Register | `spa/pages/register.html` | `spa/base.html` | `accounts/register.html` |
| Password Reset | `spa/pages/password_reset.html` | `spa/base.html` | `accounts/password_reset.html` |
| Password Reset Sent | `spa/pages/password_reset_sent.html` | `spa/base.html` | `accounts/password_reset_sent.html` |
| Password Reset Confirm | `spa/pages/password_reset_confirm.html` | `spa/base.html` | `accounts/password_reset_confirm.html` |
| Customer Profile | `spa/pages/customer_profile.html` | `spa/base.html` | `accounts/customer_profile.html` |

**Move complexity**: MEDIUM
- 6 templates
- All use `spa/base.html`
- Need to decide: keep using `spa/base.html` or create `accounts/base.html`

---

#### **3. SPA_SERVICES App** (2 templates)
Currently in: `templates/spa/pages/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Service List | `spa/pages/services.html` | `spa/base.html` | `spa_services/services.html` |
| Service Detail | `spa/pages/service_detail.html` | `spa/base.html` | `spa_services/service_detail.html` |

**Move complexity**: LOW
- Only 2 templates
- Simple structure

---

#### **4. APPOINTMENTS App** (3 templates)
Currently in: `templates/spa/pages/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Booking | `spa/pages/booking.html` | `spa/base.html` | `appointments/booking.html` |
| My Appointments | `spa/pages/my_appointments.html` | `spa/base.html` | `appointments/my_appointments.html` |
| Cancel Appointment | `spa/pages/cancel_appointment.html` | `spa/base.html` | `appointments/cancel_appointment.html` |

**Move complexity**: LOW
- Only 3 templates
- Related functionality

---

#### **5. COMPLAINTS App** (3 templates)
Currently in: `templates/spa/pages/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Create Complaint | `spa/pages/customer_complaint_create.html` | `spa/base.html` | `complaints/customer_complaint_create.html` |
| Complaint List | `spa/pages/customer_complaint_list.html` | `spa/base.html` | `complaints/customer_complaint_list.html` |
| Complaint Detail | `spa/pages/customer_complaint_detail.html` | `spa/base.html` | `complaints/customer_complaint_detail.html` |

**Move complexity**: LOW
- Only 3 templates
- Related functionality

---

#### **6. ADMIN Area** (9 templates)
Currently in: `templates/admin/`

| Template | Current Path | Extends | Target Path |
|----------|-------------|---------|-------------|
| Admin Login | `admin/pages/admin_login.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Clear Login | `admin/pages/admin_clear-login.html` | Standalone | **KEEP** (not moved) |
| Admin Appointments | `admin/pages/admin_appointments.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Services | `admin/pages/admin_services.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Complaints | `admin/pages/admin_complaints.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Complaint Detail | `admin/pages/admin_complaint_detail.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Customers | `admin/pages/admin_customers.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Staff | `admin/pages/admin_staff.html` | `admin/base.html` | **KEEP** (not moved) |
| Admin Profile | `admin/pages/profile.html` | `admin/base.html` | **KEEP** (not moved) |

**Move complexity**: NONE
- Already in correct location
- Will be handled in later phase when admin_panel app is finalized

---

### **Shared Base Templates**

| Template | Location | Used By | Size | Notes |
|----------|----------|---------|------|-------|
| `spa/base.html` | `templates/spa/` | All 15 spa/pages/* templates | 105 lines | Public-facing base |
| `admin/base.html` | `templates/admin/` | All 9 admin/pages/* templates | 107 lines | Admin area base |

---

## C. KẾ HOẠCH MOVE TEMPLATE AN TOÀN NHẤT

### **Recommended Strategy: Gradual Migration with Shared Base**

**Approach**: Keep using shared `spa/base.html` during transition, extract later if needed

---

### **Phase 1: NO-OP Phase** ✅ (Current - COMPLETED)

**What was done**:
- ✅ Fixed `spa:index` → `pages:home` in admin_login.html
- ✅ Verified all public-facing URLs already migrated (Phase 8.1 + 8.2)
- ✅ Verified all redirects already migrated (Phase 8.2)

**Result**: Templates are in clean state, ready for move

---

### **Phase 2: Template Directory Move** (Recommended Next Step)

**Approach**: Move templates WITHOUT changing extends paths initially

**Why this approach**:
- ✅ Lowest risk - just moves files, doesn't change Django template resolution
- ✅ Can test incrementally - move one app at a time
- ✅ Easy rollback - git revert if issues
- ✅ No code changes required initially

**Procedure**:
1. Create new template directories
2. Copy templates to new locations
3. Update views.py to point to new template paths
4. Test each app
5. Remove old templates after verification

---

### **Move Order by Complexity** (Low → High Risk)

#### **BATCH 1: Simple Apps** (LOWEST RISK)

**App**: spa_services, appointments, complaints
**Templates**: 2 + 3 + 3 = 8 templates
**Risk**: LOW
**Reason**: Simple, self-contained, no complex dependencies

**Steps**:
```bash
# 1. Create directories
mkdir -p templates/spa_services
mkdir -p templates/appointments
mkdir -p templates/complaints

# 2. Copy templates
cp templates/spa/pages/services.html templates/spa_services/
cp templates/spa/pages/service_detail.html templates/spa_services/

cp templates/spa/pages/booking.html templates/appointments/
cp templates/spa/pages/my_appointments.html templates/appointments/
cp templates/spa/pages/cancel_appointment.html templates/appointments/

cp templates/spa/pages/customer_complaint_*.html templates/complaints/

# 3. Update views.py template paths
# spa_services/views.py: 'spa/pages/services.html' → 'spa_services/services.html'
# appointments/views.py: 'spa/pages/booking.html' → 'appointments/booking.html'
# complaints/views.py: 'spa/pages/customer_complaint_create.html' → 'complaints/customer_complaint_create.html'

# 4. Test each app
# 5. If OK, remove old templates
```

**Estimated time**: 30-45 minutes

---

#### **BATCH 2: Medium Apps** (MEDIUM RISK)

**App**: pages, accounts
**Templates**: 2 + 6 = 8 templates
**Risk**: MEDIUM
**Reason**: More templates, accounts has authentication flows

**Steps**:
```bash
# Same procedure as Batch 1
# pages: home.html, about.html
# accounts: login, register, password_reset*, customer_profile
```

**Estimated time**: 45-60 minutes

---

#### **BATCH 3: Base Template Decision** (DEFERRED)

**Decision Point**: After moving all page templates, decide whether to:

**Option A**: Keep using `spa/base.html`
- Pros: Simple, already working
- Cons: Doesn't fully modularize

**Option B**: Extract shared base to `templates/base.html`
- Pros: True separation, no app owns the base
- Cons: More changes, higher risk

**Recommendation**: **DEFER this decision** until after model move (old Phase 8.3, now Phase 8.4)

**Reason**: Model move is higher impact, base template extraction can be done later with clearer view of final structure

---

### **Final Template Structure Target**

```
templates/
├── base.html                    # Shared base (OPTIONAL - defer decision)
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
└── admin/                       # Unchanged for now
    ├── base.html
    ├── includes/
    └── pages/
```

---

## D. CODE CLEANUP TEMPLATE

### **What Was Done in Phase 8.3**

**Single Change**:
```html
<!-- File: templates/admin/pages/admin_login.html -->
<!-- Line 444 -->

<!-- OLD -->
<a href="{% url 'spa:index' %}">

<!-- NEW -->
<a href="{% url 'pages:home' %}">
```

**Impact**:
- ✅ Fixes last `spa:` namespace remnant in public-facing area
- ✅ Admin login page now correctly redirects to `pages:home`
- ✅ Zero risk (URL already exists, just fixing reference)

**Verification**:
```bash
✅ Django check: No issues
✅ Home page: HTTP 200
✅ Admin login page: HTTP 200
```

---

### **What Was NOT Done** (Intentional)

❌ **Did NOT move templates** - Deferring to Phase 8.5
❌ **Did NOT change extends paths** - No template structure changes
❌ **Did NOT touch admin sidebar URLs** - Those `spa:` URLs are intentional (admin routes not moved yet)
❌ **Did NOT create new base templates** - Defer decision until after model move

---

## E. CÁCH TEST THỦ CÔNG

### **Pre-Move Testing** (Current State)

**Test all 28 smoke test flows** from Phase 8.2.5 to establish baseline:

**Critical Flows** (6):
1. User Registration → Home
2. User Login → Home
3. Password Reset Request → Success page
4. Password Reset Confirm → Login
5. Logout → Login
6. Book Appointment (unauth) → Login → Booking form

**Important Flows** (13):
7-19. Browse services, view details, manage appointments, update profile, file/view complaints, admin login, manage services

**Nice to Have** (9):
20-28. Admin complaints/appointments management

---

### **During Template Move Testing** (Phase 8.5)

**After each batch move**:

1. **Restart Django server** (clear template cache)
   ```bash
   # Kill and restart
   python manage.py runserver
   ```

2. **Test affected app**:
   - **spa_services**: Visit `/dich-vu/` and service detail
   - **appointments**: Visit `/booking/` (logged in)
   - **complaints**: Visit `/gui-khieu-nai/` (logged in)

3. **Check for template errors**:
   ```bash
   # Look for TemplateDoesNotExist errors
   # Check browser console for 404s
   # Verify page renders completely
   ```

4. **Verify extends still work**:
   - All pages should still include header/footer
   - CSS/JS should load
   - Navigation should work

---

### **Post-Move Testing** (All batches complete)

**Full regression test**: Run all 28 smoke test flows again

**Compare results**: Should be identical to pre-move baseline

---

## F. ĐIỀU KIỂN ĐỂ SAU NÀY MỚI XÉT MOVE MODELS

### **Readiness Checklist for Model Move** (Old Phase 8.3, Now Phase 8.4)

**Must Complete BEFORE Model Move**:

- [ ] **Phase 8.3**: ✅ Template cleanup complete
  - [x] Fix namespace remnants
  - [x] Audit template structure
  - [x] Create move plan

- [ ] **Phase 8.5**: ✅ Template move complete (RECOMMENDED before models)
  - [ ] Move spa_services templates (2)
  - [ ] Move appointments templates (3)
  - [ ] Move complaints templates (3)
  - [ ] Move pages templates (2)
  - [ ] Move accounts templates (6)
  - [ ] Test all 28 smoke test flows
  - [ ] Verify no TemplateDoesNotExist errors

- [ ] **Database Backup** (MANDATORY)
  ```bash
  python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
  ```

- [ ] **Git Commit + Tag**
  ```bash
  git add .
  git commit -m "Phase 8.3+8.5: Template cleanup and move complete"
  git tag phase-8.3-8.5-before-model-move
  ```

- [ ] **Baseline Smoke Tests** (28 flows)
  - Document all pre-existing failures
  - Create comparison baseline

---

### **Why Template Move Should Precede Model Move**

**Reason 1: Simpler Testing**
- Template changes: Can verify immediately in browser
- Model changes: Need to check database, migrations, FK relationships

**Reason 2: Lower Risk**
- Template move: Zero database impact
- Model move: High database impact, migrations required

**Reason 3: Clearer Separation**
- After templates move: Clear which templates belong to which app
- Before models move: Easier to see which models each app's templates use

**Reason 4: Incremental Progress**
- Template move: Builds confidence with visible progress
- Model move: Get harder tasks done while system is stable

---

### **Model Move Complexity** (Phase 8.4 - DEFERRED)

**Models to Move** (7 models):
1. CustomerProfile → accounts (8 files use it)
2. Service → spa_services (9 files use it)
3. Appointment → appointments (3 files use it)
4. Room → appointments (3 files use it)
5. Complaint → complaints (2 files use it)
6. ComplaintReply → complaints (2 files use it)
7. ComplaintHistory → complaints (1 file uses it)

**Cross-App FK Dependencies** (Must move in order):
```
Batch 1: CustomerProfile (accounts) - lowest FK risk
Batch 2: Service (spa_services) - only references User
Batch 3: Complaint ecosystem (complaints) - references CustomerProfile, Service
Batch 4: Appointment + Room (appointments) - references CustomerProfile, Service
```

**Estimated Time**: 2-3 hours
**Risk Level**: HIGH
**Rollback**: Git revert + database restore from backup

---

## SUMMARY

### **Phase 8.3 Status**: ✅ COMPLETED

**What Was Done**:
- ✅ Fixed last namespace remnant (`spa:index` → `pages:home`)
- ✅ Audited all 24 templates (15 spa + 9 admin)
- ✅ Created detailed move plan (4 batches, low → high complexity)
- ✅ Verified system stability (Django check, HTTP tests)

**What Was NOT Done** (Intentional):
- ❌ Did NOT move templates (deferring to Phase 8.5)
- ❌ Did NOT move models (deferring to Phase 8.4)
- ❌ Did NOT create new base templates (defer decision)

---

### **Recommended Next Steps**

```
Phase 8.3 ✅ [DONE] Template Cleanup Prep
    ↓
Phase 8.5 ⏳ [NEXT] Move Templates (16 templates to app folders)
    ├─ Batch 1: spa_services, appointments, complaints (8 templates)
    ├─ Batch 2: pages, accounts (8 templates)
    └─ Test: All 28 smoke test flows
    ↓
Phase 8.4 ⏳ [THEN] Move Models (7 models, 5 batches, HIGH RISK)
    ├─ PREREQUISITE: Database backup
    ├─ PREREQUISITE: Git commit + tag
    ├─ Batch 1: CustomerProfile → accounts
    ├─ Batch 2: Service → spa_services
    ├─ Batch 3: Complaint ecosystem → complaints
    └─ Batch 4: Appointment + Room → appointments
    ↓
Phase 8.6 ⏳ Extract remaining views/forms
Phase 8.7 ⏳ Finalize admin_panel + Delete spa
```

---

### **Risk Assessment**

**Phase 8.3 (Template Cleanup)**: ✅ LOW (Completed)
**Phase 8.5 (Template Move)**: ⚠️ LOW-MEDIUM (Recommended next)
**Phase 8.4 (Model Move)**: ❌ HIGH (Defer until after templates)

---

**Generated**: 2026-03-30
**Author**: Spa ANA Team
**Phase**: 8.3 - TEMPLATE CLEANUP PREP
**Status**: ✅ COMPLETED
**Next Phase**: 8.5 (Template Move) - RECOMMENDED before 8.4 (Model Move)
