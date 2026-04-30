// ============================================================
// SECTION 1: SETTINGS & CONSTANTS
// ============================================================
console.log("ADMIN APPOINTMENTS JS LOADED v20260426-003");
const START_HOUR = 9;  // Giờ mở cửa (9:00 sáng)
const END_HOUR = 21;   // Giờ đóng cửa (21:00 tối)
const SLOT_MIN = 30; // 1 ô lịch = 30 phút
const DEFAULT_DURATION = 60; // Thời lượng mặc định cho pending block (phút)

// ===== API BASE URL- đường dẫn API để gọi BE =====
const API_BASE = '/api';

// Constant dùng chung cho tất cả lỗi tải lịch hẹn — UC 14.2 exception flow 5a
const MSG_LOAD_APPT_ERROR = 'Không thể tải lịch hẹn. Vui lòng thử lại sau.';

// ===== UC 14.3 — Messages chuẩn hóa =====
const MSG_APPROVE_SUCCESS  = 'Xác nhận yêu cầu thành công';
const MSG_REJECT_SUCCESS   = 'Từ chối yêu cầu thành công';
const MSG_REBOOK_SUCCESS   = 'Đặt lại lịch hẹn thành công';
const MSG_WEB_EMPTY        = 'Hiện chưa có yêu cầu đặt lịch nào.';
const MSG_WEB_GENERIC_ERR  = 'Không thể xử lý yêu cầu. Vui lòng thử lại sau.';
const MSG_WEB_CONFLICT     = 'Không thể xử lý do khung giờ hoặc phòng không khả dụng.';
const MSG_APPROVE_CONFLICT = 'Không thể xác nhận do khung giờ hoặc phòng không khả dụng.';

// ===== HELPER: format variant label — tránh lặp "90 phút — 90 phút" =====
function variantLabel(v) {
  const dur = `${v.duration_minutes} phút`;
  if (!v.label || v.label.trim() === dur) return dur;
  return `${v.label} — ${dur}`;
}

// ===== HELPER: cắt ngắn chuỗi nếu quá dài =====
function _truncate(str, maxLen) {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

// ============================================================
// SECTION 2: STATE VARIABLES
// ============================================================
// PENDING BLOCKS STATE — Flow 2 bước tạo lịch hẹn
let pendingBlocks = [];
let _pendingIdCounter = 0;

// Dữ liệu ( lấy từ API) ==> lưu dữ liệu load từ DB để render giao diện, validate form, tính toán trùng lịch
let ROOMS = []; // danh sách phòng
let SERVICES = []; //dánh sách dịch vụ
let APPOINTMENTS = []; // danh sách lịch hẹn

// Biến theo dõi trạng thái đang submit để tránh submit lặp
let isSubmitting = false;

// State: đang ở chế độ "quay về grid để chọn thêm slot"
let _addingSlotMode = false;
let _savedBookerInfo = null;  // lưu tạm booker info khi quay về grid

// UC 14.3 — track rebook mode để hiển thị đúng message sau khi tạo lịch
let _isRebookMode = false;

// CREATE MODE — ACCORDION GUEST CARDS
let _guestCount = 0;
// Map pendingBlockId → guestIdx để sync slot summary
let _pendingBlockMap = []; // [{pendingId, guestIdx}]

// Current time line interval
let _ctlInterval = null;

// ============================================================
// SECTION 3: API HELPERS
// ============================================================
// ===== CSRF HELPER ======
function getCSRFToken() {
  const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookieValue ? cookieValue.split('=')[1] : '';
}

async function apiGet(url) {
  try {
    const response = await fetch(url);
    const text = await response.text();
    if (!text) {
      if (!response.ok) return { success: false, ok: false, status: response.status, error: `HTTP error ${response.status}` };
      return { success: true, ok: true, status: response.status };
    }
    try {
      const data = JSON.parse(text);
      if (!response.ok && !data.error) data.error = `HTTP error ${response.status}`;
      data.ok = response.ok;
      data.status = response.status;
      return data;
    } catch (e) {
      return {
        success: false,
        ok: response.ok,
        status: response.status,
        error: !response.ok ? `HTTP error ${response.status}: Máy chủ trả về phản hồi không hợp lệ` : 'Invalid JSON response'
      };
    }
  } catch (error) {
    console.error('API GET error:', error);
    return { success: false, error: error.message };
  }
}

async function apiPost(url, payload) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    if (!text) {
      if (!response.ok) return { success: false, ok: false, status: response.status, error: `HTTP error ${response.status}` };
      return { success: true, ok: true, status: response.status };
    }
    try {
      const data = JSON.parse(text);
      if (!response.ok && !data.error) data.error = `HTTP error ${response.status}`;
      data.ok = response.ok;
      data.status = response.status;
      return data;
    } catch (e) {
      return {
        success: false,
        ok: response.ok,
        status: response.status,
        error: !response.ok ? `HTTP error ${response.status}: Máy chủ trả về phản hồi không hợp lệ` : 'Invalid JSON response'
      };
    }
  } catch (error) {
    console.error('API POST error:', error);
    return { success: false, error: error.message };
  }
}

// ===== LOAD DATA FROM API =====
async function loadRooms() {
  const result = await apiGet(`${API_BASE}/rooms/`);
  if (result.success && result.rooms) {
    ROOMS = result.rooms;
  } else {
    // Fallback data - CẬN NHẬP: Phải khớp với database!
    ROOMS = [
      { id: "P01", name: "1", capacity: 1 },
      { id: "P02", name: "2", capacity: 2 },
      { id: "P03", name: "3", capacity: 3 },
      { id: "P04", name: "4", capacity: 4 },
      { id: "P05", name: "5", capacity: 5 },
    ];
  }
}

async function loadServices() {
  const result = await apiGet(`${API_BASE}/services/`);
  if (result.services) {
    SERVICES = result.services;
    fillServicesSelect();
  }
}

// _gridLoadError: true khi lần load gần nhất bị lỗi — dùng để renderGrid hiển thị error state
let _gridLoadError = false;

async function loadAppointments(date = '') {
  let url = `${API_BASE}/appointments/`;
  const params = [];
  if (date) params.push(`date=${date}`);

  const statusFilter  = (document.getElementById('statusFilter')  || {}).value || '';
  const serviceFilter = (document.getElementById('serviceFilter') || {}).value || '';
  const sourceFilter  = (document.getElementById('sourceFilter')  || {}).value || '';
  if (statusFilter)  params.push(`status=${encodeURIComponent(statusFilter)}`);
  if (serviceFilter) params.push(`service=${encodeURIComponent(serviceFilter)}`);
  if (sourceFilter)  params.push(`source=${encodeURIComponent(sourceFilter)}`);

  const searchInput = document.getElementById("searchInput");
  const searchTerm = (searchInput ? searchInput.value.trim() : '');
  if (searchTerm) params.push(`q=${encodeURIComponent(searchTerm)}`);

  if (params.length) url += '?' + params.join('&');

  const result = await apiGet(url);
  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
    _gridLoadError = false;
  } else {
    // API trả error hoặc network lỗi — UC 14.2 exception flow 5a
    APPOINTMENTS = [];
    _gridLoadError = true;
    showToast('error', 'Lỗi', result.error || MSG_LOAD_APPT_ERROR);
  }
}

async function loadBookingRequests(statusFilter = '', dateFilter = '', searchTerm = '', serviceFilter = '') {
  let url = `${API_BASE}/booking-requests/`;
  const queryParams = [];
  if (statusFilter)  queryParams.push(`status=${encodeURIComponent(statusFilter)}`);
  if (dateFilter)    queryParams.push(`date=${encodeURIComponent(dateFilter)}`);
  if (searchTerm)    queryParams.push(`q=${encodeURIComponent(searchTerm)}`);
  if (serviceFilter) queryParams.push(`service=${encodeURIComponent(serviceFilter)}`);
  if (queryParams.length > 0) url += '?' + queryParams.join('&');

  const result = await apiGet(url);
  if (result && result.success) {
    return result.appointments || [];
  }
  // UC 14.3 — lỗi tải không được im lặng
  showToast('error', 'Lỗi', MSG_WEB_GENERIC_ERR);
  return [];
}

// ============================================================
// SECTION 4: VALIDATION HELPERS
// ============================================================
function isValidPhone(v){ return /^\d{10}$/.test(v.replace(/\D/g,"")); }
function isValidEmail(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }

function capacityOK({roomId, day, start, end, ignoreId}){
  const roomInfo = ROOMS.find(r=>r.id===roomId);
  if(!roomInfo) return false;

  const newS = minutesFromStart(start), newE = minutesFromStart(end);
  let count = 0;

  // Mỗi appointment = 1 khách, đếm số lịch trùng giờ
  const overlappingAppts = APPOINTMENTS.filter(
    a => a.roomCode===roomId && a.date===day && !["cancelled", "rejected"].includes((a.apptStatus||'').toLowerCase()) && a.id!==ignoreId
  );

  overlappingAppts.forEach(a => {
    const s = minutesFromStart(a.start);
    const rawE = a.end ? minutesFromStart(a.end) : NaN;
    const e = (!isNaN(rawE) && rawE > s) ? rawE : s + Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
    if(overlaps(newS, newE, s, e)) count++;
  });

  return count < roomInfo.capacity;
}

// ============================================================
// SECTION 5: TIME/DATE HELPERS
// ============================================================
function pad2(n){ return String(n).padStart(2,"0"); }

function minutesFromStart(t){ const [h,m]=t.split(":").map(Number); return (h-START_HOUR)*60 + m; }

function addMinutesToTime(t, add){
  const [h,m]=t.split(":").map(Number);
  const total = h*60+m+add;
  return `${pad2(Math.floor(total/60))}:${pad2(total%60)}`;
}

function overlaps(aStart,aEnd,bStart,bEnd){ return aStart < bEnd && bStart < aEnd; }

// Tổng số phút của toàn bộ timeline (9:00 → 21:00 = 720 phút)
function totalTimelineMinutes(){ return (END_HOUR - START_HOUR) * 60; }

// Chuyển số phút từ START_HOUR sang % chiều ngang của vùng slots
function minutesToPercent(minutes){ return (minutes / totalTimelineMinutes()) * 100; }

// ============================================================
// SECTION 6: UI HELPERS
// ============================================================
function showToast(type, title, message){
  const toastEl = document.getElementById("toast");
  const header = toastEl.querySelector(".toast-header");
  const icon = header.querySelector("i");
  const toastTitle = document.getElementById("toastTitle");
  const toastBody = document.getElementById("toastBody");
  const toast = window.toast;

  header.className = "toast-header";
  if(type==="success"){ header.classList.add("bg-success","text-white"); icon.className="fas fa-check-circle me-2"; }
  else if(type==="warning"){ header.classList.add("bg-warning","text-dark"); icon.className="fas fa-exclamation-triangle me-2"; }
  else if(type==="error"){ header.classList.add("bg-danger","text-white"); icon.className="fas fa-times-circle me-2"; }
  else { header.classList.add("bg-info","text-white"); icon.className="fas fa-info-circle me-2"; }
  toastTitle.textContent = title;
  toastBody.textContent = message;
  if (toast) toast.show();
}

function statusClass(s){
  const sl = (s||'').toLowerCase();
  if(sl==="not_arrived") return "status-not_arrived";
  if(sl==="arrived") return "status-arrived";
  if(sl==="completed") return "status-completed";
  if(sl==="cancelled") return "status-cancelled";
  if(sl==="rejected") return "status-rejected";
  return "status-pending";
}

function statusLabel(s, cancelledBy){
  const sl = (s||'').toLowerCase();
  if(sl==="pending") return "Chờ xác nhận";
  if(sl==="not_arrived") return "Chưa đến";
  if(sl==="arrived") return "Đã đến";
  if(sl==="completed") return "Hoàn thành";
  if(sl==="cancelled") return cancelledBy === 'customer' ? "Khách đã hủy" : "Đã hủy";
  if(sl==="rejected") return "Đã từ chối";
  return s;
}

// ===== BOOKING BADGES UPDATE =====
function updateBookingBadges(rows) {
  // Chỉ đếm PENDING — không tính CANCELLED hay trạng thái khác
  const pendingCount = rows.filter(r => (r.apptStatus || '').toUpperCase() === 'PENDING').length;
  const webCount = document.getElementById("webCount");
  if (webCount) {
    if (pendingCount === 0) {
      webCount.textContent = '';
      webCount.classList.add('d-none');
    } else {
      webCount.textContent = String(pendingCount);
      webCount.classList.remove('d-none');
    }
  }
}

/**
 * Bật loading state cho button
 * @param {HTMLElement} btn - Button cần set loading
 * @param {string} loadingText - Text hiển thị khi loading
 * @param {string} originalText - Text gốc để restore sau này
 */
function setButtonLoading(btn, loadingText = 'Đang xử lý...', originalText = null) {
  if (!btn) return;

  // Lưu text gốc nếu chưa có
  if (!btn.dataset.originalText) {
    btn.dataset.originalText = originalText || btn.innerHTML;
  }

  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
}

/**
 * Tắt loading state và restore button về trạng thái ban đầu
 * @param {HTMLElement} btn - Button cần restore
 */
function resetButton(btn) {
  if (!btn) return;

  btn.disabled = false;
  if (btn.dataset.originalText) {
    btn.innerHTML = btn.dataset.originalText;
    delete btn.dataset.originalText;
  }
}

/**
 * Hiển thị modal xác nhận đồng bộ giao diện hệ thống
 * @param {string} title - Tiêu đề
 * @param {string} message - Nội dung xác nhận
 * @param {string} confirmText - Text nút xác nhận
 * @param {string} cancelText - Text nút hủy
 * @returns {Promise<boolean>} - true nếu người dùng xác nhận
 */
async function confirmAction(title, message, confirmText = 'Xác nhận', cancelText = 'Hủy') {
  if (window.showConfirm) {
    return window.showConfirm(message, { title, confirmText, cancelText });
  }
  return false;
}

function resetModalError(){
  const modalError = document.getElementById("modalError");
  modalError.classList.add("d-none");
  modalError.textContent = "";
}

