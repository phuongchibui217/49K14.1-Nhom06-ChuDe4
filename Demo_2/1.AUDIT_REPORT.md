# 📊 SPA MANAGEMENT SYSTEM - AUDIT REPORT
**Date:** 2026-02-03  
**Auditor:** Senior Business Analyst + Full-stack Engineer  
**Project:** Spa ANA Management Website

---

## 🚨 CRITICAL ISSUES FOUND

### Issue #1: BOOKING MODULE - VIOLATES CORE PRINCIPLE

**Severity:** 🔴 CRITICAL  
**Module:** booking.html  
**Location:** Booking Form - Customer Information Section

---

### ❌ CURRENT LOGIC (WRONG)

```javascript
// booking.html - Current Implementation
const fullName = document.getElementById("fullName").value.trim();
const phone = document.getElementById("phone").value.trim();

// ALWAYS asks for customer info, regardless of login status
// All fields required for EVERYONE
// No session check
// No distinction between logged-in vs guest users
```

**Problems:**
1. ❌ Asks logged-in customers to re-enter Họ tên, SĐT
2. ❌ No check for user session on page load
3. ❌ Creates duplicate customer data when logged-in users book
4. ❌ Booking not properly linked to customer_id for registered users
5. ❌ Poor UX - redundant data entry for returning customers

---

### ✅ CORRECT LOGIC (REAL-WORLD SPA)

```javascript
// Correct Implementation Required
const isLoggedIn = localStorage.getItem('currentUser') !== null;

if (isLoggedIn) {
    // LOGGED-IN CUSTOMER FLOW
    currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // HIDE customer info fields
    document.getElementById('customerInfoSection').style.display = 'none';
    
    // SHOW read-only customer info display
    document.getElementById('customerDisplay').innerHTML = `
        <div class="customer-info-display">
            <div class="info-item">
                <span class="label">Xin chào:</span>
                <span class="value">${currentUser.name}</span>
            </div>
            <div class="info-item">
                <span class="label">Số điện thoại:</span>
                <span class="value">${currentUser.phone}</span>
            </div>
            <div class="info-item">
                <span class="label">Email:</span>
                <span class="value">${currentUser.email || 'Chưa cập nhật'}</span>
            </div>
            <div class="edit-profile-link">
                <a href="profile.html" class="text-warning">
                    <i class="fas fa-edit me-2"></i>Cập nhật thông tin
                </a>
            </div>
        </div>
    `;
    
    // Submit booking with customer_id
    bookingData.customer_id = currentUser.id;
    
} else {
    // GUEST USER FLOW
    // SHOW customer info fields
    document.getElementById('customerInfoSection').style.display = 'block';
    
    // Require: fullName, phone
    // Create guest customer on backend
    bookingData.customer_info = { fullName, phone };
}
```

**Correct Flow:**

**Logged-in Customer:**
- ✅ Auto-recognizes user from session
- ✅ Shows: "Xin chào [Tên khách hàng]"
- ✅ Displays customer info as read-only
- ✅ Links to profile page to edit info
- ✅ Only asks for: Service, Date, Time, Notes
- ✅ Booking automatically linked to customer_id
- ✅ No redundant data entry

**Guest User:**
- ✅ Shows customer info input fields
- ✅ Requires: Họ tên, Số điện thoại
- ✅ Creates guest customer record on backend
- ✅ Links booking to created customer_id

---

### 🔧 REQUIRED CHANGES

#### 1. UI Changes (booking.html)

**Add Session-Aware Layout:**

