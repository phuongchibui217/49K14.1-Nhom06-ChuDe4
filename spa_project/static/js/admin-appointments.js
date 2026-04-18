// ===== 1. SETTINGS - cấu hình =====
const START_HOUR = 9;  // Giờ mở cửa (9:00 sáng)
const END_HOUR = 21;   // Giờ đóng cửa (21:00 tối)
const SLOT_MIN = 30; // 1 ô lịch = 30 phút

// ===== API BASE URL- đường dẫn API để gọi BE =====
const API_BASE = '/api';

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

      // click vào ô trống ==> tạo lịch
      // Dùng event delegation: chỉ xử lý khi click trực tiếp vào slotsEl
      // (click vào .appt block sẽ bị stopPropagation trước khi bubble lên đây)
      slotsEl.addEventListener("click", (e)=>{
        // Bỏ qua nếu click xuất phát từ bên trong một appointment block
        if (e.target.closest('.appt')) return;

        const rect = slotsEl.getBoundingClientRect();
        const x = e.clientX - rect.left;
        // Tính theo tỉ lệ % → phút → giờ:phút
        const ratio = Math.max(0, Math.min(1, x / rect.width));
        const totalMin = totalTimelineMinutes();
        // Làm tròn xuống bội số của SLOT_MIN
        const rawMin = ratio * totalMin;
        const minutes = Math.floor(rawMin / SLOT_MIN) * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes/60))}:${pad2(minutes%60)}`;
        // Lấy ngày hiện tại từ dayPicker (không dùng closure day để luôn đúng ngày đang chọn)
        const currentDay = dayPicker.value;
        openCreateModal({ roomId: r.id, day: currentDay, time: clickedTime });
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
// Nhận diện khách qua phone/email — không có search box riêng
let _phoneTimer = null;
let _emailTimer = null;

function initCustomerSearch() {
  const phoneEl       = document.getElementById('phone');
  const emailEl       = document.getElementById('email');
  const clearBtnPhone = document.getElementById('clearCustomerMatchBtnPhone');
  const clearBtnEmail = document.getElementById('clearCustomerMatchBtnEmail');
  if (!phoneEl) return;

  // Lookup khi nhập phone (debounce 500ms)
  phoneEl.addEventListener('input', () => {
    clearTimeout(_phoneTimer);
    _clearMatchBadge();
    const val = phoneEl.value.replace(/\D/g, '');
    if (val.length >= 9) {
      _phoneTimer = setTimeout(() => _lookupByPhone(val), 500);
    }
  });

  // Lookup khi nhập email (debounce 600ms)
  if (emailEl) {
    emailEl.addEventListener('input', () => {
      clearTimeout(_emailTimer);
      _clearMatchBadge();
      const val = emailEl.value.trim();
      if (val.includes('@') && val.length >= 6) {
        _emailTimer = setTimeout(() => _lookupByEmail(val), 600);
      }
    });
  }

  // Nhấn X → xóa liên kết + xóa toàn bộ thông tin khách
  if (clearBtnPhone) clearBtnPhone.addEventListener('click', () => _clearMatchBadge(true));
  if (clearBtnEmail) clearBtnEmail.addEventListener('click', () => _clearMatchBadge(true));
}

async function _lookupByPhone(phone) {
  if (document.getElementById('apptId').value.trim()) return; // chỉ lookup khi tạo mới
  try {
    const res = await apiGet(`${API_BASE}/customers/search/?q=${encodeURIComponent(phone)}`);
    if (!res.success) return;
    const match = res.customers.find(c => c.phone.replace(/\D/g, '') === phone);
    if (match) _applyMatch(match, 'phone');
  } catch(e) { /* silent */ }
}

async function _lookupByEmail(email) {
  if (document.getElementById('apptId').value.trim()) return;
  try {
    const res = await apiGet(`${API_BASE}/customers/search/?q=${encodeURIComponent(email)}`);
    if (!res.success) return;
    const match = res.customers.find(c => c.email && c.email.toLowerCase() === email.toLowerCase());
    if (match) _applyMatch(match, 'email');
  } catch(e) { /* silent */ }
}

function _applyMatch(c, via) {
  document.getElementById('selectedCustomerId').value = c.id;

  // Autofill chỉ các field còn trống
  const nameEl  = document.getElementById('customerName');
  const phoneEl = document.getElementById('phone');
  const emailEl = document.getElementById('email');
  if (nameEl  && !nameEl.value.trim())  nameEl.value  = c.fullName;
  if (phoneEl && !phoneEl.value.trim()) phoneEl.value = c.phone;
  if (emailEl && !emailEl.value.trim()) emailEl.value = c.email || '';

  // Hiện đúng badge theo field trigger
  const badgePhone = document.getElementById('customerMatchBadgePhone');
  const labelPhone = document.getElementById('customerMatchLabelPhone');
  const badgeEmail = document.getElementById('customerMatchBadgeEmail');
  const labelEmail = document.getElementById('customerMatchLabelEmail');

  if (via === 'email') {
    if (badgeEmail && labelEmail) {
      labelEmail.textContent = `Khách đã có hồ sơ: ${c.fullName}`;
      badgeEmail.classList.remove('d-none');
    }
    if (badgePhone) badgePhone.classList.add('d-none');
  } else {
    if (badgePhone && labelPhone) {
      labelPhone.textContent = `Khách đã có hồ sơ: ${c.fullName}`;
      badgePhone.classList.remove('d-none');
    }
    if (badgeEmail) badgeEmail.classList.add('d-none');
  }
}

// clearFields=true khi nhấn X → xóa luôn thông tin khách đã fill
function _clearMatchBadge(clearFields = false) {
  document.getElementById('selectedCustomerId').value = '';
  const badgePhone = document.getElementById('customerMatchBadgePhone');
  const badgeEmail = document.getElementById('customerMatchBadgeEmail');
  if (badgePhone) badgePhone.classList.add('d-none');
  if (badgeEmail) badgeEmail.classList.add('d-none');

  if (clearFields) {
    const nameEl  = document.getElementById('customerName');
    const phoneEl = document.getElementById('phone');
    const emailEl = document.getElementById('email');
    if (nameEl)  nameEl.value  = '';
    if (phoneEl) phoneEl.value = '';
    if (emailEl) emailEl.value = '';
  }
}

// Escape HTML để tránh XSS
function _esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function openCreateModal(prefill={}){
  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");

  // Đổi text nút save theo trạng thái tạo mới
  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Tạo lịch hẹn";

  // Reset customer match badge
  document.getElementById('selectedCustomerId').value = '';
  _clearMatchBadge();

  // Luôn lấy instance hiện tại hoặc tạo mới — tránh instance bị stale
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    if (existing) {
      modal = existing;
    } else {
      modal = new bootstrap.Modal(modalEl);
    }
  }

  // Nếu vẫn không có modal → báo lỗi rõ ràng
  if (!modal) {
    console.error('[openCreateModal] Không thể khởi tạo modal. modalEl:', modalEl, 'bootstrap:', typeof bootstrap);
    return;
  }

  // Reset customer info
  customerName.value = "";
  phone.value = "";
  email.value = "";
  guests.value = 1;
  note.value = "";

  // Reset appointment info
  service.value = "";
  const variantSelect = document.getElementById("variant");
  if (variantSelect) {
    variantSelect.innerHTML = '<option value="">-- Chọn dịch vụ trước --</option>';
    variantSelect.disabled = true;
  }
  const variantInfo = document.getElementById("variantInfo");
  if (variantInfo) variantInfo.classList.add("d-none");

  room.value = prefill.roomId || (ROOMS[0]?.id || "");
  date.value = prefill.day || dayPicker.value;
  time.value = prefill.time || "09:00";
  apptStatus.value = "NOT_ARRIVED";
  payStatus.value = "UNPAID";

  // Reset new fields
  const sourceSelect = document.getElementById("source");
  if (sourceSelect) sourceSelect.value = "DIRECT";
  const staffNoteTextarea = document.getElementById("staffNote");
  if (staffNoteTextarea) staffNoteTextarea.value = "";

  form.classList.remove("was-validated");
  if (modal) {
    modal.show();
  } else {
    console.error('[openCreateModal] modal chưa được khởi tạo — kiểm tra lại #apptModal trong HTML');
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

  // Đổi text nút save theo trạng thái chỉnh sửa
  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Lưu lịch hẹn";

  // Ẩn badge nhận diện khi edit (không lookup lại)
  _clearMatchBadge();
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
  if (isSubmitting) {
    console.log('Đang xử lý, bỏ qua submit lặp');
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
  
  // Get duration from selected variant
  const variantSelect = document.getElementById("variant");
  const variantVal = variantSelect ? variantSelect.value : "";
  let durationVal = 60; // default
  
  if (variantSelect && variantVal) {
    const selectedOption = variantSelect.options[variantSelect.selectedIndex];
    if (selectedOption && selectedOption.dataset.duration) {
      durationVal = Number(selectedOption.dataset.duration);
    }
  }

  // ===== BƯỚC 1: VALIDATE =====
  customerName.setCustomValidity(nameVal ? "" : "invalid");
  phone.setCustomValidity((phoneVal && isValidPhone(phoneVal)) ? "" : "invalid");
  service.setCustomValidity(serviceVal ? "" : "invalid");
  
  // Validate variant is selected
  if (variantSelect) {
    variantSelect.setCustomValidity(variantVal ? "" : "invalid");
  }
  
  room.setCustomValidity(roomVal ? "" : "invalid");
  guests.setCustomValidity((Number.isFinite(guestsVal) && guestsVal>0) ? "" : "invalid");
  date.setCustomValidity(dayVal ? "" : "invalid");
  time.setCustomValidity(startVal ? "" : "invalid");

  if(!form.checkValidity()){
    if(!nameVal) modalError.textContent = "Vui lòng nhập họ tên khách hàng";
    else if(!phoneVal || !isValidPhone(phoneVal)) modalError.textContent = "Số điện thoại không hợp lệ";
    else if(!serviceVal) modalError.textContent = "Vui lòng chọn dịch vụ";
    else if(!variantVal) modalError.textContent = "Vui lòng chọn gói dịch vụ";
    else if(!roomVal) modalError.textContent = "Vui lòng chọn phòng";
    else modalError.textContent = "Vui lòng điền đầy đủ thông tin";
    modalError.classList.remove("d-none");
    return;
  }

  // ===== BƯỚC 2: KIỂM TRA GIỜ HẸN =====
  const endVal = addMinutesToTime(startVal, durationVal);
  if(minutesFromStart(startVal) < 0 || minutesFromStart(endVal) > (END_HOUR-START_HOUR)*60){
    modalError.textContent = "Giờ hẹn không hợp lệ (ngoài giờ làm việc)";
    modalError.classList.remove("d-none");
    return;
  }

  // ===== BƯỚC 3: KIỂM TRA TRÙNG LỊCH =====
  if(!capacityOK({roomId: roomVal, day: dayVal, start: startVal, end: endVal, guestsCount: guestsVal, ignoreId: id || null})){
    modalError.textContent = "Phòng đã đủ chỗ ở khung giờ này";
    modalError.classList.remove("d-none");
    return;
  }
  // ===== BƯỚC 4: GỌI API =====
  const selectedCustId = document.getElementById("selectedCustomerId")?.value || "";
  const payload = { 
    customerId: selectedCustId ? Number(selectedCustId) : null,
    customerName: nameVal, 
    phone: phoneVal.replace(/\D/g,""), 
    email: email.value.trim(), 
    serviceId: serviceVal,
    variantId: variantVal,
    roomId: roomVal, 
    guests: guestsVal, 
    date: dayVal, 
    time: startVal, 
    duration: durationVal, 
    note: note.value.trim(), 
    apptStatus: apptStatus.value, 
    payStatus: payStatus.value,
    source: document.getElementById("source") ? document.getElementById("source").value : "DIRECT",
    staffNote: document.getElementById("staffNote") ? document.getElementById("staffNote").value.trim() : ""
  };

  // ===== BẬT LOADING STATE =====
  isSubmitting = true;
  const loadingText = id ? 'Đang cập nhật...' : 'Đang tạo lịch...';
  setButtonLoading(btnSave, loadingText);

  try{
    let result;
    if(id){ result = await apiPost(`${API_BASE}/appointments/${id}/update/`, payload); }
    else { result = await apiPost(`${API_BASE}/appointments/create/`, payload); }

    if (result.success) {
      if (modal) modal.hide();
      if(dayPicker.value !== dayVal) dayPicker.value = dayVal;
      await refreshData();
      await renderWebRequests(); // Refresh bảng yêu cầu đặt lịch luôn
      showToast("success","Thành công", result.message || (id ? "Cập nhật lịch hẹn thành công" : "Tạo lịch hẹn thành công"));
    } else {
      modalError.textContent = result.error || "Không thể lưu lịch hẹn";
      modalError.classList.remove("d-none");
    }
  }catch(err){
    modalError.textContent = "Không thể lưu lịch hẹn. Vui lòng thử lại sau";
    modalError.classList.remove("d-none");
  } finally {
    // ===== TẮT LOADING STATE =====
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

  // Hiển thị thông tin lịch hẹn trong modal
  document.getElementById('deleteAppointmentCode').textContent = id;

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

// ===== SEARCH =====
if(searchInput){
  searchInput.addEventListener("input", function(){
    clearTimeout(searchInput._debounce);
    searchInput._debounce = setTimeout(() => refreshData(), 350);
  });
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

  // ===== REAL-TIME BOOKING COUNT UPDATE (WebSocket badge dispatcher) =====
  let previousPendingCount = null;
  window.addEventListener('booking-pending-count:update', async function(event){
    const currentPendingCount = Number(event?.detail?.count || 0);

    if(previousPendingCount !== null && currentPendingCount !== previousPendingCount){
      console.log('🔄 Pending count changed from', previousPendingCount, 'to', currentPendingCount, '- refreshing web requests table');
      await renderWebRequests();
    }

    previousPendingCount = currentPendingCount;
  });

  if(btnToday) btnToday.addEventListener("click", ()=> setDay(todayISO()));
  if(btnPrev) btnPrev.addEventListener("click", ()=> shiftDay(-1));
  if(btnNext) btnNext.addEventListener("click", ()=> shiftDay(1));
  if(dayPicker) dayPicker.addEventListener("change", ()=> refreshData());

  // Filter bar — tab Lịch theo phòng
  const schedFilterBtn  = document.getElementById('schedFilterBtn');
  const schedClearBtn   = document.getElementById('schedClearBtn');
  const statusFilter    = document.getElementById('statusFilter');
  const serviceFilterEl = document.getElementById('serviceFilter');
  const sourceFilterEl  = document.getElementById('sourceFilter');

  if(schedFilterBtn) schedFilterBtn.addEventListener('click', ()=> refreshData());
  if(schedClearBtn) schedClearBtn.addEventListener('click', ()=>{
    if(statusFilter)    statusFilter.value    = '';
    if(serviceFilterEl) serviceFilterEl.value = '';
    if(sourceFilterEl)  sourceFilterEl.value  = '';
    if(searchInput)     searchInput.value     = '';
    refreshData();
  });
  // Auto-apply khi đổi dropdown
  if(statusFilter)    statusFilter.addEventListener('change',    ()=> refreshData());
  if(serviceFilterEl) serviceFilterEl.addEventListener('change', ()=> refreshData());
  if(sourceFilterEl)  sourceFilterEl.addEventListener('change',  ()=> refreshData());

  // Khi đổi bộ lọc trạng thái → render lại bảng yêu cầu đặt lịch (AUTO-FILTER)
  if(webStatusFilter) webStatusFilter.addEventListener("change", ()=> renderWebRequests());

  // Nút Lọc và filter ngày/search cho tab web
  const webFilterBtn = document.getElementById("webFilterBtn");
  const webDateFilter = document.getElementById("webDateFilter");
  const webSearchInput = document.getElementById("webSearchInput");

  function webHasActiveFilter() {
    return (webStatusFilter && webStatusFilter.value) ||
           (webDateFilter && webDateFilter.value) ||
           (webSearchInput && webSearchInput.value.trim());
  }

  function updateWebFilterBtn() {
    if (!webFilterBtn) return;
    if (webHasActiveFilter()) {
      webFilterBtn.className = 'btn btn-outline-secondary w-100';
      webFilterBtn.innerHTML = '<i class="fas fa-rotate-left me-1"></i>Bỏ lọc';
    } else {
      webFilterBtn.className = 'btn btn-secondary w-100';
      webFilterBtn.innerHTML = '<i class="fas fa-filter me-2"></i>Lọc';
    }
  }

  if(webFilterBtn) webFilterBtn.addEventListener("click", ()=> {
    if (webHasActiveFilter()) {
      if(webStatusFilter)  webStatusFilter.value = '';
      if(webDateFilter)    webDateFilter.value   = '';
      if(webSearchInput)   webSearchInput.value  = '';
    }
    renderWebRequests();
    updateWebFilterBtn();
  });

  if(webDateFilter) webDateFilter.addEventListener("change", ()=> { renderWebRequests(); updateWebFilterBtn(); });
  if(webSearchInput) {
    webSearchInput.addEventListener("input", function() {
      clearTimeout(webSearchInput._debounce);
      webSearchInput._debounce = setTimeout(() => { renderWebRequests(); updateWebFilterBtn(); }, 350);
    });
  }
  if(webStatusFilter) webStatusFilter.addEventListener("change", ()=> updateWebFilterBtn());

  window.openEditModal = openEditModal;
  window.renderWebRequests = renderWebRequests;
});