function getSlotWidth(){
  // Đọc chiều rộng thực tế của 1 slot từ DOM (sau khi flex giãn)
  // Dùng cho tính toán click position
  const timeHeader = document.getElementById("timeHeader");
  const firstSlot = timeHeader ? timeHeader.querySelector('.slot') : null;
  if (firstSlot) {
    const w = firstSlot.getBoundingClientRect().width;
    if (w > 0) return w;
  }
  // Fallback: chia đều chiều rộng vùng slots
  const slotsEl = timeHeader ? timeHeader.querySelector('.slots') : null;
  if (slotsEl) {
    const totalW = slotsEl.getBoundingClientRect().width;
    const totalSlots = ((END_HOUR - START_HOUR) * 60) / SLOT_MIN;
    if (totalW > 0 && totalSlots > 0) return totalW / totalSlots;
  }
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--slotW")) || 36;
}

// ===== LOADING SKELETON CHO GRID =====
function showGridLoading(){
  const grid = document.getElementById("grid");
  if (!grid) return;
  // Hiện 5 dòng skeleton để layout không bị trống trong lúc fetch
  const rowH = getComputedStyle(document.documentElement).getPropertyValue('--rowH') || '72px';
  grid.innerHTML = Array.from({length: 5}, (_, i) => `
    <div class="lane-row" style="opacity:.45;">
      <div class="roomcell"><span class="dot"></span>—</div>
      <div class="slots" style="background: repeating-linear-gradient(90deg,#f3f4f6 0,#f3f4f6 40%,#e9eaec 40%,#e9eaec 100%) 0 0 / 120px 100%;"></div>
    </div>`).join('');
}

// ============================================================
// SECTION 7: PENDING BLOCKS STATE
// ============================================================
function _nextPendingId() {
  return ++_pendingIdCounter;
}

/**
 * Kiểm tra slot có nằm trong quá khứ không.
 * day: 'YYYY-MM-DD', time: 'HH:MM'
 */
function _isSlotInPast(day, time) {
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  if (day > todayStr) return false;
  if (day < todayStr) return true;
  // Cùng ngày hôm nay — so sánh giờ
  const [h, m] = time.split(':').map(Number);
  const slotMinutes = h * 60 + m;
  const nowMinutes  = now.getHours() * 60 + now.getMinutes();
  return slotMinutes <= nowMinutes;
}

/**
 * Toggle slot: click ô trống → chọn, click lại block xanh → bỏ chọn.
 * Đây là hàm duy nhất xử lý add/remove pending block.
 */
function handleToggleSlot({ roomId, laneIndex, day, time, slotsEl }) {
  console.log("slot clicked", `${roomId}|lane${laneIndex}|${day}|${time}`);
  console.log("toggle path running");
  const duration = DEFAULT_DURATION;
  const endTime  = addMinutesToTime(time, duration);
  const startMin = minutesFromStart(time);
  const endMin   = minutesFromStart(endTime);

  // Kiểm tra ngoài giờ
  if (startMin < 0 || endMin > totalTimelineMinutes()) {
    showToast("warning", "Ngoài giờ hoạt động", `Spa hoạt động từ ${START_HOUR}:00 đến ${END_HOUR}:00`);
    return;
  }

  // Chặn slot trong quá khứ
  if (_isSlotInPast(day, time)) {
    showToast("warning", "Không thể chọn slot này", "Không thể tạo lịch hẹn trong quá khứ");
    return;
  }

  // Tìm pending block trùng slot này (cùng room + lane + day + time)
  const existing = pendingBlocks.find(pb =>
    pb.roomId === roomId &&
    pb.laneIndex === laneIndex &&
    pb.day === day &&
    pb.time === time
  );

  if (existing) {
    // ── TOGGLE OFF: bỏ chọn ──
    pendingBlocks = pendingBlocks.filter(pb => pb.id !== existing.id);
    document.querySelectorAll(`.appt-pending[data-pending-id="${existing.id}"]`).forEach(el => el.remove());
    _syncActionBar();
    return;
  }

  // ── TOGGLE ON: kiểm tra conflict rồi thêm ──

  // Conflict với appointment đã có
  const dayAppts = APPOINTMENTS.filter(a =>
    a.roomCode === roomId && a.date === day && !["CANCELLED", "REJECTED"].includes((a.apptStatus || "").toUpperCase())
  );
  const { placements } = allocateRoomLanes(roomId, day, dayAppts);
  const laneAppts = placements.filter(p => p.laneIndex === laneIndex).map(p => p.appt);
  const conflictAppt = laneAppts.find(a =>
    overlaps(startMin, endMin, minutesFromStart(a.start), minutesFromStart(a.end))
  );
  if (conflictAppt) {
    showToast("warning", "Slot đã có lịch", "Khung giờ đã có lịch, vui lòng chọn thời gian khác");
    if (slotsEl) {
      slotsEl.classList.add("conflict-flash");
      setTimeout(() => slotsEl.classList.remove("conflict-flash"), 450);
    }
    return;
  }

  // Conflict với pending block khác trong cùng lane
  const conflictPending = pendingBlocks.find(pb =>
    pb.roomId === roomId && pb.laneIndex === laneIndex && pb.day === day &&
    overlaps(startMin, endMin, minutesFromStart(pb.time), minutesFromStart(pb.endTime))
  );
  if (conflictPending) {
    showToast("warning", "Trùng với slot đang chọn", `Lane này đã có slot đang chọn lúc ${conflictPending.time}–${conflictPending.endTime}`);
    return;
  }

  const block = { id: _nextPendingId(), roomId, laneIndex, day, time, endTime, duration };
  pendingBlocks.push(block);
  _syncActionBar();
  if (slotsEl) _mountPendingBlock(block, slotsEl);
}

function clearPendingBlocks() {
  pendingBlocks = [];
  document.querySelectorAll(".appt-pending").forEach(el => el.remove());
  _syncActionBar();
}

function _syncActionBar() {
  const bar   = document.getElementById("pendingActionBar");
  const badge = document.getElementById("pbCountBadge");
  const label = document.getElementById("pbCountLabel");
  const btnContinue = document.getElementById("btnContinuePending");
  if (!bar) return;

  const count = pendingBlocks.length;
  if (badge) badge.textContent = String(count);
  if (label) label.textContent = count === 1 ? "1 khách đã chọn" : `${count} khách đã chọn`;

  // Khi đang ở chế độ thêm slot, đổi label nút Tiếp tục
  if (btnContinue) {
    if (_addingSlotMode) {
      btnContinue.innerHTML = '<i class="fas fa-arrow-right me-1"></i>Quay lại & thêm khách';
    } else {
      btnContinue.innerHTML = '<i class="fas fa-arrow-right me-1"></i>Tiếp tục';
    }
  }

  if (count > 0) {
    bar.style.display = "block";
    requestAnimationFrame(() => bar.classList.add("visible"));
  } else {
    bar.classList.remove("visible");
    setTimeout(() => { if (!pendingBlocks.length) bar.style.display = "none"; }, 180);
  }
}

function _mountPendingBlock(pb, slotsEl) {
  if (!slotsEl) return null;

  // Xóa block cũ nếu đã tồn tại
  slotsEl.querySelector(`.appt-pending[data-pending-id="${pb.id}"]`)?.remove();

  const block = document.createElement("div");
  block.className = "appt appt-pending";
  block.dataset.pendingId = String(pb.id);

  // Chỉ có top-bar xanh + hint giờ — không có nút X
  block.innerHTML = `
    <div class="pb-selection-bar"></div>
    <div class="pb-time-hint">${pb.time} – ${pb.endTime}</div>
  `;

  block.style.cssText = "position:absolute;top:0;height:var(--rowH);z-index:30;cursor:pointer;";

  const leftMin = minutesFromStart(pb.time);
  const durMin  = Math.max(SLOT_MIN, minutesFromStart(pb.endTime) - leftMin);
  block.style.left  = `calc(${minutesToPercent(leftMin)}% + 1px)`;
  block.style.width = `calc(${minutesToPercent(durMin)}% - 2px)`;

  // Click vào block xanh → toggle off (bỏ chọn)
  block.addEventListener("click", (e) => {
    e.stopPropagation();
    const sEl = block.closest(".slots");
    handleToggleSlot({
      roomId:     pb.roomId,
      laneIndex:  pb.laneIndex,
      day:        pb.day,
      time:       pb.time,
      slotsEl:    sEl,
    });
  });

  slotsEl.appendChild(block);
  return block;
}

function renderPendingBlocks(slotsEl, roomId, laneIndex, day) {
  if (!slotsEl) return;
  slotsEl.querySelectorAll(".appt-pending").forEach(el => el.remove());
  pendingBlocks
    .filter(pb => pb.roomId === roomId && pb.laneIndex === laneIndex && pb.day === day)
    .forEach(pb => _mountPendingBlock(pb, slotsEl));
}

// ============================================================
// SECTION 8: TAB 1 - LỊCH THEO PHÒNG (GRID)
// ============================================================
function renderHeader(){
  const timeHeader = document.getElementById("timeHeader");
  const totalSlots = ((END_HOUR-START_HOUR)*60)/SLOT_MIN;
  document.documentElement.style.setProperty("--totalSlots", totalSlots);
  let html = `<div class="leftcell">Phòng</div><div class="slots">`;
  for(let i=0;i<totalSlots;i++){
    const mins = i*SLOT_MIN, hour = START_HOUR + Math.floor(mins/60), minute = mins%60;
    html += `<div class="slot ${minute===0?'major':''}">${minute===0?`${hour}:00`:''}</div>`;
  }
  html += `</div>`;
  timeHeader.innerHTML = html;
}

function allocateRoomLanes(roomId, day, appts){
  const cap = (ROOMS.find(r=>r.id===roomId)?.capacity) || 1;
  const laneIntervals = Array.from({length: cap}, ()=>[]);
  const sorted = [...appts].sort((a,b)=> minutesFromStart(a.start)-minutesFromStart(b.start));
  const placements = [];
  for(const a of sorted){
    const need = Math.max(1, Number(a.guests)||1);
    const s = minutesFromStart(a.start);
    // Tính end: ưu tiên a.end, fallback về durationMin
    const rawE = a.end ? minutesFromStart(a.end) : NaN;
    const e = (!isNaN(rawE) && rawE > s) ? rawE : s + Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
    // Đảm bảo end > start (tránh block width = 0)
    const eFixed = e > s ? e : s + SLOT_MIN;
    for(let g=0; g<need; g++){
      let foundLane = -1;
      for(let li=0; li<cap; li++){
        if(!laneIntervals[li].some(it => overlaps(s, eFixed, it.startMin, it.endMin))){ foundLane = li; break; }
      }
      if(foundLane === -1) foundLane = 0; // fallback: lane 0 nếu hết chỗ
      laneIntervals[foundLane].push({startMin:s, endMin:eFixed, apptId:a.id});
      placements.push({ appt: a, laneIndex: foundLane });
    }
  }
  return { cap, placements };
}

function renderGrid(){
  const grid = document.getElementById("grid");
  const dayPicker = document.getElementById("dayPicker");
  grid.innerHTML = "";
  const day = dayPicker.value;

  // UC 14.2 exception flow 5a — hiển thị error state thay vì grid rỗng im lặng
  if (_gridLoadError) {
    grid.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;padding:3rem 1rem;gap:.75rem;color:#b91c1c;">
        <i class="fas fa-exclamation-circle" style="font-size:1.25rem;flex-shrink:0;"></i>
        <span style="font-size:.9rem;font-weight:500;">${MSG_LOAD_APPT_ERROR}</span>
      </div>`;
    return;
  }

  ROOMS.forEach((r)=>{
    // Lọc lịch theo phòng — dùng roomCode (khớp với serializer)
    // Hiển thị tất cả trừ CANCELLED/REJECTED
    let appts = APPOINTMENTS.filter(a =>
      a.date === day &&
      a.roomCode === r.id &&
      !['CANCELLED', 'REJECTED'].includes((a.apptStatus || '').toUpperCase())
    );

    // Phân bổ Lane (dòng) cho từng khách
    const { cap, placements } = allocateRoomLanes(r.id, day, appts);
    for(let lane=0; lane<cap; lane++){
      const laneRow = document.createElement("div");
      laneRow.className = "lane-row";
      laneRow.dataset.roomId = r.id;
      laneRow.dataset.lane = lane;

      // tên phòng
      laneRow.innerHTML = `${lane===0?`<div class="roomcell"><span class="dot"></span>${r.name}</div>`:`<div class="roomcell muted"><span class="dot"></span>${r.name}</div>`}<div class="slots" data-room="${r.id}" data-lane="${lane}"></div>`;
      const slotsEl = laneRow.querySelector(".slots");

      // click vào ô trống → toggle slot (chọn hoặc bỏ chọn)
      slotsEl.addEventListener("click", (e) => {
        if (e.target.closest('.appt') || e.target.closest('.appt-pending')) return;

        const rect        = slotsEl.getBoundingClientRect();
        const ratio       = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const minutes     = Math.floor(ratio * totalTimelineMinutes() / SLOT_MIN) * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes / 60))}:${pad2(minutes % 60)}`;

        handleToggleSlot({ roomId: r.id, laneIndex: lane, day: dayPicker.value, time: clickedTime, slotsEl });
      });

      // vẽ block lịch hẹn
      placements.filter(p => p.laneIndex === lane).forEach(p=>{
        const a = p.appt;
        const block = document.createElement("div");
        block.className = `appt ${statusClass(a.apptStatus)}`;
        block.dataset.id = a.id;
        const leftMin = minutesFromStart(a.start);
        // Tính durMin: ưu tiên end - start, fallback về durationMin, tối thiểu SLOT_MIN
        const endMin  = a.end ? minutesFromStart(a.end) : NaN;
        const durMin  = (!isNaN(endMin) && endMin > leftMin)
          ? endMin - leftMin
          : Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
        const endLabel = a.end || addMinutesToTime(a.start, durMin);
        // Dùng % thay vì px → tự co giãn theo chiều rộng thực tế của vùng slots
        const leftPct  = minutesToPercent(leftMin);
        const widthPct = minutesToPercent(durMin);
        block.style.left  = `calc(${leftPct}% + 2px)`;
        block.style.width = `calc(${widthPct}% - 4px)`;
        const paidIcon = (a.payStatus || '').toUpperCase() === 'PAID'
          ? `<span class="appt-paid-icon" title="Đã thanh toán"><i class="fas fa-receipt"></i></span>`
          : '';
        const svcText   = a.serviceCode || a.service || '';
        const custText  = a.customerName || '';
        const titleText = svcText && custText ? `${svcText} · ${custText}` : (svcText || custText || 'Chưa chọn DV');
        block.innerHTML = `<div class="appt-content"><div class="t1">${titleText}</div><div class="t2">${a.start}–${endLabel}</div></div>${paidIcon}`;

        // click vào lịch ==> sửa
        block.addEventListener("click", (ev)=>{ ev.stopPropagation(); openEditModal(a.id); });
        slotsEl.appendChild(block);
      });

      // Vẽ pending blocks đúng theo lane
      renderPendingBlocks(slotsEl, r.id, lane, day);

      grid.appendChild(laneRow);
    }
  });

  // Vẽ đường dọc thời điểm hiện tại — element được tạo 1 lần, cập nhật bởi updateCurrentTimeLine()
  updateCurrentTimeLine();
}

