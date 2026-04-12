// ============================================================
// QUẢN LÝ LỊCH HẸN SPA - PHIÊN BẢN ĐƠN GIẢN
// Mô tả: JS chỉ làm giao diện, logic xử lý ở Backend (Django)
// ============================================================

// ===== 1. CẤU HÌNH =====
const API_BASE = '/api';

// ===== 2. BIẾN TOÀN CỤC =====
let ROOMS = [];
let SERVICES = [];
let APPOINTMENTS = [];

// ===== 3. DOM ELEMENTS =====
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

// ===== 4. BIẾN CHẠN SUBMIT LẶP =====
let isSubmitting = false;

// ===== 5. HELPER: HIỂN THỊ TOAST =====
function showToast(type, title, message) {
  const header = toastEl.querySelector(".toast-header");
  const icon = header.querySelector("i");
  header.className = "toast-header";

  if (type === "success") {
    header.classList.add("bg-success", "text-white");
    icon.className = "fas fa-check-circle me-2";
  } else if (type === "warning") {
    header.classList.add("bg-warning", "text-dark");
    icon.className = "fas fa-exclamation-triangle me-2";
  } else if (type === "error") {
    header.classList.add("bg-danger", "text-white");
    icon.className = "fas fa-times-circle me-2";
  } else {
    header.classList.add("bg-info", "text-white");
    icon.className = "fas fa-info-circle me-2";
  }

  toastTitle.textContent = title;
  toastBody.textContent = message;
  if (toast) toast.show();
}

// ===== 6. HELPER: RESET MODAL ERROR =====
function resetModalError() {
  modalError.classList.add("d-none");
  modalError.textContent = "";
}

// ===== 7. HELPER: LOADING STATE CHO BUTTON =====
function setButtonLoading(btn, loadingText = 'Đang xử lý...') {
  if (!btn) return;
  if (!btn.dataset.originalText) {
    btn.dataset.originalText = btn.innerHTML;
  }
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
}

function resetButton(btn) {
  if (!btn) return;
  btn.disabled = false;
  if (btn.dataset.originalText) {
    btn.innerHTML = btn.dataset.originalText;
    delete btn.dataset.originalText;
  }
}

// ===== 8. API CALLS =====
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

function getCSRFToken() {
  const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookieValue ? cookieValue.split('=')[1] : '';
}

// ===== 9. LOAD DỮ LIỆU TỪ API =====
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
  if (date) url += `?date=${date}`;
  const result = await apiGet(url);
  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
  } else {
    APPOINTMENTS = [];
  }
}

async function loadBookingRequests() {
  const result = await apiGet(`${API_BASE}/booking-requests/`);
  return result.success && result.appointments ? result.appointments : [];
}

// ===== 10. RENDER ĐƠN GIẢN =====
function fillRoomsSelect() {
  room.innerHTML = ROOMS.map(r => `<option value="${r.id}">${r.name}</option>`).join("");
}

function fillServicesSelect() {
  service.innerHTML = `<option value="">-- Chọn dịch vụ --</option>` +
    SERVICES.map(s => `<option value="${s.id}">${s.name} (${s.duration} phút)</option>`).join("");
}

// Render lưới lịch - Backend đã tính toán xong, JS chỉ cần hiển thị
async function renderGrid() {
  const day = dayPicker.value;
  const searchTerm = searchInput.value.toLowerCase().trim();

  // Gọi API để backend render lưới (backend đã tính toán lane allocation)
  let url = `${API_BASE}/appointments/render-grid/?date=${day}`;
  if (searchTerm) url += `&search=${searchTerm}`;

  const result = await apiGet(url);

  if (result.success && result.html) {
    // Backend trả về HTML đã render xong
    grid.innerHTML = result.html;

    // Gắn event listener cho các block lịch
    document.querySelectorAll('.appt-block').forEach(block => {
      block.addEventListener('click', function() {
        const apptId = this.dataset.id;
        openEditModal(apptId);
      });
    });

    // Gắn event listener cho các ô trống
    document.querySelectorAll('.empty-slot').forEach(slot => {
      slot.addEventListener('click', function() {
        const roomId = this.dataset.roomId;
        const time = this.dataset.time;
        openCreateModal({ roomId, day, time });
      });
    });
  } else {
    grid.innerHTML = `<div class="text-center p-4 text-muted">
      Không thể tải lịch. Vui lòng thử lại.
    </div>`;
  }
}

