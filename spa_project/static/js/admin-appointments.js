// ===== 1. SETTINGS - cấu hình =====
console.log("ADMIN APPOINTMENTS JS LOADED - NEW TOGGLE VERSION v20260422-003");
const START_HOUR = 9;  // Giờ mở cửa (9:00 sáng)
const END_HOUR = 21;   // Giờ đóng cửa (21:00 tối)
const SLOT_MIN = 30; // 1 ô lịch = 30 phút
const DEFAULT_DURATION = 60; // Thời lượng mặc định cho pending block (phút)

// ===== API BASE URL- đường dẫn API để gọi BE =====
const API_BASE = '/api';

// ===== HELPER: format variant label — tránh lặp "90 phút — 90 phút" =====
function variantLabel(v) {
  const dur = `${v.duration_minutes} phút`;
  // Nếu label trùng với duration hoặc label rỗng → chỉ hiện duration
  if (!v.label || v.label.trim() === dur) return dur;
  return `${v.label} — ${dur}`;
}

// ===================================================
/// ===================================================
// PENDING BLOCKS STATE — Flow 2 bước tạo lịch hẹn
// ===================================================
let pendingBlocks = [];
let _pendingIdCounter = 0;

function _nextPendingId() {
  return ++_pendingIdCounter;
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
    a.roomCode === roomId && a.date === day && (a.apptStatus || "").toUpperCase() !== "CANCELLED"
  );
  const { placements } = allocateRoomLanes(roomId, day, dayAppts);
  const laneAppts = placements.filter(p => p.laneIndex === laneIndex).map(p => p.appt);
  const conflictAppt = laneAppts.find(a =>
    overlaps(startMin, endMin, minutesFromStart(a.start), minutesFromStart(a.end))
  );
  if (conflictAppt) {
    showToast("warning", "Slot đã có lịch", `Lane này đã có lịch hẹn lúc ${conflictAppt.start}–${conflictAppt.end}`);
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
// ===== Dữ liệu ( lấy từ API) ==> lưu dữ liệu load từ DB để render giao diện, validate form, tính toán trùng lịch =====
let ROOMS = []; // danh sách phòng
let SERVICES = []; //dánh sách dịch vụ
let APPOINTMENTS = []; // danh sách lịch hẹn

// ===== 2. DOM =====
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const timeHeader = document.getElementById("timeHeader");
const grid = document.getElementById("grid");
const dayPicker = document.getElementById("dayPicker");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnToday = document.getElementById("btnToday");
const searchInput = document.getElementById("searchInput");
const webTbody = document.getElementById("webTbody");
const webCount = document.getElementById("webCount");
const webStatusFilter = document.getElementById("webStatusFilter");
const modalEl = document.getElementById("apptModal");
let modal = null;
const modalTitle = document.getElementById("modalTitle");
const modalError = document.getElementById("modalError");
const btnSave = document.getElementById("btnSave");
const btnDelete = document.getElementById("btnDelete");
const apptId = document.getElementById("apptId");
const toastEl = document.getElementById("toast");
let toast = null;
const toastTitle = document.getElementById("toastTitle");
const toastBody = document.getElementById("toastBody");

// ===== CSRF HELPER ======
function getCSRFToken() {
  const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookieValue ? cookieValue.split('=')[1] : '';
}

// ===== BOOKING BADGES UPDATE =====
function updateBookingBadges(rows) {
  // Chỉ đếm PENDING — không tính CANCELLED hay trạng thái khác
  const pendingCount = rows.filter(r => (r.apptStatus || '').toUpperCase() === 'PENDING').length;
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

// ===== LOADING STATE HELPER =====
// Biến theo dõi trạng thái đang submit để tránh submit lặp
let isSubmitting = false;

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
 * Hiển thị confirm dialog rõ ràng hơn
 * @param {string} title - Tiêu đề
 * @param {string} message - Nội dung xác nhận
 * @param {string} confirmText - Text nút xác nhận
 * @param {string} cancelText - Text nút hủy
 * @returns {boolean} - true nếu người dùng xác nhận
 */
function confirmAction(title, message, confirmText = 'Xác nhận', cancelText = 'Hủy') {
  // Sử dụng confirm mặc định của browser (đơn giản, không cần thêm thư viện)
  // Có thể nâng cấp lên modal đẹp hơn sau
  const fullMessage = `${title}\n\n${message}`;
  return confirm(fullMessage);
}

// ===== API CALLS =====
async function apiGet(url) {
  try {
    const response = await fetch(url);
    return await response.json();
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
    return await response.json();
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

  const searchTerm = (searchInput ? searchInput.value.trim() : '');
  if (searchTerm) params.push(`q=${encodeURIComponent(searchTerm)}`);

  if (params.length) url += '?' + params.join('&');

  const result = await apiGet(url);
  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
  } else {
    APPOINTMENTS = [];
  }
}

async function loadBookingRequests(statusFilter = '', dateFilter = '', searchTerm = '') {
  let url = `${API_BASE}/booking-requests/`;
  const queryParams = [];
  if (statusFilter) queryParams.push(`status=${encodeURIComponent(statusFilter)}`);
  if (dateFilter)   queryParams.push(`date=${encodeURIComponent(dateFilter)}`);
  if (searchTerm)   queryParams.push(`q=${encodeURIComponent(searchTerm)}`);
  if (queryParams.length > 0) url += '?' + queryParams.join('&');

  const result = await apiGet(url);
  if (result && result.success) {
    return result.appointments || [];
  }
  return [];
}

// ===== HELPERS =====
function pad2(n){ return String(n).padStart(2,"0"); }

function showToast(type, title, message){
  const header = toastEl.querySelector(".toast-header");
  const icon = header.querySelector("i");
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
  return "status-pending";
}

function statusLabel(s){
  const sl = (s||'').toLowerCase();
  if(sl==="pending") return "Chờ xác nhận";
  if(sl==="not_arrived") return "Chưa đến";
  if(sl==="arrived") return "Đã đến";
  if(sl==="completed") return "Hoàn thành";
  if(sl==="cancelled") return "Đã hủy";
  return s;
}

function isValidPhone(v){ return /^\d{10}$/.test(v.replace(/\D/g,"")); }

function minutesFromStart(t){ const [h,m]=t.split(":").map(Number); return (h-START_HOUR)*60 + m; }

function addMinutesToTime(t, add){
  const [h,m]=t.split(":").map(Number);
  const total = h*60+m+add;
  return `${pad2(Math.floor(total/60))}:${pad2(total%60)}`;
}

function overlaps(aStart,aEnd,bStart,bEnd){ return aStart < bEnd && bStart < aEnd; }

function resetModalError(){ modalError.classList.add("d-none"); modalError.textContent = ""; }

// Tổng số phút của toàn bộ timeline (9:00 → 21:00 = 720 phút)
function totalTimelineMinutes(){ return (END_HOUR - START_HOUR) * 60; }

// Chuyển số phút từ START_HOUR sang % chiều ngang của vùng slots
function minutesToPercent(minutes){ return (minutes / totalTimelineMinutes()) * 100; }

function getSlotWidth(){
  // Đọc chiều rộng thực tế của 1 slot từ DOM (sau khi flex giãn)
  // Dùng cho tính toán click position
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

function capacityOK({roomId, day, start, end, guestsCount, ignoreId}){
  const roomInfo = ROOMS.find(r=>r.id===roomId);
  if(!roomInfo) return false;

  const newS = minutesFromStart(start), newE = minutesFromStart(end);
  let sum = 0;

  const overlappingAppts = APPOINTMENTS.filter(
    a => a.roomCode===roomId && a.date===day && (a.apptStatus||'').toLowerCase()!=="cancelled" && a.id!==ignoreId
  );

  overlappingAppts.forEach(a => {
    const s = minutesFromStart(a.start);
    const rawE = a.end ? minutesFromStart(a.end) : NaN;
    const e = (!isNaN(rawE) && rawE > s) ? rawE : s + Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
    if(overlaps(newS, newE, s, e)) {
      sum += Number(a.guests) || 0;
    }
  });

  return (sum + guestsCount) <= roomInfo.capacity;
}

// ===== LOADING SKELETON CHO GRID =====
function showGridLoading(){
  if (!grid) return;
  // Hiện 5 dòng skeleton để layout không bị trống trong lúc fetch
  const rowH = getComputedStyle(document.documentElement).getPropertyValue('--rowH') || '72px';
  grid.innerHTML = Array.from({length: 5}, (_, i) => `
    <div class="lane-row" style="opacity:.45;">
      <div class="roomcell"><span class="dot"></span>—</div>
      <div class="slots" style="background: repeating-linear-gradient(90deg,#f3f4f6 0,#f3f4f6 40%,#e9eaec 40%,#e9eaec 100%) 0 0 / 120px 100%;"></div>
    </div>`).join('');
}

// ===== RENDER NHÓM VẼ GIAO DIỆN RENDER-UI =====
function renderHeader(){
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
  grid.innerHTML = "";
  const day = dayPicker.value;

  ROOMS.forEach((r)=>{
    // Lọc lịch theo phòng — dùng roomCode (khớp với serializer)
    // Hiển thị tất cả trừ CANCELLED
    let appts = APPOINTMENTS.filter(a =>
      a.date === day &&
      a.roomCode === r.id &&
      (a.apptStatus || '').toUpperCase() !== 'CANCELLED'
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
        block.innerHTML = `<div class="t1">${a.customerName} • ${a.service}</div><div class="t2">${a.start}–${endLabel} • ${a.guests} khách</div>`;

        // click vào lịch ==> sửa
        block.addEventListener("click", (ev)=>{ ev.stopPropagation(); openEditModal(a.id); });
        slotsEl.appendChild(block);
      });

      // Vẽ pending blocks đúng theo lane
      renderPendingBlocks(slotsEl, r.id, lane, day);

      grid.appendChild(laneRow);
    }
  });
}

// vẽ bảng yêu cầu đặt lịch online
async function renderWebRequests(){
  const statusFilter = (document.getElementById("webStatusFilter") || {}).value || '';
  const dateFilter   = (document.getElementById("webDateFilter")   || {}).value || '';
  const searchTerm   = ((document.getElementById("webSearchInput") || {}).value || '').trim();

  let rows = await loadBookingRequests(statusFilter, dateFilter, searchTerm);

  updateBookingBadges(rows);

  if(rows.length === 0){
    webTbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">Không có yêu cầu đặt lịch trực tuyến</td></tr>`;
    return;
  }
  webTbody.innerHTML = rows.map(a => `<tr>
    <td class="fw-semibold">${a.id}</td><td>${a.customerName}</td><td>${a.phone}</td><td>${a.service}</td>
    <td>${a.date}</td><td>${a.start} - ${a.end}</td><td>${a.durationMin||""} phút</td>
    <td><span class="badge ${a.apptStatus==='PENDING'||a.apptStatus==='pending'?'bg-warning':(a.apptStatus==='CANCELLED'||a.apptStatus==='cancelled'?'bg-danger':'bg-success')} text-white">${statusLabel(a.apptStatus)}</span></td>
    <td class="text-end">${(a.apptStatus==="PENDING"||a.apptStatus==="pending")?`<div class="btn-group btn-group-sm"><button class="btn btn-warning px-2" data-id="${a.id}" onclick="approveWeb('${a.id}')"><i class="fas fa-check"></i><span class="d-none d-md-inline ms-1">Xác nhận</span></button><button class="btn btn-outline-danger px-2" data-id="${a.id}" onclick="rejectWeb('${a.id}')"><i class="fas fa-xmark"></i><span class="d-none d-md-inline ms-1">Từ chối</span></button></div>`:`<button class="btn btn-sm btn-outline-secondary" data-id="${a.id}" onclick="openEditModal('${a.id}')"><i class="fas fa-pen me-1"></i>Xem/Sửa</button>`}</td>
  </tr>`).join("");
}

window.approveWeb = async function(id){
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (result.success && result.appointment) {
    const a = result.appointment;
    // Mở edit modal với status mặc định NOT_ARRIVED
    openEditModalWithData({ ...a, apptStatus: 'NOT_ARRIVED' });
    if (a.date) dayPicker.value = a.date;
    showToast("info", "Xác nhận lịch", "Kiểm tra phòng & giờ rồi bấm Lưu để xác nhận lên timeline");
  } else {
    showToast("error","Lỗi","Không tìm thấy lịch hẹn");
  }
}

window.rejectWeb = async function(id){
  if(!confirm("Từ chối yêu cầu đặt lịch này?")) return;
  const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'CANCELLED' });
  if (result.success) { showToast("success","OK","Đã từ chối yêu cầu"); await renderWebRequests(); await refreshData(); }
  else showToast("error","Lỗi", result.error || "Không thể từ chối yêu cầu");
}

