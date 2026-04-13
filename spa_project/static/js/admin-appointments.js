/**
 * =============================================
 * QUẢN LÝ LỊCH HẸN - ADMIN SCHEDULER
 * =============================================
 * File này quản lý toàn bộ chức năng lịch hẹn ở trang admin:
 * - Hiển thị lưới lịch (timeline scheduler)
 * - Tạo / Sửa / Xóa lịch hẹn
 * - Quản lý yêu cầu đặt lịch từ web
 * - Auto-update real-time (SSE)
 */
/**
// ============================================================
admin-appointments.js (950 dòng)
├──  PHẦN 1: CẤU HÌNH (đơn giản rồi)
├──  PHẦN 2: BIẾN TOÀN CỤC (đơn giản rồi)
├──  PHẦN 3: DOM ELEMENTS (đơn giản rồi)
├──  PHẦN 4: HELPER FUNCTIONS (ĐÃ LÀM xong!)
├──  PHẦN 5: API CALLS (2 hàm apiGet, apiPost)
├──  PHẦN 6: DATA LOADING (4 hàm load...)
├──  PHẦN 7: UI HELPERS (2 hàm)
├──  PHẦN 8: RENDER SCHEDULER GRID (3 hàm phức tạp)
├──  PHẦN 9: RENDER BOOKING REQUESTS TABLE (2 hàm + window functions)
├──  PHẦN 10: MODAL & FORM HANDLERS (3 hàm + event listeners)
├──  PHẦN 11: DATE NAVIGATION (4 hàm)
├──  PHẦN 12: SEARCH & FILTER (đơn giản rồi)
└──  PHẦN 13: INITIALIZATION (DOMContentLoaded - logic phức tạp)
// ============================================================
**/
// ============================================================
// PHẦN 1: CẤU HÌNH - SETTINGS & CONSTANTS
// ============================================================

/** Thời gian làm việc */
const START_HOUR = 9;  // Giờ mở cửa: 9:00 sáng
const END_HOUR = 21;   // Giờ đóng cửa: 21:00 tối
const SLOT_MIN = 30;   // 1 ô lịch = 30 phút

/** API Base URL - Đường dẫn để gọi Backend */
const API_BASE = '/api';

// ============================================================
// PHẦN 2: BIẾN TOÀN CỤC - GLOBAL VARIABLES
// ============================================================

/**
 * Dữ liệu load từ Backend
 * - ROOMS: Danh sách phòng
 * - SERVICES: Danh sách dịch vụ
 * - APPOINTMENTS: Danh sách lịch hẹn
 */
let ROOMS = [];
let SERVICES = [];
let APPOINTMENTS = [];

/**
 * Trạng thái form - Ngăn submit lặp
 * - isSubmitting: true nếu đang submit form
 */
let isSubmitting = false;

// ============================================================
// PHẦN 3: DOM ELEMENTS - THAM CHIẾU CÁC PHẦN TỬ HTML
// ============================================================

/** Sidebar & Navigation */
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");

/** Scheduler Grid - Lưới lịch hẹn */
const timeHeader = document.getElementById("timeHeader");
const grid = document.getElementById("grid");

/** Date Navigation - Điểu khiển ngày */
const dayPicker = document.getElementById("dayPicker");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnToday = document.getElementById("btnToday");

/** Search - Tìm kiếm */
const searchInput = document.getElementById("searchInput");

/** Booking Requests Table - Bảng yêu cầu đặt lịch */
const webTbody = document.getElementById("webTbody");
const webCount = document.getElementById("webCount");
const webStatusFilter = document.getElementById("webStatusFilter");

/** Modal - Form tạo/sửa lịch */
const modalEl = document.getElementById("apptModal");
let modal = null;
const modalTitle = document.getElementById("modalTitle");
const modalError = document.getElementById("modalError");

/** Form Fields - Các trường trong form */
const form = document.getElementById("apptForm");
const btnSave = document.getElementById("btnSave");
const btnDelete = document.getElementById("btnDelete");

/** Form Inputs */
const apptId = document.getElementById("apptId");
const customerName = document.getElementById("customerName");
const phone = document.getElementById("phone");
const email = document.getElementById("email");
const service = document.getElementById("service");
const room = document.getElementById("room");
const guests = document.getElementById("guests");
const date = document.getElementById("date");
const time = document.getElementById("time");
const duration = document.getElementById("duration");
const apptStatus = document.getElementById("apptStatus");
const payStatus = document.getElementById("payStatus");
const note = document.getElementById("note");

/** Toast Notification - Thông báo */
const toastEl = document.getElementById("toast");
let toast = null;
const toastTitle = document.getElementById("toastTitle");
const toastBody = document.getElementById("toastBody");

// ============================================================
// PHẦN 4: HELPER FUNCTIONS - CÁC HÀM HỖ TRỢ
// ============================================================
// Phần này chứa các hàm nhỏ, dùng chung cho nhiều chỗ
// Mỗi hàm làm 1 việc đơn giản, dễ hiểu

// ------------------------------------------------------------
// HÀM 1: Lấy CSRF Token
// ------------------------------------------------------------
// Mục đích: Lấy mã bảo mật từ cookie để gửi kèm request
// Cần thiết: Django yêu cầu CSRF token cho mọi request POST/PUT/DELETE
//
// Ví dụ cookie: "csrftoken=abc123xyz; session=xyz789"
// Kết quả: "abc123xyz"
function getCSRFToken() {
  // Bước 1: Tách cookie thành mảng theo dấu "; "
  var cookies = document.cookie.split('; ');

  // Bước 2: Tìm cookie có tên bắt đầu bằng "csrftoken="
  var csrfCookie = cookies.find(function(row) {
    return row.startsWith('csrftoken=');
  });

  // Bước 3: Nếu tìm thấy, tách lấy giá trị sau dấu "="
  if (csrfCookie) {
    return csrfCookie.split('=')[1];
  }

  // Nếu không tìm thấy, trả về chuỗi rỗng
  return '';
}

