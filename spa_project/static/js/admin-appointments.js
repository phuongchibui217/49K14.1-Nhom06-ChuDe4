// ===== 1. SETTINGS - cấu hình =====
const START_HOUR = 9;  // Giờ mở cửa (9:00 sáng)
const END_HOUR = 21;   // Giờ đóng cửa (21:00 tối)
const SLOT_MIN = 30; // 1 ô lịch = 30 phút
const DEFAULT_DURATION = 60; // Thời lượng mặc định cho pending block (phút)

// ===== API BASE URL- đường dẫn API để gọi BE =====
const API_BASE = '/api';

// ===================================================
/// ===================================================
// PENDING BLOCKS STATE — Flow 2 bước tạo lịch hẹn
// ===================================================
let pendingBlocks = [];
let _pendingIdCounter = 0;

function _nextPendingId() {
  return ++_pendingIdCounter;
}

function addPendingBlock({ roomId, laneIndex, day, time }) {
  const duration = DEFAULT_DURATION;
  const endTime = addMinutesToTime(time, duration);

  const startMin = minutesFromStart(time);
  const endMin = minutesFromStart(endTime);

  if (startMin < 0 || endMin > totalTimelineMinutes()) {
    showToast(
      "warning",
      "Ngoài giờ hoạt động",
      `Spa hoạt động từ ${START_HOUR}:00 đến ${END_HOUR}:00`
    );
    return null;
  }

  // Conflict với appointment đã có: chỉ check cùng lane (laneIndex)
  // Dùng allocateRoomLanes để biết appointment nào đang ở lane nào
  const dayAppts = APPOINTMENTS.filter(a =>
    a.roomCode === roomId &&
    a.date === day &&
    (a.apptStatus || "").toUpperCase() !== "CANCELLED"
  );
  const { placements } = allocateRoomLanes(roomId, day, dayAppts);
  const laneAppts = placements.filter(p => p.laneIndex === laneIndex).map(p => p.appt);

  const conflictAppt = laneAppts.find(a =>
    overlaps(startMin, endMin, minutesFromStart(a.start), minutesFromStart(a.end))
  );

  if (conflictAppt) {
    showToast(
      "warning",
      "Slot đã có lịch",
      `Lane này đã có lịch hẹn lúc ${conflictAppt.start}–${conflictAppt.end}`
    );
    const slotsEl = document.querySelector(
      `.lane-row[data-room-id="${roomId}"] .slots[data-room="${roomId}"][data-lane="${laneIndex}"]`
    );
    if (slotsEl) {
      slotsEl.classList.add("conflict-flash");
      setTimeout(() => slotsEl.classList.remove("conflict-flash"), 450);
    }
    return null;
  }

  // Conflict với pending block khác: chỉ check cùng roomId + laneIndex
  const conflictPending = pendingBlocks.find(pb =>
    pb.roomId === roomId &&
    pb.laneIndex === laneIndex &&
    pb.day === day &&
    overlaps(startMin, endMin, minutesFromStart(pb.time), minutesFromStart(pb.endTime))
  );

  if (conflictPending) {
    showToast(
      "warning",
      "Trùng với slot đang chọn",
      `Lane này đã có slot đang chọn lúc ${conflictPending.time}–${conflictPending.endTime}`
    );
    return null;
  }

  const block = {
    id: _nextPendingId(),
    roomId,
    laneIndex,
    day,
    time,
    endTime,
    duration,
  };

  pendingBlocks.push(block);
  _syncActionBar();
  return block;
}

function removePendingBlock(id) {
  pendingBlocks = pendingBlocks.filter(pb => pb.id !== id);
  document.querySelectorAll(`.appt-pending[data-pending-id="${id}"]`).forEach(el => el.remove());
  _syncActionBar();
}

function clearPendingBlocks() {
  pendingBlocks = [];
  document.querySelectorAll(".appt-pending").forEach(el => el.remove());
  _syncActionBar();
}

function _syncActionBar() {
  const bar = document.getElementById("pendingActionBar");
  const badge = document.getElementById("pbCountBadge");
  const label = document.getElementById("pbCountLabel");

  if (!bar) return;

  const count = pendingBlocks.length;

  if (badge) badge.textContent = String(count);
  if (label) label.textContent = count === 1 ? "1 khách đã chọn" : `${count} khách đã chọn`;

  if (count > 0) {
    bar.style.display = "block";
    requestAnimationFrame(() => bar.classList.add("visible"));
  } else {
    bar.classList.remove("visible");
    setTimeout(() => {
      if (!pendingBlocks.length) bar.style.display = "none";
    }, 180);
  }
}