// ── Current time line — realtime, không phụ thuộc reload ──────────────────

/**
 * Tạo hoặc cập nhật vị trí đường đỏ thời gian hiện tại.
 * Gọi khi: renderGrid, đổi ngày, resize, setInterval.
 */
function updateCurrentTimeLine() {
  const grid = document.getElementById("grid");
  const dayPicker = document.getElementById("dayPicker");
  if (!grid) return;

  // Lấy hoặc tạo element (chỉ tạo 1 lần duy nhất)
  let line = grid.querySelector('.current-time-line');

  const viewDay  = dayPicker ? dayPicker.value : '';
  const now      = new Date();
  const todayStr = `${now.getFullYear()}-${pad2(now.getMonth()+1)}-${pad2(now.getDate())}`;

  // Chỉ hiện khi đang xem đúng ngày hôm nay
  if (viewDay !== todayStr) {
    if (line) line.style.display = 'none';
    return;
  }

  const nowMinutes = now.getHours() * 60 + now.getMinutes() - START_HOUR * 60;
  const pct        = (nowMinutes / totalTimelineMinutes()) * 100;

  // Ngoài khung giờ → ẩn
  if (pct <= 0 || pct >= 100) {
    if (line) line.style.display = 'none';
    return;
  }

  const label = `${pad2(now.getHours())}:${pad2(now.getMinutes())}`;

  if (!line) {
    line = document.createElement('div');
    line.className = 'current-time-line';
    line.style.cssText = 'position:absolute;top:0;bottom:0;width:2px;background:#ef4444;z-index:20;pointer-events:none;';
    line.innerHTML = '<span class="ctl-label" style="position:absolute;top:4px;left:50%;transform:translateX(-50%);background:#ef4444;color:#fff;font-size:.6rem;font-weight:700;padding:1px 5px;border-radius:4px;white-space:nowrap;line-height:1.5;"></span>';
    grid.appendChild(line);
  }

  // Cập nhật vị trí và label
  line.style.display = '';
  line.style.left    = `calc(var(--leftCol) + ${pct} * (100% - var(--leftCol)) / 100)`;
  const labelEl = line.querySelector('.ctl-label');
  if (labelEl) labelEl.textContent = label;
}

// Khởi động interval realtime — cập nhật mỗi 30 giây
function startCurrentTimeLineInterval() {
  if (_ctlInterval) clearInterval(_ctlInterval);
  _ctlInterval = setInterval(updateCurrentTimeLine, 30_000);
}

// ============================================================
// SECTION 9: TAB 2 - YÊU CẦU ĐẶT LỊCH (WEB REQUESTS)
// ============================================================
// vẽ bảng yêu cầu đặt lịch online
async function renderWebRequests(){
  const statusFilter  = (document.getElementById("webStatusFilter")  || {}).value || '';
  const dateFilter    = (document.getElementById("webDateFilter")     || {}).value || '';
  const searchTerm    = ((document.getElementById("webSearchInput")   || {}).value || '').trim();
  const serviceFilter = (document.getElementById("webServiceFilter")  || {}).value || '';

  let rows = await loadBookingRequests(statusFilter, dateFilter, searchTerm, serviceFilter);

  updateBookingBadges(rows);
  window._webAppts = rows;

  const webTbody = document.getElementById("webTbody");
  if(rows.length === 0){
    webTbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">${MSG_WEB_EMPTY}</td></tr>`;
    return;
  }
  webTbody.innerHTML = rows.map(a => {
    const st = (a.apptStatus || '').toUpperCase();
    let actionBtn = '';
    if (st === 'PENDING') {
      actionBtn = `<div class="action-buttons">
        <button type="button" class="web-action-btn web-action-btn-approve" data-id="${a.id}" onclick="approveWeb('${a.id}')"><i class="fas fa-check"></i><span>Xác nhận</span></button>
        <button type="button" class="web-action-btn web-action-btn-reject" data-id="${a.id}" onclick="rejectWeb('${a.id}')"><i class="fas fa-xmark"></i><span>Từ chối</span></button>
      </div>`;
    } else if (st === 'CANCELLED' || st === 'REJECTED') {
      actionBtn = `<div class="action-buttons"><button type="button" class="web-action-btn web-action-btn-rebook" data-id="${a.id}" onclick="rebookAppointment('${a.id}')"><i class="fas fa-redo"></i><span>Đặt lại</span></button></div>`;
    } else {
      actionBtn = `<div class="action-buttons"><button type="button" class="web-action-btn web-action-btn-edit" data-id="${a.id}" onclick="openEditModal('${a.id}')"><i class="fas fa-pen"></i><span>Xem/Sửa</span></button></div>`;
    }
    const badgeClass = st === 'PENDING' ? 'bg-warning text-dark'
      : (st === 'REJECTED' ? 'bg-danger' : (st === 'CANCELLED' ? 'bg-secondary' : 'bg-success'));
    const cancelledBadge = (st === 'CANCELLED' && a.cancelledBy === 'customer')
      ? ` <span class="badge bg-warning text-dark ms-1" title="Khách tự hủy"><i class="fas fa-user-times"></i></span>` : '';
    return `<tr>
      <td class="fw-semibold">${a.id}</td><td>${a.customerName}</td><td>${a.phone}</td><td>${a.service}</td>
      <td>${a.date}</td><td>${a.start} - ${a.end}</td><td>${a.durationMin||""} phút</td>
      <td><span class="badge ${badgeClass}">${statusLabel(a.apptStatus, a.cancelledBy)}</span>${cancelledBadge}</td>
      <td class="action-cell">${actionBtn}</td>
    </tr>`;
  }).join("");
}

window.approveWeb = async function(id){
  // UC 14.3 — Xác nhận trực tiếp qua API, không mở modal
  try {
    const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'NOT_ARRIVED' });
    if (result.success) {
      showToast("success", "Thành công", MSG_APPROVE_SUCCESS);
      await renderWebRequests();
      await refreshData();
    } else {
      // Phân biệt lỗi conflict vs lỗi chung — UC 14.3 case 6
      const errLower = (result.error || '').toLowerCase();
      const isConflict = errLower.includes('trùng') || errLower.includes('đầy') || errLower.includes('khả dụng') || errLower.includes('capacity') || errLower.includes('conflict');
      showToast("error", "Không thể xác nhận", isConflict ? MSG_APPROVE_CONFLICT : MSG_WEB_GENERIC_ERR);
    }
  } catch (err) {
    showToast("error", "Lỗi", MSG_WEB_GENERIC_ERR);
  }
}

window.rejectWeb = async function(id){
  const appt = (window._webAppts || []).find(a => a.id === id);
  const info = appt ? `${appt.customerName || appt.bookerName || ''} — ${appt.date} ${appt.start}` : id;

  const infoEl = document.getElementById('rejectWebInfo');
  if (infoEl) infoEl.textContent = info;

  const modalEl = document.getElementById('rejectWebModal');
  modalEl.addEventListener('shown.bs.modal', () => {
    document.querySelectorAll('.modal-backdrop').forEach(el => el.classList.add('reject-web-backdrop'));
  }, { once: true });
  modalEl.addEventListener('hidden.bs.modal', () => {
    document.querySelectorAll('.modal-backdrop').forEach(el => el.classList.remove('reject-web-backdrop'));
  }, { once: true });
  const modal = new bootstrap.Modal(modalEl);

  // Gắn handler một lần, tránh duplicate
  const btn = document.getElementById('confirmRejectWebBtn');
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);

  newBtn.addEventListener('click', async () => {
    modal.hide();
    try {
      const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'REJECTED' });
      if (result.success) {
        showToast("success", "Thành công", MSG_REJECT_SUCCESS);
        await renderWebRequests();
        await refreshData();
      } else {
        showToast("error", "Lỗi", MSG_WEB_GENERIC_ERR);
      }
    } catch (err) {
      showToast("error", "Lỗi", MSG_WEB_GENERIC_ERR);
    }
  });

  modal.show();
}

window.rebookAppointment = async function(id) {
  // Fetch data lịch cũ để pre-fill form tạo mới
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (!result || !result.success || !result.appointment) {
    showToast('error', 'Lỗi', MSG_WEB_GENERIC_ERR);
    return;
  }
  openRebookAsCreate(result.appointment);
};

/**
 * Mở modal TẠO lịch mới, pre-fill từ lịch cũ.
 * Không copy ngày/giờ/phòng — admin phải chọn lại.
 */
function openRebookAsCreate(a) {
  // Đóng modal edit nếu đang mở
  const modalEl = document.getElementById("apptModal");
  let modal = null;
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (modal) modal.hide();

  // Mở modal tạo mới với booker + khách pre-fill, không có slot
  openCreateModal({
    _fromRebook: true,
    _booker: {
      name:   a.bookerName  || '',
      phone:  a.bookerPhone || '',
      email:  a.bookerEmail || '',
      source: a.source      || 'DIRECT',
    },
    _guest: {
      name:      a.customerName || '',
      phone:     a.phone        || '',
      email:     a.email        || '',
      serviceId: a.serviceId    || null,
      variantId: a.variantId    || null,
      // Không copy: roomId, date, time
    },
  });
}

// Điền dropdown dịch vụ cho filter bar scheduler
function fillServiceFilter(){
  const sel = document.getElementById('serviceFilter');
  if (sel) {
    sel.innerHTML = '<option value="">Tất cả dịch vụ</option>' +
      SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }
  // Điền dropdown dịch vụ cho tab Yêu cầu đặt lịch
  const webSel = document.getElementById('webServiceFilter');
  if (webSel) {
    webSel.innerHTML = '<option value="">Tất cả dịch vụ</option>' +
      SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }
}

// ============================================================
// SECTION 10: CUSTOMER LOOKUP (STUB)
// ============================================================
// ===== CUSTOMER INLINE LOOKUP =====
// Spec: nhập SĐT/email → gợi ý → nhân viên xác nhận ✓ hoặc bỏ qua ✕
// Không tự fill, không tạo duplicate CustomerProfile

let _phoneTimer = null;
let _emailTimer = null;
// Lưu kết quả match đang chờ xác nhận (chưa nhấn ✓ hay ✕)
let _pendingMatch = { phone: null, email: null };

function initCustomerSearch() {
  // Customer search badges đã được bỏ cùng editModeBody cũ.
  // Lookup khách hàng hiện tại thực hiện qua bookerPhone trong shared form.
  // Giữ hàm rỗng để tránh lỗi nếu có nơi nào gọi.
}

// Customer lookup — không còn dùng badge cũ, giữ stubs để tránh lỗi
async function _lookupByPhone(phoneVal) { /* no-op */ }
async function _lookupByEmail(emailVal) { /* no-op */ }
function _showSuggestion(c, via) { /* no-op */ }
function _confirmMatch(c, via) {
  document.getElementById('selectedCustomerId').value = c.id;
  document.getElementById('bookerName').value  = c.fullName || '';
  document.getElementById('bookerPhone').value = c.phone || '';
  document.getElementById('bookerEmail').value = c.email || '';
}
function _dismissMatch(c, via) { /* no-op */ }
function _unlinkCustomer(via) {
  document.getElementById('selectedCustomerId').value = '';
}
function _resetPhoneState() {
  _pendingMatch.phone = null;
  document.getElementById('selectedCustomerId').value = '';
}
function _resetEmailState() {
  _pendingMatch.email = null;
}
function _resetAllCustomerState() {
  _pendingMatch = { phone: null, email: null };
  document.getElementById('selectedCustomerId').value = '';
}

// ============================================================
// SECTION 11: MODAL & FORM HELPERS
// ============================================================
// ===== MODAL =====
// fillRoomsSelect / fillServicesSelect không còn dùng — rooms/services load vào guest card trực tiếp
function fillRoomsSelect(){ /* no-op — rooms rendered per guest card */ }
function fillServicesSelect(){ /* no-op — services rendered per guest card */ }

// Escape HTML để tránh XSS
function _esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function _roomShortLabel(room) {
  var raw = String(room?.id || room?.code || room?.name || '').trim();
  if (!raw) return 'P?';
  var pCode = raw.match(/^P0*(\d+)$/i);
  if (pCode) return 'P' + Number(pCode[1]);
  if (/^\d+$/.test(raw)) return 'P' + Number(raw);
  return raw;
}

// ── Helpers ──
function _getGuestItems() {
  return Array.from(document.querySelectorAll('#guestList .gc-item'));
}

function _getGuestItem(idx) {
  return document.querySelector(`#guestList .gc-item[data-idx="${idx}"]`);
}

/** Kiểm tra 1 guest row đã đủ trường bắt buộc chưa */
function _isGuestComplete(item) {
  if (!item) return false;
  const svc  = item.querySelector('.gc-service')?.value;
  const vari = item.querySelector('.gc-variant')?.value;
  const room = item.dataset.slotRoom || item.querySelector('.gc-room')?.value;
  const date = item.dataset.slotDate || item.querySelector('.gc-date')?.value;
  const time = item.dataset.slotTime || item.querySelector('.gc-time')?.value;
  return !!(svc && vari && room && date && time);
}

