# Admin Appointments JS - Reorganized Version

> **File**: [admin-appointments-organized.js](./admin-appointments-organized.js)
> **Mô tả**: Quản lý lịch hẹn theo phòng và xử lý yêu cầu đặt lịch trực tuyến

---

## 📋 Mục lục

1. [Cải thiện cấu trúc](#-cải thiện-cấu-trúc)
2. [Chi tiết các Section](#-chi-tiết-các-section)
3. [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)

---

## ✨ Cải thiện cấu trúc

File đã được reorganize từ 2556 dòng lộn xộn thành **15 sections rõ ràng**:

### 📊 Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Dòng code** | 2556 | 2654 (+98 headers) |
| **Sections** | 0 | 15 |
| **Functions** | 67 | 67 (không đổi) |
| **Logic thay đổi** | - | ❌ None |
| **Dễ theo dõi** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🗂️ Chi tiết các Section

### **SECTION 1: SETTINGS & CONSTANTS**
**📍 Dòng**: 1-25
**🎯 Chức năng**: Cấu hình hệ thống và constants

```javascript
const START_HOUR = 9;  // Giờ mở cửa (9:00 sáng)
const END_HOUR = 21;   // Giờ đóng cửa (21:00 tối)
const API_BASE = '/api'; // Base URL cho API calls
```

**Công dụng**:
- ✅ Định nghĩa giờ hoạt động của spa
- ✅ Cấu hình thời gian slot (30 phút/slot)
- ✅ Helper functions cho format text
- ✅ Dùng chung cho toàn bộ ứng dụng

**Functions**:
- `variantLabel(v)` - Format label cho gói dịch vụ (tránh lặp "90 phút — 90 phút")
- `_truncate(str, maxLen)` - Cắt ngắn string nếu quá dài

---

### **SECTION 2: STATE VARIABLES**
**📍 Dòng**: 26-52
**🎯 Chức năng**: Quản lý trạng thái toàn cục

```javascript
let pendingBlocks = [];  // Danh sách slot đang chờ tạo
let ROOMS = [];          // Danh sách phòng
let SERVICES = [];       // Danh sách dịch vụ
let APPOINTMENTS = [];   // Danh sách lịch hẹn
```

**Công dụng**:
- ✅ Lưu trữ data load từ API
- ✅ Track trạng thái đang submit
- ✅ Lưu mode đang "quay về grid chọn slot"
- ✅ Manage guest cards trong modal

**Key Variables**:
- `isSubmitting` - Tránh submit lặp
- `_addingSlotMode` - State khi quay về grid chọn thêm slot
- `_savedBookerInfo` - Lưu tạm booker info
- `_guestCount` - Số lượng guest cards
- `_pendingBlockMap` - Map pending block ID → guest index

---

### **SECTION 3: API HELPERS**
**📍 Dòng**: 53-188
**🎯 Chức năng**: Giao tiếp với Backend API

**Công dụng**:
- ✅ Wrapper cho HTTP requests (GET/POST)
- ✅ Xử lý errors chung
- ✅ CSRF token management
- ✅ Load data từ database

**Functions**:
- `getCSRFToken()` - Lấy CSRF token từ cookies
- `apiGet(url)` - Wrapper cho GET requests với error handling
- `apiPost(url, payload)` - Wrapper cho POST requests với CSRF
- `loadRooms()` - Load danh sách phòng từ API
- `loadServices()` - Load danh sách dịch vụ
- `loadAppointments(date)` - Load appointments theo ngày
- `loadBookingRequests(filters)` - Load booking requests với filters

**Flow**:
```
UI → apiGet/apiPost → Django Backend → Database
                      ↓
                 Error Handling
                      ↓
                     Toast UI
```

---

### **SECTION 4: VALIDATION HELPERS**
**📍 Dòng**: 189-218
**🎯 Chức năng**: Validate input data

**Công dụng**:
- ✅ Validate form inputs trước khi submit
- ✅ Kiểm tra business rules
- ✅ Tránh invalid data gửi lên server

**Functions**:
- `isValidPhone(v)` - Validate SĐT Việt Nam (10 số)
- `isValidEmail(v)` - Validate email format
- `capacityOK({roomId, day, start, end, ignoreId})` - Kiểm tra phòng có đủ sức chứa không

**Use Cases**:
```javascript
// Trong form submission
if (!isValidPhone(phoneInput.value)) {
  showToast('error', 'Lỗi', 'SĐT không hợp lệ');
  return;
}

// Khi chọn slot
if (!capacityOK({roomId, day, start, end})) {
  showToast('error', 'Lỗi', 'Phòng đã đầy');
  return;
}
```

---

### **SECTION 5: TIME/DATE HELPERS**
**📍 Dòng**: 219-238
**🎯 Chức năng**: Xử lý thời gian và ngày tháng

**Công dụng**:
- ✅ Convert giữa các format thời gian
- ✅ Tính toán khoảng cách thời gian
- ✅ Check overlap appointments
- ✅ Render timeline UI

**Functions**:
- `pad2(n)` - Pad số thành 2 chữ số (5 → "05")
- `minutesFromStart(t)` - Tính phút từ giờ mở cửa (9:00)
- `addMinutesToTime(t, add)` - Cộng phút vào thời gian ("09:30" + 60 → "10:30")
- `overlaps(aStart, aEnd, bStart, bEnd)` - Kiểm tra 2 appointment có chồng nhau không
- `totalTimelineMinutes()` - Tổng phút timeline (12 giờ = 720 phút)
- `minutesToPercent(minutes)` - Chuyển phút sang % width

**Use Cases**:
```javascript
// Tính end time từ start time + duration
const endTime = addMinutesToTime("09:00", 60); // "10:00"

// Check overlap
if (overlaps(appt1Start, appt1End, appt2Start, appt2End)) {
  // Conflict!
}

// Render appointment block width
const width = minutesToPercent(60); // 60 phút = 8.33%
```

---

### **SECTION 6: UI HELPERS**
**📍 Dòng**: 239-382
**🎯 Chức năng**: UI utilities và notifications

**Công dụng**:
- ✅ Hiển thị notifications/toast
- ✅ Format status badges
- ✅ Button loading states
- ✅ Confirmation dialogs
- ✅ Update badges

**Functions**:
- `showToast(type, title, message)` - Hiển thị toast notification (success/error/info)
- `statusClass(s)` - CSS class cho status badge (PENDING/COMPLETED/CANCELLED)
- `statusLabel(s, cancelledBy)` - Label text cho status
- `setButtonLoading(btn, text)` - Set button trong trạng thái loading
- `resetButton(btn)` - Reset button về trạng thái bình thường
- `confirmAction(title, message)` - Hiển thị modal xác nhận
- `updateBookingBadges(rows)` - Update pending count badges
- `showGridLoading()` - Hiển thị skeleton loading

**Examples**:
```javascript
// Show success toast
showToast('success', 'Thành công', 'Đã lưu lịch hẹn');

// Show loading state
setButtonLoading(btnSave, 'Đang lưu...');

// Confirm before delete
const confirmed = await confirmAction('Xóa lịch?', 'Bạn có chắc không?');
if (!confirmed) return;
```

---

### **SECTION 7: PENDING BLOCKS STATE**
**📍 Dòng**: 383-518
**🎯 Chức năng**: Quản lý slot selection (flow 2 bước)

**Công dụng**:
- ✅ Handle click vào slot để chọn
- ✅ Render pending blocks (slot đang chọn)
- ✅ Sync action bar UI
- ✅ Clear pending blocks

**Flow**:
```
1. User click vào slot trống
   ↓
2. handleToggleSlot() → Tạo pending block
   ↓
3. renderPendingBlocks() → Hiển thị block trên grid
   ↓
4. User click "Tiếp tục" → openCreateModalFromPending()
   ↓
5. Modal mở với pre-filled data
```

**Functions**:
- `_nextPendingId()` - Generate ID cho pending block
- `handleToggleSlot()` - Main handler: click slot → tạo/hủy pending block
- `clearPendingBlocks()` - Xóa tất cả pending blocks
- `_syncActionBar()` - Update action bar (nút Hủy/Tiếp tục)
- `_mountPendingBlock()` - Render một pending block
- `renderPendingBlocks()` - Render tất cả pending blocks

**UI Components**:
- Pending blocks trên timeline (màu cam)
- Action bar (nút "Hủy chọn", "Tiếp tục")
- Badge count ("0 khách đã chọn")

---

### **SECTION 8: TAB 1 - LỊCH THEO PHÒNG (GRID)**
**📍 Dòng**: 519-644
**🎯 Chức năng**: Render và manage room calendar grid

**Công dụng**:
- ✅ Render timeline header (9:00 - 21:00)
- ✅ Render appointments theo phòng
- ✅ Allocate lanes để tránh chồng chéo
- ✅ Update current time line realtime
- ✅ Handle grid interactions

**Functions**:
- `renderHeader()` - Render header timeline với time slots
- `allocateRoomLanes(roomId, day, appts)` - Phân bổ appointments vào lanes
- `renderGrid()` - Main render function cho toàn bộ grid
- `updateCurrentTimeLine()` - Update đường kẻ thời gian thực
- `startCurrentTimeLineInterval()` - Bắt đầu interval update mỗi phút
- `_isSlotInPast(day, time)` - Kiểm tra slot có nằm trong quá khứ không

**Grid Structure**:
```
┌─────────────────────────────────────────────────────┐
│ Phòng │ 9:00 │ 9:30 │ 10:00 │ ... │ 21:00 │        │
├─────────────────────────────────────────────────────┤
│ P101  │ [Appt│      │ [Appt]│     │       │        │
├─────────────────────────────────────────────────────┤
│ P102  │      │ [Appt]│      │     │       │        │
└─────────────────────────────────────────────────────┘
         ↑ Current time line (cập nhật realtime)
```

---

### **SECTION 9: TAB 2 - YÊU CẦU ĐẶT LỊCH (WEB REQUESTS)**
**📍 Dòng**: 645-767
**🎯 Chức năng**: Manage booking requests từ website

**Công dụng**:
- ✅ Render danh sách booking requests
- ✅ Filter theo status, dịch vụ, ngày
- ✅ Approve/Reject/Rebook requests
- ✅ Update status badges

**Flow**:
```
PENDING → (approveWeb) → NOT_ARRIVED → (checkin) → COMPLETED
           ↓
         (rejectWeb) → REJECTED

PENDING → (customer cancel) → CANCELLED → (rebook) → New appointment
```

**Functions**:
- `renderWebRequests()` - Render table booking requests
- `window.approveWeb(id)` - Approve request → Open edit modal
- `window.rejectWeb(id)` - Reject request → Show confirm modal
- `window.rebookAppointment(id)` - Rebook cancelled/rejected
- `openRebookAsCreate()` - Open create modal với pre-filled data
- `fillServiceFilter()` - Đền dropdown filter dịch vụ

**Table Columns**:
- Mã | Khách | SĐT | Dịch vụ | Ngày | Giờ | Thời lượng | Trạng thái | Hành động

---

### **SECTION 10: CUSTOMER LOOKUP (STUB)**
**📍 Dòng**: 768-891
**🎯 Chức năng**: Customer search (chưa implement)

**Công dụng**:
- ⚠️ **STUB** - Chưa được implement
- 📝 Dành cho future feature: lookup customer theo SĐT/email
- 🔜 Sẽ auto-fill customer info nếu đã tồn tại

**Functions** (tất cả đều no-op):
- `initCustomerSearch()` - Initialize customer search
- `_lookupByPhone(phoneVal)` - Lookup customer theo SĐT
- `_lookupByEmail(emailVal)` - Lookup customer theo email
- `_showSuggestion(c, via)` - Show suggestion dropdown
- `_confirmMatch(c, via)` - User xác nhận match
- `_dismissMatch(c, via)` - User bỏ qua match
- `_unlinkCustomer(via)` - Unlink customer
- `_resetPhoneState()` - Reset phone input state
- `_resetEmailState()` - Reset email input state
- `_resetAllCustomerState()` - Reset all customer state

**Future Implementation**:
```
User nhập SĐT → _lookupByPhone() → API tìm customer
                                      ↓
                               _showSuggestion()
                                      ↓
                            User xác nhận ✓ hoặc bỏ qua ✕
```

---

### **SECTION 11: MODAL & FORM HELPERS**
**📍 Dòng**: 892-2208
**🎯 Chức năng**: Modal và form management 

**Công dụng**:
- ✅ Manage create/edit appointment modal
- ✅ Handle guest cards (accordion style)
- ✅ Validate form inputs
- ✅ Submit form với data preparation
- ✅ Xử lý "Apply to all" functionality

**Sub-sections**:

#### **A. Modal Management**
- `openCreateModal(prefill)` - Mở modal tạo mới
- `openEditModal(id)` - Mở modal sửa
- `openEditModalWithData(a)` - Mở modal với data sẵn có
- `openCreateModalFromPending()` - Mở modal từ pending blocks

#### **B. Guest Card Management**
- `_buildGuestItem(idx, prefill)` - Build guest card HTML
- `addGuestCard(prefill)` - Thêm guest card mới
- `window.removeGuestCard(idx)` - Xóa guest card
- `window.toggleGuestCard(idx)` - Toggle expand/collapse
- `window.focusGuestCard(idx)` - Scroll đến guest card
- `_renumberGuests()` - Renumber sau khi add/remove

#### **C. Form Validation**
- `_isGuestComplete(item)` - Check guest card đã đủ fields chưa
- `_markRowValidity(item)` - Highlight validity
- `_markRowError(item)` - Mark error state
- `_collectGuestCards()` - Collect data từ tất cả guest cards

#### **D. Service & Variant Handling**
- `_loadGuestVariants(item, serviceId)` - Load variants khi chọn service
- `_updateGuestEndTime(item)` - Update end time theo variant duration
- `window.onGuestServiceChange(idx)` - Handle service change

#### **E. Payment Handling**
- `_onGuestPayChange(item)` - Handle payment method change
- `_updateGuestPayFinal(item)` - Update final payment amount
- `_syncSharedPayFields(val)` - Sync shared payment fields
- `_showSharedStatusBlock()` - Show status/payment block

#### **F. "Apply to All" Feature**
- `_initApplyAllBar()` - Initialize "apply to all" bar
- Apply service/variant to all guests

**Form Structure**:
```
┌─────────────────────────────────────────┐
│ PANEL 1: Người đặt                      │
│ - Họ tên, SĐT, Email, Nguồn, Ghi chú   │
├─────────────────────────────────────────┤
│ Apply All Bar (chỉ CREATE mode)         │
│ - Apply service/variant to all guests   │
├─────────────────────────────────────────┤
│ GUEST CARDS (accordion style)           │
│ - Phòng, Ngày, Giờ                      │
│ - Tên khách, SĐT, Dịch vụ, Gói          │
│ - [Expand] [Delete] buttons             │
├─────────────────────────────────────────┤
│ Status & Payment Block (chỉ EDIT mode)  │
│ - Trạng thái, Thanh toán                │
└─────────────────────────────────────────┘
```

---

### **SECTION 12: DATE NAVIGATION**
**📍 Dòng**: 2209-2227
**🎯 Chức năng**: Điều hướng ngày tháng

**Công dụng**:
- ✅ Navigate giữa các ngày
- ✅ Jump to today
- ✅ Refresh data khi change date

**Functions**:
- `setDay(d)` - Set ngày cho date picker
- `todayISO()` - Return today's date in ISO format (YYYY-MM-DD)
- `shiftDay(delta)` - Shift ngày (+1 hoặc -1)
- `refreshData()` - Refresh appointments khi change date

**UI Components**:
- Nút "Hôm nay"
- Nút "Ngày trước" (←)
- Nút "Ngày sau" (→)
- Date picker input

---

### **SECTION 13: SEARCH MODAL**
**📍 Dòng**: 2228-2460
**🎯 Chức năng**: Tìm kiếm lịch hẹn

**Công dụng**:
- ✅ Search appointments theo nhiều criteria
- ✅ Filter theo tên, SĐT, email, dịch vụ, status, nguồn
- ✅ Navigate từ search results đến appointment

**Functions**:
- `initSearchModal()` - Initialize search modal
- `_resetSearchModalState()` - Reset form fields
- `_fillSearchDropdowns()` - Fill dropdown options
- `_setSearchWarning(show, text)` - Show/hide warning
- `_doSearch()` - Execute search với filters
- `_srchStatusBadgeClass(s)` - CSS class cho status badge
- `window._srchGoToAppt(apptId, apptDate)` - Jump to appointment

**Search Criteria**:
- Tên khách / người đặt
- Số điện thoại
- Email
- Dịch vụ / gói
- Trạng thái
- Nguồn (Trực tiếp/Online/Điện thoại/Facebook/Zalo)
- Từ ngày / Đến ngày

**Flow**:
```
User nhập criteria → Bấm "Tìm kiếm"
                       ↓
                    _doSearch()
                       ↓
                  API call
                       ↓
               Render results
                       ↓
    Click result → _srchGoToAppt() → Jump to appointment
```

---

### **SECTION 14: CUSTOMER CANCEL POLLING**
**📍 Dòng**: 2461-2539
**🎯 Chức năng**: Real-time cancellation detection

**Công dụng**:
- ✅ Poll mỗi 30s để detect customer cancellations
- ✅ Hiển thị notification nếu customer tự hủy
- ✅ Update UI realtime

**Functions**:
- `_pollCancelledByCustomer()` - Main polling function

**Flow**:
```
Every 30s → Check database for cancelled appointments
              ↓
         If customer cancelled → Show notification
                                   ↓
                            Update UI
```

---

### **SECTION 15: INITIALIZATION**
**📍 Dòng**: 2540-2654
**🎯 Chức năng**: Khởi tạo ứng dụng

**Công dụng**:
- ✅ Initialize modals (Bootstrap)
- ✅ Load initial data (rooms, services, appointments, web requests)
- ✅ Setup event listeners
- ✅ Start intervals (current time line, polling)
- ✅ Render initial UI

**Initialization Flow**:
```javascript
DOMContentLoaded
    ↓
1. Initialize modals (appointment, toast, delete)
    ↓
2. Render header timeline NGAY LAP TUC (skeleton loading)
    ↓
3. Fetch song song: rooms + services
    ↓
4. Fetch song song: appointments + web requests
    ↓
5. Start current time line interval
    ↓
6. Setup event listeners:
   - Date navigation (Today, Prev, Next)
   - Day picker change
   - Window resize
   - Pending action bar
    ↓
7. Setup FilterManager cho tab Yêu cầu đặt lịch
    ↓
8. Initialize search modal
    ↓
9. Start polling (pending count, customer cancel)
```

**Event Listeners Attached**:
- `btnToday` → `setDay(todayISO())`
- `btnPrev` → `shiftDay(-1)`
- `btnNext` → `shiftDay(1)`
- `dayPicker` → `refreshData()`
- Window resize → `updateCurrentTimeLine()`
- `btnCancelPending` → `clearPendingBlocks()`
- `btnContinuePending` → `openCreateModalFromPending()`
- Modal hide → `clearPendingBlocks()`

---

## 🚀 Hướng dẫn sử dụng

### **Quick Navigation**

Muốn tìm gì? Search trong file organized:

| Tìm | Ctrl+F | Section |
|-----|--------|---------|
| **Cấu hình hệ thống** | `SECTION 1` | Settings & Constants |
| **API calls** | `SECTION 3` | API Helpers |
| **Validate input** | `SECTION 4` | Validation Helpers |
| **Xử lý thời gian** | `SECTION 5` | Time/Date Helpers |
| **Notifications** | `SECTION 6` | UI Helpers |
| **Slot selection** | `SECTION 7` | Pending Blocks |
| **Tab Lịch phòng** | `SECTION 8` | Grid Functions |
| **Tab Yêu cầu** | `SECTION 9` | Web Requests |
| **Modal logic** | `SECTION 11` | Modal & Form |
| **Search** | `SECTION 13` | Search Modal |
| **Initialization** | `SECTION 15` | DOMContentLoaded |

---

### **Debugging Tips**

#### **Common Issues**

**1. Slot không click được**
```javascript
// Check console log
console.log('Slot clicked', { roomId, day, time });

// Check handleToggleSlot() ở SECTION 7
// Check event delegation ở grid
```

**2. Pending blocks không clear**
```javascript
// Gọi manual
clearPendingBlocks();

// Check action bar buttons
console.log(pendingBlocks.length);
```

**3. Timeline không update**
```javascript
// Force update
updateCurrentTimeLine();

// Check interval
console.log('Interval active:', !!currentTimeInterval);
```

**4. Form không submit**
```javascript
// Check validation
const items = _getGuestItems();
items.forEach((item, idx) => {
  console.log(`Guest ${idx}:`, _isGuestComplete(item));
});
```

#### **Console Commands**

```javascript
// Xem data hiện tại
console.log('Rooms:', ROOMS);
console.log('Services:', SERVICES);
console.log('Appointments:', APPOINTMENTS);
console.log('Pending blocks:', pendingBlocks);

// Force refresh
await refreshData();
await renderWebRequests();

// Xem guest cards
console.log('Guests:', _getGuestItems());

// Test validation
console.log('Valid phone:', isValidPhone('0123456789'));
console.log('Valid email:', isValidEmail('test@example.com'));
```

---

### **Development Workflow**

#### **1. Thêm feature mới vào Tab Lịch phòng**
1. Add function vào **SECTION 8**
2. Update initialization ở **SECTION 15** nếu cần
3. Test với grid interactions

#### **2. Thêm field vào form**
1. Update `_buildGuestItem()` ở **SECTION 11**
2. Update `_isGuestComplete()` để validate
3. Update `_collectGuestCards()` để collect data
4. Update API payload

#### **3. Thêm filter vào tab Yêu cầu**
1. Add filter input vào HTML
2. Update `renderWebRequests()` ở **SECTION 9**
3. Update FilterManager ở **SECTION 15**

#### **4. Modify API calls**
1. Update function ở **SECTION 3**
2. Update error handling nếu cần
3. Test với UI

---

### **Best Practices**

1. **✅ Luôn validate trước khi gọi API**
   ```javascript
   if (!isValidPhone(phone)) return;
   if (!capacityOK(params)) return;
   ```

2. **✅ Sử dụng helper functions thay vì lặp code**
   ```javascript
   // Good
   showToast('success', 'Thành công', 'Đã lưu');

   // Bad
   // ... 20 lines of toast code
   ```

3. **✅ Clear state sau khi dùng xong**
   ```javascript
   pendingBlocks = [];  // Clear after modal close
   ```

4. **✅ Handle errors gracefully**
   ```javascript
   try {
     const result = await apiPost(url, data);
   } catch (error) {
     showToast('error', 'Lỗi', error.message);
     return;
   }
   ```

5. **✅ Update UI sau khi data change**
   ```javascript
   await refreshData();
   updateCurrentTimeLine();
   ```

---

## ✅ Checklist before deploying

- [ ] Test tất cả features trong tab "Lịch theo phòng"
- [ ] Test tất cả features trong tab "Yêu cầu đặt lịch"
- [ ] Test modal tạo/sửa appointment
- [ ] Test search functionality
- [ ] Test real-time polling
- [ ] Check console không có errors
- [ ] Test trên các browsers khác nhau
- [ ] Test responsive (mobile/tablet)
- [ ] Test edge cases (invalid data, network errors)

---

**Last updated**: 2026-04-30
**Version**: v2.0 (Reorganized)
**File**: admin-appointments-organized.js (2654 lines)