// ------------------------------------------------------------
// HÀM 2: Định dạng số thành 2 chữ số
// ------------------------------------------------------------
// Mục đích: Thêm số 0 phía trước nếu số chỉ có 1 chữ số
//
// Ví dụ:
//   pad2(9)   → "09"
//   pad2(5)   → "05"
//   pad2(12)  → "12" (không đổi)
function pad2(n) {
  // Chuyển số thành chuỗi
  var str = String(n);

  // Nếu chuỗi chưa đủ 2 ký tự, thêm số 0 vào đầu
  if (str.length < 2) {
    str = '0' + str;
  }

  return str;
}

// ------------------------------------------------------------
// HÀM 3: Hiển thị thông báo (Toast)
// ------------------------------------------------------------
// Mục đích: Hiển thị thông báo nhỏ ở góc màn hình
//        (thành công, lỗi, cảnh báo, thông tin)
//
// Tham số:
//   type: 'success' | 'warning' | 'error' | 'info'
//   title: Tiêu đề ngắn
//   message: Nội dung chi tiết
//
// Ví dụ:
//   showToast('success', 'Thành công', 'Đã tạo lịch hẹn!')
//   showToast('error', 'Lỗi', 'Không thể lưu lịch hẹn')
function showToast(type, title, message) {
  // Bước 1: Tìm phần tử header và icon trong toast
  var header = toastEl.querySelector(".toast-header");
  var icon = header.querySelector("i");

  // Bước 2: Xóa hết class cũ
  header.className = "toast-header";

  // Bước 3: Thêm class và icon theo loại thông báo
  if (type === "success") {
    // Xanh lá - Thành công
    header.classList.add("bg-success", "text-white");
    icon.className = "fas fa-check-circle me-2";
  }
  else if (type === "warning") {
    // Vàng - Cảnh báo
    header.classList.add("bg-warning", "text-dark");
    icon.className = "fas fa-exclamation-triangle me-2";
  }
  else if (type === "error") {
    // Đỏ - Lỗi
    header.classList.add("bg-danger", "text-white");
    icon.className = "fas fa-times-circle me-2";
  }
  else {
    // Xanh dương - Thông tin
    header.classList.add("bg-info", "text-white");
    icon.className = "fas fa-info-circle me-2";
  }

  // Bước 4: Đặt nội dung
  toastTitle.textContent = title;
  toastBody.textContent = message;

  // Bước 5: Hiển thị toast
  if (toast) {
    toast.show();
  }
}

// ------------------------------------------------------------
// HÀM 4: Lấy màu CSS cho badge trạng thái
// ------------------------------------------------------------
// Mục đích: Trả về class CSS tương ứng với trạng thái
//
// Ví dụ:
//   statusClass('pending')     → "status-pending" (vàng)
//   statusClass('completed')   → "status-completed" (xanh)
function statusClass(s) {
  // Kiểm tra từng trạng thái và trả về class tương ứng
  if (s === "not_arrived") {
    return "status-not_arrived";
  }
  if (s === "arrived") {
    return "status-arrived";
  }
  if (s === "completed") {
    return "status-completed";
  }
  if (s === "cancelled") {
    return "status-cancelled";
  }

  // Mặc định: pending
  return "status-pending";
}

// ------------------------------------------------------------
// HÀM 5: Lấy text tiếng Việt cho trạng thái
// ------------------------------------------------------------
// Mục đích: Chuyển mã trạng thái sang tiếng Việt
//
// Ví dụ:
//   statusLabel('pending')    → "Chờ xác nhận"
//   statusLabel('completed')  → "Hoàn thành"
function statusLabel(s) {
  // Dùng if-else để kiểm tra từng trạng thái
  if (s === "pending") {
    return "Chờ xác nhận";
  }
  if (s === "not_arrived") {
    return "Chưa đến";
  }
  if (s === "arrived") {
    return "Đã đến";
  }
  if (s === "completed") {
    return "Hoàn thành";
  }
  if (s === "cancelled") {
    return "Đã hủy";
  }

  // Nếu không khớp, trả về nguyên mã
  return s;
}

// ------------------------------------------------------------
// HÀM 6: Kiểm tra số điện thoại hợp lệ
// ------------------------------------------------------------
// Mục đích: Kiểm tra SĐT có đúng 10 số không
//
// Ví dụ:
//   isValidPhone("0912345678")  → true  (hợp lệ)
//   isValidPhone("0123")         → false (quá ngắn)
//   isValidPhone("09xx1234")     → false (có chữ)
function isValidPhone(v) {
  // Bước 1: Xóa hết ký tự không phải số
  // Ví dụ: "0912-345.678" → "0912345678"
  var onlyNumbers = v.replace(/\D/g, "");

  // Bước 2: Kiểm tra có đúng 10 số không
  // ^\d{10}$ nghĩa là: bắt đầu bằng số, đúng 10 chữ số, kết thúc
  var has10Digits = /^\d{10}$/.test(onlyNumbers);

  return has10Digits;
}

// ------------------------------------------------------------
// HÀM 7: Tính số phút từ giờ mở cửa
// ------------------------------------------------------------
// Mục đích: Tính xem một giờ nào đó cách giờ mở cửa bao nhiêu phút
//          Giờ mở cửa là 9:00 (START_HOUR = 9)
//
// Ví dụ:
//   minutesFromStart("09:00")  → 0   (đúng giờ mở cửa)
//   minutesFromStart("10:30")  → 90  (90 phút sau 9h)
//   minutesFromStart("12:00")  → 180 (3 tiếng sau 9h)
function minutesFromStart(t) {
  // Bước 1: Tách giờ và phút từ chuỗi "HH:MM"
  var parts = t.split(":");
  var hours = parseInt(parts[0], 10);  // Chuyển "10" thành 10
  var minutes = parseInt(parts[1], 10); // Chuyển "30" thành 30

  // Bước 2: Tính tổng số phút từ 0:00
  var totalMinutes = hours * 60 + minutes;

  // Bước 3: Tính số phút từ giờ mở cửa (9:00 = 9 * 60 = 540 phút)
  var minutesFrom9AM = totalMinutes - START_HOUR * 60;

  return minutesFrom9AM;
}