/** Highlight ô thiếu trong 1 row */
function _markRowValidity(item) {
  if (!item) return;
  const row = item.querySelector('.gc-row');
  if (row) {
    const complete = _isGuestComplete(item);
    row.style.background      = '#fff';
    row.style.borderLeftColor = complete ? '#86efac' : '#fca5a5';
  }
}

/** Highlight lỗi khi submit — chỉ gọi khi user bấm Lưu */
function _markRowError(item) {
  if (!item) return;
  const svcSel = item.querySelector('.gc-service');
  const varSel = item.querySelector('.gc-variant');
  [svcSel, varSel].forEach(el => {
    if (!el) return;
    el.style.borderColor = el.value ? '#d1d5db' : '#ef4444';
    el.style.background  = el.value ? '#fff'    : '#fef2f2';
  });
  const nameInp = item.querySelector('.gc-name');
  if (nameInp) {
    nameInp.style.borderColor = nameInp.value.trim() ? '#d1d5db' : '#ef4444';
    nameInp.style.background  = nameInp.value.trim() ? '#fff'    : '#fef2f2';
  }
}

/** Cập nhật progress bar */
function _updateGuestProgress() {
  const items   = _getGuestItems();
  const total   = items.length;
  const done    = items.filter(it => _isGuestComplete(it)).length;
  const labelEl = document.getElementById('guestProgressLabel');
  const fillEl  = document.getElementById('guestProgressFill');
  if (labelEl) labelEl.textContent = `${done}/${total} đã đủ`;
  if (fillEl)  fillEl.style.width  = total ? `${Math.round(done / total * 100)}%` : '0%';
}

/** Không còn dùng slot summary panel riêng — slot info nằm trong từng row */
function _updateSlotSummary() { /* no-op — slot info is inline in each row */ }

/** Toggle expand detail panel của 1 row (chỉ Email + 2 ghi chú) */
window.toggleGuestCard = function(idx) {
  const item = _getGuestItem(idx);
  if (!item) return;
  const wrap   = item.querySelector('.gc-detail-wrap');
  const detail = item.querySelector('.gc-detail');
  const icon   = item.querySelector('.gc-expand-btn i');
  if (!wrap || !detail) return;
  const isOpen = wrap.style.maxHeight && wrap.style.maxHeight !== '0px' && wrap.style.maxHeight !== '0';
  if (isOpen) {
    wrap.style.maxHeight = '0';
    detail.style.display = 'none';
    if (icon) icon.style.transform = '';
    item.classList.remove('open');
  } else {
    detail.style.display = 'flex';
    wrap.style.maxHeight = detail.scrollHeight + 'px';
    if (icon) icon.style.transform = 'rotate(90deg)';
    item.classList.add('open');
  }
};

/** Focus 1 row (scroll vào view) */
window.focusGuestCard = function(idx) {
  const item = _getGuestItem(idx);
  if (item) item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
};

/** Không còn dùng header summary */
function _refreshGuestHeader(item) { /* no-op */ }

/** Load variants cho 1 guest card */
function _loadGuestVariants(item, serviceId, selectedVariantId) {
  const varSel = item.querySelector('.gc-variant');
  if (!varSel) return;
  varSel.innerHTML = '<option value="">-- Chọn gói --</option>';
  varSel.disabled  = true;
  varSel.style.color      = '#9ca3af';
  varSel.style.background = '#f9fafb';

  const svc = SERVICES.find(s => s.id == serviceId);
  if (!svc || !svc.variants?.length) {
    // Không có variant → giữ disabled nhưng placeholder rõ ràng
    varSel.innerHTML = '<option value="">-- Chọn dịch vụ trước --</option>';
    return;
  }

  svc.variants.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = variantLabel(v);
    opt.dataset.duration = v.duration_minutes;
    if (selectedVariantId && v.id == selectedVariantId) opt.selected = true;
    varSel.appendChild(opt);
  });

  // Enable + reset style về bình thường
  varSel.disabled         = false;
  varSel.style.color      = '#111827';
  varSel.style.background = '#fff';
  varSel.style.opacity    = '1';

  if (!selectedVariantId && svc.variants.length === 1) {
    varSel.value = svc.variants[0].id;
  }
  _updateGuestEndTime(item);
}

/** Tính và lưu end_time vào dataset + cập nhật hiển thị (giờ kết thúc auto-tính) */
function _updateGuestEndTime(item) {
  const varSel = item.querySelector('.gc-variant');
  const timeVal = item.dataset.slotTime;
  if (!varSel || !timeVal) return;
  const opt = varSel.options[varSel.selectedIndex];
  const dur = opt?.dataset?.duration ? Number(opt.dataset.duration) : 60;
  const newEnd = addMinutesToTime(timeVal, dur);
  item.dataset.endTime = newEnd;
  // Cập nhật hidden input
  const endHidden = item.querySelector('.gc-time-end');
  if (endHidden) endHidden.value = newEnd;
  // Cập nhật time-range display (giờ kết thúc readonly)
  const disp = item.querySelector('.gc-time-range-display');
  if (disp) {
    const startVal = item.dataset.slotTime || '--:--';
    disp.innerHTML = startVal + '<span class="gc-time-range-sep"> – </span>' + newEnd;
  }
  // Cập nhật legacy gc-slot-time nếu còn
  const endEl = item.querySelector('.gc-slot-time');
  if (endEl && item.dataset.slotTime) {
    endEl.textContent = `${item.dataset.slotTime}–${newEnd}`;
  }
}

/** Cập nhật hiển thị "Số tiền thu" (readonly) khi variant thay đổi */
function _updateGuestPayFinal(item) {
  const finalEl = item.querySelector('.gc-pay-final');
  if (!finalEl) return;
  const varSel = item.querySelector('.gc-variant');
  const opt = varSel?.options[varSel.selectedIndex];
  // Lấy price từ SERVICES data
  const svcSel = item.querySelector('.gc-service');
  const svc = SERVICES.find(s => s.id == svcSel?.value);
  const variant = svc?.variants?.find(v => v.id == varSel?.value);
  const price = variant?.price || svc?.price || 0;
  finalEl.value = price ? Number(price).toLocaleString('vi-VN') + 'đ' : '—';
  // Lưu raw price vào dataset để dùng khi validate
  item.dataset.finalAmount = price || 0;
}

/** Hiện/ẩn payment detail fields khi thay đổi gc-pay */
function _onGuestPayChange(item) {
  const paySel    = item.querySelector('.gc-pay');
  const payFields = item.querySelector('.gc-pay-fields');
  const amountWrap = item.querySelector('.gc-pay-amount-wrap');
  const finalWrap  = item.querySelector('.gc-pay-final-wrap');
  if (!paySel || !payFields) return;

  const val = paySel.value;
  if (val === 'PAID') {
    payFields.style.display = 'flex';
    if (amountWrap) amountWrap.style.display = 'none';
    if (finalWrap)  finalWrap.style.display  = 'flex';
    _updateGuestPayFinal(item);
  } else {
    // UNPAID hoặc PARTIAL — ẩn toàn bộ payment fields
    payFields.style.display = 'none';
  }
}

/** Show/hide phương thức & số tiền trong block thanh toán chung */
function _syncSharedPayFields(val) {
  const methodWrap = document.getElementById('sharedPayMethodWrap');
  const amountWrap = document.getElementById('sharedPayAmountWrap');
  if (methodWrap) methodWrap.style.display = (val === 'PAID' || val === 'PARTIAL') ? 'flex' : 'none';
  if (amountWrap) amountWrap.style.display = (val === 'PARTIAL') ? 'flex' : 'none';
}

function _setSelectValue(sel, value, fallback) {
  if (!sel) return;
  const wanted = value || fallback || '';
  const hasOption = Array.from(sel.options).some(opt => opt.value === wanted);
  sel.value = hasOption ? wanted : (fallback || '');
}

function _showSharedStatusBlock(statusValue, payValue) {
  const sharedBlock = document.getElementById('sharedStatusBlock');
  if (sharedBlock) sharedBlock.style.display = 'block';

  const sharedStatusSel = document.getElementById('sharedApptStatus');
  const sharedPaySel = document.getElementById('sharedPayStatus');
  _setSelectValue(sharedStatusSel, statusValue, 'NOT_ARRIVED');
  _setSelectValue(sharedPaySel, payValue, 'UNPAID');

  if (sharedPaySel) {
    _syncSharedPayFields(sharedPaySel.value);
    sharedPaySel.onchange = function() { _syncSharedPayFields(this.value); };
  }
}