// ===== MODAL  =====
// fillRoomsSelect / fillServicesSelect không còn dùng — rooms/services load vào guest card trực tiếp
function fillRoomsSelect(){ /* no-op — rooms rendered per guest card */ }
function fillServicesSelect(){ /* no-op — services rendered per guest card */ }

// Điền dropdown dịch vụ cho filter bar scheduler
function fillServiceFilter(){
  const sel = document.getElementById('serviceFilter');
  if (!sel) return;
  sel.innerHTML = '<option value="">Tất cả dịch vụ</option>' +
    SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
}

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

// Escape HTML để tránh XSS
function _esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ===== CREATE MODE — ACCORDION GUEST CARDS =====
let _guestCount = 0;
// Map pendingBlockId → guestIdx để sync slot summary
let _pendingBlockMap = []; // [{pendingId, guestIdx}]

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

/** Toggle expand detail panel của 1 row */
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
    wrap.style.maxHeight = '300px';
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

  const svc = SERVICES.find(s => s.id == serviceId);
  if (!svc || !svc.variants?.length) return;

  svc.variants.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = variantLabel(v);
    opt.dataset.duration = v.duration_minutes;
    if (selectedVariantId && v.id == selectedVariantId) opt.selected = true;
    varSel.appendChild(opt);
  });
  varSel.disabled = false;
  if (!selectedVariantId && svc.variants.length === 1) {
    varSel.value = svc.variants[0].id;
  }
  // Cập nhật end_time khi variant thay đổi
  _updateGuestEndTime(item);
}