```html
<!-- BEFORE CURRENT FORM -->
<div class="row g-4">
    
    <!-- Customer Info Section - ONLY FOR GUESTS -->
    <div id="guestCustomerInfo" style="display: none;">
        <h6 class="section-title">
            <i class="fas fa-user"></i>Thông tin khách hàng
        </h6>
        
        <div class="mb-4">
            <label for="fullName" class="form-label">
                Họ tên <span class="required-mark">*</span>
            </label>
            <input type="text" class="form-control" id="fullName" required />
            <div class="field-error" id="fullNameError"></div>
        </div>
        
        <div class="mb-4">
            <label for="phone" class="form-label">
                Số điện thoại <span class="required-mark">*</span>
            </label>
            <input type="tel" class="form-control" id="phone" required />
            <div class="field-error" id="phoneError"></div>
        </div>
    </div>
    
    <!-- Logged-in Customer Info Display -->
    <div id="loggedInCustomerInfo" style="display: none;">
        <div class="customer-info-display card bg-light p-4 mb-4">
            <div class="text-center mb-3">
                <div class="avatar-circle mb-2">
                    <i class="fas fa-user fa-2x text-warning"></i>
                </div>
                <h5 class="mb-1" id="displayCustomerName"></h5>
                <p class="text-muted small mb-3">Khách hàng thân thiết</p>
            </div>
            
            <div class="info-row">
                <i class="fas fa-phone text-warning me-2"></i>
                <span id="displayCustomerPhone"></span>
            </div>
            <div class="info-row">
                <i class="fas fa-envelope text-warning me-2"></i>
                <span id="displayCustomerEmail"></span>
            </div>
            
            <div class="mt-3 pt-3 border-top">
                <a href="profile.html" class="btn btn-outline-warning btn-sm w-100">
                    <i class="fas fa-edit me-2"></i>Cập nhật thông tin
                </a>
            </div>
        </div>
    </div>
    
    <!-- Rest of booking form (Date, Time, Service, Notes) -->
    <!-- ... -->
</div>
```

#### 2. Frontend Logic Changes

**Add Session Check on Page Load:**

```javascript
// booking.html - JavaScript
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
});

function checkLoginStatus() {
    const currentUser = localStorage.getItem('currentUser');
    
    if (currentUser) {
        // LOGGED-IN FLOW
        const user = JSON.parse(currentUser);
        
        // Hide guest form, show logged-in display
        document.getElementById('guestCustomerInfo').style.display = 'none';
        document.getElementById('loggedInCustomerInfo').style.display = 'block';
        
        // Populate customer info
        document.getElementById('displayCustomerName').textContent = user.name;
        document.getElementById('displayCustomerPhone').textContent = user.phone;
        document.getElementById('displayCustomerEmail').textContent = user.email || 'Chưa cập nhật';
        
        // Update header to show logged-in state
        updateHeaderForLoggedInUser(user);
        
        return true;
    } else {
        // GUEST FLOW
        document.getElementById('guestCustomerInfo').style.display = 'block';
        document.getElementById('loggedInCustomerInfo').style.display = 'none';
        
        // Update header to show guest state
        updateHeaderForGuest();
        
        return false;
    }
}

function updateHeaderForLoggedInUser(user) {
    // Update user dropdown in header
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        userDropdown.innerHTML = `
            <button class="btn btn-warning dropdown-toggle" data-bs-toggle="dropdown">
                <i class="fas fa-user me-2"></i>${user.name}
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="profile.html"><i class="fas fa-user-circle me-2"></i>Tài khoản</a></li>
                <li><a class="dropdown-item" href="my-appointments.html"><i class="fas fa-calendar-check me-2"></i>Lịch của tôi</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-danger" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Đăng xuất</a></li>
            </ul>
        `;
    }
}

function updateHeaderForGuest() {
    // Show login/register buttons
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        userDropdown.innerHTML = `
            <button class="btn btn-outline-warning dropdown-toggle" data-bs-toggle="dropdown">
                <i class="fas fa-user"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="login.html"><i class="fas fa-sign-in-alt me-2"></i>Đăng nhập</a></li>
                <li><a class="dropdown-item" href="register.html"><i class="fas fa-user-plus me-2"></i>Đăng ký</a></li>
            </ul>
        `;
    }
}
```

**Modify Form Submission Logic:**

```javascript
function simulateBooking(bookingData) {
    const isLoggedIn = localStorage.getItem('currentUser') !== null;
    
    showAlert("Đang xử lý đặt lịch...", "info");
    
    setTimeout(() => {
        if (isLoggedIn) {
            // LOGGED-IN: Include customer_id
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            bookingData.customer_id = currentUser.id;
            bookingData.customer_name = currentUser.name;
            bookingData.customer_phone = currentUser.phone;
        } else {
            // GUEST: Include customer info
            bookingData.customer_id = null;
            bookingData.customer_name = bookingData.fullName;
            bookingData.customer_phone = bookingData.phone;
        }
        
        // API call (simulated)
        console.log("Booking data:", bookingData);
        
        showAlert(
            "Đặt lịch thành công! Chúng tôi sẽ liên hệ với bạn để xác nhận.",
            "success"
        );
        
        // Reset form
        resetBookingForm();
    }, 1500);
}
```