function _mountPendingBlock(pb, slotsEl) {
  if (!slotsEl) return null;

  const existed = slotsEl.querySelector(`.appt-pending[data-pending-id="${pb.id}"]`);
  if (existed) existed.remove();

  const block = document.createElement("div");
  block.className = "appt appt-pending";
  block.dataset.pendingId = String(pb.id);

  // Selection block: chỉ có top-bar xanh + nền translucent + nút xóa
  block.innerHTML = `
    <div class="pb-selection-bar"></div>
    <div class="pb-time-hint">${pb.time} – ${pb.endTime}</div>
    <button type="button" class="pb-remove" title="Xóa slot này">
      <i class="fas fa-times"></i>
    </button>
  `;

  block.style.position = "absolute";
  block.style.top = "0";
  block.style.height = "var(--rowH)";
  block.style.zIndex = "30";
  block.style.display = "block";

  const leftMin = minutesFromStart(pb.time);
  const durMin = Math.max(SLOT_MIN, minutesFromStart(pb.endTime) - leftMin);

  block.style.left = `calc(${minutesToPercent(leftMin)}% + 1px)`;
  block.style.width = `calc(${minutesToPercent(durMin)}% - 2px)`;

  const removeBtn = block.querySelector(".pb-remove");
  if (removeBtn) {
    removeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      removePendingBlock(pb.id);
    });
  }

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
const form = document.getElementById("apptForm");
const btnSave = document.getElementById("btnSave");
const btnDelete = document.getElementById("btnDelete");
const apptId = document.getElementById("apptId");
const customerName = document.getElementById("customerName");
const phone = document.getElementById("phone");
const email = document.getElementById("email");
const service = document.getElementById("service");
const room = document.getElementById("room");
const guests = document.getElementById("guests");
const date = document.getElementById("date");
const time = document.getElementById("time");
const apptStatus = document.getElementById("apptStatus");
const payStatus = document.getElementById("payStatus");
const note = document.getElementById("note");
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
    const e = minutesFromStart(a.end);
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
    const s = minutesFromStart(a.start), e = minutesFromStart(a.end);
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

      // click vào ô trống ==> tạo pending block (flow 2 bước)
      slotsEl.addEventListener("click", (e)=>{
        if (e.target.closest('.appt') || e.target.closest('.appt-pending')) return;

        const rect     = slotsEl.getBoundingClientRect();
        const x        = e.clientX - rect.left;
        const ratio    = Math.max(0, Math.min(1, x / rect.width));
        const rawMin   = ratio * totalTimelineMinutes();
        const minutes  = Math.floor(rawMin / SLOT_MIN) * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes/60))}:${pad2(minutes%60)}`;
        const currentDay  = dayPicker.value;

        const newBlock = addPendingBlock({ roomId: r.id, laneIndex: lane, day: currentDay, time: clickedTime });
        // Inject block trực tiếp vào slotsEl — KHÔNG gọi renderGrid()
        if (newBlock) _mountPendingBlock(newBlock, slotsEl);
      });

      // vẽ block lịch hẹn
      placements.filter(p => p.laneIndex === lane).forEach(p=>{
        const a = p.appt;
        const block = document.createElement("div");
        block.className = `appt ${statusClass(a.apptStatus)}`;
        block.dataset.id = a.id;
        const leftMin = minutesFromStart(a.start);
        const durMin = Math.max(SLOT_MIN, minutesFromStart(a.end) - leftMin);
        // Dùng % thay vì px → tự co giãn theo chiều rộng thực tế của vùng slots
        const leftPct  = minutesToPercent(leftMin);
        const widthPct = minutesToPercent(durMin);
        block.style.left  = `calc(${leftPct}% + 2px)`;
        block.style.width = `calc(${widthPct}% - 4px)`;
        block.innerHTML = `<div class="t1">${a.customerName} • ${a.service}</div><div class="t2">${a.start}–${a.end} • ${a.guests} khách</div>`;

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
    openEditModalWithData(a);
    // Đặt status mặc định là NOT_ARRIVED khi xác nhận
    apptStatus.value = "NOT_ARRIVED";
    // Đồng bộ dayPicker sang ngày của lịch hẹn để timeline hiện đúng sau khi save
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
function fillRoomsSelect(){ room.innerHTML = ROOMS.map(r=>`<option value="${r.id}">${r.name}</option>`).join(""); }
function fillServicesSelect(){ service.innerHTML = `<option value="">-- Chọn dịch vụ --</option>` + SERVICES.map(s=>`<option value="${s.id}">${s.name}</option>`).join(""); }

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
  const phoneEl = document.getElementById('phone');
  const emailEl = document.getElementById('email');
  if (!phoneEl) return;

  // ── Phone input ──
  phoneEl.addEventListener('input', () => {
    clearTimeout(_phoneTimer);
    _resetPhoneState();                          // reset mọi badge phone
    const val = phoneEl.value.replace(/\D/g, '');
    if (val.length >= 9) {
      _phoneTimer = setTimeout(() => _lookupByPhone(val), 500);
    }
  });

  // ── Email input ──
  if (emailEl) {
    emailEl.addEventListener('input', () => {
      clearTimeout(_emailTimer);
      _resetEmailState();                        // reset mọi badge email
      const val = emailEl.value.trim();
      if (val.includes('@') && val.length >= 6) {
        _emailTimer = setTimeout(() => _lookupByEmail(val), 600);
      }
    });
  }

  // ── Nút ✓ Dùng (phone) ──
  document.getElementById('confirmMatchBtnPhone')?.addEventListener('click', () => {
    if (_pendingMatch.phone) _confirmMatch(_pendingMatch.phone, 'phone');
  });
  // ── Nút ✕ Bỏ qua (phone) ──
  document.getElementById('dismissMatchBtnPhone')?.addEventListener('click', () => {
    if (_pendingMatch.phone) _dismissMatch(_pendingMatch.phone, 'phone');
  });
  // ── Nút ✓ Dùng (email) ──
  document.getElementById('confirmMatchBtnEmail')?.addEventListener('click', () => {
    if (_pendingMatch.email) _confirmMatch(_pendingMatch.email, 'email');
  });
  // ── Nút ✕ Bỏ qua (email) ──
  document.getElementById('dismissMatchBtnEmail')?.addEventListener('click', () => {
    if (_pendingMatch.email) _dismissMatch(_pendingMatch.email, 'email');
  });
  // ── Nút bỏ liên kết (phone) ──
  document.getElementById('unlinkBtnPhone')?.addEventListener('click', () => _unlinkCustomer('phone'));
  // ── Nút bỏ liên kết (email) ──
  document.getElementById('unlinkBtnEmail')?.addEventListener('click', () => _unlinkCustomer('email'));
}

// Lookup theo phone — exact match
async function _lookupByPhone(phoneVal) {
  if (document.getElementById('apptId').value.trim()) return; // chỉ khi tạo mới
  try {
    const res = await apiGet(`${API_BASE}/customers/search/?q=${encodeURIComponent(phoneVal)}`);
    if (!res.success) return;
    const match = res.customers.find(c => c.phone.replace(/\D/g, '') === phoneVal);
    if (match) _showSuggestion(match, 'phone');
  } catch(e) { /* silent */ }
}

// Lookup theo email — exact match
async function _lookupByEmail(emailVal) {
  if (document.getElementById('apptId').value.trim()) return;
  try {
    const res = await apiGet(`${API_BASE}/customers/search/?q=${encodeURIComponent(emailVal)}`);
    if (!res.success) return;
    const match = res.customers.find(c => c.email && c.email.toLowerCase() === emailVal.toLowerCase());
    if (match) _showSuggestion(match, 'email');
  } catch(e) { /* silent */ }
}

// Hiện badge gợi ý — CHƯA fill form, chờ nhân viên xác nhận
function _showSuggestion(c, via) {
  _pendingMatch[via] = c;
  if (via === 'phone') {
    const badge = document.getElementById('customerMatchBadgePhone');
    const label = document.getElementById('customerMatchLabelPhone');
    if (label) label.textContent = `Khách đã có hồ sơ: ${c.fullName} · ${c.phone}`;
    if (badge) badge.classList.remove('d-none');
  } else {
    const badge = document.getElementById('customerMatchBadgeEmail');
    const label = document.getElementById('customerMatchLabelEmail');
    if (label) label.textContent = `Khách đã có hồ sơ: ${c.fullName} · ${c.phone}`;
    if (badge) badge.classList.remove('d-none');
  }
}

// Nhấn ✓ — xác nhận dùng hồ sơ: gán customer_id + fill form
function _confirmMatch(c, via) {
  // Gán customer_id
  document.getElementById('selectedCustomerId').value = c.id;

  // Fill toàn bộ thông tin từ profile
  const nameEl  = document.getElementById('customerName');
  const phoneEl = document.getElementById('phone');
  const emailEl = document.getElementById('email');
  if (nameEl)  nameEl.value  = c.fullName;
  if (phoneEl) phoneEl.value = c.phone;
  if (emailEl) emailEl.value = c.email || '';

  // Ẩn badge gợi ý, hiện badge đã liên kết
  if (via === 'phone') {
    document.getElementById('customerMatchBadgePhone')?.classList.add('d-none');
    const linked = document.getElementById('customerLinkedBadgePhone');
    const label  = document.getElementById('customerLinkedLabelPhone');
    if (label)  label.textContent = `Đã liên kết: ${c.fullName}`;
    if (linked) linked.classList.remove('d-none');
  } else {
    document.getElementById('customerMatchBadgeEmail')?.classList.add('d-none');
    const linked = document.getElementById('customerLinkedBadgeEmail');
    const label  = document.getElementById('customerLinkedLabelEmail');
    if (label)  label.textContent = `Đã liên kết: ${c.fullName}`;
    if (linked) linked.classList.remove('d-none');
  }
  _pendingMatch[via] = null;
}

// Nhấn ✕ — bỏ qua: không fill, không gán customer_id, hiện cảnh báo nếu trùng
function _dismissMatch(c, via) {
  // Ẩn badge gợi ý
  if (via === 'phone') {
    document.getElementById('customerMatchBadgePhone')?.classList.add('d-none');
    // Hiện cảnh báo trùng SĐT
    const warn  = document.getElementById('customerWarnBadgePhone');
    const label = document.getElementById('customerWarnLabelPhone');
    if (label) label.textContent = `SĐT này đã thuộc về khách "${c.fullName}" — lịch sẽ tạo dạng khách vãng lai`;
    if (warn)  warn.classList.remove('d-none');
  } else {
    document.getElementById('customerMatchBadgeEmail')?.classList.add('d-none');
    const warn  = document.getElementById('customerWarnBadgeEmail');
    const label = document.getElementById('customerWarnLabelEmail');
    if (label) label.textContent = `Email này đã thuộc về khách "${c.fullName}" — lịch sẽ tạo dạng khách vãng lai`;
    if (warn)  warn.classList.remove('d-none');
  }
  _pendingMatch[via] = null;
  // customer_id vẫn = '' (null khi submit)
}

// Nhấn X trên badge đã liên kết — bỏ liên kết, xóa form
function _unlinkCustomer(via) {
  document.getElementById('selectedCustomerId').value = '';
  const nameEl  = document.getElementById('customerName');
  const phoneEl = document.getElementById('phone');
  const emailEl = document.getElementById('email');
  if (nameEl)  nameEl.value  = '';
  if (phoneEl) phoneEl.value = '';
  if (emailEl) emailEl.value = '';
  if (via === 'phone') {
    document.getElementById('customerLinkedBadgePhone')?.classList.add('d-none');
  } else {
    document.getElementById('customerLinkedBadgeEmail')?.classList.add('d-none');
  }
}

// Reset toàn bộ state phone (khi user sửa lại SĐT)
function _resetPhoneState() {
  _pendingMatch.phone = null;
  document.getElementById('selectedCustomerId').value = '';
  document.getElementById('customerMatchBadgePhone')?.classList.add('d-none');
  document.getElementById('customerLinkedBadgePhone')?.classList.add('d-none');
  document.getElementById('customerWarnBadgePhone')?.classList.add('d-none');
}

// Reset toàn bộ state email (khi user sửa lại email)
function _resetEmailState() {
  _pendingMatch.email = null;
  // Chỉ xóa customer_id nếu nó được set từ email (không đụng nếu đã link qua phone)
  const linkedPhone = !document.getElementById('customerLinkedBadgePhone')?.classList.contains('d-none');
  if (!linkedPhone) document.getElementById('selectedCustomerId').value = '';
  document.getElementById('customerMatchBadgeEmail')?.classList.add('d-none');
  document.getElementById('customerLinkedBadgeEmail')?.classList.add('d-none');
  document.getElementById('customerWarnBadgeEmail')?.classList.add('d-none');
}

// Reset toàn bộ khi mở modal tạo mới
function _resetAllCustomerState() {
  _pendingMatch = { phone: null, email: null };
  document.getElementById('selectedCustomerId').value = '';
  ['customerMatchBadgePhone','customerLinkedBadgePhone','customerWarnBadgePhone',
   'customerMatchBadgeEmail','customerLinkedBadgeEmail','customerWarnBadgeEmail']
    .forEach(id => document.getElementById(id)?.classList.add('d-none'));
}

// Escape HTML để tránh XSS
function _esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ===== CREATE MODE — GUEST CARDS =====
let _guestCount = 0;

function _buildGuestCard(idx, prefill = {}) {
  const n = idx + 1;
  const roomOpts = ROOMS.map(r =>
    `<option value="${r.id}"${prefill.roomId && r.id === prefill.roomId ? ' selected' : ''}>${r.name}</option>`
  ).join('');
  const svcOpts  = `<option value="">-- Dịch vụ --</option>` +
                   SERVICES.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

  // Badge hiển thị slot đã chọn từ grid
  const roomName = prefill.roomId ? (ROOMS.find(r => r.id === prefill.roomId)?.name || prefill.roomId) : '';
  const slotBadge = (prefill.time && prefill.roomId) ? `
    <span style="display:inline-flex;align-items:center;gap:5px;background:#eff6ff;border:1px solid #bfdbfe;
                 color:#1d4ed8;border-radius:6px;padding:2px 8px;font-size:.72rem;font-weight:600;">
      <i class="fas fa-map-marker-alt" style="font-size:.6rem;"></i>Phòng ${_esc(roomName)}
      &nbsp;·&nbsp;
      <i class="fas fa-clock" style="font-size:.6rem;"></i>${prefill.time}
      ${prefill.pendingDuration ? `&nbsp;·&nbsp;${prefill.pendingDuration}'` : ''}
    </span>` : '';

  return `
  <div class="guest-card" data-idx="${idx}"
       style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
    <div style="background:#f8fafc;padding:.6rem 1rem;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #f0f0f0;gap:8px;flex-wrap:wrap;">
      <span style="font-weight:600;font-size:.82rem;color:#374151;">
        <i class="fas fa-user-circle me-1" style="color:#c9a96e;"></i>Khách ${n}
      </span>
      ${slotBadge}
      <button type="button" class="btn-remove-guest"
              style="background:none;border:none;color:#9ca3af;font-size:.75rem;cursor:pointer;padding:0 4px;"
              onclick="removeGuestCard(${idx})">
        <i class="fas fa-times"></i> Xóa
      </button>
    </div>
    <div style="padding:.85rem 1rem;">
      <div class="row g-2">
        <div class="col-md-4">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Họ tên khách</label>
          <input class="form-control form-control-sm gc-name" placeholder="Để trống = dùng tên người đặt"
                 value="${prefill.name || ''}" />
        </div>
        <div class="col-md-3">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">SĐT khách</label>
          <input class="form-control form-control-sm gc-phone" placeholder="Để trống = dùng SĐT người đặt"
                 inputmode="numeric" value="${prefill.phone || ''}" />
        </div>
        <div class="col-md-5">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Email khách</label>
          <input type="email" class="form-control form-control-sm gc-email" placeholder="Email (nếu có)"
                 value="${prefill.email || ''}" />
        </div>

        <div class="col-md-4">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Dịch vụ <span class="text-danger">*</span></label>
          <select class="form-select form-select-sm gc-service" onchange="onGuestServiceChange(this, ${idx})">${svcOpts}</select>
        </div>
        <div class="col-md-4">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Gói dịch vụ <span class="text-danger">*</span></label>
          <select class="form-select form-select-sm gc-variant" disabled>
            <option value="">-- Chọn dịch vụ trước --</option>
          </select>
        </div>
        <div class="col-md-4">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Phòng <span class="text-danger">*</span></label>
          <select class="form-select form-select-sm gc-room">${roomOpts}</select>
        </div>

        <div class="col-md-3">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Ngày hẹn <span class="text-danger">*</span></label>
          <input type="date" class="form-control form-control-sm gc-date" value="${prefill.date || dayPicker.value}" />
        </div>
        <div class="col-md-2">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Giờ hẹn <span class="text-danger">*</span></label>
          <input type="time" class="form-control form-control-sm gc-time" value="${prefill.time || '09:00'}" min="09:00" max="21:00" />
        </div>
        <div class="col-md-3">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Trạng thái</label>
          <select class="form-select form-select-sm gc-status">
            <option value="NOT_ARRIVED">Chưa đến</option>
            <option value="PENDING">Chờ xác nhận</option>
            <option value="ARRIVED">Đã đến</option>
            <option value="COMPLETED">Hoàn thành</option>
          </select>
        </div>
        <div class="col-md-4">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Thanh toán</label>
          <select class="form-select form-select-sm gc-pay">
            <option value="UNPAID">Chưa thanh toán</option>
            <option value="PARTIAL">Một phần</option>
            <option value="PAID">Đã thanh toán</option>
          </select>
        </div>

        <div class="col-md-6">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Ghi chú khách</label>
          <input class="form-control form-control-sm gc-note" placeholder="Ghi chú từ khách..." value="${prefill.note || ''}" />
        </div>
        <div class="col-md-6">
          <label style="font-size:.72rem;font-weight:600;color:#6b7280;display:block;margin-bottom:3px;">Ghi chú nội bộ</label>
          <input class="form-control form-control-sm gc-staff-note" placeholder="Chỉ nhân viên thấy..." value="${prefill.staffNote || ''}" />
        </div>
      </div>
    </div>
  </div>`;
}

function addGuestCard(prefill = {}) {
  const list = document.getElementById('guestList');
  if (!list) return;
  const idx = _guestCount++;
  const div = document.createElement('div');
  div.innerHTML = _buildGuestCard(idx, prefill);
  list.appendChild(div.firstElementChild);
  // Renumber headings
  _renumberGuests();
}

window.removeGuestCard = function(idx) {
  const card = document.querySelector(`#guestList .guest-card[data-idx="${idx}"]`);
  if (card) card.remove();
  _renumberGuests();
};

