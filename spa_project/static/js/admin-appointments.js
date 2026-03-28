// ===== SETTINGS =====
const START_HOUR = 9;
const END_HOUR = 22;
const SLOT_MIN = 30;

// ===== API BASE URL =====
const API_BASE = '/api';

// ===== DATA (loaded from API) =====
let ROOMS = [];
let SERVICES = [];
let APPOINTMENTS = [];

// ===== DOM =====
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
const duration = document.getElementById("duration");
const apptStatus = document.getElementById("apptStatus");
const payStatus = document.getElementById("payStatus");
const note = document.getElementById("note");
const toastEl = document.getElementById("toast");
let toast = null;
const toastTitle = document.getElementById("toastTitle");
const toastBody = document.getElementById("toastBody");

// ===== CSRF HELPER =====
function getCSRFToken() {
  const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookieValue ? cookieValue.split('=')[1] : '';
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
    ROOMS = [
      { id: "P01", name: "1", capacity: 3 },
      { id: "P02", name: "2", capacity: 2 },
      { id: "P03", name: "3", capacity: 4 },
      { id: "P04", name: "4", capacity: 2 },
      { id: "P05", name: "5", capacity: 3 },
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
  if (date) url += `?date=${date}`;
  const result = await apiGet(url);
  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
  } else {
    APPOINTMENTS = [];
  }
}

async function loadBookingRequests() {
  console.log('Loading booking requests from:', `${API_BASE}/booking-requests/`);
  const result = await apiGet(`${API_BASE}/booking-requests/`);
  console.log('Booking requests result:', result);
  return result.success && result.appointments ? result.appointments : [];
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
  if(s==="not_arrived") return "status-not_arrived";
  if(s==="arrived") return "status-arrived";
  if(s==="completed") return "status-completed";
  if(s==="cancelled") return "status-cancelled";
  return "status-pending";
}

function statusLabel(s){
  if(s==="pending") return "Chờ xác nhận";
  if(s==="not_arrived") return "Chưa đến";
  if(s==="arrived") return "Đã đến";
  if(s==="completed") return "Hoàn thành";
  if(s==="cancelled") return "Đã hủy";
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

function getSlotWidth(){ return parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--slotW")) || 52; }

function capacityOK({roomId, day, start, end, guestsCount, ignoreId}){
  const roomInfo = ROOMS.find(r=>r.id===roomId);
  if(!roomInfo) return false;
  const newS = minutesFromStart(start), newE = minutesFromStart(end);
  let sum = 0;
  APPOINTMENTS.filter(a => a.roomId===roomId && a.date===day && a.apptStatus!=="cancelled" && a.id!==ignoreId)
    .forEach(a=>{ const s=minutesFromStart(a.start), e=minutesFromStart(a.end); if(overlaps(newS,newE,s,e)) sum += Number(a.guests)||0; });
  return (sum + guestsCount) <= roomInfo.capacity;
}

// ===== RENDER =====
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
    for(let g=0; g<need; g++){
      let foundLane = -1;
      for(let li=0; li<cap; li++){
        if(!laneIntervals[li].some(it => overlaps(s,e,it.startMin,it.endMin))){ foundLane = li; break; }
      }
      if(foundLane === -1) break;
      laneIntervals[foundLane].push({startMin:s, endMin:e, apptId:a.id});
      placements.push({ appt: a, laneIndex: foundLane });
    }
  }
  return { cap, placements };
}