// ------------------------------------------------------------
// HÀM 8: Thêm phút vào thời gian
// ------------------------------------------------------------
// Mục đích: Cộng thêm số phút vào một thời gian
//
// Ví dụ:
//   addMinutesToTime("09:00", 60)  → "10:00" (cộng 1 tiếng)
//   addMinutesToTime("10:30", 30)  → "11:00" (cộng 30 phút)
//   addMinutesToTime("08:45", 90)  → "10:15" (cộng 1 tiếng 30 phút)
function addMinutesToTime(t, add) {
  // Bước 1: Tách giờ và phút
  var parts = t.split(":");
  var h = parseInt(parts[0], 10);
  var m = parseInt(parts[1], 10);

  // Bước 2: Tính tổng số phút
  var totalMinutes = h * 60 + m + add;

  // Bước 3: Chuyển ngược lại giờ:phút
  var newHours = Math.floor(totalMinutes / 60);  // Lấy phần nguyên
  var newMinutes = totalMinutes % 60;            // Lấy phần dư

  // Bước 4: Định dạng lại thành 2 chữ số
  return pad2(newHours) + ":" + pad2(newMinutes);
}

// ------------------------------------------------------------
// HÀM 9: Kiểm tra 2 khoảng thời gian có trùng không
// ------------------------------------------------------------
// Mục đích: Kiểm tra 2 lịch có giao nhau về thời gian không
//
// Ví dụ:
//   overlaps(540, 600, 570, 630)  → true
//   # Khoảng 1: 540-600 (9:00-10:00)
//   # Khoảng 2: 570-630 (9:30-10:30)
//   # Giao nhau: 9:30-10:00 → TRÙNG
//
// Công thức: 2 khoảng trùng nhau khi:
//   (bắt đầu 1 < kết thúc 2) VÀ (bắt đầu 2 < kết thúc 1)
function overlaps(aStart, aEnd, bStart, bEnd) {
  var condition1 = aStart < bEnd;  // Khoảng 1 bắt đầu trước khi khoảng 2 kết thúc
  var condition2 = bStart < aEnd;  // Khoảng 2 bắt đầu trước khi khoảng 1 kết thúc

  // Cả 2 điều kiện đúng → TRÙNG
  return condition1 && condition2;
}

// ------------------------------------------------------------
// HÀM 10: Xóa thông báo lỗi trong modal
// ------------------------------------------------------------
// Mục đích: Ẩn text báo lỗi và xóa nội dung
//
// Khi dùng:
//   - Trước khi validate lại form
//   - Khi mở modal mới
function resetModalError() {
  // Ẩn phần tử lỗi
  modalError.classList.add("d-none");

  // Xóa nội dung
  modalError.textContent = "";
}

// ------------------------------------------------------------
// HÀM 11: Lấy độ rộng của 1 ô lịch
// ------------------------------------------------------------
// Mục đích: Lấy độ rộng tính bằng pixel của 1 ô lịch (30 phút)
//          Được lưu trong CSS variable: --slotW
//
// Kết quả: Số pixel, thường là 52px
function getSlotWidth() {
  // Bước 1: Lấy giá trị CSS từ thẻ <html>
  var cssValue = getComputedStyle(document.documentElement)
    .getPropertyValue("--slotW");

  // Bước 2: Chuyển chuỗi thành số
  var widthInPixels = parseFloat(cssValue);

  // Bước 3: Nếu không có giá trị, dùng mặc định 52
  if (!widthInPixels) {
    widthInPixels = 52;
  }

  return widthInPixels;
}

// ------------------------------------------------------------
// HÀM 12: Kiểm tra phòng còn đủ sức chứa không
// ------------------------------------------------------------
// Mục đích: Kiểm tra khi thêm lịch mới, phòng có quá tải không
//
// Tham số:
//   roomId:       Mã phòng (ví dụ "P01")
//   day:          Ngày (ví dụ "2026-04-13")
//   start:        Giờ bắt đầu (ví dụ "10:00")
//   end:          Giờ kết thúc (ví dụ "11:00")
//   guestsCount:  Số khách mới
//   ignoreId:     ID lịch cần bỏ qua (khi sửa lịch)
//
// Trả về: true nếu còn chỗ, false nếu hết chỗ
//
// Ví dụ:
//   Phòng P01 có sức chứa 3 giường
//   Đã có 2 khách trong khung giờ 10:00-11:00
//   Thêm 1 khách → capacityOK() trả về true  (2+1=3 ≤ 3)
//   Thêm 2 khách → capacityOK() trả về false (2+2=4 > 3)
function capacityOK(roomId, day, start, end, guestsCount, ignoreId) {
  // BƯỚC 1: Tìm thông tin phòng
  var roomInfo = ROOMS.find(function(r) {
    return r.id === roomId;
  });

  // Nếu không tìm thấy phòng → báo lỗi
  if (!roomInfo) {
    return false;
  }

  // BƯỚC 2: Tính số phút của lịch mới
  var newStartMinutes = minutesFromStart(start);
  var newEndMinutes = minutesFromStart(end);

  // BƯỚC 3: Tính tổng số khách đang có trong khung giờ này
  var totalGuests = 0;

  // Debug: In thông tin kiểm tra
  console.log('=== KIỂM TRA SỨ CHỨA PHÒNG ===');
  console.log('Phòng: ' + roomInfo.name + ', Sức chứa: ' + roomInfo.capacity);
  console.log('Lịch mới: ' + start + '-' + end + ', Số khách: ' + guestsCount);

  // Lọc các lịch trùng thời gian với lịch mới
  var overlappingAppts = APPOINTMENTS.filter(function(a) {
    var sameRoom = a.roomId === roomId;
    var sameDay = a.date === day;
    var notCancelled = a.apptStatus !== "cancelled";
    var notThisOne = a.id !== ignoreId;

    return sameRoom && sameDay && notCancelled && notThisOne;
  });

  console.log('Tìm thấy ' + overlappingAppts.length + ' lịch trùng thời gian:');

  // Với mỗi lịch trùng, kiểm tra xem có trùng về giờ không
  for (var i = 0; i < overlappingAppts.length; i++) {
    var a = overlappingAppts[i];
    var existingStart = minutesFromStart(a.start);
    var existingEnd = minutesFromStart(a.end);

    // Nếu trùng giờ → cộng thêm số khách
    if (overlaps(newStartMinutes, newEndMinutes, existingStart, existingEnd)) {
      console.log('  - ' + a.appointment_code + ': ' + a.start + '-' + a.end + ', ' + a.guests + ' khách → TRÙNG');
      totalGuests = totalGuests + (Number(a.guests) || 0);
    }
  }

  // BƯỚC 4: Kiểm tra tổng có vượt quá sức chứa không
  console.log('Tổng khách trùng giờ: ' + totalGuests);
  console.log('Khách mới: ' + guestsCount);
  console.log('Tổng: ' + (totalGuests + guestsCount) + ' <= ' + roomInfo.capacity + ' ?');

  var hasSpace = (totalGuests + guestsCount) <= roomInfo.capacity;
  console.log(hasSpace ? '✅ ĐỦ CHỖ' : '❌ HẾT CHỖ');
  console.log('========================');

  return hasSpace;
}