function _renumberGuests() {
  document.querySelectorAll('#guestList .guest-card').forEach((card, i) => {
    const title = card.querySelector('.btn-remove-guest')?.previousElementSibling;
    if (title) title.innerHTML = `<i class="fas fa-user-circle me-1" style="color:#c9a96e;"></i>Khách ${i + 1}`;
  });
}

window.onGuestServiceChange = function(sel, idx) {
  const card = document.querySelector(`#guestList .guest-card[data-idx="${idx}"]`);
  if (!card) return;
  const variantSel = card.querySelector('.gc-variant');
  variantSel.innerHTML = '<option value="">-- Chọn gói --</option>';
  variantSel.disabled = true;

  const svc = SERVICES.find(s => s.id == sel.value);
  if (!svc || !svc.variants?.length) return;

  svc.variants.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = `${v.label} — ${v.duration_minutes} phút`;
    opt.dataset.duration = v.duration_minutes;
    variantSel.appendChild(opt);
  });
  variantSel.disabled = false;
  if (svc.variants.length === 1) variantSel.value = svc.variants[0].id;
};

function _collectGuestCards() {
  const cards = document.querySelectorAll('#guestList .guest-card');
  return Array.from(cards).map(card => {
    const variantSel = card.querySelector('.gc-variant');
    const selectedVariantOpt = variantSel?.options[variantSel.selectedIndex];
    return {
      name:       card.querySelector('.gc-name')?.value.trim() || '',
      phone:      card.querySelector('.gc-phone')?.value.trim() || '',
      email:      card.querySelector('.gc-email')?.value.trim() || '',
      serviceId:  card.querySelector('.gc-service')?.value || '',
      variantId:  variantSel?.value || '',
      roomId:     card.querySelector('.gc-room')?.value || '',
      date:       card.querySelector('.gc-date')?.value || '',
      time:       card.querySelector('.gc-time')?.value || '',
      apptStatus: card.querySelector('.gc-status')?.value || 'NOT_ARRIVED',
      payStatus:  card.querySelector('.gc-pay')?.value || 'UNPAID',
      note:       card.querySelector('.gc-note')?.value.trim() || '',
      staffNote:  card.querySelector('.gc-staff-note')?.value.trim() || '',
      _duration:  selectedVariantOpt?.dataset?.duration || 60,
    };
  });
}