/** Build 1 compact guest row — detail panel ẩn mặc định, toggle bằng JS */
function _buildGuestItem(idx, prefill) {
  prefill = prefill || {};
  var roomName = prefill.roomId ? (ROOMS.find(function(r){ return r.id === prefill.roomId; }) || {}).name || prefill.roomId : '';
  const dayPicker = document.getElementById("dayPicker");
  var dateVal  = prefill.date || dayPicker.value;
  var timeVal  = prefill.time || '';
  var endTime  = (timeVal && prefill.pendingDuration) ? addMinutesToTime(timeVal, prefill.pendingDuration) : '';
  var hasSlot  = !!(timeVal && prefill.roomId);

  var svcOpts = '<option value="">Dịch vụ</option>' +
    SERVICES.map(function(s){ return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');

  var inp = 'width:100%;height:36px;padding:0 12px;font-size:14px;border:1px solid #d1d5db;border-radius:6px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;';
  var sel = 'width:100%;height:36px;padding:0 10px;font-size:14px;border:1px solid #d1d5db;border-radius:6px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;appearance:auto;';
  var roomSelectCss = sel.replace('width:100%;', 'width:112px;max-width:100%;');
  var sInp = 'width:100%;height:32px;padding:0 10px;font-size:13px;border:1px solid #e5e7eb;border-radius:5px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#374151;display:block;';
  var lbl  = 'font-size:13px;font-weight:600;color:#6b7280;display:block;margin-bottom:4px;white-space:nowrap;';
  var selectedRoomId = prefill.roomId || '';

  // Slot badge: phòng dropdown + time-range field gọn đẹp
  var roomOpts = '<option value="" disabled' + (selectedRoomId ? '' : ' selected') + ' hidden>Chọn phòng</option>' +
    ROOMS.map(function(r){
      var roomId = r.id || r.code || '';
      var isSel = (roomId == selectedRoomId) ? ' selected' : '';
      var label = _roomShortLabel(r);
      var capacity = r.capacity || '';
      var title = label + (capacity ? ' - ' + capacity + ' giường' : '');
      return '<option value="' + _esc(roomId) + '"' + isSel + ' data-capacity="' + _esc(capacity) + '" title="' + _esc(title) + '">' + _esc(label) + '</option>';
    }).join('');

  var slotBadge = '<div class="gc-slot-badge">'
    + '<select class="gc-room-select" required style="' + roomSelectCss + '">' + roomOpts + '</select>'
    + '<input type="date" class="gc-date-input" value="' + _esc(dateVal) + '" title="Ngày hẹn" style="width:125px;max-width:100%;height:32px;padding:0 8px;font-size:13px;border:1px solid #d1d5db;border-radius:6px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#374151;margin:0;" />'
    + '<div class="gc-time-range-field" title="Click để chỉnh giờ">'
      + '<i class="far fa-clock gc-time-range-icon"></i>'
      + '<span class="gc-time-range-display">'
        + (timeVal ? _esc(timeVal) : '--:--')
        + '<span class="gc-time-range-sep"> – </span>'
        + (endTime ? _esc(endTime) : '--:--')
      + '</span>'
      + '<div class="gc-time-range-inputs">'
        + '<input type="time" class="gc-time-input" value="' + _esc(timeVal) + '" title="Giờ bắt đầu" />'
      + '</div>'
    + '</div>'
  + '</div>';

  var item = document.createElement('div');
  item.className = 'gc-item';
  item.dataset.idx      = idx;
  item.dataset.slotTime = timeVal;
  item.dataset.slotDate = dateVal;
  item.dataset.slotRoom = selectedRoomId;
  item.dataset.endTime  = endTime;
  item.dataset.detailOpen = '0';
  item.style.cssText = 'border-bottom:1px solid #eef0f3;';

  item.innerHTML =
    '<input type="hidden" class="gc-room" value="' + _esc(selectedRoomId) + '" />'
  + '<input type="hidden" class="gc-date" value="' + _esc(dateVal) + '" />'
  + '<input type="hidden" class="gc-time" value="' + _esc(timeVal) + '" />'
  + '<input type="hidden" class="gc-time-end" value="' + _esc(endTime) + '" />'

  // ── DÒNG CHÍNH ──
  // Grid: # | Phòng·Giờ | Tên khách (+ checkbox) | SĐT | Dịch vụ | Gói | Actions
  + '<div class="gc-row gc-row-grid">'

    // Col 1 — số thứ tự
    + '<div class="gc-num" style="text-align:center;font-size:13px;font-weight:700;color:#94a3b8;">—</div>'

    // Col 2 — phòng · giờ
    + '<div class="gc-slot-cell">' + slotBadge + '</div>'

    // Col 3 — tên khách + checkbox "= người đặt"
    + '<div class="gc-name-cell">'
      + '<div class="gc-name-inline">'
        + '<input class="gc-name" style="' + inp + 'flex:1 1 220px;min-width:0;" placeholder="Tên khách *" value="' + _esc(prefill.name || '') + '" />'
        + '<label class="gc-same-booker-label" title="Điền từ người đặt">'
          + '<input type="checkbox" class="gc-same-as-booker" style="width:14px;height:14px;cursor:pointer;accent-color:#1d4ed8;margin:0;" />'
          + '<span>= người đặt</span>'
        + '</label>'
      + '</div>'
    + '</div>'

    // Col 4 — SĐT
    + '<div class="gc-phone-cell"><input class="gc-phone" style="' + inp + '" placeholder="SĐT" inputmode="numeric" value="' + _esc(prefill.phone || '') + '" /></div>'

    // Col 5 — dịch vụ
    + '<div class="gc-service-cell"><select class="gc-service" style="' + sel + '">' + svcOpts + '</select></div>'

    // Col 6 — gói
    + '<div class="gc-variant-cell"><select class="gc-variant" style="' + sel + '" disabled><option value="">-- Chọn dịch vụ trước --</option></select></div>'

    // Col 7 — actions
    + '<div class="gc-actions-cell" style="display:flex;align-items:center;justify-content:center;gap:6px;">'
      + '<button type="button" class="gc-expand-btn" onclick="toggleGuestCard(' + idx + ')" title="Email & ghi chú"'
      + ' style="height:36px;width:36px;padding:0;font-size:15px;background:#f1f5f9;border:1px solid #e2e8f0;color:#64748b;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;">'
      + '<i class="fas fa-ellipsis-h"></i></button>'
      + '<button type="button" class="gc-delete-btn" onclick="removeGuestCard(' + idx + ')" title="Xóa khách"'
      + ' style="height:36px;width:36px;padding:0;font-size:15px;background:#fff5f5;border:1px solid #fecaca;color:#ef4444;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s,opacity .15s;">'
      + '<i class="fas fa-trash-alt"></i></button>'
    + '</div>'

  + '</div>'

  // gc-sub-row đã chuyển thành block chung ở footer — không render per-guest anymore

  // ── PHẦN MỞ RỘNG — Email + Ghi chú (toggle bằng dấu 3 chấm) ──
  + '<div class="gc-detail-wrap">'
    + '<div class="gc-detail">'
      + '<div style="display:flex;flex-direction:column;gap:2px;min-width:150px;flex:1;">'
        + '<label style="' + lbl + '">Email</label>'
        + '<input type="email" class="gc-email" style="' + sInp + '" placeholder="Email (nếu có)" value="' + _esc(prefill.email || '') + '" />'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;flex:2;min-width:140px;">'
        + '<label style="' + lbl + '">Ghi chú khách</label>'
        + '<input class="gc-customer-note" readonly style="' + sInp + 'background:#f8fafc;color:#6b7280;cursor:default;" placeholder="Chưa có ghi chú từ hồ sơ" value="' + _esc(prefill.customerNote || '') + '" title="Ghi chú lâu dài từ hồ sơ khách — chỉnh sửa tại trang Quản lý khách hàng" />'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;flex:2;min-width:140px;">'
        + '<label style="' + lbl + '">Ghi chú nội bộ</label>'
        + '<input class="gc-staff-note" style="' + sInp + '" placeholder="Chỉ nhân viên thấy..." value="' + _esc(prefill.staffNote || '') + '" />'
      + '</div>'
    + '</div>'
  + '</div>';

  // Bind events
  var roomSel = item.querySelector('.gc-room-select');
  if (roomSel) {
    roomSel.addEventListener('change', function() {
      item.dataset.slotRoom = roomSel.value;
      var roomInp = item.querySelector('.gc-room');
      if (roomInp) roomInp.value = roomSel.value;
      _markRowValidity(item);
      _updateGuestProgress();
    });
  }

  // Bind date input event
  var dateInp = item.querySelector('.gc-date-input');
  var dateHid = item.querySelector('.gc-date');
  if (dateInp) {
    dateInp.addEventListener('change', function() {
      var newDate = dateInp.value;
      item.dataset.slotDate = newDate;
      if (dateHid) dateHid.value = newDate;
      _markRowValidity(item);
      _updateGuestProgress();
    });
  }

  var svcSel = item.querySelector('.gc-service');
  var varSel = item.querySelector('.gc-variant');
  if (svcSel) {
    svcSel.addEventListener('change', function() {
      svcSel.style.borderColor = svcSel.value ? '#d1d5db' : '';
      svcSel.style.background  = '#fff';
      _loadGuestVariants(item, svcSel.value, null);
      _markRowValidity(item);
      _updateGuestProgress();
    });
  }
  if (varSel) {
    varSel.addEventListener('change', function() {
      varSel.style.borderColor = varSel.value ? '#d1d5db' : '';
      varSel.style.background  = '#fff';
      varSel.style.color       = varSel.value ? '#111827' : '#9ca3af';
      _updateGuestEndTime(item);
      _markRowValidity(item);
      _updateGuestProgress();
      _updateGuestPayFinal(item);
    });
  }
  var nameInp = item.querySelector('.gc-name');
  if (nameInp) nameInp.addEventListener('input', function() {
    nameInp.style.borderColor = nameInp.value.trim() ? '#d1d5db' : '';
    nameInp.style.background  = '#fff';
    _updateGuestProgress();
  });

  // Checkbox "= người đặt" — sync tên + SĐT + email từ booker khi tick
  var sameChk = item.querySelector('.gc-same-as-booker');
  if (sameChk) {
    sameChk.addEventListener('change', function() {
      var nameI  = item.querySelector('.gc-name');
      var phoneI = item.querySelector('.gc-phone');
      var emailI = item.querySelector('.gc-email');
      var noteI  = item.querySelector('.gc-customer-note');
      if (sameChk.checked) {
        if (nameI)  nameI.value  = document.getElementById('bookerName')?.value.trim()  || '';
        if (phoneI) phoneI.value = document.getElementById('bookerPhone')?.value.trim() || '';
        if (emailI) emailI.value = document.getElementById('bookerEmail')?.value.trim() || '';
        if (nameI)  nameI.readOnly  = true;
        if (phoneI) phoneI.readOnly = true;
        // Ghi chú khách: khi tick "= người đặt", giữ nguyên giá trị hiện tại
        // (đã được BE populate đúng từ profile người đặt nếu có)
      } else {
        if (nameI)  { nameI.value  = ''; nameI.readOnly  = false; }
        if (phoneI) { phoneI.value = ''; phoneI.readOnly = false; }
        if (emailI) emailI.readOnly = false;
        // Bỏ tick → khách là người khác, xóa ghi chú khách vì chưa biết profile của họ
        if (noteI)  noteI.value = '';
      }
      _updateGuestProgress();
    });
  }

  // Bind gc-pay change → show/hide payment fields
  var paySel = item.querySelector('.gc-pay');
  if (paySel) {
    paySel.addEventListener('change', function() { _onGuestPayChange(item); });
  }

  // ── Bind time inputs — sync về hidden fields + dataset ──
  var startInp = item.querySelector('.gc-time-input');
  var timeHid  = item.querySelector('.gc-time');
  var endHid   = item.querySelector('.gc-time-end');

  function _syncTimeDisplay() {
    var disp = item.querySelector('.gc-time-range-display');
    if (!disp) return;
    var s = startInp ? startInp.value : '';
    // Giờ kết thúc luôn tính từ giờ bắt đầu + duration
    var varSel = item.querySelector('.gc-variant');
    var dur = 60;
    if (varSel && varSel.selectedIndex >= 0) {
      var opt = varSel.options[varSel.selectedIndex];
      dur = opt?.dataset?.duration ? Number(opt.dataset.duration) : 60;
    }
    var e = s ? addMinutesToTime(s, dur) : '--:--';
    disp.innerHTML = (s || '--:--') + '<span class="gc-time-range-sep"> – </span>' + e;
  }

  if (startInp) {
    startInp.addEventListener('change', function() {
      var v = startInp.value;
      item.dataset.slotTime = v;
      if (timeHid) timeHid.value = v;
      // Tính lại end từ variant duration (luôn luôn tính)
      var varSel2 = item.querySelector('.gc-variant');
      var dur2 = 60;
      if (varSel2 && varSel2.selectedIndex >= 0) {
        var opt2 = varSel2.options[varSel2.selectedIndex];
        dur2 = opt2?.dataset?.duration ? Number(opt2.dataset.duration) : 60;
      }
      var newEnd = addMinutesToTime(v, dur2);
      item.dataset.endTime = newEnd;
      if (endHid) endHid.value = newEnd;
      _syncTimeDisplay();
      _markRowValidity(item);
      _updateGuestProgress();
    });
  }

  // ── Click vào cụm time-range → toggle editing mode ──
  var timeRangeField = item.querySelector('.gc-time-range-field');
  if (timeRangeField) {
    timeRangeField.addEventListener('click', function(e) {
      if (e.target.tagName === 'INPUT') return; // đang trong input thì không toggle
      var isEditing = timeRangeField.classList.contains('is-editing');
      if (!isEditing) {
        timeRangeField.classList.add('is-editing');
        // Focus vào input giờ bắt đầu
        setTimeout(function() {
          var inp = timeRangeField.querySelector('.gc-time-input');
          if (inp) inp.focus();
        }, 30);
      }
    });
    // Click ra ngoài → đóng editing
    document.addEventListener('click', function _closeTimeRange(e) {
      if (!timeRangeField.contains(e.target)) {
        timeRangeField.classList.remove('is-editing');
      }
    });
    // Enter từ input → đóng editing
    var startTimeInp = timeRangeField.querySelector('.gc-time-input');
    if (startTimeInp) {
      startTimeInp.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          timeRangeField.classList.remove('is-editing');
        }
      });
    }
  }

  return item;
}

function addGuestCard(prefill = {}) {
  const list = document.getElementById('guestList');
  if (!list) return;
  const idx  = _guestCount++;
  const item = _buildGuestItem(idx, prefill);
  list.appendChild(item);

  if (prefill.serviceId) {
    const svcSel = item.querySelector('.gc-service');
    if (svcSel) {
      svcSel.value = prefill.serviceId;
      _loadGuestVariants(item, prefill.serviceId, prefill.variantId);
    }
  }

  // Set status / payStatus nếu có prefill
  if (prefill.apptStatus) {
    const statusSel = item.querySelector('.gc-status');
    if (statusSel) statusSel.value = prefill.apptStatus;
  }
  if (prefill.payStatus) {
    const paySel = item.querySelector('.gc-pay');
    if (paySel) {
      paySel.value = prefill.payStatus;
      _onGuestPayChange(item);
    }
  }

  // Set room/date/time từ prefill nếu có (edit mode)
  if (prefill.roomId) {
    item.dataset.slotRoom = prefill.roomId;
    const roomInp = item.querySelector('.gc-room');
    if (roomInp) roomInp.value = prefill.roomId;
    // Cập nhật select phòng
    const roomSel = item.querySelector('.gc-room-select');
    if (roomSel) roomSel.value = prefill.roomId;
  }
  if (prefill.date) {
    item.dataset.slotDate = prefill.date;
    const dateInp = item.querySelector('.gc-date');
    if (dateInp) dateInp.value = prefill.date;
  }
  if (prefill.time) {
    item.dataset.slotTime = prefill.time;
    const timeHid = item.querySelector('.gc-time');
    if (timeHid) timeHid.value = prefill.time;
    // Sync editable start input
    const startInp = item.querySelector('.gc-time-input');
    if (startInp) startInp.value = prefill.time;
  }

  _renumberGuests();
  _markRowValidity(item);
  _updateGuestProgress();
  _updateDeleteBtnState();
}

window.removeGuestCard = function(idx) {
  const items = _getGuestItems();
  if (items.length <= 1) {
    showToast('warning', 'Không thể xóa', 'Phải có ít nhất 1 khách sử dụng dịch vụ');
    return;
  }
  const item = _getGuestItem(idx);
  if (item) item.remove();
  _renumberGuests();
  _updateGuestProgress();
  _updateDeleteBtnState();
};

/** Điền thông tin từ người đặt vào 1 guest row */
window.fillGuestFromBooker = function(idx) {
  const item = _getGuestItem(idx);
  if (!item) return;
  const bookerName  = document.getElementById('bookerName')?.value.trim() || '';
  const bookerPhone = document.getElementById('bookerPhone')?.value.trim() || '';
  const bookerEmail = document.getElementById('bookerEmail')?.value.trim() || '';
  const nameInp  = item.querySelector('.gc-name');
  const phoneInp = item.querySelector('.gc-phone');
  const emailInp = item.querySelector('.gc-email');
  if (nameInp)  nameInp.value  = bookerName;
  if (phoneInp) phoneInp.value = bookerPhone;
  if (emailInp) emailInp.value = bookerEmail;
};

/** Xóa thông tin cá nhân của 1 guest row */
window.clearGuestInfo = function(idx) {
  const item = _getGuestItem(idx);
  if (!item) return;
  const nameInp  = item.querySelector('.gc-name');
  const phoneInp = item.querySelector('.gc-phone');
  const emailInp = item.querySelector('.gc-email');
  if (nameInp)  nameInp.value  = '';
  if (phoneInp) phoneInp.value = '';
  if (emailInp) emailInp.value = '';
};

function _renumberGuests() {
  _getGuestItems().forEach((item, i) => {
    const numEl = item.querySelector('.gc-num');
    if (numEl) numEl.textContent = i + 1;
  });
}

/** Disable nút xóa khi chỉ còn 1 dòng, enable lại khi có nhiều hơn */
function _updateDeleteBtnState() {
  const items = _getGuestItems();
  const onlyOne = items.length <= 1;
  items.forEach(item => {
    const btn = item.querySelector('.gc-delete-btn');
    if (!btn) return;
    btn.disabled = onlyOne;
    btn.style.opacity  = onlyOne ? '0.3' : '1';
    btn.style.cursor   = onlyOne ? 'not-allowed' : 'pointer';
  });
}

// Deprecated — kept for compatibility, now handled by event listeners on each item
window.onGuestServiceChange = function(sel, idx) {
  const item = _getGuestItem(idx);
  if (!item) return;
  _loadGuestVariants(item, sel.value, null);
  _refreshGuestHeader(item);
  _updateGuestProgress();
  _updateSlotSummary();
};