/** Tính và lưu end_time vào dataset */
function _updateGuestEndTime(item) {
  const varSel = item.querySelector('.gc-variant');
  const timeVal = item.dataset.slotTime;
  if (!varSel || !timeVal) return;
  const opt = varSel.options[varSel.selectedIndex];
  const dur = opt?.dataset?.duration ? Number(opt.dataset.duration) : 60;
  item.dataset.endTime = addMinutesToTime(timeVal, dur);
  const endEl = item.querySelector('.gc-slot-time');
  if (endEl && item.dataset.slotTime) {
    endEl.textContent = `${item.dataset.slotTime}–${item.dataset.endTime}`;
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

/** Build 1 compact guest row — detail panel ẩn mặc định, toggle bằng JS */
function _buildGuestItem(idx, prefill) {
  prefill = prefill || {};
  var roomName = prefill.roomId ? (ROOMS.find(function(r){ return r.id === prefill.roomId; }) || {}).name || prefill.roomId : '';
  var dateVal  = prefill.date || dayPicker.value;
  var timeVal  = prefill.time || '';
  var endTime  = (timeVal && prefill.pendingDuration) ? addMinutesToTime(timeVal, prefill.pendingDuration) : '';
  var hasSlot  = !!(timeVal && prefill.roomId);

  var svcOpts = '<option value="">-- Dịch vụ --</option>' +
    SERVICES.map(function(s){ return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');

  var inp = 'width:100%;height:30px;padding:0 8px;font-size:.8rem;border:1px solid #d1d5db;border-radius:5px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;';
  var sel = 'width:100%;height:30px;padding:0 6px;font-size:.8rem;border:1px solid #d1d5db;border-radius:5px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;appearance:auto;';
  var sInp = 'width:100%;height:26px;padding:0 6px;font-size:.75rem;border:1px solid #e5e7eb;border-radius:4px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#374151;display:block;';
  var lbl  = 'font-size:.65rem;font-weight:600;color:#9ca3af;display:block;margin-bottom:2px;white-space:nowrap;';

  var slotBadge = hasSlot
    ? '<div style="text-align:center;line-height:1.3;">'
      + '<div style="font-size:.78rem;font-weight:700;color:#1d4ed8;white-space:nowrap;">P.' + _esc(roomName) + '</div>'
      + '<div class="gc-slot-time" style="font-size:.7rem;color:#6b7280;white-space:nowrap;">' + timeVal + (endTime ? '\u2013' + endTime : '') + '</div>'
      + '</div>'
    : '<span style="font-size:.72rem;color:#9ca3af;font-style:italic;display:block;text-align:center;">—</span>';

  var item = document.createElement('div');
  item.className = 'gc-item';
  item.dataset.idx      = idx;
  item.dataset.slotTime = timeVal;
  item.dataset.slotDate = dateVal;
  item.dataset.slotRoom = prefill.roomId || '';
  item.dataset.endTime  = endTime;
  item.dataset.detailOpen = '0';
  item.style.cssText = 'border-bottom:1px solid #eef0f3;';

  item.innerHTML =
    '<input type="hidden" class="gc-room" value="' + _esc(prefill.roomId || '') + '" />'
  + '<input type="hidden" class="gc-date" value="' + _esc(dateVal) + '" />'
  + '<input type="hidden" class="gc-time" value="' + _esc(timeVal) + '" />'

  // ── COMPACT ROW ──
  // Grid: # | Phòng·Giờ | Tên khách (+ checkbox) | SĐT | Dịch vụ | Gói | Actions
  + '<div class="gc-row" style="display:grid;grid-template-columns:24px 100px 1fr 130px 1fr 1fr 60px;gap:6px;padding:5px 12px;align-items:center;min-height:46px;box-sizing:border-box;background:#fff;border-left:3px solid transparent;transition:border-color .15s;">'

    // Col 1 — số thứ tự
    + '<div class="gc-num" style="text-align:center;font-size:.72rem;font-weight:700;color:#94a3b8;">—</div>'

    // Col 2 — phòng · giờ
    + '<div style="display:flex;align-items:center;justify-content:center;">' + slotBadge + '</div>'

    // Col 3 — tên khách + checkbox "= người đặt"
    + '<div style="display:flex;flex-direction:column;gap:2px;">'
      + '<div style="display:flex;align-items:center;gap:5px;">'
        + '<input class="gc-name" style="' + inp + 'flex:1;min-width:0;" placeholder="Tên khách *" value="' + _esc(prefill.name || '') + '" />'
        + '<label style="display:inline-flex;align-items:center;gap:3px;white-space:nowrap;cursor:pointer;padding:0 5px;height:30px;border:1px solid #e5e7eb;border-radius:5px;background:#f8fafc;font-size:.65rem;color:#6b7280;flex-shrink:0;" title="Điền từ người đặt">'
          + '<input type="checkbox" class="gc-same-as-booker" style="width:11px;height:11px;cursor:pointer;accent-color:#1d4ed8;margin:0;" />'
          + '<span>= người đặt</span>'
        + '</label>'
      + '</div>'
    + '</div>'

    // Col 4 — SĐT
    + '<div><input class="gc-phone" style="' + inp + '" placeholder="SĐT" inputmode="numeric" value="' + _esc(prefill.phone || '') + '" /></div>'

    // Col 5 — dịch vụ
    + '<div><select class="gc-service" style="' + sel + '">' + svcOpts + '</select></div>'

    // Col 6 — gói
    + '<div><select class="gc-variant" style="' + sel + 'color:#9ca3af;" disabled><option value="">-- Chọn dịch vụ --</option></select></div>'

    // Col 7 — actions
    + '<div style="display:flex;align-items:center;justify-content:flex-end;gap:4px;">'
      + '<button type="button" class="gc-expand-btn" onclick="toggleGuestCard(' + idx + ')" title="Chi tiết"'
      + ' style="height:28px;width:28px;padding:0;font-size:.72rem;background:#f1f5f9;border:1px solid #e2e8f0;color:#64748b;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;">'
      + '<i class="fas fa-ellipsis-h"></i></button>'
      + '<button type="button" class="gc-delete-btn" onclick="removeGuestCard(' + idx + ')" title="Xóa khách"'
      + ' style="height:28px;width:28px;padding:0;font-size:.7rem;background:#fff5f5;border:1px solid #fecaca;color:#ef4444;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s,opacity .15s;">'
      + '<i class="fas fa-trash-alt"></i></button>'
    + '</div>'

  + '</div>'

  // ── DETAIL PANEL (hidden, toggled by JS via visibility wrapper) ──
  + '<div class="gc-detail-wrap" style="overflow:hidden;max-height:0;transition:max-height .2s ease;">'
    + '<div class="gc-detail" style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;padding:8px 14px 10px 158px;background:#f8fafc;border-top:1px dashed #e5e7eb;box-sizing:border-box;">'
      + '<div style="display:flex;flex-direction:column;gap:2px;min-width:150px;flex:1;">'
        + '<label style="' + lbl + '">Email</label>'
        + '<input type="email" class="gc-email" style="' + sInp + '" placeholder="Email (nếu có)" value="' + _esc(prefill.email || '') + '" />'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;width:115px;">'
        + '<label style="' + lbl + '">Trạng thái</label>'
        + '<select class="gc-status" style="' + sInp + '">'
          + '<option value="NOT_ARRIVED" selected>Chưa đến</option>'
          + '<option value="PENDING">Chờ xác nhận</option>'
          + '<option value="ARRIVED">Đã đến</option>'
          + '<option value="COMPLETED">Hoàn thành</option>'
          + '<option value="CANCELLED">Đã hủy</option>'
        + '</select>'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;width:130px;">'
        + '<label style="' + lbl + '">Thanh toán</label>'
        + '<select class="gc-pay" style="' + sInp + '">'
          + '<option value="UNPAID" selected>Chưa thanh toán</option>'
          + '<option value="PARTIAL">Một phần</option>'
          + '<option value="PAID">Đã thanh toán</option>'
        + '</select>'
      + '</div>'
      + '<div class="gc-pay-fields" style="display:none;flex-wrap:wrap;gap:6px;align-items:flex-end;width:100%;margin-top:4px;padding:6px 8px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;">'
        + '<div style="display:flex;flex-direction:column;gap:2px;width:130px;">'
          + '<label style="' + lbl + '">Phương thức <span style="color:#ef4444;">*</span></label>'
          + '<select class="gc-pay-method" style="' + sInp + '">'
            + '<option value="">-- Chọn --</option>'
            + '<option value="CASH">Tiền mặt</option>'
            + '<option value="CARD">Thẻ</option>'
            + '<option value="BANK_TRANSFER">Chuyển khoản</option>'
            + '<option value="E_WALLET">Ví điện tử</option>'
          + '</select>'
        + '</div>'
        + '<div class="gc-pay-amount-wrap" style="display:none;flex-direction:column;gap:2px;width:120px;">'
          + '<label style="' + lbl + '">Số tiền đã trả <span style="color:#ef4444;">*</span></label>'
          + '<input type="number" class="gc-pay-amount" style="' + sInp + '" placeholder="0" min="1" step="1000" />'
        + '</div>'
        + '<div class="gc-pay-final-wrap" style="display:none;flex-direction:column;gap:2px;width:120px;">'
          + '<label style="' + lbl + '">Số tiền thu</label>'
          + '<input type="text" class="gc-pay-final" style="' + sInp + 'background:#f1f5f9;" readonly />'
        + '</div>'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;flex:2;min-width:140px;">'
        + '<label style="' + lbl + '">Ghi chú khách</label>'
        + '<input class="gc-note" style="' + sInp + '" placeholder="Ghi chú từ khách..." value="' + _esc(prefill.note || '') + '" />'
      + '</div>'
      + '<div style="display:flex;flex-direction:column;gap:2px;flex:2;min-width:140px;">'
        + '<label style="' + lbl + '">Ghi chú nội bộ</label>'
        + '<input class="gc-staff-note" style="' + sInp + '" placeholder="Chỉ nhân viên thấy..." value="' + _esc(prefill.staffNote || '') + '" />'
      + '</div>'
      + '<div style="display:flex;gap:5px;align-items:flex-end;">'
        + '<button type="button" onclick="fillGuestFromBooker(' + idx + ')"'
        + ' style="height:26px;padding:0 8px;font-size:.68rem;font-weight:600;background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;border-radius:5px;cursor:pointer;white-space:nowrap;">'
        + '<i class="fas fa-user" style="font-size:.6rem;margin-right:2px;"></i>Từ người đặt</button>'
      + '</div>'
    + '</div>'
  + '</div>';

  // Bind events
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
      if (sameChk.checked) {
        if (nameI)  nameI.value  = document.getElementById('bookerName')?.value.trim()  || '';
        if (phoneI) phoneI.value = document.getElementById('bookerPhone')?.value.trim() || '';
        if (emailI) emailI.value = document.getElementById('bookerEmail')?.value.trim() || '';
        if (nameI)  nameI.readOnly  = true;
        if (phoneI) phoneI.readOnly = true;
      } else {
        if (nameI)  { nameI.value  = ''; nameI.readOnly  = false; }
        if (phoneI) { phoneI.value = ''; phoneI.readOnly = false; }
        if (emailI) emailI.readOnly = false;
      }
      _updateGuestProgress();
    });
  }

  // Bind gc-pay change → show/hide payment fields
  var paySel = item.querySelector('.gc-pay');
  if (paySel) {
    paySel.addEventListener('change', function() { _onGuestPayChange(item); });
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
    // Cập nhật slot badge
    const roomName = (ROOMS.find(r => r.id === prefill.roomId) || {}).name || prefill.roomId;
    const badgeEl = item.querySelector('.gc-slot-time')?.closest('div[style*="text-align:center"]');
    if (!badgeEl) {
      // Tạo lại slot badge nếu chưa có
      const slotCell = item.querySelector('.gc-row > div:nth-child(2)');
      if (slotCell) {
        slotCell.innerHTML = '<div style="text-align:center;line-height:1.3;">'
          + '<div style="font-size:.78rem;font-weight:700;color:#1d4ed8;white-space:nowrap;">P.' + _esc(roomName) + '</div>'
          + '<div class="gc-slot-time" style="font-size:.7rem;color:#6b7280;white-space:nowrap;">' + (prefill.time || '') + '</div>'
          + '</div>';
      }
    }
  }
  if (prefill.date) {
    item.dataset.slotDate = prefill.date;
    const dateInp = item.querySelector('.gc-date');
    if (dateInp) dateInp.value = prefill.date;
  }
  if (prefill.time) {
    item.dataset.slotTime = prefill.time;
    const timeInp = item.querySelector('.gc-time');
    if (timeInp) timeInp.value = prefill.time;
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
  return _getGuestItems().map(item => {
    const variantSel = item.querySelector('.gc-variant');
    const selectedVariantOpt = variantSel?.options[variantSel.selectedIndex];
    const guestNote      = item.querySelector('.gc-note')?.value.trim() || '';
    const guestStaffNote = item.querySelector('.gc-staff-note')?.value.trim() || '';
    return {
      name:               item.querySelector('.gc-name')?.value.trim() || '',
      phone:              item.querySelector('.gc-phone')?.value.trim() || '',
      email:              item.querySelector('.gc-email')?.value.trim() || '',
      serviceId:          item.querySelector('.gc-service')?.value || '',
      variantId:          variantSel?.value || '',
      roomId:             item.dataset.slotRoom || item.querySelector('.gc-room')?.value || '',
      date:               item.dataset.slotDate || item.querySelector('.gc-date')?.value || '',
      time:               item.dataset.slotTime || item.querySelector('.gc-time')?.value || '',
      apptStatus:         item.querySelector('.gc-status')?.value || 'NOT_ARRIVED',
      payStatus:          item.querySelector('.gc-pay')?.value || 'UNPAID',
      paymentMethod:      item.querySelector('.gc-pay-method')?.value || '',
      paymentAmount:      item.querySelector('.gc-pay-amount')?.value || 0,
      paymentRecordedNo:  item.querySelector('.gc-pay-ref')?.value.trim() || '',
      paymentNote:        item.querySelector('.gc-pay-note-field')?.value.trim() || '',
      note:               guestNote || bookerNote,
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
    applyAllSvc.innerHTML = '<option value="">-- Dịch vụ --</option>' +
      SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }

  if (applyAllSvc) {
    applyAllSvc.onchange = function() {
      const varSel = document.getElementById('applyAllVariant');
      if (!varSel) return;
      varSel.innerHTML = '<option value="">-- Gói --</option>';
      varSel.disabled  = true;
      const svc = SERVICES.find(s => s.id == this.value);
      if (!svc || !svc.variants?.length) return;
      svc.variants.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = variantLabel(v);
        opt.dataset.duration = v.duration_minutes;
        varSel.appendChild(opt);
      });
      varSel.disabled = false;
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

function openCreateModal(prefill={}) {
  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");

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

  if (prefill._fromPending && prefill._blocks && prefill._blocks.length > 0) {
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
    addGuestCard({ date: prefill.day || dayPicker.value, time: prefill.time || '' });
    if (prefill.roomId) {
      const firstItem = _getGuestItems()[0];
      if (firstItem) {
        const roomSel = firstItem.querySelector('.gc-room');
        if (roomSel) roomSel.value = prefill.roomId;
      }
    }
  }

  _initApplyAllBar();
  _updateGuestProgress();
  _updateSlotSummary();
  _resetAllCustomerState();

  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (!modal) return;
  modal.show();
}

// ── State: đang ở chế độ "quay về grid để chọn thêm slot" ──
let _addingSlotMode = false;
let _savedBookerInfo = null;  // lưu tạm booker info khi quay về grid

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
  if (result.success && result.appointment) openEditModalWithData(result.appointment);
  else { const a = APPOINTMENTS.find(x=>x.id===id); if (a) openEditModalWithData(a); else showToast("error","Lỗi","Không tìm thấy lịch hẹn"); }
}

function openEditModalWithData(a){
  resetModalError();
  modalTitle.textContent = `Chỉnh sửa • ${a.id}`;
  apptId.value = a.id;
  btnDelete.classList.remove("d-none");

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Lưu lịch hẹn";

  // Hiện shared form, ẩn create-only bar
  _showSharedForm();
  _setCreateOnlyVisible(false);

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
    name:       a.customerName || '',
    phone:      a.phone || '',
    email:      a.email || '',
    serviceId:  a.serviceId,
    variantId:  a.variantId,
    roomId:     a.roomCode || a.roomId || '',
    date:       a.date || '',
    time:       a.start || '',
    apptStatus: a.apptStatus || 'NOT_ARRIVED',
    payStatus:  a.payStatus || 'UNPAID',
    note:       a.note || '',
    staffNote:  a.staffNotes || '',
    _editMode:  true,
  });

  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (modal) modal.show();
}

btnSave.addEventListener("click", ()=> {
  // Trigger submit trên form
  const f = document.getElementById('apptForm');
  if (f) f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
});

// Validate Form
document.getElementById('apptForm').addEventListener("submit", async (e)=>{
  e.preventDefault();

  if (isSubmitting) return;
  resetModalError();

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
    if (!phoneVal || !isValidPhone(phoneVal)) { modalError.textContent = "Số điện thoại người đặt không hợp lệ"; modalError.classList.remove("d-none"); return; }
    if (!g.name || !g.name.trim()) { modalError.textContent = "Khách: Vui lòng nhập tên khách sử dụng dịch vụ"; modalError.classList.remove("d-none"); return; }
    if (!g.serviceId) { modalError.textContent = "Vui lòng chọn dịch vụ"; modalError.classList.remove("d-none"); return; }
    if (!g.variantId) { modalError.textContent = "Vui lòng chọn gói dịch vụ"; modalError.classList.remove("d-none"); return; }
    if (!g.roomId)    { modalError.textContent = "Vui lòng chọn phòng"; modalError.classList.remove("d-none"); return; }
    if (!g.date)      { modalError.textContent = "Vui lòng chọn ngày hẹn"; modalError.classList.remove("d-none"); return; }
    if (!g.time)      { modalError.textContent = "Vui lòng chọn giờ hẹn"; modalError.classList.remove("d-none"); return; }

    const durationVal = Number(g._duration) || 60;
    const endVal = addMinutesToTime(g.time, durationVal);
    if (minutesFromStart(g.time) < 0 || minutesFromStart(endVal) > (END_HOUR - START_HOUR) * 60) {
      modalError.textContent = "Giờ hẹn ngoài giờ làm việc"; modalError.classList.remove("d-none"); return;
    }
    if (!capacityOK({ roomId: g.roomId, day: g.date, start: g.time, end: endVal, guestsCount: 1, ignoreId: id })) {
      modalError.textContent = "Phòng đã đủ chỗ ở khung giờ này"; modalError.classList.remove("d-none"); return;
    }

    const payload = {
      customerId:   Number(document.getElementById("selectedCustomerId")?.value) || null,
      bookerName:   nameVal,
      bookerPhone:  phoneVal.replace(/\D/g, ""),
      bookerEmail:  emailVal,
      customerName: g.name || '',
      phone:        (g.phone || '').replace(/\D/g, ""),
      email:        g.email || emailVal,
      serviceId:    g.serviceId,
      variantId:    g.variantId,
      roomId:       g.roomId,
      guests:       1,
      date:         g.date,
      time:         g.time,
      duration:     durationVal,
      note:         document.getElementById('bookerNote')?.value.trim() || '',
      apptStatus:   g.apptStatus,
      payStatus:    g.payStatus,
      source:       sourceVal,
      staffNote:    g.staffNote || '',
    };

    isSubmitting = true;
    setButtonLoading(btnSave, 'Đang cập nhật...');
    try {
      const result = await apiPost(`${API_BASE}/appointments/${id}/update/`, payload);
      if (result.success) {
        if (modal) modal.hide();
        if (dayPicker.value !== g.date) dayPicker.value = g.date;
        await refreshData();
        await renderWebRequests();
        showToast("success", "Thành công", result.message || "Cập nhật lịch hẹn thành công");
      } else {
        modalError.textContent = result.error || "Không thể lưu lịch hẹn";
        modalError.classList.remove("d-none");
      }
    } catch(err) {
      modalError.textContent = "Không thể lưu. Vui lòng thử lại";
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
    modalError.textContent = "Vui lòng nhập tên người đặt";
    modalError.classList.remove("d-none");
    return;
  }
  if (!bookerPhone || !isValidPhone(bookerPhone)) {
    modalError.textContent = "Số điện thoại người đặt không hợp lệ";
    modalError.classList.remove("d-none");
    return;
  }

  const guestCards = _collectGuestCards();
  if (!guestCards.length) {
    modalError.textContent = "Cần ít nhất 1 khách sử dụng dịch vụ";
    modalError.classList.remove("d-none");
    return;
  }

  const VALID_METHODS = ['CASH', 'CARD', 'BANK_TRANSFER', 'E_WALLET'];
  for (let i = 0; i < guestCards.length; i++) {
    const g = guestCards[i];
    const label = `Khách ${i + 1}`;
    const gItem = _getGuestItems()[i];
    if (!g.name || !g.name.trim()) {
      if (gItem) _markRowError(gItem);
      modalError.textContent = `${label}: Vui lòng nhập tên khách`;
      modalError.classList.remove("d-none"); return;
    }
    if (!g.serviceId) {
      if (gItem) _markRowError(gItem);
      modalError.textContent = `${label}: Chưa chọn dịch vụ`;
      modalError.classList.remove("d-none"); return;
    }
    if (!g.variantId) {
      if (gItem) _markRowError(gItem);
      modalError.textContent = `${label}: Chưa chọn gói dịch vụ`;
      modalError.classList.remove("d-none"); return;
    }
    if (!g.roomId)    { modalError.textContent = `${label}: Chưa chọn phòng`; modalError.classList.remove("d-none"); return; }
    if (!g.date)      { modalError.textContent = `${label}: Chưa chọn ngày hẹn`; modalError.classList.remove("d-none"); return; }
    if (!g.time)      { modalError.textContent = `${label}: Chưa chọn giờ hẹn`; modalError.classList.remove("d-none"); return; }
    const endV = addMinutesToTime(g.time, Number(g._duration) || 60);
    if (!capacityOK({ roomId: g.roomId, day: g.date, start: g.time, end: endV, guestsCount: 1, ignoreId: null })) {
      modalError.textContent = `${label}: Phòng đã đủ chỗ ở khung giờ này`;
      modalError.classList.remove("d-none");
      return;
    }
    if (g.payStatus === 'PAID') {
      if (!g.paymentMethod || !VALID_METHODS.includes(g.paymentMethod)) {
        modalError.textContent = `${label}: Vui lòng chọn phương thức thanh toán`;
        modalError.classList.remove("d-none");
        return;
      }
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
      if (modal) modal.hide();
      _addingSlotMode = false;
      _savedBookerInfo = null;
      const firstDate = guestCards[0]?.date;
      if (firstDate && dayPicker.value !== firstDate) dayPicker.value = firstDate;
      clearPendingBlocks();
      await refreshData();
      await renderWebRequests();
      showToast("success", "Thành công", result.message || `Đã tạo ${result.appointments?.length || 0} lịch hẹn`);
      if (result.errors?.length) {
        setTimeout(() => showToast("warning", "Một số lỗi", result.errors.join(' | ')), 1500);
      }
    } else {
      modalError.textContent = result.error || "Không thể tạo lịch hẹn";
      modalError.classList.remove("d-none");
    }
  } catch(err) {
    modalError.textContent = "Không thể tạo lịch. Vui lòng thử lại";
    modalError.classList.remove("d-none");
  } finally {
    isSubmitting = false;
    resetButton(btnSave);
  }
});

btnDelete.addEventListener("click", async ()=>{
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
          if (modal) modal.hide();
          await refreshData();
          await renderWebRequests();  // Refresh lại tab Yêu cầu đặt lịch
          showToast("success","Đã xóa thành công", `Đã xóa hoàn toàn lịch hẹn ${id} khỏi hệ thống`);
        } else {
          showToast("error","Lỗi", result.error || "Không thể xóa lịch hẹn");
          isSubmitting = false; // Reset khi lỗi
        }
      } catch (err) {
        console.error('Error:', err);
        showToast("error","Lỗi", "Không thể xóa lịch hẹn. Vui lòng thử lại sau");
        isSubmitting = false; // Reset khi lỗi
      } finally {
        // ===== TẬT LOADING STATE =====
        isSubmitting = false;
      }
    });

    // Cập nhật reference
    document.getElementById('confirmDeleteAppointmentBtn').id = 'confirmDeleteAppointmentBtn';
  }

  // Mở modal
  deleteModal.show();
});