function openCreateModal(prefill={}) {
  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Lưu lịch hẹn";

  // Chuyển sang create mode
  document.getElementById('editModeBody').classList.add('d-none');
  const createBody = document.getElementById('createModeBody');
  createBody.style.display = 'flex';

  // Reset người đặt
  document.getElementById('bookerName').value   = '';
  document.getElementById('bookerPhone').value  = '';
  document.getElementById('bookerEmail').value  = '';
  document.getElementById('bookerSource').value = 'DIRECT';

  // Reset danh sách khách — sinh từ pendingBlocks nếu có, fallback về prefill
  _guestCount = 0;
  document.getElementById('guestList').innerHTML = '';

  if (prefill._fromPending && prefill._blocks && prefill._blocks.length > 0) {
    // Sinh guest card từ mỗi pending block — truyền đủ date/time/roomId/duration
    prefill._blocks.forEach(pb => {
      addGuestCard({ date: pb.day, time: pb.time, roomId: pb.roomId, pendingDuration: pb.duration });
    });
  } else {
    addGuestCard({ date: prefill.day || dayPicker.value, time: prefill.time || '09:00' });
    // Set phòng cho card đầu nếu có prefill
    if (prefill.roomId) {
      const firstCard = document.querySelector('#guestList .guest-card');
      if (firstCard) {
        const roomSel = firstCard.querySelector('.gc-room');
        if (roomSel) roomSel.value = prefill.roomId;
      }
    }
  }

  _resetAllCustomerState();

  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (!modal) return;
  form.classList.remove("was-validated");
  modal.show();
}