// ------------------------------------------------------------
// HÀM 13: Bật chế độ loading cho button
// ------------------------------------------------------------
// Mục đích: Hiển thị icon xoay và text "Đang xử lý..."
//        Vô hiệu hóa button để tránh bấm lặp
//
// Ví dụ:
//   setButtonLoading(btnSave, 'Đang lưu...')
//   Button sẽ hiển thị: [🔄 Đang lưu...] (vô hiệu hóa)
function setButtonLoading(btn, loadingText, originalText) {
  // Giá trị mặc định nếu không truyền vào
  if (loadingText === undefined) {
    loadingText = 'Đang xử lý...';
  }
  if (originalText === undefined) {
    originalText = null;
  }

  // Nếu không có button → không làm gì
  if (!btn) {
    return;
  }

  // Lưu text gốc nếu chưa lưu
  if (!btn.dataset.originalText) {
    btn.dataset.originalText = originalText || btn.innerHTML;
  }

  // Vô hiệu hóa button
  btn.disabled = true;

  // Hiển thị icon xoay + text
  btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>' + loadingText;
}

// ------------------------------------------------------------
// HÀM 14: Tắt chế độ loading cho button
// ------------------------------------------------------------
// Mục đích: Khôi phục lại button về trạng thái ban đầu
//
// Ví dụ:
//   resetButton(btnSave)
//   Button sẽ hiển thị lại như cũ: [Lưu lịch hẹn] (có thể bấm)
function resetButton(btn) {
  // Nếu không có button → không làm gì
  if (!btn) {
    return;
  }

  // Kích hoạt lại button
  btn.disabled = false;

  // Khôi phục text gốc
  if (btn.dataset.originalText) {
    btn.innerHTML = btn.dataset.originalText;
    delete btn.dataset.originalText;
  }
}

// ============================================================
// PHẦN 5: API CALLS - GỌI BACKEND API
// ============================================================

/**
 * Gọi API GET request
 * @param {string} url - URL cần gọi
 * @return {Object} - Response data
 */
async function apiGet(url) {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error('API GET error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Gọi API POST request
 * @param {string} url - URL cần gọi
 * @param {Object} payload - Dữ liệu gửi đi
 * @return {Object} - Response data
 */
async function apiPost(url, payload) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify(payload),
    });
    return await response.json();
  } catch (error) {
    console.error('API POST error:', error);
    return { success: false, error: error.message };
  }
}

// ============================================================
// PHẦN 6: DATA LOADING - TẢI DỮ LIỆU TỪ BACKEND
// ============================================================

/**
 * Tải danh sách phòng từ Backend
 */
async function loadRooms() {
  const result = await apiGet(`${API_BASE}/rooms/`);
  if (result.success && result.rooms) {
    ROOMS = result.rooms;
  } else {
    // Dữ liệu fallback nếu API lỗi
    ROOMS = [
      { id: "P01", name: "1", capacity: 1 },
      { id: "P02", name: "2", capacity: 2 },
      { id: "P03", name: "3", capacity: 3 },
      { id: "P04", name: "4", capacity: 4 },
      { id: "P05", name: "5", capacity: 5 },
    ];
  }
  console.log('✅ Đã tải', ROOMS.length, 'phòng');
}

/**
 * Tải danh sách dịch vụ từ Backend
 */
async function loadServices() {
  const result = await apiGet(`${API_BASE}/services/`);
  if (result.services) {
    SERVICES = result.services;
    fillServicesSelect();
  }
  console.log('✅ Đã tải', SERVICES.length, 'dịch vụ');
}

/**
 * Tải danh sách lịch hẹn theo ngày
 * @param {string} date - Ngày cần tải (YYYY-MM-DD)
 */
async function loadAppointments(date = '') {
  let url = `${API_BASE}/appointments/`;
  if (date) url += `?date=${date}`;

  const result = await apiGet(url);

  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
    console.log('✅ Đã tải', APPOINTMENTS.length, 'lịch hẹn');
  } else {
    APPOINTMENTS = [];
    console.log('❌ Không có lịch hẹn nào');
  }
}

/**
 * Tải danh sách yêu cầu đặt lịch từ web
 * @param {string} statusFilter - Bộ lọc trạng thái (optional)
 * @return {Array} - Danh sách booking requests
 */
async function loadBookingRequests(statusFilter = '') {
  let url = `${API_BASE}/booking-requests/`;
  const queryParams = [];

  if (statusFilter) {
    queryParams.push(`status=${statusFilter}`);
  }

  if (queryParams.length > 0) {
    url += '?' + queryParams.join('&');
  }

  const result = await apiGet(url);

  if (result && result.success) {
    return result.appointments || [];
  } else {
    console.error('❌ Lỗi API:', result);
    return [];
  }
}