// Render bảng yêu cầu đặt lịch online
async function renderWebRequests() {
  const searchTerm = searchInput.value.toLowerCase().trim();
  let rows = await loadBookingRequests();

  if (searchTerm) {
    rows = rows.filter(a =>
      a.customerName.toLowerCase().includes(searchTerm) ||
      a.phone.includes(searchTerm) ||
      a.service.toLowerCase().includes(searchTerm) ||
      a.id.toLowerCase().includes(searchTerm)
    );
  }

  rows = rows.sort((a, b) => (a.date + a.start).localeCompare(b.date + b.start));
  webCount.textContent = String(rows.length);

  if (rows.length === 0) {
    webTbody.innerHTML = `<tr><td colspan="11" class="text-center text-muted py-4">
      Không có yêu cầu đặt lịch trực tuyến
    </td></tr>`;
    return;
  }

  webTbody.innerHTML = rows.map(a => `
    <tr>
      <td class="fw-semibold">${a.id}</td>
      <td>${a.customerName}</td>
      <td>${a.phone}</td>
      <td>${a.email || ""}</td>
      <td>${a.service}</td>
      <td>${a.date}</td>
      <td>${a.start} - ${a.end}</td>
      <td>${a.durationMin || ""} phút</td>
      <td class="text-truncate" style="max-width:220px;" title="${(a.note || "").replaceAll('"', '&quot;')}">${a.note || ""}</td>
      <td><span class="badge ${a.apptStatus === 'pending' ? 'bg-warning' : (a.apptStatus === 'cancelled' ? 'bg-danger' : 'bg-success')} text-white">${statusLabel(a.apptStatus)}</span></td>
      <td class="text-end">${a.apptStatus === "pending" ? `<div class="btn-group btn-group-sm"><button class="btn btn-warning px-2" data-id="${a.id}" onclick="approveWeb('${a.id}')"><i class="fas fa-check"></i><span class="d-none d-md-inline ms-1">Xác nhận</span></button><button class="btn btn-outline-danger px-2" data-id="${a.id}" onclick="rejectWeb('${a.id}')"><i class="fas fa-xmark"></i><span class="d-none d-md-inline ms-1">Từ chối</span></button></div>` : `<button class="btn btn-sm btn-outline-secondary" data-id="${a.id}" onclick="openEditModal('${a.id}')"><i class="fas fa-pen me-1"></i>Xem/Sửa</button>`}</td>
    </tr>
  `).join("");
}

function statusLabel(s) {
  if (s === "pending") return "Chờ xác nhận";
  if (s === "not_arrived") return "Chưa đến";
  if (s === "arrived") return "Đã đến";
  if (s === "completed") return "Hoàn thành";
  if (s === "cancelled") return "Đã hủy";
  return s;
}

// ===== 11. MODAL =====
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
  guests.value = 1;
  date.value = prefill.day || dayPicker.value;
  time.value = prefill.time || "09:00";
  duration.value = "60";
  apptStatus.value = "not_arrived";
  payStatus.value = "unpaid";
  note.value = "";
  form.classList.remove("was-validated");

  // Auto-fill room nếu có
  if (prefill.roomId) {
    room.value = prefill.roomId;
  }

  if (modal) modal.show();
}

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

function openEditModalWithData(a) {
  resetModalError();
  modalTitle.textContent = `Chỉnh sửa • ${a.id}`;
  apptId.value = a.id;
  btnDelete.classList.remove("d-none");

  // Điền form
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

  // Trigger service change để auto-fill duration
  if (service.value) {
    service.dispatchEvent(new Event('change'));
  }

  if (modal) modal.show();
}

// ===== 12. FORM SUBMIT - ĐƠN GIẢN HÓA =====
btnSave.addEventListener("click", () => form.requestSubmit());

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // ===== NGĂN SUBMIT LẶP =====
  if (isSubmitting) {
    console.log('Đang xử lý, bỏ qua submit lặp');
    return;
  }

  resetModalError();

  // Thu thập dữ liệu từ form (KHÔNG validate ở frontend)
  const payload = {
    customerName: customerName.value.trim(),
    phone: phone.value.trim(),
    email: email.value.trim(),
    serviceId: service.value,
    roomId: room.value,
    guests: Number(guests.value),
    date: date.value,
    time: time.value,
    duration: Number(duration.value),
    note: note.value.trim(),
    apptStatus: apptStatus.value,
    payStatus: payStatus.value
  };

  // ===== BẬT LOADING =====
  isSubmitting = true;
  const loadingText = apptId.value ? 'Đang cập nhật...' : 'Đang tạo lịch...';
  setButtonLoading(btnSave, loadingText);

  try {
    // GỌI API - BACKEND SẼ LO TẤT CẢ VALIDATE
    let result;
    if (apptId.value) {
      result = await apiPost(`${API_BASE}/appointments/${apptId.value}/update/`, payload);
    } else {
      result = await apiPost(`${API_BASE}/appointments/create/`, payload);
    }

    if (result.success) {
      if (modal) modal.hide();
      if (dayPicker.value !== payload.date) dayPicker.value = payload.date;
      await refreshData();
      showToast("success", "Thành công",
        result.message || (apptId.value ? "Cập nhật lịch hẹn thành công" : "Tạo lịch hẹn thành công"));
    } else {
      // Backend trả về lỗi, hiển thị
      modalError.textContent = result.error || "Không thể lưu lịch hẹn";
      modalError.classList.remove("d-none");
    }
  } catch (err) {
    modalError.textContent = "Không thể lưu lịch hẹn. Vui lòng thử lại sau";
    modalError.classList.remove("d-none");
  } finally {
    // ===== TẮT LOADING =====
    isSubmitting = false;
    resetButton(btnSave);
  }
});