/** Mở modal tạo lịch từ pending blocks đã chọn trên grid */
function openCreateModalFromPending() {
  if (!pendingBlocks.length) return;
  openCreateModal({ _fromPending: true, _blocks: [...pendingBlocks] });
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

  // Chuyển sang edit mode
  document.getElementById('createModeBody').style.display = 'none';
  document.getElementById('editModeBody').classList.remove('d-none');
  _resetAllCustomerState();
  document.getElementById('selectedCustomerId').value = a.customerId || '';
  
  // Customer info
  customerName.value = a.customerName;
  phone.value = a.phone;
  email.value = a.email || "";
  guests.value = a.guests;
  note.value = a.note || "";
  
  // Appointment info
  service.value = a.serviceId || "";
  
  // Trigger service change to load variants
  const serviceSelect = document.getElementById("service");
  if (serviceSelect && a.serviceId) {
    serviceSelect.dispatchEvent(new Event('change'));
    // Đợi variants load xong rồi chọn đúng variant
    // Serializer trả về field 'variantId' (không phải serviceVariantId)
    const variantIdToSelect = a.variantId || a.serviceVariantId || null;
    if (variantIdToSelect) {
      setTimeout(() => {
        const variantSelect = document.getElementById("variant");
        if (variantSelect) {
          variantSelect.value = variantIdToSelect;
          variantSelect.dispatchEvent(new Event('change'));
        }
      }, 300);
    }
  }
  
  room.value = a.roomCode || a.roomId || (ROOMS[0]?.id || "");
  date.value = a.date;
  time.value = a.start;
  apptStatus.value = a.apptStatus || "NOT_ARRIVED";
  payStatus.value = a.payStatus || "UNPAID";
  
  // New fields
  const sourceSelect = document.getElementById("source");
  if (sourceSelect) sourceSelect.value = a.source || "DIRECT";
  const staffNoteTextarea = document.getElementById("staffNote");
  if (staffNoteTextarea) staffNoteTextarea.value = a.staffNotes || "";
  
  form.classList.remove("was-validated");
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (modal) modal.show();
}