// ============================================================
// PHẦN 7: UI HELPERS - CÁC HÀM HỖ TRỢ GIAO DIỆN
// ============================================================

/**
 * Cập nhật booking badge số lượng
 * @param {number} count - Số lượng bookings
 */
function updateBookingBadges(count) {
  if (webCount) {
    const oldCount = webCount.textContent;
    webCount.textContent = String(count);
    webCount.setAttribute('data-count', String(count));

    // Animation khi count thay đổi
    if (oldCount !== String(count)) {
      webCount.classList.add('badge-update');
      setTimeout(() => {
        webCount.classList.remove('badge-update');
      }, 500);
    }

    console.log(`✅ Badge cập nhật: ${oldCount} → ${count}`);
  }
}

/**
 * Điền danh sách phòng vào select box
 */
function fillRoomsSelect() {
  room.innerHTML = ROOMS.map(r => `<option value="${r.id}">${r.name}</option>`).join("");
}

/**
 * Điền danh sách dịch vụ vào select box
 */
function fillServicesSelect() {
  service.innerHTML = `<option value="">-- Chọn dịch vụ --</option>` +
    SERVICES.map(s => `<option value="${s.id}">${s.name} (${s.duration} phút)</option>`).join("");
}

// ============================================================
// PHẦN 8: RENDER SCHEDULER GRID - VẼ LƯỚI LỊCH
// ============================================================

/**
 * Vẽ header timeline (9:00, 9:30, 10:00, ...)
 */
function renderHeader() {
  const totalSlots = ((END_HOUR - START_HOUR) * 60) / SLOT_MIN;
  document.documentElement.style.setProperty("--totalSlots", totalSlots);

  let html = `<div class="leftcell">Phòng</div><div class="slots">`;
  for (let i = 0; i < totalSlots; i++) {
    const mins = i * SLOT_MIN;
    const hour = START_HOUR + Math.floor(mins / 60);
    const minute = mins % 60;
    html += `<div class="slot ${minute === 0 ? 'major' : ''}">${minute === 0 ? `${hour}:00` : ''}</div>`;
  }
  html += `</div>`;
  timeHeader.innerHTML = html;
}

/**
 * Phân bổ lane (dòng) cho các khách trong phòng
 * @param {string} roomId - Mã phòng
 * @param {string} day - Ngày
 * @param {Array} appts - Danh sách lịch hẹn
 * @return {Object} - { cap: số capacity, placements: mảng vị trí }
 */
function allocateRoomLanes(roomId, day, appts) {
  const cap = (ROOMS.find(r => r.id === roomId)?.capacity) || 1;
  const laneIntervals = Array.from({ length: cap }, () => []);
  const sorted = [...appts].sort((a, b) => minutesFromStart(a.start) - minutesFromStart(b.start));
  const placements = [];

  for (const a of sorted) {
    const need = Math.max(1, Number(a.guests) || 1);
    const s = minutesFromStart(a.start), e = minutesFromStart(a.end);

    for (let g = 0; g < need; g++) {
      let foundLane = -1;
      for (let li = 0; li < cap; li++) {
        if (!laneIntervals[li].some(it => overlaps(s, e, it.startMin, it.endMin))) {
          foundLane = li;
          break;
        }
      }
      if (foundLane === -1) break;
      laneIntervals[foundLane].push({ startMin: s, endMin: e, apptId: a.id });
      placements.push({ appt: a, laneIndex: foundLane });
    }
  }
  return { cap, placements };
}

/**
 * Vẽ toàn bộ lưới lịch (scheduler grid)
 */