function renderGrid(){
  grid.innerHTML = "";
  const day = dayPicker.value;
  const searchTerm = searchInput.value.toLowerCase().trim();
  ROOMS.forEach((r)=>{
    let appts = APPOINTMENTS.filter(a => a.date===day && a.roomId===r.id);
    if(searchTerm) appts = appts.filter(a => a.customerName.toLowerCase().includes(searchTerm) || a.phone.includes(searchTerm) || a.service.toLowerCase().includes(searchTerm) || a.id.toLowerCase().includes(searchTerm));
    const { cap, placements } = allocateRoomLanes(r.id, day, appts);
    for(let lane=0; lane<cap; lane++){
      const laneRow = document.createElement("div");
      laneRow.className = "lane-row";
      laneRow.dataset.roomId = r.id;
      laneRow.dataset.lane = lane;
      laneRow.innerHTML = `${lane===0?`<div class="roomcell"><span class="dot"></span>${r.name}</div>`:`<div class="roomcell muted"><span class="dot"></span>${r.name}</div>`}<div class="slots" data-room="${r.id}" data-lane="${lane}"></div>`;
      const slotsEl = laneRow.querySelector(".slots");
      slotsEl.addEventListener("click", (e)=>{
        const rect = slotsEl.getBoundingClientRect();
        const x = e.clientX - rect.left + slotsEl.scrollLeft;
        const slotIndex = Math.floor(x / getSlotWidth());
        const minutes = slotIndex * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes/60))}:${pad2(minutes%60)}`;
        openCreateModal({ roomId: r.id, day, time: clickedTime });
      });
      placements.filter(p => p.laneIndex === lane).forEach(p=>{
        const a = p.appt;
        const block = document.createElement("div");
        block.className = `appt ${statusClass(a.apptStatus)}`;
        block.dataset.id = a.id;
        const leftMin = minutesFromStart(a.start), durMin = Math.max(30, minutesFromStart(a.end)-leftMin);
        block.style.left = `${(leftMin/SLOT_MIN) * getSlotWidth()}px`;
        block.style.width = `${Math.max(36, (durMin/SLOT_MIN) * getSlotWidth())}px`;
        block.innerHTML = `<div class="t1">${a.customerName} • ${a.service}</div><div class="t2">${a.start}-${a.end} • ${a.guests} khách</div>`;
        block.addEventListener("click", (ev)=>{ ev.stopPropagation(); openEditModal(a.id); });
        slotsEl.appendChild(block);
      });
      grid.appendChild(laneRow);
    }
  });
}

async function renderWebRequests(){
  const searchTerm = searchInput.value.toLowerCase().trim();
  let rows = await loadBookingRequests();
  console.log('Rendering web requests, rows:', rows);

  // Debug: log chi tiết từng row
  rows.forEach(r => console.log('  -', r.id, r.customerName, 'roomId:', r.roomId, 'status:', r.apptStatus));

  if(searchTerm) rows = rows.filter(a => a.customerName.toLowerCase().includes(searchTerm) || a.phone.includes(searchTerm) || a.service.toLowerCase().includes(searchTerm) || a.id.toLowerCase().includes(searchTerm));
  rows = rows.sort((a,b)=> (a.date+a.start).localeCompare(b.date+b.start));
  webCount.textContent = String(rows.length);
  if(rows.length === 0){ webTbody.innerHTML = `<tr><td colspan="11" class="text-center text-muted py-4">Không có yêu cầu đặt lịch trực tuyến</td></tr>`; return; }
  webTbody.innerHTML = rows.map(a => `<tr>
    <td class="fw-semibold">${a.id}</td><td>${a.customerName}</td><td>${a.phone}</td><td>${a.email||""}</td><td>${a.service}</td>
    <td>${a.date}</td><td>${a.start} - ${a.end}</td><td>${a.durationMin||""} phút</td>
    <td class="text-truncate" style="max-width:220px;" title="${(a.note||"").replaceAll('"','&quot;')}">${a.note||""}</td>
    <td><span class="badge ${a.apptStatus==='pending'?'bg-warning':(a.apptStatus==='cancelled'?'bg-danger':'bg-success')} text-white">${statusLabel(a.apptStatus)}</span></td>
    <td class="text-end">${a.apptStatus==="pending"?`<div class="btn-group btn-group-sm"><button class="btn btn-warning px-2" data-id="${a.id}" onclick="approveWeb('${a.id}')"><i class="fas fa-check"></i><span class="d-none d-md-inline ms-1">Xác nhận</span></button><button class="btn btn-outline-danger px-2" data-id="${a.id}" onclick="rejectWeb('${a.id}')"><i class="fas fa-xmark"></i><span class="d-none d-md-inline ms-1">Từ chối</span></button></div>`:`<button class="btn btn-sm btn-outline-secondary" data-id="${a.id}" onclick="openEditModal('${a.id}')"><i class="fas fa-pen me-1"></i>Xem/Sửa</button>`}</td>
  </tr>`).join("");
}

window.approveWeb = async function(id){
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (result.success && result.appointment) { openEditModalWithData(result.appointment); apptStatus.value = "not_arrived"; showToast("info","Gợi ý","Chọn phòng/thời gian nếu cần rồi bấm Lưu để xác nhận"); }
  else showToast("error","Lỗi","Không tìm thấy lịch hẹn");
}

window.rejectWeb = async function(id){
  if(!confirm("Từ chối yêu cầu đặt lịch này?")) return;
  const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'cancelled' });
  if (result.success) { showToast("success","OK","Đã từ chối yêu cầu"); await renderWebRequests(); await refreshData(); }
  else showToast("error","Lỗi", result.error || "Không thể từ chối yêu cầu");
}

// ===== MODAL =====
function fillRoomsSelect(){ room.innerHTML = ROOMS.map(r=>`<option value="${r.id}">${r.name}</option>`).join(""); }
function fillServicesSelect(){ service.innerHTML = `<option value="">-- Chọn dịch vụ --</option>` + SERVICES.map(s=>`<option value="${s.id}">${s.name} (${s.duration} phút)</option>`).join(""); }

function openCreateModal(prefill={}){
  resetModalError();
  modalTitle.textContent = "Tạo lịch hẹn";
  apptId.value = "";
  btnDelete.classList.add("d-none");
  customerName.value = ""; phone.value = ""; email.value = ""; service.value = "";
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

btnSave.addEventListener("click", ()=> form.requestSubmit());

form.addEventListener("submit", async (e)=>{
  e.preventDefault();
  
  // ===== NGĂN SUBMIT LẶP =====
  if (isSubmitting) {
    console.log('Đang xử lý, bỏ qua submit lặp');
    return;
  }
  
  resetModalError();
  form.classList.add("was-validated");
  const id = apptId.value.trim();
  const nameVal = customerName.value.trim();
  const phoneVal = phone.value.trim();
  const serviceVal = service.value;
  const roomVal = room.value;
  const guestsVal = Number(guests.value);
  const dayVal = date.value;
  const startVal = time.value;
  const durationVal = Number(duration.value);

  customerName.setCustomValidity(nameVal ? "" : "invalid");
  phone.setCustomValidity((phoneVal && isValidPhone(phoneVal)) ? "" : "invalid");
  service.setCustomValidity(serviceVal ? "" : "invalid");
  room.setCustomValidity(roomVal ? "" : "invalid");
  guests.setCustomValidity((Number.isFinite(guestsVal) && guestsVal>0) ? "" : "invalid");
  date.setCustomValidity(dayVal ? "" : "invalid");
  time.setCustomValidity(startVal ? "" : "invalid");
  duration.setCustomValidity((Number.isFinite(durationVal) && durationVal>0) ? "" : "invalid");

  if(!form.checkValidity()){
    if(!nameVal) modalError.textContent = "Vui lòng nhập họ tên khách hàng";
    else if(!phoneVal || !isValidPhone(phoneVal)) modalError.textContent = "Số điện thoại không hợp lệ";
    else if(!serviceVal) modalError.textContent = "Vui lòng chọn dịch vụ";
    else if(!roomVal) modalError.textContent = "Vui lòng chọn phòng";
    else modalError.textContent = "Vui lòng điền đầy đủ thông tin";
    modalError.classList.remove("d-none");
    return;
  }

  const endVal = addMinutesToTime(startVal, durationVal);
  if(minutesFromStart(startVal) < 0 || minutesFromStart(endVal) > (END_HOUR-START_HOUR)*60){
    modalError.textContent = "Giờ hẹn không hợp lệ (ngoài giờ làm việc)";
    modalError.classList.remove("d-none");
    return;
  }

  if(!capacityOK({roomId: roomVal, day: dayVal, start: startVal, end: endVal, guestsCount: guestsVal, ignoreId: id || null})){
    modalError.textContent = "Phòng đã đủ chỗ ở khung giờ này";
    modalError.classList.remove("d-none");
    return;
  }

  const payload = { customerName: nameVal, phone: phoneVal.replace(/\D/g,""), email: email.value.trim(), serviceId: serviceVal, roomId: roomVal, guests: guestsVal, date: dayVal, time: startVal, duration: durationVal, note: note.value.trim(), apptStatus: apptStatus.value, payStatus: payStatus.value };

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
if(searchInput){ searchInput.addEventListener("input", function(){ renderGrid(); renderWebRequests(); }); }

// ===== INIT =====
document.addEventListener("DOMContentLoaded", async ()=>{
  if (modalEl) modal = new bootstrap.Modal(modalEl);
  if (toastEl) toast = new bootstrap.Toast(toastEl);

  // Initialize delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  if(sidebarToggle) sidebarToggle.addEventListener("click", ()=> sidebar.classList.toggle("show"));

  await loadRooms();
  await loadServices();
  fillRoomsSelect();

  dayPicker.value = todayISO();
  renderHeader();
  await refreshData();
  await renderWebRequests();

  if(btnToday) btnToday.addEventListener("click", ()=> setDay(todayISO()));
  if(btnPrev) btnPrev.addEventListener("click", ()=> shiftDay(-1));
  if(btnNext) btnNext.addEventListener("click", ()=> shiftDay(1));
  if(dayPicker) dayPicker.addEventListener("change", ()=> refreshData());

  window.openEditModal = openEditModal;
});