function _collectGuestCards() {
  const bookerNote = document.getElementById('bookerNote')?.value.trim() || '';
  // Đọc trạng thái & thanh toán từ block footer
  const sharedStatus  = document.getElementById('sharedApptStatus')?.value  || 'NOT_ARRIVED';
  const sharedPay     = document.getElementById('sharedPayStatus')?.value   || 'UNPAID';
  const sharedMethod  = document.getElementById('sharedPayMethod')?.value   || '';
  const sharedAmount  = document.getElementById('sharedPayAmount')?.value   || 0;
  return _getGuestItems().map(item => {
    const variantSel = item.querySelector('.gc-variant');
    const selectedVariantOpt = variantSel?.options[variantSel.selectedIndex];
    const guestStaffNote = item.querySelector('.gc-staff-note')?.value.trim() || '';
    return {
      name:               item.querySelector('.gc-name')?.value.trim() || '',
      phone:              item.querySelector('.gc-phone')?.value.trim() || '',
      email:              item.querySelector('.gc-email')?.value.trim() || '',
      serviceId:          item.querySelector('.gc-service')?.value || '',
      variantId:          variantSel?.value || '',
      roomId:             item.dataset.slotRoom || item.querySelector('.gc-room')?.value || '',
      date:               item.dataset.slotDate || item.querySelector('.gc-date')?.value || '',
      time:               item.querySelector('.gc-time-input')?.value || item.dataset.slotTime || item.querySelector('.gc-time')?.value || '',
      apptStatus:         sharedStatus,
      payStatus:          sharedPay,
      paymentMethod:      sharedMethod,
      paymentAmount:      sharedAmount,
      paymentRecordedNo:  '',
      paymentNote:        '',
      note:               bookerNote,
      staffNote:          guestStaffNote,
      _duration:          selectedVariantOpt?.dataset?.duration || 60,
      _finalAmount:       item.dataset.finalAmount || 0,
    };
  });
}

/** Áp dụng service/variant cho tất cả guest rows */
function _initApplyAllBar() {
  const applyAllSvc = document.getElementById('applyAllService');
  if (applyAllSvc) {
    applyAllSvc.innerHTML = '<option value="">Dịch vụ</option>' +
      SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }

  if (applyAllSvc) {
    applyAllSvc.onchange = function() {
      const varSel = document.getElementById('applyAllVariant');
      if (!varSel) return;
      varSel.innerHTML = '<option value="">-- Gói --</option>';
      varSel.disabled  = true;
      varSel.style.color      = '#9ca3af';
      varSel.style.background = '#f9fafb';
      const svc = SERVICES.find(s => s.id == this.value);
      if (!svc || !svc.variants?.length) return;
      svc.variants.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = variantLabel(v);
        opt.dataset.duration = v.duration_minutes;
        varSel.appendChild(opt);
      });
      varSel.disabled         = false;
      varSel.style.color      = '#111827';
      varSel.style.background = '#fff';
      varSel.style.opacity    = '1';
      if (svc.variants.length === 1) varSel.value = svc.variants[0].id;
    };
  }

  const btnApply = document.getElementById('btnApplyAll');
  if (btnApply) {
    btnApply.onclick = function() {
      const svcVal = document.getElementById('applyAllService')?.value;
      const varVal = document.getElementById('applyAllVariant')?.value;
      if (!svcVal) return;
      _getGuestItems().forEach(item => {
        const svcSel = item.querySelector('.gc-service');
        if (svcSel) {
          svcSel.value = svcVal;
          _loadGuestVariants(item, svcVal, varVal || null);
        }
        _markRowValidity(item);
      });
      _updateGuestProgress();
    };
  }

  const btnAdd = document.getElementById('btnAddGuest');
  if (btnAdd) {
    btnAdd.onclick = function() {
      _savedBookerInfo = {
        name:   document.getElementById('bookerName')?.value  || '',
        phone:  document.getElementById('bookerPhone')?.value || '',
        email:  document.getElementById('bookerEmail')?.value || '',
        source: document.getElementById('bookerSource')?.value || 'DIRECT',
        note:   document.getElementById('bookerNote')?.value  || '',
      };
      _addingSlotMode = true;
      const modalEl = document.getElementById("apptModal");
      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.hide();
      showToast('info', 'Chọn thêm slot', 'Hãy chọn thêm 1 slot trên lịch để thêm khách mới, rồi bấm "Tiếp tục"');
    };
  }

  // Không auto-fill booker → guest: dữ liệu khách và người đặt hoàn toàn độc lập
}

// ── Helpers để show/hide shared form ──
function _showSharedForm() {
  const f = document.getElementById('apptForm');
  if (f) { f.style.display = 'flex'; }
}
function _hideSharedForm() {
  const f = document.getElementById('apptForm');
  if (f) { f.style.display = 'none'; }
}
function _setCreateOnlyVisible(visible) {
  const bar = document.getElementById('createOnlyBar');
  if (bar) bar.style.display = visible ? 'flex' : 'none';
  const progress = document.getElementById('guestProgressLabel')?.closest('div[style*="margin-left:auto"]');
  // progress bar nằm trong createOnlyBar nên tự ẩn theo
}

function openCreateModal(prefill={}){
  const modalEl = document.getElementById("apptModal");
  const modalTitle = document.getElementById("modalTitle");
  const apptId = document.getElementById("apptId");
  const btnDelete = document.getElementById("btnDelete");
  const dayPicker = document.getElementById("dayPicker");

  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");
  document.getElementById('btnRebook')?.classList.add('d-none');

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Tạo lịch hẹn";

  // Hiện shared form, bật create-only bar
  _showSharedForm();
  _setCreateOnlyVisible(true);

  // Label panel
  const lbl = document.getElementById('bookerPanelLabel');
  if (lbl) lbl.textContent = 'Người đặt lịch';

  // Reset người đặt
  document.getElementById('bookerName').value   = '';
  document.getElementById('bookerPhone').value  = '';
  document.getElementById('bookerEmail').value  = '';
  document.getElementById('bookerSource').value = 'DIRECT';
  const bookerNoteEl = document.getElementById('bookerNote');
  if (bookerNoteEl) bookerNoteEl.value = '';

  // Reset danh sách khách
  _guestCount = 0;
  _pendingBlockMap = [];
  document.getElementById('guestList').innerHTML = '';

  if (prefill._fromRebook && prefill._booker) {
    // Tạo lại lịch từ lịch cũ — pre-fill booker + khách, KHÔNG copy ngày/giờ/phòng
    _isRebookMode = true;  // UC 14.3 — đánh dấu để hiển thị đúng message sau khi tạo
    const rb = prefill._booker;
    document.getElementById('bookerName').value   = rb.name   || '';
    document.getElementById('bookerPhone').value  = rb.phone  || '';
    document.getElementById('bookerEmail').value  = rb.email  || '';
    document.getElementById('bookerSource').value = rb.source || 'DIRECT';
    // Guest card trống slot — admin bắt buộc chọn ngày/giờ/phòng mới
    // ✅ Thêm ngày mặc định (hôm nay) để admin dễ chỉnh sửa
    addGuestCard({
      name:      prefill._guest?.name      || '',
      phone:     prefill._guest?.phone     || '',
      email:     prefill._guest?.email     || '',
      serviceId: prefill._guest?.serviceId || null,
      variantId: prefill._guest?.variantId || null,
      date:      dayPicker.value,  // ✅ Thêm ngày mặc định
    });
    modalTitle.textContent = 'Đặt lại lịch hẹn';
    // Ẩn nút "Thêm khách" khi đặt lại lịch (chỉ có 1 khách)
    _setCreateOnlyVisible(false);
    showToast('info', 'Đặt lại', 'Vui lòng chọn ngày, giờ và phòng mới');
  } else if (prefill._fromPending && prefill._blocks && prefill._blocks.length > 0) {
    _isRebookMode = false;
    if (prefill._restoreBooker) {
      const rb = prefill._restoreBooker;
      document.getElementById('bookerName').value   = rb.name   || '';
      document.getElementById('bookerPhone').value  = rb.phone  || '';
      document.getElementById('bookerEmail').value  = rb.email  || '';
      document.getElementById('bookerSource').value = rb.source || 'DIRECT';
      const bookerNoteEl2 = document.getElementById('bookerNote');
      if (bookerNoteEl2) bookerNoteEl2.value = rb.note || '';
    }
    prefill._blocks.forEach(pb => {
      addGuestCard({ date: pb.day, time: pb.time, roomId: pb.roomId, pendingDuration: pb.duration });
    });
  } else {
    _isRebookMode = false;
    addGuestCard({
      date: prefill.day || dayPicker.value,
      time: prefill.time || '',
      roomId: prefill.roomId || ''
    });
  }

  _initApplyAllBar();
  _updateGuestProgress();
  _updateSlotSummary();
  _resetAllCustomerState();

  // Hiện block trạng thái & thanh toán, reset về mặc định
  _showSharedStatusBlock('NOT_ARRIVED', 'UNPAID');

  let modal = null;
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (!modal) return;
  modal.show();
}

/** Mở modal tạo lịch từ pending blocks đã chọn trên grid */
function openCreateModalFromPending() {
  if (!pendingBlocks.length) return;

  if (_addingSlotMode && _savedBookerInfo) {
    // Quay lại modal sau khi user chọn thêm slot — khôi phục booker info
    _addingSlotMode = false;
    openCreateModal({ _fromPending: true, _blocks: [...pendingBlocks], _restoreBooker: _savedBookerInfo });
    _savedBookerInfo = null;
  } else {
    openCreateModal({ _fromPending: true, _blocks: [...pendingBlocks] });
  }
}

async function openEditModal(id){
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  const modalError = document.getElementById("modalError");
  if (result.success && result.appointment) openEditModalWithData(result.appointment);
  else { const a = APPOINTMENTS.find(x=>x.id===id); if (a) openEditModalWithData(a); else { modalError.textContent = "Không tìm thấy lịch hẹn"; modalError.classList.remove("d-none"); } }
}

function openEditModalWithData(a){
  const modalEl = document.getElementById("apptModal");
  const modalTitle = document.getElementById("modalTitle");
  const apptId = document.getElementById("apptId");
  const btnDelete = document.getElementById("btnDelete");
  const dayPicker = document.getElementById("dayPicker");

  resetModalError();
  modalTitle.textContent = `Chỉnh sửa • ${a.id}`;
  apptId.value = a.id;

  // Hiện nút "Đặt lại" nếu lịch đã hủy hoặc đã từ chối
  const btnRebook = document.getElementById('btnRebook');
  const st = (a.apptStatus || '').toUpperCase();

  // Ẩn nút Xóa nếu lịch đã COMPLETED — không cho phép xóa lịch đã hoàn thành
  if (st === 'COMPLETED') {
    btnDelete.classList.add("d-none");
  } else {
    btnDelete.classList.remove("d-none");
  }
  if (btnRebook) {
    if (st === 'CANCELLED' || st === 'REJECTED') {
      btnRebook.classList.remove('d-none');
    } else {
      btnRebook.classList.add('d-none');
    }
  }

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Lưu lịch hẹn";

  // Hiện shared form, ẩn create-only bar
  _showSharedForm();
  _setCreateOnlyVisible(false);

  // Dùng chung block trạng thái & thanh toán với create mode, nhưng load đúng dữ liệu hiện tại.
  _showSharedStatusBlock(a.apptStatus || 'NOT_ARRIVED', a.payStatus || 'UNPAID');

  // Label panel
  const lbl = document.getElementById('bookerPanelLabel');
  if (lbl) lbl.textContent = 'Người đặt lịch';

  // Reset guest list — chỉ 1 row cho edit
  _guestCount = 0;
  _pendingBlockMap = [];
  document.getElementById('guestList').innerHTML = '';
  _resetAllCustomerState();
  document.getElementById('selectedCustomerId').value = a.customerId || '';

  // Điền booker panel từ appointment data — dùng đúng booker_* fields
  document.getElementById('bookerName').value   = a.bookerName  || '';
  document.getElementById('bookerPhone').value  = a.bookerPhone || '';
  document.getElementById('bookerEmail').value  = a.bookerEmail || '';
  document.getElementById('bookerSource').value = a.source || 'DIRECT';
  const bookerNoteEl = document.getElementById('bookerNote');
  if (bookerNoteEl) bookerNoteEl.value = a.note || '';

  // Thêm 1 guest card duy nhất với đầy đủ data
  addGuestCard({
    name:         a.customerName || '',
    phone:        a.phone || '',
    email:        a.email || '',
    serviceId:    a.serviceId,
    variantId:    a.variantId,
    roomId:       a.roomCode || a.roomId || '',
    date:         a.date || '',
    time:         a.start || '',
    apptStatus:   a.apptStatus || 'NOT_ARRIVED',
    payStatus:    a.payStatus || 'UNPAID',
    note:         a.note || '',
    staffNote:    a.staffNotes || '',
    customerNote: a.customerNote || '',
    _editMode:    true,
  });

  let modal = null;
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (modal) modal.show();
}

const btnSave = document.getElementById("btnSave");
btnSave.addEventListener("click", ()=> {
  // Trigger submit trên form
  const f = document.getElementById('apptForm');
  if (f) f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
});