// ===== 13. XÓA LỊCH =====
btnDelete.addEventListener("click", async () => {
  const id = apptId.value.trim();

  if (isSubmitting) {
    console.log('Đang xử lý, bỏ qua click lặp');
    return;
  }

  if (!id) return;

  // Hiển thị modal xác nhận
  document.getElementById('deleteAppointmentCode').textContent = id;
  const deleteModal = new bootstrap.Modal(document.getElementById('deleteAppointmentModal'));
  const confirmDeleteBtn = document.getElementById('confirmDeleteAppointmentBtn');

  // Xóa event listener cũ
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
        showToast("success", "Đã xóa thành công", `Đã xóa hoàn toàn lịch hẹn ${id} khỏi hệ thống`);
      } else {
        showToast("error", "Lỗi", result.error || "Không thể xóa lịch hẹn");
        isSubmitting = false;
      }
    } catch (err) {
      console.error('Error:', err);
      showToast("error", "Lỗi", "Không thể xóa lịch hẹn. Vui lòng thử lại sau");
      isSubmitting = false;
    } finally {
      isSubmitting = false;
    }
  });

  deleteModal.show();
});

// ===== 14. XỬ LÝ YÊU CẦU ONLINE =====
window.approveWeb = async function (id) {
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (result.success && result.appointment) {
    openEditModalWithData(result.appointment);
    apptStatus.value = "not_arrived";
    showToast("info", "Gợi ý", "Chọn phòng/thời gian nếu cần rồi bấm Lưu để xác nhận");
  } else {
    showToast("error", "Lỗi", "Không tìm thấy lịch hẹn");
  }
}

window.rejectWeb = async function (id) {
  if (!confirm("Từ chối yêu cầu đặt lịch này?")) return;
  const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'cancelled' });
  if (result.success) {
    showToast("success", "OK", "Đã từ chối yêu cầu");
    await renderWebRequests();
    await refreshData();
  } else {
    showToast("error", "Lỗi", result.error || "Không thể từ chối yêu cầu");
  }
}

// ===== 15. AUTO-FILL DURATION KHI CHỌN SERVICE =====
if (service) {
  service.addEventListener("change", function () {
    const serviceId = parseInt(this.value);
    const selectedService = SERVICES.find(s => s.id === serviceId);

    if (selectedService && selectedService.duration) {
      const serviceDuration = selectedService.duration;
      const durationOptions = Array.from(duration.options).map(opt => parseInt(opt.value));

      if (durationOptions.includes(serviceDuration)) {
        duration.value = serviceDuration;
      } else {
        const closest = durationOptions.reduce((prev, curr) =>
          Math.abs(curr - serviceDuration) < Math.abs(prev - serviceDuration) ? curr : prev
        );
        duration.value = closest;
      }
    }
  });
}

// ===== 16. DATE NAVIGATION =====
function setDay(d) {
  dayPicker.value = d;
  date.value = d;
  refreshData();
}

function todayISO() {
  const t = new Date();
  return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
}

function shiftDay(delta) {
  const d = new Date(dayPicker.value + "T00:00:00");
  d.setDate(d.getDate() + delta);
  setDay(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`);
}

async function refreshData() {
  await loadAppointments(dayPicker.value);
  await renderGrid();
}

// ===== 17. SEARCH =====
if (searchInput) {
  searchInput.addEventListener("input", function () {
    renderGrid();
    renderWebRequests();
  });
}

// ===== 18. INIT =====
document.addEventListener("DOMContentLoaded", async () => {
  // Khởi tạo modal
  if (modalEl) modal = new bootstrap.Modal(modalEl);
  if (toastEl) toast = new bootstrap.Toast(toastEl);

  // Khởi tạo delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  // Sidebar toggle
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
  }

  // Load dữ liệu
  await loadRooms();
  await loadServices();
  fillRoomsSelect();

  // Set ngày hôm nay
  dayPicker.value = todayISO();

  // Vẽ header giờ (đơn giản)
  renderHeader();

  // Render lưới
  await refreshData();
  await renderWebRequests();

  // Event listeners
  if (btnToday) btnToday.addEventListener("click", () => setDay(todayISO()));
  if (btnPrev) btnPrev.addEventListener("click", () => shiftDay(-1));
  if (btnNext) btnNext.addEventListener("click", () => shiftDay(1));
  if (dayPicker) dayPicker.addEventListener("change", () => refreshData());

  // Export function
  window.openEditModal = openEditModal;
});

// Render header giờ (đơn giản)
function renderHeader() {
  const START_HOUR = 9;
  const END_HOUR = 22;
  const totalSlots = ((END_HOUR - START_HOUR) * 60) / 30;

  document.documentElement.style.setProperty("--totalSlots", totalSlots);

  let html = `<div class="leftcell">Phòng</div><div class="slots">`;
  for (let i = 0; i < totalSlots; i++) {
    const mins = i * 30;
    const hour = START_HOUR + Math.floor(mins / 60);
    const minute = mins % 60;
    html += `<div class="slot ${minute === 0 ? 'major' : ''}">${minute === 0 ? `${hour}:00` : ''}</div>`;
  }
  html += `</div>`;
  timeHeader.innerHTML = html;
}