#### 3. Backend Data Flow Changes

**API Endpoint Structure:**

```
POST /api/bookings

Request Body for LOGGED-IN User:
{
    "customer_id": "CUST123",           // From session
    "service_id": "2",
    "date": "2026-02-15",
    "time": "10:00",
    "notes": "Request..."
}

Request Body for GUEST User:
{
    "customer_info": {                     // Create new customer
        "full_name": "Nguyễn Văn A",
        "phone": "0901234567"
    },
    "service_id": "2",
    "date": "2026-02-15",
    "time": "10:00",
    "notes": "Request..."
}

Response:
{
    "success": true,
    "booking_id": "BOOK001",
    "customer_id": "CUST123",           // Same for logged-in, new for guest
    "message": "Đặt lịch thành công"
}
```

---

### Issue #2: MY-APPOINTMENTS PAGE - NO SESSION INTEGRATION

**Severity:** 🟠 HIGH  
**Module:** my-appointments.html  
**Location:** Page initialization and data loading

---

### ❌ CURRENT LOGIC (WRONG)

```html
<!-- my-appointments.html -->
<!-- Hardcoded mock data -->
<div class="appointment-item" data-status="confirmed">
    <!-- Static HTML, no dynamic loading -->
</div>
```

**Problems:**
1. ❌ No session check on page load
2. ❌ Shows same data for everyone (mock data)
3. ❌ No filtering by logged-in user
4. ❌ Header shows "Đăng nhập/Đăng ký" instead of user name
5. ❌ No actual data fetching based on customer_id

---

### ✅ CORRECT LOGIC (REAL-WORLD SPA)

```javascript
// my-appointments.html - Correct Implementation

document.addEventListener('DOMContentLoaded', async function() {
    const isLoggedIn = await checkLoginStatus();
    
    if (!isLoggedIn) {
        // Redirect to login if trying to access appointments
        window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
        return;
    }
    
    // Load user's appointments
    await loadUserAppointments();
});

async function loadUserAppointments() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    try {
        // API call to get user's appointments
        const response = await fetch(`/api/customers/${currentUser.id}/appointments`);
        const appointments = await response.json();
        
        renderAppointments(appointments);
    } catch (error) {
        console.error('Error loading appointments:', error);
        showEmptyState('Không thể tải lịch hẹn');
    }
}
```

---

### 🔧 REQUIRED CHANGES

#### 1. Add Session Check

```javascript
// my-appointments.html
document.addEventListener('DOMContentLoaded', async function() {
    await initializePage();
});

async function initializePage() {
    const currentUser = localStorage.getItem('currentUser');
    
    if (!currentUser) {
        // Redirect to login
        window.location.href = 'login.html?redirect=my-appointments';
        return;
    }
    
    // Update header
    updateHeaderForLoggedInUser(JSON.parse(currentUser));
    
    // Load appointments
    await loadUserAppointments();
    
    // Load consultations
    await loadUserConsultations();
}
```

#### 2. Dynamic Data Loading