// Validate Form
document.getElementById('apptForm').addEventListener("submit", async (e)=>{
  e.preventDefault();
  const modalError = document.getElementById("modalError");
  const dayPicker = document.getElementById("dayPicker");

  if (isSubmitting) return;
  resetModalError();

  const apptId = document.getElementById("apptId");
  const id = apptId.value.trim();

  // ── EDIT MODE — đọc data từ guest card duy nhất ──
  if (id) {
    const cards = _collectGuestCards();
    const g = cards[0];
    if (!g) { modalError.textContent = "Lỗi: không tìm thấy dữ liệu"; modalError.classList.remove("d-none"); return; }

    const nameVal   = document.getElementById('bookerName')?.value.trim() || '';
    const phoneVal  = document.getElementById('bookerPhone')?.value.trim() || '';
    const emailVal  = document.getElementById('bookerEmail')?.value.trim() || '';
    const sourceVal = document.getElementById('bookerSource')?.value || 'DIRECT';

    if (!nameVal) { modalError.textContent = "Vui lòng nhập họ tên người đặt"; modalError.classList.remove("d-none"); return; }
    if (!phoneVal || !isValidPhone(phoneVal)) { modalError.textContent = "Số điện thoại không hợp lệ"; modalError.classList.remove("d-none"); return; }
    if (emailVal && !isValidEmail(emailVal)) { modalError.textContent = "Email không hợp lệ"; modalError.classList.remove("d-none"); return; }
    if (!g.name || !g.name.trim()) { modalError.textContent = "Vui lòng nhập tên khách"; modalError.classList.remove("d-none"); return; }
    if (g.phone && !isValidPhone(g.phone)) { modalError.textContent = "Số điện thoại khách không hợp lệ"; modalError.classList.remove("d-none"); return; }
    if (g.email && !isValidEmail(g.email)) { modalError.textContent = "Email không hợp lệ"; modalError.classList.remove("d-none"); return; }
    if (g.serviceId && !g.variantId) { modalError.textContent = "Vui lòng chọn gói dịch vụ"; modalError.classList.remove("d-none"); return; }

    // Validate trạng thái "Hoàn thành"
    const editApptStatus = document.getElementById('sharedApptStatus')?.value || g.apptStatus || '';
    const editPayStatus  = document.getElementById('sharedPayStatus')?.value  || g.payStatus  || '';
    if (editApptStatus === 'COMPLETED' && (!g.serviceId || !editPayStatus || editPayStatus === 'UNPAID')) {
      modalError.textContent = "Không thể hoàn thành lịch hẹn khi chưa có dịch vụ hoặc chưa có thông tin thanh toán";
      modalError.classList.remove("d-none"); return;
    }

    const payload = {
      customerId:   Number(document.getElementById("selectedCustomerId")?.value) || null,
      bookerName:   nameVal,
      bookerPhone:  phoneVal.replace(/\D/g, ""),
      bookerEmail:  emailVal,
      customerName: g.name || '',
      phone:        (g.phone || '').replace(/\D/g, ""),
      email:        g.email || '',
      variantId:    g.variantId || null,
      roomId:       g.roomId,
      date:         g.date,
      time:         g.time,
      note:         document.getElementById('bookerNote')?.value.trim() || '',
      apptStatus:   g.apptStatus,
      payStatus:    g.payStatus,
      status:       g.apptStatus,
      payment_status: g.payStatus,
      paymentData:  {
        payment_method: g.paymentMethod || 'CASH',
        amount: g.paymentAmount || 0,
      },
      source:       sourceVal,
      staffNote:    g.staffNote || '',
    };

    isSubmitting = true;
    setButtonLoading(btnSave, 'Đang cập nhật...');
    try {
      const result = await apiPost(`${API_BASE}/appointments/${id}/update/`, payload);
      if (result.success) {
        const modalEl = document.getElementById("apptModal");
        let modal = null;
        if (modalEl) {
          const existing = bootstrap.Modal.getInstance(modalEl);
          modal = existing || new bootstrap.Modal(modalEl);
        }
        if (modal) modal.hide();
        if (dayPicker.value !== g.date) dayPicker.value = g.date;
        await refreshData();
        await renderWebRequests();
        showToast("success", "Thành công", result.message || "Cập nhật lịch hẹn thành công");
      } else {
        // UC 14.3 — phân biệt lỗi conflict khi xác nhận vs lỗi chung
        const errLower = (result.error || '').toLowerCase();
        const isConflict = errLower.includes('trùng') || errLower.includes('đầy') || errLower.includes('khả dụng') || errLower.includes('capacity') || errLower.includes('conflict');
        modalError.textContent = isConflict ? MSG_APPROVE_CONFLICT : (result.error || MSG_WEB_GENERIC_ERR);
        modalError.classList.remove("d-none");
      }
    } catch(err) {
      modalError.textContent = MSG_WEB_GENERIC_ERR;
      modalError.classList.remove("d-none");
    } finally {
      isSubmitting = false;
      resetButton(btnSave);
    }
    return;
  }

  // ── CREATE MODE (batch) ──
  const bookerName  = document.getElementById('bookerName')?.value.trim() || '';
  const bookerPhone = document.getElementById('bookerPhone')?.value.trim() || '';
  if (!bookerName) {
    modalError.textContent = "Vui lòng nhập họ tên người đặt";
    modalError.classList.remove("d-none");
    return;
  }
  if (!bookerPhone || !isValidPhone(bookerPhone)) {
    modalError.textContent = "Số điện thoại không hợp lệ";
    modalError.classList.remove("d-none");
    return;
  }
  const bookerEmail = document.getElementById('bookerEmail')?.value.trim() || '';
  if (bookerEmail && !isValidEmail(bookerEmail)) {
    modalError.textContent = "Email không hợp lệ";
    modalError.classList.remove("d-none");
    return;
  }

  const guestCards = _collectGuestCards();
  if (!guestCards.length) {
    modalError.textContent = "Vui lòng thêm ít nhất 1 khách";
    modalError.classList.remove("d-none");
    return;
  }

  const VALID_METHODS = ['CASH', 'CARD', 'BANK_TRANSFER', 'E_WALLET'];
  // Validate thanh toán chung
  const sharedPayVal    = document.getElementById('sharedPayStatus')?.value || 'UNPAID';
  const sharedMethodVal = document.getElementById('sharedPayMethod')?.value || '';
  if (sharedPayVal === 'PAID') {
    if (!sharedMethodVal || !VALID_METHODS.includes(sharedMethodVal)) {
      modalError.textContent = 'Vui lòng chọn phương thức thanh toán';
      modalError.classList.remove('d-none');
      return;
    }
  }
  for (let i = 0; i < guestCards.length; i++) {
    const g = guestCards[i];
    const label = `Khách ${i + 1}`;
    const gItem = _getGuestItems()[i];
    if (!g.name || !g.name.trim()) {
      if (gItem) _markRowError(gItem);
      modalError.textContent = `Vui lòng nhập tên khách`;
      modalError.classList.remove("d-none"); return;
    }
    if (g.phone && !isValidPhone(g.phone)) {
      modalError.textContent = `Số điện thoại khách không hợp lệ`;
      modalError.classList.remove("d-none"); return;
    }
    if (g.email && !isValidEmail(g.email)) {
      modalError.textContent = `Email không hợp lệ`;
      modalError.classList.remove("d-none"); return;
    }
    if (g.serviceId && !g.variantId) {
      modalError.textContent = `Vui lòng chọn gói dịch vụ`;
      modalError.classList.remove("d-none"); return;
    }
  }

  // Validate trạng thái "Hoàn thành"
  const createApptStatus = document.getElementById('sharedApptStatus')?.value || '';
  const createPayStatus  = document.getElementById('sharedPayStatus')?.value  || '';
  if (createApptStatus === 'COMPLETED') {
    const hasService = guestCards.some(g => g.serviceId);
    if (!hasService || !createPayStatus || createPayStatus === 'UNPAID') {
      modalError.textContent = "Không thể hoàn thành lịch hẹn khi chưa có dịch vụ hoặc chưa có thông tin thanh toán";
      modalError.classList.remove("d-none"); return;
    }
  }

  const batchPayload = {
    booker: {
      name:   bookerName,
      phone:  bookerPhone.replace(/\D/g, ''),
      email:  document.getElementById('bookerEmail')?.value.trim() || '',
      source: document.getElementById('bookerSource')?.value || 'DIRECT',
    },
    guests: guestCards,
  };

  isSubmitting = true;
  setButtonLoading(btnSave, 'Đang tạo lịch...');
  try {
    const result = await apiPost(`${API_BASE}/appointments/create-batch/`, batchPayload);
    if (result.success) {
      const modalEl = document.getElementById("apptModal");
      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.hide();
      _addingSlotMode = false;
      _savedBookerInfo = null;
      const firstDate = guestCards[0]?.date;
      if (firstDate && dayPicker.value !== firstDate) dayPicker.value = firstDate;
      clearPendingBlocks();
      await refreshData();
      await renderWebRequests();
      // UC 14.3 — phân biệt rebook vs tạo mới thông thường
      const successMsg = _isRebookMode ? MSG_REBOOK_SUCCESS : (result.message || 'Tạo lịch hẹn thành công');
      _isRebookMode = false;
      showToast("success", "Thành công", successMsg);
      if (result.errors?.length) {
        setTimeout(() => showToast("warning", "Một số lỗi", result.errors.join(' | ')), 1500);
      }
    } else {
      // UC 14.3 — chuẩn hóa lỗi conflict vs lỗi chung
      const errLower = (result.error || '').toLowerCase();
      const isConflict = errLower.includes('trùng') || errLower.includes('đầy') || errLower.includes('khả dụng') || errLower.includes('capacity') || errLower.includes('conflict');
      modalError.textContent = isConflict ? MSG_WEB_CONFLICT : (result.error || MSG_WEB_GENERIC_ERR);
      modalError.classList.remove("d-none");
    }
    } catch(err) {
      modalError.textContent = MSG_WEB_GENERIC_ERR;
      modalError.classList.remove("d-none");
  } finally {
    isSubmitting = false;
    resetButton(btnSave);
  }
});

// ===== NÚT ĐẶT LẠI trong modal =====
document.getElementById('btnRebook')?.addEventListener('click', async () => {
  const apptId = document.getElementById("apptId");
  const id = apptId.value.trim();
  if (!id) return;
  await rebookAppointment(id);
});

const btnDelete = document.getElementById("btnDelete");
btnDelete.addEventListener("click", async ()=>{
  const apptId = document.getElementById("apptId");
  const id = apptId.value.trim();
  if (isSubmitting || !id) return;

  // Đọc info từ guest card duy nhất (edit mode)
  const firstCard = _getGuestItems()[0];
  const customerNameVal = firstCard?.querySelector('.gc-name')?.value.trim()
    || document.getElementById('bookerName')?.value.trim() || '';
  const timeVal = firstCard?.dataset.slotTime || '';

  const infoEl = document.getElementById('deleteAppointmentInfo');
  if (infoEl) {
    const parts = [];
    if (customerNameVal) parts.push(customerNameVal);
    if (timeVal) parts.push(timeVal);
    infoEl.textContent = parts.join(' · ');
    infoEl.style.display = parts.length ? '' : 'none';
  }

  const deleteModal = new bootstrap.Modal(document.getElementById('deleteAppointmentModal'));
  const confirmDeleteBtn = document.getElementById('confirmDeleteAppointmentBtn');

  // Xử lý nút Xóa trong modal
  if (confirmDeleteBtn) {
    // Xóa event listener cũ (nếu có) để tránh trùng lặp
    const newBtn = confirmDeleteBtn.cloneNode(true);
    confirmDeleteBtn.parentNode.replaceChild(newBtn, confirmDeleteBtn);

    // Thêm event listener mới
    newBtn.addEventListener('click', async () => {
      // Đóng modal
      deleteModal.hide();

      // ===== BẬT LOADING STATE =====
      isSubmitting = true;
      showToast("warning", "Đang xử lý...", "Đang xóa lịch hẹn...");

      try {
        const result = await apiPost(`${API_BASE}/appointments/${id}/delete/`, {});
        if (result.success) {
          const modalEl = document.getElementById("apptModal");
          let modal = null;
          if (modalEl) {
            const existing = bootstrap.Modal.getInstance(modalEl);
            modal = existing || new bootstrap.Modal(modalEl);
          }
          if (modal) modal.hide();
          await refreshData();
          await renderWebRequests();  // Refresh lại tab Yêu cầu đặt lịch
          showToast("success", "Thành công", result.message || "Đã xóa lịch hẹn");
        } else {
          showToast("error","Lỗi", result.error || "Không thể xóa lịch hẹn");
          isSubmitting = false; // Reset khi lỗi
        }
      } catch (err) {
        console.error('Error:', err);
        showToast("error","Lỗi", "Xóa thất bại, vui lòng thử lại sau.");
        isSubmitting = false; // Reset khi lỗi
      } finally {
        // ===== TẮT LOADING STATE =====
        isSubmitting = false;
      }
    });

    // Cập nhật reference
    document.getElementById('confirmDeleteAppointmentBtn').id = 'confirmDeleteAppointmentBtn';
  }

  // Mở modal
  deleteModal.show();
});

// ============================================================
// SECTION 12: DATE NAVIGATION
// ============================================================
const dayPicker = document.getElementById("dayPicker");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnToday = document.getElementById("btnToday");

function setDay(d){ dayPicker.value = d; refreshData(); }
function todayISO(){ const t = new Date(); return `${t.getFullYear()}-${pad2(t.getMonth()+1)}-${pad2(t.getDate())}`; }
function shiftDay(delta){ const d = new Date(dayPicker.value + "T00:00:00"); d.setDate(d.getDate()+delta); setDay(`${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`); }

// ===== REFRESH DATA =====
async function refreshData(){
  try {
    await loadAppointments(dayPicker.value);
  } catch (err) {
    // Network lỗi hoàn toàn (offline, DNS fail...) — UC 14.2 exception flow 5a
    console.error('refreshData error:', err);
    APPOINTMENTS = [];
    _gridLoadError = true;
    showToast('error', 'Lỗi', MSG_LOAD_APPT_ERROR);
  }
  renderGrid();
}

// ============================================================
// SECTION 13: SEARCH MODAL
// ============================================================
function initSearchModal() {
  const searchModalEl = document.getElementById('searchModal');
  if (!searchModalEl) return;

  const searchModal = new bootstrap.Modal(searchModalEl);
  const resetSearchModal = () => _resetSearchModalState(searchModalEl);

  searchModalEl.addEventListener('hidden.bs.modal', resetSearchModal);

  // Nút mở modal
  const btnOpen = document.getElementById('btnOpenSearch');
  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      _fillSearchDropdowns();
      searchModal.show();
    });
  }

  // Nút Tìm kiếm
  const btnDo = document.getElementById('btnDoSearch');
  if (btnDo) btnDo.addEventListener('click', () => _doSearch());

  // Nút Đặt lại
  const btnReset = document.getElementById('btnResetSearch');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      _resetSearchModalState(searchModalEl);
      refreshData();        // Refresh grid lịch theo phòng về toàn bộ danh sách
      renderWebRequests();  // Refresh tab Yêu cầu đặt lịch
    });
  }

  // Enter trong các input → trigger search
  ['srchName','srchPhone','srchEmail'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') _doSearch(); });
  });
}

function _resetSearchModalState(searchModalEl) {
  const root = searchModalEl || document.getElementById('searchModal');
  if (!root) return;

  root.querySelectorAll('input').forEach(input => {
    if (input.type === 'checkbox' || input.type === 'radio') input.checked = false;
    else input.value = '';
  });

  root.querySelectorAll('select').forEach(select => {
    select.selectedIndex = 0;
  });

  delete root.dataset.currentFilters;
  _setSearchWarning(false);

  const results = root.querySelector('#srchResults');
  if (results) {
    results.innerHTML = `
      <div class="text-center text-muted py-5" id="srchPlaceholder">
        <i class="fas fa-search fa-2x mb-2 d-block opacity-25"></i>
        Nhập điều kiện và bấm Tìm kiếm
      </div>`;
  }
}