function renderGrid() {
  console.log('=== BẮT ĐẦU VẼ LƯỚI LỊCH ===');
  grid.innerHTML = "";

  const day = dayPicker.value;
  const searchTerm = searchInput.value.toLowerCase().trim();

  // Duyệt qua từng phòng
  ROOMS.forEach((r) => {
    // Lọc lịch theo phòng
    let appts = APPOINTMENTS.filter(a => a.date === day && a.roomId === r.id);

    // Tìm kiếm
    if (searchTerm) {
      appts = appts.filter(a =>
        a.customerName.toLowerCase().includes(searchTerm) ||
        a.phone.includes(searchTerm) ||
        a.service.toLowerCase().includes(searchTerm) ||
        a.id.toLowerCase().includes(searchTerm)
      );
    }

    // Phân bổ lane
    const { cap, placements } = allocateRoomLanes(r.id, day, appts);

    // Vẽ từng lane
    for (let lane = 0; lane < cap; lane++) {
      const laneRow = document.createElement("div");
      laneRow.className = "lane-row";
      laneRow.dataset.roomId = r.id;
      laneRow.dataset.lane = lane;

      // Tên phòng
      laneRow.innerHTML = `
        ${lane === 0
          ? `<div class="roomcell"><span class="dot"></span>${r.name}</div>`
          : `<div class="roomcell muted"><span class="dot"></span>${r.name}</div>`
        }
        <div class="slots" data-room="${r.id}" data-lane="${lane}"></div>
      `;

      const slotsEl = laneRow.querySelector(".slots");

      // Click vào ô trống → Tạo lịch mới
      slotsEl.addEventListener("click", (e) => {
        const rect = slotsEl.getBoundingClientRect();
        const x = e.clientX - rect.left + slotsEl.scrollLeft;
        const slotIndex = Math.floor(x / getSlotWidth());
        const minutes = slotIndex * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes / 60))}:${pad2(minutes % 60)}`;
        openCreateModal({ roomId: r.id, day, time: clickedTime });
      });

      // Vẽ các block lịch hẹn
      placements.filter(p => p.laneIndex === lane).forEach(p => {
        const a = p.appt;
        const block = document.createElement("div");
        block.className = `appt ${statusClass(a.apptStatus)}`;
        block.dataset.id = a.id;

        const leftMin = minutesFromStart(a.start);
        const durMin = Math.max(30, minutesFromStart(a.end) - leftMin);

        block.style.left = `${(leftMin / SLOT_MIN) * getSlotWidth()}px`;
        block.style.width = `${Math.max(36, (durMin / SLOT_MIN) * getSlotWidth())}px`;
        block.innerHTML = `
          <div class="t1">${a.customerName} • ${a.service}</div>
          <div class="t2">${a.start}-${a.end} • ${a.guests} khách</div>
        `;

        // Click vào lịch → Sửa
        block.addEventListener("click", (ev) => {
          ev.stopPropagation();
          openEditModal(a.id);
        });

        slotsEl.appendChild(block);
      });

      grid.appendChild(laneRow);
    }
  });

  console.log('=== KẾT THÚC VẼ LƯỚI LỊCH ===');
}

// ============================================================
// PHẦN 9: R.ENDER BOOKING REQUESTS TABLE - BẢNG YÊU CẦU ĐẶT LỊCH
// ============================================================

/**
 * Vẽ bảng yêu cầu đặt lịch từ web
 */
async function renderWebRequests() {
  console.log('=== BẮT ĐẦU VẼ BẢNG YÊU CẦU ĐẶT LỊCH ===');

  const searchTerm = searchInput.value.toLowerCase().trim();
  const filterEl = document.getElementById("webStatusFilter");
  const statusFilter = filterEl ? filterEl.value : '';

  // Load bookings với bộ lọc
  let rows = await loadBookingRequests(statusFilter);

  // Lưu tổng số trước khi search
  const totalCount = rows.length;

  // Search filter (client-side)
  if (searchTerm) {
    rows = rows.filter(a =>
      a.customerName.toLowerCase().includes(searchTerm) ||
      a.phone.includes(searchTerm) ||
      a.service.toLowerCase().includes(searchTerm) ||
      a.id.toLowerCase().includes(searchTerm)
    );
  }

  // Update badge
  updateBookingBadges(totalCount);

  // Nếu không có dữ liệu
  if (rows.length === 0) {
    webTbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">Không có yêu cầu đặt lịch trực tuyến</td></tr>`;
    return;
  }

  // Vẽ bảng
  webTbody.innerHTML = rows.map(a => `<tr>
    <td class="fw-semibold">${a.id}</td>
    <td>${a.customerName}</td>
    <td>${a.phone}</td>
    <td>${a.service}</td>
    <td>${a.date}</td>
    <td>${a.start} - ${a.end}</td>
    <td>${a.durationMin || ""} phút</td>
    <td>
      <span class="badge ${
        a.apptStatus === 'pending' ? 'bg-warning' :
        (a.apptStatus === 'cancelled' ? 'bg-danger' : 'bg-success')
      } text-white">${statusLabel(a.apptStatus)}</span>
    </td>
    <td class="text-end">
      ${a.apptStatus === "pending"
        ? `<div class="btn-group btn-group-sm">
            <button class="btn btn-warning px-2" data-id="${a.id}" onclick="approveWeb('${a.id}')">
              <i class="fas fa-check"></i><span class="d-none d-md-inline ms-1">Xác nhận</span>
            </button>
            <button class="btn btn-outline-danger px-2" data-id="${a.id}" onclick="rejectWeb('${a.id}')">
              <i class="fas fa-xmark"></i><span class="d-none d-md-inline ms-1">Từ chối</span>
            </button>
          </div>`
        : `<button class="btn btn-sm btn-outline-secondary" data-id="${a.id}" onclick="openEditModal('${a.id}')">
            <i class="fas fa-pen me-1"></i>Xem/Sửa
          </button>`
      }
    </td>
  </tr>`).join("");

  console.log('=== KẾT THÚC VẼ BẢNG ===');
}

/**
 * Xác nhận yêu cầu đặt lịch (chuyển sang "Chưa đến")
 * @param {string} id - Mã lịch hẹn
 */
window.approveWeb = async function(id) {
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (result.success && result.appointment) {
    openEditModalWithData(result.appointment);
    apptStatus.value = "not_arrived";
    showToast("info", "Gợi ý", "Chọn phòng/thời gian nếu cần rồi bấm Lưu để xác nhận");
  } else {
    showToast("error", "Lỗi", "Không tìm thấy lịch hẹn");
  }
};

/**
 * Từ chối yêu cầu đặt lịch (chuyển sang "Đã hủy")
 * @param {string} id - Mã lịch hẹn
 */
window.rejectWeb = async function(id) {
  if (!confirm("Từ chối yêu cầu đặt lịch này?")) return;

  const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'cancelled' });
  if (result.success) {
    showToast("success", "OK", "Đã từ chối yêu cầu");
    await renderWebRequests();
    await refreshData();
  } else {
    showToast("error", "Lỗi", result.error || "Không thể từ chối yêu cầu");
  }
};

// ============================================================
// PHẦN 10: MODAL & FORM HANDLERS - XỬ LÝ MODAL VÀ FORM
// ============================================================

/**
 * Mở modal tạo lịch hẹn mới
 * @param {Object} prefill - Dữ liệu điền trước (optional)
 */
function openCreateModal(prefill = {}) {
  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");

  // Reset form
  customerName.value = "";
  phone.value = "";
  email.value = "";
  service.value = "";
  room.value = prefill.roomId || (ROOMS[0]?.id || "");
  guests.value = 1;
  date.value = prefill.day || dayPicker.value;
  time.value = prefill.time || "09:00";
  duration.value = "60";
  apptStatus.value = "not_arrived";
  payStatus.value = "unpaid";
  note.value = "";

  form.classList.remove("was-validated");
  if (modal) modal.show();
}

/**
 * Mở modal sửa lịch hẹn (load data từ Backend)
 * @param {string} id - Mã lịch hẹn
 */
async function openEditModal(id) {
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (result.success && result.appointment) {
    openEditModalWithData(result.appointment);
  } else {
    const a = APPOINTMENTS.find(x => x.id === id);
    if (a) openEditModalWithData(a);
    else showToast("error", "Lỗi", "Không tìm thấy lịch hẹn");
  }
}