// ===== DATE NAV =====
function setDay(d){ dayPicker.value = d; refreshData(); }
function todayISO(){ const t = new Date(); return `${t.getFullYear()}-${pad2(t.getMonth()+1)}-${pad2(t.getDate())}`; }
function shiftDay(delta){ const d = new Date(dayPicker.value + "T00:00:00"); d.setDate(d.getDate()+delta); setDay(`${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`); }

// ===== REFRESH DATA =====
async function refreshData(){
  await loadAppointments(dayPicker.value);
  renderGrid();
}

// ===== INIT =====
document.addEventListener("DOMContentLoaded", async ()=>{

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
  if(dayPicker) dayPicker.addEventListener("change", ()=> { clearPendingBlocks(); refreshData(); });

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

  // Filter bar — tab Lịch theo phòng (dùng FilterManager chung)
  const schedFM = new FilterManager({
    fields:   ['searchInput', 'statusFilter', 'serviceFilter', 'sourceFilter'],
    btnId:    'schedFilterBtn',
    searchId: 'searchInput',
    onApply:  () => refreshData(),
  });

  // Filter bar — tab Yêu cầu đặt lịch (dùng FilterManager chung)
  const webFM = new FilterManager({
    fields:   ['webSearchInput', 'webStatusFilter', 'webDateFilter'],
    btnId:    'webFilterBtn',
    searchId: 'webSearchInput',
    onApply:  () => renderWebRequests(),
  });

  window.openEditModal = openEditModal;
  window.renderWebRequests = renderWebRequests;
});