```javascript
async function loadUserAppointments() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const container = document.getElementById('appointmentsList');
    
    try {
        // Show loading
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-warning" role="status">
                    <span class="visually-hidden">Đang tải...</span>
                </div>
            </div>
        `;
        
        // API call
        const response = await fetch(`/api/customers/${currentUser.id}/appointments`);
        const data = await response.json();
        
        if (data.appointments.length === 0) {
            showEmptyState('Bạn chưa có lịch hẹn nào', 'calendar');
            return;
        }
        
        // Render appointments
        container.innerHTML = data.appointments.map(apt => `
            <div class="appointment-item" data-status="${apt.status}">
                ${renderAppointmentCard(apt)}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error:', error);
        showEmptyState('Không thể tải lịch hẹn', 'exclamation-triangle');
    }
}
```

#### 3. Header State Management

Create a reusable header update function that can be called from any page:

```javascript
// js/main.js - Add this function

window.updateHeaderUserState = function() {
    const currentUser = localStorage.getItem('currentUser');
    const userDropdown = document.querySelector('.user-dropdown-menu');
    
    if (!userDropdown) return;
    
    if (currentUser) {
        const user = JSON.parse(currentUser);
        userDropdown.innerHTML = `
            <li><a class="dropdown-item" href="profile.html"><i class="fas fa-user-circle me-2"></i>Tài khoản: ${user.name}</a></li>
            <li><a class="dropdown-item" href="my-appointments.html"><i class="fas fa-calendar-check me-2"></i>Lịch của tôi</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-danger" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Đăng xuất</a></li>
        `;
    } else {
        userDropdown.innerHTML = `
            <li><a class="dropdown-item" href="login.html"><i class="fas fa-sign-in-alt me-2"></i>Đăng nhập</a></li>
            <li><a class="dropdown-item" href="register.html"><i class="fas fa-user-plus me-2"></i>Đăng ký</a></li>
        `;
    }
};

// Logout function
window.logout = function() {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
};

// Call on every page load
document.addEventListener('DOMContentLoaded', function() {
    window.updateHeaderUserState();
});
```

---

## 📋 SUMMARY OF REQUIRED REFACTORING

### Priority 1: CRITICAL (Must Fix Immediately)

1. ✅ **booking.html** - Add session-aware form
   - Detect logged-in vs guest
   - Show appropriate UI
   - Link booking to customer_id
   - Update header state

2. ✅ **my-appointments.html** - Add session check
   - Redirect if not logged in
   - Load user's actual appointments
   - Update header state
   - Dynamic rendering

3. ✅ **Global header** - Session state management
   - Create reusable header update function
   - Apply to all pages
   - Handle login/logout state transitions

### Priority 2: HIGH (Should Fix Soon)

4. ✅ **profile.html (customer)** - Create customer profile page
   - Currently only admin profile exists
   - Customers need to view/edit their own info
   - Link from booking page

5. ✅ **login.html/register.html** - Session management
   - Store user data in localStorage on login
   - Handle redirect after login
   - Session persistence

### Priority 3: MEDIUM (Nice to Have)

6. ✅ **Chat widget** - Session integration
   - Logged-in users: chat linked to customer_id
   - Guest users: session-based chat
   - No re-entry of customer info

---

## 🎯 REALITY CHECK

### Would a real spa do this?

| Scenario | Current System | Real Spa |
|-----------|---------------|-----------|
| Logged-in customer books | ❌ Asks for name/phone again | ✅ Auto-recognizes customer |
| Guest visits appointments page | ❌ Shows mock data | ✅ Redirects to login |
| After booking | ❌ No confirmation of who booked | ✅ Shows "Xin chào [Tên]" |
| Multiple bookings by same user | ❌ Creates duplicate customers | ✅ Links to existing customer |

**Answer: NO** ❌ Current system does NOT match real spa operations.

---

## 🚀 NEXT STEPS

1. **Immediate:**
   - Refactor booking.html with session-aware logic
   - Refactor my-appointments.html with session check
   - Create global header state management

2. **Short-term:**
   - Create customer profile page
   - Implement proper session management
   - Test both logged-in and guest flows

3. **Medium-term:**
   - Integrate chat with session
   - Add real API endpoints
   - Test full user journey

---

## 📊 IMPACT ASSESSMENT

**User Experience Impact:** ⭐⭐⭐⭐⭐ (Critical improvement)  
**Business Impact:** ⭐⭐⭐⭐⭐ (Prevents data duplication)  
**Technical Debt:** ⭐⭐⭐⭐⭐ (Fixes fundamental logic error)  
**Development Effort:** ⭐⭐⭐ (Moderate refactoring required)

---

## ✅ RECOMMENDATION

**START IMMEDIATELY WITH:**
1. Booking page refactoring
2. My-appointments page refactoring  
3. Global header state management

These 3 changes will resolve the core principle violation and dramatically improve UX.

**PROCEED IN THIS ORDER:**
1. Booking → Chat → Profile (as suggested)
2. Test logged-in flow end-to-end
3. Test guest flow end-to-end
4. Create logic flow diagram for defense

---

*End of Audit Report*