/**
 * Mở modal sửa với dữ liệu đã có
 * @param {Object} a - Dữ liệu lịch hẹn
 */
function openEditModalWithData(a) {
  resetModalError();
  modalTitle.textContent = `Chỉnh sửa • ${a.id}`;
  apptId.value = a.id;
  btnDelete.classList.remove("d-none");

  customerName.value = a.customerName;
  phone.value = a.phone;
  email.value = a.email || "";
  service.value = a.serviceId || "";
  room.value = a.roomId || (ROOMS[0]?.id || "");
  guests.value = a.guests;
  date.value = a.date;
  time.value = a.start;
  duration.value = String(a.durationMin || 60);
  apptStatus.value = a.apptStatus || "not_arrived";
  payStatus.value = a.payStatus || "unpaid";
  note.value = a.note || "";

  form.classList.remove("was-validated");
  if (modal) modal.show();
}

// Nút Save submit form
btnSave.addEventListener("click", () => form.requestSubmit());

/**
 * Xử lý submit form (Tạo / Sửa lịch hẹn)
 */
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Ngăn submit lặp
  if (isSubmitting) {
    console.log('⚠️ Đang xử lý, bỏ qua submit lặp');
    return;
  }

  resetModalError();
  form.classList.add("was-validated");

  // Lấy giá trị từ form
  const id = apptId.value.trim();
  const nameVal = customerName.value.trim();
  const phoneVal = phone.value.trim();
  const serviceVal = service.value;
  const roomVal = room.value;
  const guestsVal = Number(guests.value);
  const dayVal = date.value;
  const startVal = time.value;
  const durationVal = Number(duration.value);

  // === BƯỚC 1: VALIDATE CƠ BẢN ===
  customerName.setCustomValidity(nameVal ? "" : "invalid");
  phone.setCustomValidity((phoneVal && isValidPhone(phoneVal)) ? "" : "invalid");
  service.setCustomValidity(serviceVal ? "" : "invalid");
  room.setCustomValidity(roomVal ? "" : "invalid");
  guests.setCustomValidity((Number.isFinite(guestsVal) && guestsVal > 0) ? "" : "invalid");
  date.setCustomValidity(dayVal ? "" : "invalid");
  time.setCustomValidity(startVal ? "" : "invalid");
  duration.setCustomValidity((Number.isFinite(durationVal) && durationVal > 0) ? "" : "invalid");

  if (!form.checkValidity()) {
    if (!nameVal) modalError.textContent = "Vui lòng nhập họ tên khách hàng";
    else if (!phoneVal || !isValidPhone(phoneVal)) modalError.textContent = "Số điện thoại không hợp lệ";
    else if (!serviceVal) modalError.textContent = "Vui lòng chọn dịch vụ";
    else if (!roomVal) modalError.textContent = "Vui lòng chọn phòng";
    else modalError.textContent = "Vui lòng điền đầy đủ thông tin";
    modalError.classList.remove("d-none");
    return;
  }

  // === BƯỚC 2: KIỂM TRA GIỜ HẸN ===
  const endVal = addMinutesToTime(startVal, durationVal);
  if (minutesFromStart(startVal) < 0 || minutesFromStart(endVal) > (END_HOUR - START_HOUR) * 60) {
    modalError.textContent = "Giờ hẹn không hợp lệ (ngoài giờ làm việc)";
    modalError.classList.remove("d-none");
    return;
  }

  // === BƯỚC 3: KIỂM TRA TRÙNG LỊCH ===
  if (!capacityOK({ roomId: roomVal, day: dayVal, start: startVal, end: endVal, guestsCount: guestsVal, ignoreId: id || null })) {
    modalError.textContent = "Phòng đã đủ chỗ ở khung giờ này";
    modalError.classList.remove("d-none");
    return;
  }

  // === BƯỚC 4: GỌI API ===
  const payload = {
    customerName: nameVal,
    phone: phoneVal.replace(/\D/g, ""),
    email: email.value.trim(),
    serviceId: serviceVal,
    roomId: roomVal,
    guests: guestsVal,
    date: dayVal,
    time: startVal,
    duration: durationVal,
    note: note.value.trim(),
    apptStatus: apptStatus.value,
    payStatus: payStatus.value
  };

  // Bật loading
  isSubmitting = true;
  const loadingText = id ? 'Đang cập nhật...' : 'Đang tạo lịch...';
  setButtonLoading(btnSave, loadingText);

  try {
    let result;
    if (id) {
      result = await apiPost(`${API_BASE}/appointments/${id}/update/`, payload);
    } else {
      result = await apiPost(`${API_BASE}/appointments/create/`, payload);
    }

    if (result.success) {
      if (modal) modal.hide();
      if (dayPicker.value !== dayVal) dayPicker.value = dayVal;
      await refreshData();
      await renderWebRequests();
      showToast("success", "Thành công", result.message || (id ? "Cập nhật lịch hẹn thành công" : "Tạo lịch hẹn thành công"));
    } else {
      modalError.textContent = result.error || "Không thể lưu lịch hẹn";
      modalError.classList.remove("d-none");
    }
  } catch (err) {
    modalError.textContent = "Không thể lưu lịch hẹn. Vui lòng thử lại sau";
    modalError.classList.remove("d-none");
  } finally {
    isSubmitting = false;
    resetButton(btnSave);
  }
});

/**
 * Xử lý xóa lịch hẹn
 */