btnSave.addEventListener("click", ()=> form.requestSubmit());

// Validate Form
form.addEventListener("submit", async (e)=>{
  e.preventDefault();

  // ===== NGĂN SUBMIT LẶP =====
  if (isSubmitting) return;

  resetModalError();
  const id = apptId.value.trim();

  // ── EDIT MODE ──
  if (id) {
    form.classList.add("was-validated");
    const nameVal    = customerName.value.trim();
    const phoneVal   = phone.value.trim();
    const serviceVal = service.value;
    const roomVal    = room.value;
    const guestsVal  = Number(guests.value);
    const dayVal     = date.value;
    const startVal   = time.value;
    const variantSelect = document.getElementById("variant");
    const variantVal = variantSelect ? variantSelect.value : "";
    let durationVal  = 60;
    if (variantSelect && variantVal) {
      const opt = variantSelect.options[variantSelect.selectedIndex];
      if (opt?.dataset.duration) durationVal = Number(opt.dataset.duration);
    }

    customerName.setCustomValidity(nameVal ? "" : "invalid");
    phone.setCustomValidity((phoneVal && isValidPhone(phoneVal)) ? "" : "invalid");
    service.setCustomValidity(serviceVal ? "" : "invalid");
    if (variantSelect) variantSelect.setCustomValidity(variantVal ? "" : "invalid");
    room.setCustomValidity(roomVal ? "" : "invalid");
    guests.setCustomValidity((Number.isFinite(guestsVal) && guestsVal > 0) ? "" : "invalid");
    date.setCustomValidity(dayVal ? "" : "invalid");
    time.setCustomValidity(startVal ? "" : "invalid");

    if (!form.checkValidity()) {
      if (!nameVal) modalError.textContent = "Vui lòng nhập họ tên";
      else if (!phoneVal || !isValidPhone(phoneVal)) modalError.textContent = "Số điện thoại không hợp lệ";
      else if (!serviceVal) modalError.textContent = "Vui lòng chọn dịch vụ";
      else if (!variantVal) modalError.textContent = "Vui lòng chọn gói dịch vụ";
      else if (!roomVal) modalError.textContent = "Vui lòng chọn phòng";
      else modalError.textContent = "Vui lòng điền đầy đủ thông tin";
      modalError.classList.remove("d-none");
      return;
    }

    const endVal = addMinutesToTime(startVal, durationVal);
    if (minutesFromStart(startVal) < 0 || minutesFromStart(endVal) > (END_HOUR - START_HOUR) * 60) {
      modalError.textContent = "Giờ hẹn ngoài giờ làm việc";
      modalError.classList.remove("d-none");
      return;
    }
    if (!capacityOK({ roomId: roomVal, day: dayVal, start: startVal, end: endVal, guestsCount: guestsVal, ignoreId: id })) {
      modalError.textContent = "Phòng đã đủ chỗ ở khung giờ này";
      modalError.classList.remove("d-none");
      return;
    }

    const payload = {
      customerId:   Number(document.getElementById("selectedCustomerId")?.value) || null,
      customerName: nameVal,
      phone:        phoneVal.replace(/\D/g, ""),
      email:        email.value.trim(),
      serviceId:    serviceVal,
      variantId:    variantVal,
      roomId:       roomVal,
      guests:       guestsVal,
      date:         dayVal,
      time:         startVal,
      duration:     durationVal,
      note:         note.value.trim(),
      apptStatus:   apptStatus.value,
      payStatus:    payStatus.value,
      source:       document.getElementById("source")?.value || "DIRECT",
      staffNote:    document.getElementById("staffNote")?.value.trim() || "",
    };

    isSubmitting = true;
    setButtonLoading(btnSave, 'Đang cập nhật...');
    try {
      const result = await apiPost(`${API_BASE}/appointments/${id}/update/`, payload);
      if (result.success) {
        if (modal) modal.hide();
        if (dayPicker.value !== dayVal) dayPicker.value = dayVal;
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

  // Validate từng card
  for (let i = 0; i < guestCards.length; i++) {
    const g = guestCards[i];
    const label = `Khách ${i + 1}`;
    if (!g.serviceId) { modalError.textContent = `${label}: Chưa chọn dịch vụ`; modalError.classList.remove("d-none"); return; }
    if (!g.variantId) { modalError.textContent = `${label}: Chưa chọn gói dịch vụ`; modalError.classList.remove("d-none"); return; }
    if (!g.roomId)    { modalError.textContent = `${label}: Chưa chọn phòng`; modalError.classList.remove("d-none"); return; }
    if (!g.date)      { modalError.textContent = `${label}: Chưa chọn ngày hẹn`; modalError.classList.remove("d-none"); return; }
    if (!g.time)      { modalError.textContent = `${label}: Chưa chọn giờ hẹn`; modalError.classList.remove("d-none"); return; }
    const endV = addMinutesToTime(g.time, Number(g._duration) || 60);
    if (!capacityOK({ roomId: g.roomId, day: g.date, start: g.time, end: endV, guestsCount: 1, ignoreId: null })) {
      modalError.textContent = `${label}: Phòng đã đủ chỗ ở khung giờ này`;
      modalError.classList.remove("d-none");
      return;
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
      // Chuyển dayPicker sang ngày của lịch đầu tiên
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

  // ===== NGĂN XÓA LẶP =====
  if (isSubmitting) {
    console.log('Đang xử lý, bỏ qua click lặp');
    return;
  }

  if(!id) return;

  // ===== MỞ MODAL XÁC NHẬN =====
  const customerNameVal = customerName.value.trim();
  const timeVal = time.value || '';
  const dateVal = date.value || '';

  // Hiển thị tên khách + giờ hẹn (không hiện mã kỹ thuật)
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
function setDay(d){ dayPicker.value = d; date.value = d; refreshData(); }
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

  // Initialize customer search
  initCustomerSearch();

  // Initialize delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  // ===== SERVICE VARIANT LOADING =====
  const serviceSelect = document.getElementById('service');
  const variantSelect = document.getElementById('variant');
  const variantInfo = document.getElementById('variantInfo');
  
  if (serviceSelect && variantSelect) {
    serviceSelect.addEventListener('change', async function() {
      const serviceId = this.value;
      
      // Reset variant select
      variantSelect.innerHTML = '<option value="">-- Chọn gói dịch vụ --</option>';
      variantSelect.disabled = !serviceId;
      if (variantInfo) variantInfo.classList.add('d-none');
      
      if (!serviceId) return;
      
      // Find service in SERVICES array
      const service = SERVICES.find(s => s.id == serviceId);
      if (!service || !service.variants || service.variants.length === 0) {
        variantSelect.innerHTML = '<option value="">Dịch vụ này chưa có gói</option>';
        return;
      }
      
      // Load variants
      service.variants.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = `${v.label} - ${v.duration_minutes} phút`;
        opt.dataset.duration = v.duration_minutes;
        opt.dataset.price = v.price;
        variantSelect.appendChild(opt);
      });
      
      // Auto select first if only one
      if (service.variants.length === 1) {
        variantSelect.value = service.variants[0].id;
        variantSelect.dispatchEvent(new Event('change'));
      }
    });
    
    // Show variant info when selected
    variantSelect.addEventListener('change', function() {
      if (!variantInfo) return;
      
      const selected = this.options[this.selectedIndex];
      if (this.value && selected.dataset.duration) {
        const duration = selected.dataset.duration;
        const price = parseFloat(selected.dataset.price).toLocaleString('vi-VN');
        variantInfo.textContent = `${duration} phút • ${price}đ`;
        variantInfo.classList.remove('d-none');
      } else {
        variantInfo.classList.add('d-none');
      }
    });
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

  // Khi modal đóng → xóa pending blocks (nếu user bấm Hủy)
  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', () => {
      // Chỉ xóa pending nếu không vừa save thành công (isSubmitting đã reset về false)
      if (!isSubmitting) {
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