function _fillSearchDropdowns() {
  // Điền dropdown dịch vụ
  const srchSvc = document.getElementById('srchService');
  if (srchSvc && srchSvc.options.length <= 1 && SERVICES.length) {
    SERVICES.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.name;
      srchSvc.appendChild(opt);
    });
  }
  // Điền dropdown phòng
  const srchRoom = document.getElementById('srchRoom');
  if (srchRoom && srchRoom.options.length <= 1 && ROOMS.length) {
    ROOMS.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = `Phòng ${r.name}`;
      srchRoom.appendChild(opt);
    });
  }
}

function _setSearchWarning(show, text) {
  const warn = document.getElementById('srchWarning');
  const warnText = document.getElementById('srchWarningText');
  if (!warn) return;
  if (show) {
    if (warnText && text) warnText.textContent = text;
    warn.classList.remove('d-none');
  } else {
    warn.classList.add('d-none');
  }
}

async function _doSearch() {
  const name      = (document.getElementById('srchName')     || {}).value?.trim() || '';
  const phone     = (document.getElementById('srchPhone')    || {}).value?.trim() || '';
  const email     = (document.getElementById('srchEmail')    || {}).value?.trim() || '';
  const code      = (document.getElementById('srchCode')     || {}).value?.trim() || '';
  const service   = (document.getElementById('srchService')  || {}).value || '';
  const status    = (document.getElementById('srchStatus')   || {}).value || '';
  const source    = (document.getElementById('srchSource')   || {}).value || '';
  const room      = (document.getElementById('srchRoom')     || {}).value || '';
  const dateFrom  = (document.getElementById('srchDateFrom') || {}).value || '';
  const dateTo    = (document.getElementById('srchDateTo')   || {}).value || '';

  const hasCondition = name || phone || email || code || service || status || source || room || dateFrom || dateTo;
  if (!hasCondition) {
    _setSearchWarning(true, 'Vui lòng nhập điều kiện tìm kiếm');
    return;
  }

  if (dateFrom && dateTo && dateFrom > dateTo) {
    _setSearchWarning(true, 'Khoảng ngày tìm kiếm không hợp lệ.');
    return;
  }

  _setSearchWarning(false);

  const resultsEl = document.getElementById('srchResults');
  if (resultsEl) {
    resultsEl.innerHTML = `<div class="text-center text-muted py-5"><i class="fas fa-spinner fa-spin fa-2x mb-2 d-block"></i>Đang tìm kiếm...</div>`;
  }

  const params = new URLSearchParams();
  if (name)     params.append('name', name);
  if (phone)    params.append('phone', phone);
  if (email)    params.append('email', email);
  if (code)     params.append('code', code);
  if (service)  params.append('service', service);
  if (status)   params.append('status', status);
  if (source)   params.append('source', source);
  if (room)     params.append('room', room);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo)   params.append('date_to', dateTo);

  const searchModalEl = document.getElementById('searchModal');
  if (searchModalEl) searchModalEl.dataset.currentFilters = params.toString();

  const result = await apiGet(`${API_BASE}/appointments/search/?${params.toString()}`);

  if (!result.success) {
    if (resultsEl) resultsEl.innerHTML = `<div class="alert alert-danger m-3"><i class="fas fa-exclamation-circle me-2"></i>Không thể tìm kiếm lịch hẹn. Vui lòng thử lại sau.</div>`;
    return;
  }

  const appts = result.appointments || [];
  if (!appts.length) {
    if (resultsEl) resultsEl.innerHTML = `<div class="text-center text-muted py-5"><i class="fas fa-inbox fa-2x mb-2 d-block opacity-25"></i>Không tìm thấy lịch hẹn phù hợp.</div>`;
    return;
  }

  const rows = appts.map(a => {
    const statusBadge = `<span class="badge ${_srchStatusBadgeClass(a.apptStatus)}">${statusLabel(a.apptStatus, a.cancelledBy)}</span>`;
    const svcDisplay = a.serviceCode
      ? `<span class="fw-semibold">${_esc(a.serviceCode)}</span>${a.service ? ` <span class="text-muted small">— ${_esc(a.service)}</span>` : ''}`
      : (a.service ? _esc(a.service) : '<span class="text-muted fst-italic">Chưa chọn DV</span>');
    return `
      <div class="srch-result-item d-flex align-items-center gap-3 px-3 py-2 border-bottom"
           style="cursor:pointer;transition:background .15s;"
           onmouseenter="this.style.background='#f0f7ff'" onmouseleave="this.style.background=''"
           onclick="window._srchGoToAppt('${_esc(a.id)}', '${_esc(a.date)}')">
        <div style="min-width:80px;">
          <div class="fw-semibold small">${_esc(a.date)}</div>
          <div class="text-muted small">${_esc(a.start)}${a.end ? '–'+_esc(a.end) : ''}</div>
        </div>
        <div style="min-width:70px;" class="text-muted small">
          <i class="fas fa-door-open me-1"></i>${_esc(a.roomName || a.roomCode || '—')}
        </div>
        <div style="flex:1;min-width:0;">
          <div class="fw-semibold text-truncate">${_esc(a.customerName || a.bookerName || '—')}</div>
          <div class="text-muted small text-truncate">${svcDisplay}</div>
        </div>
        <div style="min-width:90px;text-align:right;">${statusBadge}</div>
        <div class="text-muted" style="font-size:.75rem;min-width:60px;text-align:right;">
          <span class="text-primary small fw-semibold">${_esc(a.id)}</span>
        </div>
      </div>`;
  }).join('');

  if (resultsEl) {
    resultsEl.innerHTML = `
      <div class="px-3 py-2 border-bottom bg-light d-flex align-items-center justify-content-between">
        <span class="small text-muted"><i class="fas fa-list me-1"></i>Tìm thấy <strong>${appts.length}</strong> kết quả${appts.length === 100 ? ' (hiển thị tối đa 100)' : ''}</span>
        <span class="small text-muted">Click vào kết quả để xem trên lịch</span>
      </div>
      ${rows}`;
  }
}

function _srchStatusBadgeClass(s) {
  const sl = (s || '').toLowerCase();
  if (sl === 'pending')     return 'bg-warning text-dark';
  if (sl === 'not_arrived') return 'bg-secondary';
  if (sl === 'arrived')     return 'bg-info text-dark';
  if (sl === 'completed')   return 'bg-success';
  if (sl === 'cancelled')   return 'bg-secondary';
  if (sl === 'rejected')    return 'bg-danger';
  return 'bg-secondary';
}

window._srchGoToAppt = async function(apptId, apptDate) {
  // Đóng modal tìm kiếm
  const searchModalEl = document.getElementById('searchModal');
  if (searchModalEl) {
    const searchModal = bootstrap.Modal.getInstance(searchModalEl);
    if (searchModal) searchModal.hide();
  }

  // Chuyển grid sang đúng ngày
  if (apptDate && dayPicker) {
    dayPicker.value = apptDate;
    await refreshData();
  }

  // Highlight block trên grid
  setTimeout(() => {
    const block = document.querySelector(`.appt[data-id="${CSS.escape(apptId)}"]`);
    if (block) {
      block.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      block.classList.add('appt-highlight');
      setTimeout(() => block.classList.remove('appt-highlight'), 2500);
    }
  }, 350);
};

// ============================================================
// SECTION 14: CUSTOMER CANCEL POLLING
// ============================================================
(function initCustomerCancelPolling() {
  // Lưu các mã lịch đã toast để không hiện lại
  const _seenCodes = new Set();

  function _showCancelToast(customerName, code) {
    const container = document.getElementById('cancelToastContainer') || _createToastContainer();
    const id = `ct_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const el = document.createElement('div');
    el.id = id;
    el.style.cssText = `
      display:flex;align-items:flex-start;gap:10px;
      background:#fff;border:1px solid #fecdd3;border-left:4px solid #ef4444;
      border-radius:10px;padding:12px 14px;box-shadow:0 4px 16px rgba(0,0,0,.12);
      min-width:280px;max-width:360px;animation:slideInToast .3s ease;
    `;
    el.innerHTML = `
      <div style="flex-shrink:0;width:32px;height:32px;border-radius:50%;background:#fee2e2;
                  display:flex;align-items:center;justify-content:center;color:#ef4444;">
        <i class="fas fa-user-times" style="font-size:13px;"></i>
      </div>
      <div style="flex:1;min-width:0;">
        <div style="font-size:13px;font-weight:700;color:#111827;margin-bottom:2px;">Khách vừa hủy lịch</div>
        <div style="font-size:12px;color:#6b7280;">
          <span style="font-weight:600;color:#374151;">${customerName}</span>
          đã hủy lịch <span style="font-weight:600;color:#ef4444;">${code}</span>
        </div>
      </div>
      <button onclick="document.getElementById('${id}').remove()"
              style="flex-shrink:0;background:none;border:none;cursor:pointer;color:#9ca3af;font-size:16px;line-height:1;padding:0;">×</button>
    `;
    container.appendChild(el);
    setTimeout(() => { if (el.parentNode) el.remove(); }, 8000);
  }

  function _createToastContainer() {
    const c = document.createElement('div');
    c.id = 'cancelToastContainer';
    c.style.cssText = `
      position:fixed;bottom:24px;right:24px;z-index:9999;
      display:flex;flex-direction:column;gap:8px;align-items:flex-end;
    `;
    // Inject animation keyframe once
    if (!document.getElementById('cancelToastStyle')) {
      const s = document.createElement('style');
      s.id = 'cancelToastStyle';
      s.textContent = `@keyframes slideInToast{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}`;
      document.head.appendChild(s);
    }
    document.body.appendChild(c);
    return c;
  }

  async function _pollCancelledByCustomer() {
    try {
      const res = await fetch('/api/appointments/customer-cancelled-recent/?minutes=10', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!res.ok) return;
      const data = await res.json();
      if (!data.success || !data.appointments) return;
      data.appointments.forEach(a => {
        if (!_seenCodes.has(a.code)) {
          _seenCodes.add(a.code);
          _showCancelToast(a.customerName, a.code);
        }
      });
    } catch (e) { /* silent */ }
  }

  // Chạy lần đầu sau 5s (tránh spam khi mới load), sau đó mỗi 30s
  setTimeout(() => {
    _pollCancelledByCustomer();
    setInterval(_pollCancelledByCustomer, 30000);
  }, 5000);
})();

// ============================================================
// SECTION 15: INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", async ()=>{
  const modalEl = document.getElementById("apptModal");
  const toastEl = document.getElementById("toast");
  const webCount = document.getElementById("webCount");
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const grid = document.getElementById("grid");

  let modal = null;
  let toast = null;

  if (modalEl) modal = new bootstrap.Modal(modalEl);
  if (toastEl) toast = new bootstrap.Toast(toastEl);

  // Initialize customer search (stub — badges đã bỏ)
  initCustomerSearch();

  // Initialize delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  if(sidebarToggle) sidebarToggle.addEventListener("click", ()=> sidebar.classList.toggle("show"));

  // ── Render header timeline NGAY LẬP TỨC trước khi fetch ──
  // Để layout ổn định, không bị trống trong lúc chờ API
  dayPicker.value = todayISO();
  renderHeader();
  showGridLoading();   // hiện skeleton trong vùng grid

  // ── Fetch song song rooms + services để giảm thời gian chờ ──
  await Promise.all([loadRooms(), loadServices()]);

  fillRoomsSelect();
  fillServiceFilter();

  // ── Fetch appointments + web requests song song ──
  await Promise.all([
    refreshData(),
    renderWebRequests(),
  ]);

  // ===== POLLING: cập nhật badge pending count mỗi 15 giây =====
  setInterval(async () => {
    try {
      const res = await apiGet(`${API_BASE}/booking/pending-count/`);
      if (res.success && typeof res.count === 'number') {
        if (webCount) {
          if (res.count === 0) {
            webCount.textContent = '';
            webCount.classList.add('d-none');
          } else {
            webCount.textContent = String(res.count);
            webCount.classList.remove('d-none');
          }
        }
      }
    } catch(e) { /* silent */ }
  }, 15000);

  if(btnToday) btnToday.addEventListener("click", ()=> setDay(todayISO()));
  if(btnPrev) btnPrev.addEventListener("click", ()=> shiftDay(-1));
  if(btnNext) btnNext.addEventListener("click", ()=> shiftDay(1));
  if(dayPicker) dayPicker.addEventListener("change", ()=> { clearPendingBlocks(); refreshData(); updateCurrentTimeLine(); });

  // ── Current time line: interval realtime + resize ──
  startCurrentTimeLineInterval();
  window.addEventListener('resize', updateCurrentTimeLine);

  // ===== ACTION BAR — Pending blocks =====
  const btnCancelPending   = document.getElementById('btnCancelPending');
  const btnContinuePending = document.getElementById('btnContinuePending');

  if (btnCancelPending) {
    btnCancelPending.addEventListener('click', () => {
      _addingSlotMode = false;
      _savedBookerInfo = null;
      clearPendingBlocks();
      showToast('info', 'Đã hủy', 'Đã xóa toàn bộ slot đang chọn');
    });
  }

  if (btnContinuePending) {
    btnContinuePending.addEventListener('click', () => {
      if (!pendingBlocks.length) return;
      openCreateModalFromPending();
    });
  }

  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', () => {
      if (!isSubmitting && !_addingSlotMode) {
        clearPendingBlocks();
      }
    });
  }

  // Filter bar — tab Yêu cầu đặt lịch (dùng FilterManager chung)
  const webFM = new FilterManager({
    fields:   ['webSearchInput', 'webStatusFilter', 'webServiceFilter', 'webDateFilter'],
    btnId:    'webFilterBtn',
    searchId: 'webSearchInput',
    onApply:  () => renderWebRequests(),
  });

  // ===== SEARCH MODAL =====
  initSearchModal();

  window.openEditModal = openEditModal;
  window.renderWebRequests = renderWebRequests;
});