btnDelete.addEventListener("click", async () => {
  const id = apptId.value.trim();

  if (isSubmitting) {
    console.log('⚠️ Đang xử lý, bỏ qua click lặp');
    return;
  }

  if (!id) return;

  // Hiển thị thông tin trong modal xác nhận
  document.getElementById('deleteAppointmentCode').textContent = id;

  const deleteModal = new bootstrap.Modal(document.getElementById('deleteAppointmentModal'));
  const confirmDeleteBtn = document.getElementById('confirmDeleteAppointmentBtn');

  // Xóa event listener cũ
  if (confirmDeleteBtn) {
    const newBtn = confirmDeleteBtn.cloneNode(true);
    confirmDeleteBtn.parentNode.replaceChild(newBtn, confirmDeleteBtn);

    // Thêm event listener mới
    newBtn.addEventListener('click', async () => {
      deleteModal.hide();
      isSubmitting = true;
      showToast("warning", "Đang xử lý...", "Đang xóa lịch hẹn...");

      try {
        const result = await apiPost(`${API_BASE}/appointments/${id}/delete/`, {});
        if (result.success) {
          if (modal) modal.hide();
          await refreshData();
          await renderWebRequests();
          showToast("success", "Đã xóa thành công", `Đã xóa hoàn toàn lịch hẹn ${id}`);
        } else {
          showToast("error", "Lỗi", result.error || "Không thể xóa lịch hẹn");
        }
      } catch (err) {
        console.error('Error:', err);
        showToast("error", "Lỗi", "Không thể xóa lịch hẹn. Vui lòng thử lại sau");
      } finally {
        isSubmitting = false;
      }
    });
  }

  deleteModal.show();
});

// ============================================================
// PHẦN 11: DATE NAVIGATION - ĐIỀU KHIỂN NGÀY
// ============================================================

/**
 * Thiết lập ngày và refresh data
 * @param {string} d - Ngày cần set (YYYY-MM-DD)
 */
function setDay(d) {
  dayPicker.value = d;
  date.value = d;
  refreshData();
}

/**
 * Lấy ngày hôm nay dạng YYYY-MM-DD
 * @return {string} - Ngày hôm nay
 */
function todayISO() {
  const t = new Date();
  return `${t.getFullYear()}-${pad2(t.getMonth() + 1)}-${pad2(t.getDate())}`;
}

/**
 * Dịch chuyển ngày (+/-)
 * @param {number} delta - Số ngày cần dịch (+1 hoặc -1)
 */
function shiftDay(delta) {
  const d = new Date(dayPicker.value + "T00:00:00");
  d.setDate(d.getDate() + delta);
  setDay(`${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`);
}

/**
 * Refresh lại data và render lại lưới
 */
async function refreshData() {
  await loadAppointments(dayPicker.value);
  renderGrid();
}

// ============================================================
// PHẦN 12: SEARCH & FILTER - TÌM KIẾM VÀ BỘ LỌC
// ============================================================

// Search input - render lại khi gõ
if (searchInput) {
  searchInput.addEventListener("input", function() {
    renderGrid();
    renderWebRequests();
  });
}

// ============================================================
// PHẦN 13: INITIALIZATION - KHỞI TẠO ỨNG DỤNG
// ============================================================

document.addEventListener("DOMContentLoaded", async () => {
  console.log('🚀 BẮT ĐẦU KHỞI TẠO SCHEDULER...');

  // Khởi tạo Bootstrap components
  if (modalEl) modal = new bootstrap.Modal(modalEl);
  if (toastEl) toast = new bootstrap.Toast(toastEl);

  // Khởi tạo delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  // Sidebar toggle (mobile)
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
  }

  // Load dữ liệu
  console.log('📦 Đang tải phòng...');
  await loadRooms();

  console.log('📦 Đang tải dịch vụ...');
  await loadServices();

  fillRoomsSelect();

  // Set ngày hôm nay
  dayPicker.value = todayISO();
  console.log('📅 Hôm nay:', dayPicker.value);

  // Vẽ header timeline
  renderHeader();

  // Load lịch hẹn
  await refreshData();
  await renderWebRequests();

  // === SSE: REAL-TIME UPDATE ===
  if (window.EventSource) {
    try {
      const eventSource = new EventSource('/api/booking/pending-count/stream/');
      let previousPendingCount = null;

      eventSource.addEventListener("message", async function(event) {
        try {
          const data = JSON.parse(event.data);
          const currentPendingCount = data.count;

          console.log('🔔 SSE - Pending count:', currentPendingCount);

          // Update sidebar badge
          const sidebarBadge = document.getElementById('adminSidebarBookingBadge');
          if (sidebarBadge) {
            sidebarBadge.textContent = String(currentPendingCount);
            sidebarBadge.setAttribute('data-count', String(currentPendingCount));
          }

          // Auto-refresh nếu có thay đổi
          if (previousPendingCount !== null && currentPendingCount !== previousPendingCount) {
            console.log('🔄 Pending count thay đổi - refreshing...');
            await renderWebRequests();
          }

          previousPendingCount = currentPendingCount;
        } catch (err) {
          console.error('SSE parse error:', err);
        }
      });

      eventSource.onerror = function(error) {
        console.error('SSE connection error:', error);
      };

      console.log('✅ SSE connected');
    } catch (err) {
      console.error('SSE init error:', err);
    }
  } else {
    console.warn('EventSource not supported');
  }

  // Event listeners cho điều khiển ngày
  if (btnToday) btnToday.addEventListener("click", () => setDay(todayISO()));
  if (btnPrev) btnPrev.addEventListener("click", () => shiftDay(-1));
  if (btnNext) btnNext.addEventListener("click", () => shiftDay(1));
  if (dayPicker) dayPicker.addEventListener("change", () => refreshData());

  // Bộ lọc trạng thái
  if (webStatusFilter) {
    webStatusFilter.addEventListener("change", () => renderWebRequests());
  }

  // Auto-fill duration khi chọn service
  if (service) {
    service.addEventListener("change", function() {
      const serviceId = parseInt(this.value);
      const selectedService = SERVICES.find(s => s.id === serviceId);

      if (selectedService && selectedService.duration) {
        duration.value = selectedService.duration;
      } else {
        duration.value = 60;
      }
    });
  }

  // Export functions để dùng từ HTML
  window.openEditModal = openEditModal;
  window.renderWebRequests = renderWebRequests;

  console.log('✅ KHỞI TẠO HOÀN TẤT!');
});

/**
 * =============================================
 * KẾT THÚC FILE
 * =============================================
 */
