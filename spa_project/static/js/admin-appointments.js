// ============================================================
// ADMIN APPOINTMENTS - Má»¤C Lá»¤C
// ============================================================
// SECTION 1:  Cáº¤U HÃŒNH & Háº°NG Sá»            (Line ~25)  - Constants, URLs, Messages
// SECTION 2:  BIáº¾N TRáº NG THÃI (STATE)       (Line ~33)  - Quáº£n lÃ½ state toÃ n cá»¥c
// SECTION 3:  HÃ€M API                        (Line ~60)  - Gá»i HTTP, táº£i dá»¯ liá»‡u
// SECTION 4:  HÃ€M VALIDATION                 (Line ~204) - Kiá»ƒm tra form
// SECTION 5:  HÃ€M Xá»¬ LÃ THá»œI GIAN            (Line ~355) - DateTime utilities
// SECTION 6:  HÃ€M GIAO DIá»†N (UI)            (Line ~376) - Toast, buttons, modals
// SECTION 7:  QUáº¢N LÃ PENDING BLOCKS         (Line ~625) - Slot Ä‘ang chá»n
// SECTION 8:  TAB 1 - Lá»ŠCH THEO PHÃ’NG        (Line ~805) - Grid hiá»ƒn thá»‹ lá»‹ch
// SECTION 9:  TAB 2 - YÃŠU Cáº¦U Äáº¶T Lá»ŠCH      (Line ~1017)- Xá»­ lÃ½ booking online
// SECTION 10: TÃŒM KIáº¾M KHÃCH HÃ€NG           (Line ~1238)- Tra cá»©u khÃ¡ch theo SÄT
// SECTION 11: MODAL & FORM                   (Line ~1326)- Dialog & form helpers
// SECTION 12: CHá»ŒN NGÃ€Y (DATE NAVIGATION)    (Line ~3215)- DatePicker
// SECTION 13: MODAL TÃŒM KIáº¾M                (Line ~3241)- TÃ¬m kiáº¿m lá»‹ch háº¹n
// SECTION 14: AUTO-REFRESH CANCEL            (Line ~3467)- Cáº­p nháº­t khÃ¡ch há»§y
// SECTION 15: KHá»žI Táº O APP                  (Line ~3546)- Startup & event listeners
// SECTION 16: MODAL HÃ“A ÄÆ N (INVOICE)        (Line ~3663)- Thanh toÃ¡n
// ============================================================

// ============================================================
// SECTION 1: SETTINGS & CONSTANTS
// ============================================================
console.log("ADMIN APPOINTMENTS JS LOADED v20260501-005");
const START_HOUR = 9;  // Giá» má»Ÿ cá»­a (9:00 sÃ¡ng)
const END_HOUR = 21;   // Giá» Ä‘Ã³ng cá»­a (21:00 tá»‘i)
const SLOT_MIN = 30; // 1 Ã´ lá»‹ch = 30 phÃºt
const DEFAULT_DURATION = 60; // Thá»i lÆ°á»£ng máº·c Ä‘á»‹nh cho pending block (phÃºt)

// ===== API BASE URL- Ä‘Æ°á»ng dáº«n API Ä‘á»ƒ gá»i BE =====
const API_BASE = '/api';

// Constant dÃ¹ng chung cho táº¥t cáº£ lá»—i táº£i lá»‹ch háº¹n â€” UC 14.2 exception flow 5a
const MSG_LOAD_APPT_ERROR = 'KhÃ´ng thá»ƒ táº£i lá»‹ch háº¹n. Vui lÃ²ng thá»­ láº¡i sau.';

// ===== UC 14.3 â€” Messages chuáº©n hÃ³a =====
const MSG_APPROVE_SUCCESS  = 'XÃ¡c nháº­n yÃªu cáº§u thÃ nh cÃ´ng';
const MSG_REJECT_SUCCESS   = 'Tá»« chá»‘i yÃªu cáº§u thÃ nh cÃ´ng';
const MSG_REBOOK_SUCCESS   = 'Äáº·t láº¡i lá»‹ch háº¹n thÃ nh cÃ´ng';
const MSG_WEB_EMPTY        = 'Hiá»‡n chÆ°a cÃ³ yÃªu cáº§u Ä‘áº·t lá»‹ch nÃ o.';
const MSG_WEB_GENERIC_ERR  = 'KhÃ´ng thá»ƒ xá»­ lÃ½ yÃªu cáº§u. Vui lÃ²ng thá»­ láº¡i sau.';
const MSG_WEB_CONFLICT     = 'KhÃ´ng thá»ƒ xá»­ lÃ½ do khung giá» hoáº·c phÃ²ng khÃ´ng kháº£ dá»¥ng.';
const MSG_APPROVE_CONFLICT = 'KhÃ´ng thá»ƒ xÃ¡c nháº­n do khung giá» hoáº·c phÃ²ng khÃ´ng kháº£ dá»¥ng.';

// ===== HELPER: format variant label â€” trÃ¡nh láº·p "90 phÃºt â€” 90 phÃºt" =====
function variantLabel(v) {
  const dur = `${v.duration_minutes} phÃºt`;
  if (!v.label || v.label.trim() === dur) return dur;
  return `${v.label} â€” ${dur}`;
}

// ============================================================
// SECTION 2: STATE VARIABLES
// ============================================================
// PENDING BLOCKS STATE â€” Flow 2 bÆ°á»›c táº¡o lá»‹ch háº¹n
let pendingBlocks = [];
let _pendingIdCounter = 0;

// Dá»¯ liá»‡u ( láº¥y tá»« API) ==> lÆ°u dá»¯ liá»‡u load tá»« DB Ä‘á»ƒ render giao diá»‡n, validate form, tÃ­nh toÃ¡n trÃ¹ng lá»‹ch
let ROOMS = []; // danh sÃ¡ch phÃ²ng
let SERVICES = []; //dÃ¡nh sÃ¡ch dá»‹ch vá»¥
let APPOINTMENTS = []; // danh sÃ¡ch lá»‹ch háº¹n

// Biáº¿n theo dÃµi tráº¡ng thÃ¡i Ä‘ang submit Ä‘á»ƒ trÃ¡nh submit láº·p
let isSubmitting = false;

// State: Ä‘ang á»Ÿ cháº¿ Ä‘á»™ "quay vá» grid Ä‘á»ƒ chá»n thÃªm slot"
let _addingSlotMode = false;
let _savedBookerInfo = null;  // lÆ°u táº¡m booker info khi quay vá» grid
let _addingSlotEditBookingCode = null; // náº¿u Ä‘ang thÃªm slot tá»« edit mode, lÆ°u bookingCode Ä‘á»ƒ quay láº¡i

// UC 14.3 â€” track rebook mode Ä‘á»ƒ hiá»ƒn thá»‹ Ä‘Ãºng message sau khi táº¡o lá»‹ch
let _isRebookMode = false;

// CREATE MODE â€” ACCORDION GUEST CARDS
let _guestCount = 0;
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
        error: !response.ok ? `HTTP error ${response.status}: MÃ¡y chá»§ tráº£ vá» pháº£n há»“i khÃ´ng há»£p lá»‡` : 'Invalid JSON response'
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
        error: !response.ok ? `HTTP error ${response.status}: MÃ¡y chá»§ tráº£ vá» pháº£n há»“i khÃ´ng há»£p lá»‡` : 'Invalid JSON response'
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
    ROOMS = [];
  }
}

async function loadServices() {
  const result = await apiGet(`${API_BASE}/services/`);
  if (result.services) {
    SERVICES = result.services;
  }
}

// _gridLoadError: true khi láº§n load gáº§n nháº¥t bá»‹ lá»—i â€” dÃ¹ng Ä‘á»ƒ renderGrid hiá»ƒn thá»‹ error state
let _gridLoadError = false;

async function loadAppointments(date = '') {
  let url = `${API_BASE}/appointments/`;
  const params = [];
  if (date) params.push(`date=${date}`);

  if (params.length) url += '?' + params.join('&');

  const result = await apiGet(url);
  if (result.success && result.appointments) {
    APPOINTMENTS = result.appointments;
    _gridLoadError = false;
  } else {
    // API tráº£ error hoáº·c network lá»—i â€” UC 14.2 exception flow 5a
    APPOINTMENTS = [];
    _gridLoadError = true;
    showToast('error', 'Lá»—i', result.error || MSG_LOAD_APPT_ERROR);
  }
}

async function loadBookingRequests(dateFilter = '', searchTerm = '', serviceFilter = '') {
  let url = `${API_BASE}/booking-requests/`;
  const queryParams = [];
  // Backend chá»‰ tráº£ vá» PENDING bookings - khÃ´ng cáº§n status filter
  if (dateFilter)    queryParams.push(`date=${encodeURIComponent(dateFilter)}`);
  if (searchTerm)    queryParams.push(`q=${encodeURIComponent(searchTerm)}`);
  if (serviceFilter) queryParams.push(`service=${encodeURIComponent(serviceFilter)}`);
  if (queryParams.length > 0) url += '?' + queryParams.join('&');

  const result = await apiGet(url);
  if (result && result.success) {
    return result.appointments || [];
  }
  //lá»—i táº£i khÃ´ng Ä‘Æ°á»£c im láº·ng
  showToast('error', 'Lá»—i', MSG_WEB_GENERIC_ERR);
  return [];
}

// ============================================================
// SECTION 4: VALIDATION HELPERS
// ============================================================
function isValidPhone(v){ return /^0\d{9}$/.test(v.replace(/\D/g,"")); }
function isValidEmail(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }

/**
 * Hiá»ƒn thá»‹ lá»—i trong #modalError.
 * Thay tháº¿ pattern láº·p: modalError.textContent = msg; modalError.classList.remove("d-none");
 */
function _showModalError(msg) {
  const el = document.getElementById('modalError');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('d-none');
}

/**
 * TÃ­nh discount_amount tá»« subtotal + type + value.
 * Káº¿t quáº£ Ä‘Æ°á»£c clamp vá» [0, subtotal].
 * @param {number} subtotal
 * @param {string} dtype  - 'NONE' | 'AMOUNT' | 'PERCENT'
 * @param {number} value
 * @returns {number}
 */
function _calcDiscountAmount(subtotal, dtype, value) {
  let amount = 0;
  if (dtype === 'PERCENT') {
    amount = Math.round(subtotal * value / 100);
  } else if (dtype === 'AMOUNT') {
    amount = Math.min(value, subtotal);
  }
  return Math.max(0, Math.min(amount, subtotal));
}

/**
 * TÃ­nh payment status tá»« final_amount vÃ  total_paid.
 * @param {number} finalAmount
 * @param {number} totalPaid
 * @returns {'UNPAID'|'PARTIAL'|'PAID'}
 */
function _calcPayStatus(finalAmount, totalPaid, hasAnyService = false) {
  if (finalAmount === 0 && hasAnyService) return 'PAID';  // discount 100% + cÃ³ dá»‹ch vá»¥
  if (totalPaid <= 0) return 'UNPAID';
  if (totalPaid >= finalAmount && finalAmount > 0) return 'PAID';
  return 'PARTIAL';
}

/**
 * Validate Ä‘iá»u kiá»‡n COMPLETED pháº£i Ä‘i kÃ¨m PAID.
 * @param {string} apptStatus
 * @param {string} payStatus
 * @returns {{ ok: boolean, error: string }}
 */
function _validateCompletedStatus(apptStatus, payStatus) {
  if (apptStatus === 'COMPLETED' && payStatus !== 'PAID') {
    return { ok: false, error: 'KhÃ´ng thá»ƒ hoÃ n thÃ nh lá»‹ch khi chÆ°a thanh toÃ¡n Ä‘á»§' };
  }
  return { ok: true, error: '' };
}

/**
 * Validate thÃ´ng tin ngÆ°á»i Ä‘áº·t lá»‹ch (booker).
 * DÃ¹ng chung cho cáº£ CREATE vÃ  EDIT branch trong submit handler.
 *
 * @param {string} name   - há» tÃªn ngÆ°á»i Ä‘áº·t
 * @param {string} phone  - sá»‘ Ä‘iá»‡n thoáº¡i (raw, chÆ°a strip)
 * @param {string} email  - email (cÃ³ thá»ƒ rá»—ng)
 * @returns {{ ok: boolean, error: string }}
 */
function _validateBookerFields(name, phone, email) {
  if (!name) return { ok: false, error: 'Vui lÃ²ng nháº­p há» tÃªn ngÆ°á»i Ä‘áº·t' };
  if (!phone) return { ok: false, error: 'Sá»‘ Ä‘iá»‡n thoáº¡i khÃ´ng há»£p lá»‡' };
  if (!isValidPhone(phone)) return { ok: false, error: 'Sá»‘ Ä‘iá»‡n thoáº¡i khÃ´ng há»£p lá»‡' };
  if (email && !isValidEmail(email)) return { ok: false, error: 'Email khÃ´ng há»£p lá»‡' };
  return { ok: true, error: '' };
}

/**
 * Validate ghi chÃº lá»‹ch háº¹n (max 1000 kÃ½ tá»±).
 * Giá»¯ nguyÃªn message Ä‘á»™ng cÃ³ sá»‘ kÃ½ tá»± hiá»‡n táº¡i.
 * @param {string} note
 * @returns {{ ok: boolean, error: string }}
 */
function _validateBookerNote(note) {
  if (note && note.length > 1000) {
    return { ok: false, error: `Ghi chÃº lá»‹ch háº¹n quÃ¡ dÃ i (tá»‘i Ä‘a 1000 kÃ½ tá»±, hiá»‡n táº¡i ${note.length})` };
  }
  return { ok: true, error: '' };
}

/**
 * Validate date / time / room cá»§a 1 guest card â€” logic giá»‘ng nhau giá»¯a CREATE vÃ  EDIT.
 * KHÃ”NG bao gá»“m: validate quÃ¡ khá»©, fallback apptId.dataset (khÃ¡c nhau giá»¯a 2 branch).
 *
 * @param {Object} g      - guest data tá»« _collectGuestCards()
 * @param {number} index  - 0-based index
 * @param {number} total  - tá»•ng sá»‘ cards
 * @returns {{ ok: boolean, error: string, type: 'date'|'time'|'room'|null }}
 *   type dÃ¹ng Ä‘á»ƒ caller quyáº¿t Ä‘á»‹nh cÃ³ gá»i _markRowError khÃ´ng.
 */
function _validateGuestDateTimeRoom(g, index, total) {
  const label = total > 1 ? `KhÃ¡ch ${index + 1}: ` : '';
  if (!g.date)   return { ok: false, error: `${label}Vui lÃ²ng chá»n ngÃ y háº¹n`, type: 'date' };
  if (!g.time)   return { ok: false, error: `${label}Vui lÃ²ng chá»n giá» háº¹n`,  type: 'time' };
  if (!g.roomId) return { ok: false, error: `${label}Vui lÃ²ng chá»n phÃ²ng`,     type: 'room' };
  return { ok: true, error: '', type: null };
}

/**
 * Validate cÃ¡c trÆ°á»ng cÆ¡ báº£n cá»§a 1 guest card â€” giá»‘ng nhau 100% giá»¯a CREATE vÃ  EDIT.
 * Bao gá»“m: tÃªn, phone, email, service+variant.
 * KHÃ”NG bao gá»“m: date, time, room, validate quÃ¡ khá»© (khÃ¡c nhau giá»¯a 2 branch).
 *
 * @param {Object} g      - guest data tá»« _collectGuestCards()
 * @param {number} index  - 0-based index
 * @param {number} total  - tá»•ng sá»‘ cards
 * @returns {{ ok: boolean, error: string }}
 */
function _validateGuestBasic(g, index, total) {
  const label = total > 1 ? `KhÃ¡ch ${index + 1}: ` : '';
  if (!g.name || !g.name.trim())          return { ok: false, error: `${label}Vui lÃ²ng nháº­p tÃªn khÃ¡ch` };
  if (g.phone && !isValidPhone(g.phone))  return { ok: false, error: `${label}Sá»‘ Ä‘iá»‡n thoáº¡i khÃ¡ch khÃ´ng há»£p lá»‡` };
  if (g.email && !isValidEmail(g.email))  return { ok: false, error: `${label}Email khÃ´ng há»£p lá»‡` };
  if (g.serviceId && !g.variantId)        return { ok: false, error: `${label}Vui lÃ²ng chá»n gÃ³i dá»‹ch vá»¥` };
  return { ok: true, error: '' };
}

/**
 * Validate thá»i Ä‘iá»ƒm ARRIVED / COMPLETED cho tá»«ng card trong máº£ng.
 * DÃ¹ng chung cho EDIT vÃ  CREATE branch.
 *
 * @param {Array}    cards     - máº£ng guest card data tá»« _collectGuestCards()
 * @param {Function} getStatus - (g, i) => string â€” tráº£ vá» apptStatus cá»§a card
 * @param {Function} getDate   - (g, i) => string â€” tráº£ vá» date (YYYY-MM-DD)
 * @param {Function} getTime   - (g, i) => string â€” tráº£ vá» time (HH:MM)
 * @param {Function} getDur    - (g, i) => number â€” tráº£ vá» duration (phÃºt)
 * @returns {{ ok: boolean, error: string }}
 */
function _validateAllCardsTiming(cards, getStatus, getDate, getTime, getDur) {
  for (let i = 0; i < cards.length; i++) {
    const g      = cards[i];
    const status = getStatus(g, i);
    if (status !== 'ARRIVED' && status !== 'COMPLETED') continue;
    const timing = _validateStatusTiming(getDate(g, i), getTime(g, i), getDur(g, i), status);
    // Tráº¡ng thÃ¡i lÃ  shared cho toÃ n booking â€” khÃ´ng gáº¯n "KhÃ¡ch N:" vÃ o lá»—i timing
    if (!timing.ok) return { ok: false, error: timing.error };
  }
  return { ok: true, error: '' };
}

// ============================================================
// SECTION 5: TIME/DATE HELPERS
// ============================================================
function pad2(n){ return String(n).padStart(2,"0"); }

function minutesFromStart(t){ const [h,m]=t.split(":").map(Number); return (h-START_HOUR)*60 + m; }

function addMinutesToTime(t, add){
  // Extract HH:MM from time string in case it contains date or other info
  const timeMatch = t.match(/(\d{1,2}):(\d{2})/);
  if (!timeMatch) return t;
  const h = parseInt(timeMatch[1], 10);
  const m = parseInt(timeMatch[2], 10);
  const total = h*60+m+add;
  return `${pad2(Math.floor(total/60))}:${pad2(total%60)}`;
}

function overlaps(aStart,aEnd,bStart,bEnd){ return aStart < bEnd && bStart < aEnd; }

// Tá»•ng sá»‘ phÃºt cá»§a toÃ n bá»™ timeline (9:00 â†’ 21:00 = 720 phÃºt)
function totalTimelineMinutes(){ return (END_HOUR - START_HOUR) * 60; }

// Chuyá»ƒn sá»‘ phÃºt tá»« START_HOUR sang % chiá»u ngang cá»§a vÃ¹ng slots
function minutesToPercent(minutes){ return (minutes / totalTimelineMinutes()) * 100; }

// ============================================================
// SECTION 6: UI HELPERS
// ============================================================
function showToast(type, title, message){
  const toastEl = document.getElementById("toast");
  if (!toastEl) return;
  const header = toastEl.querySelector(".toast-header");
  const icon = header ? header.querySelector("i") : null;
  const toastTitle = document.getElementById("toastTitle");
  const toastBody = document.getElementById("toastBody");

  if (header) {
    header.className = "toast-header";
    if(type==="success"){ header.classList.add("bg-success","text-white"); if(icon) icon.className="fas fa-check-circle me-2"; }
    else if(type==="warning"){ header.classList.add("bg-warning","text-dark"); if(icon) icon.className="fas fa-exclamation-triangle me-2"; }
    else if(type==="error"){ header.classList.add("bg-danger","text-white"); if(icon) icon.className="fas fa-times-circle me-2"; }
    else { header.classList.add("bg-info","text-white"); if(icon) icon.className="fas fa-info-circle me-2"; }
  }
  if (toastTitle) toastTitle.textContent = title;
  if (toastBody) toastBody.textContent = message;

  // Láº¥y instance Bootstrap Toast tá»« element, khÃ´ng dÃ¹ng window.toast
  // (window.toast cÃ³ thá»ƒ bá»‹ ghi Ä‘Ã¨ bá»Ÿi extension hoáº·c code khÃ¡c)
  const toast = bootstrap.Toast.getInstance(toastEl) || new bootstrap.Toast(toastEl);
  toast.show();
}

function statusClass(s){
  const sl = (s||'').toLowerCase();
  if(sl==="not_arrived") return "status-not_arrived";
  if(sl==="arrived") return "status-arrived";
  if(sl==="completed") return "status-completed";
  if(sl==="cancelled") return "status-cancelled";
  if(sl==="rejected") return "status-rejected";
  if(sl==="confirmed") return "status-not_arrived";
  return "status-pending";
}

function statusLabel(s){
  const sl = (s||'').toLowerCase();
  if(sl==="pending") return "Chá» xÃ¡c nháº­n";
  if(sl==="confirmed") return "ÄÃ£ xÃ¡c nháº­n";
  if(sl==="not_arrived") return "ChÆ°a Ä‘áº¿n";
  if(sl==="arrived") return "ÄÃ£ Ä‘áº¿n";
  if(sl==="completed") return "HoÃ n thÃ nh";
  if(sl==="cancelled") return "ÄÃ£ há»§y";
  if(sl==="rejected") return "ÄÃ£ tá»« chá»‘i";
  return s;
}

// ===== BOOKING BADGES UPDATE =====
function updateBookingBadges(rows) {
  // Äáº¿m Booking PENDING theo bookingCode (má»—i booking chá»‰ Ä‘áº¿m 1 láº§n)
  const pendingBookings = new Set(
    rows
      .filter(r => (r.bookingStatus || '').toUpperCase() === 'PENDING')
      .map(r => r.bookingCode)
  );
  _setWebCountBadge(pendingBookings.size);
}

/**
 * Báº­t loading state cho button
 * @param {HTMLElement} btn - Button cáº§n set loading
 * @param {string} loadingText - Text hiá»ƒn thá»‹ khi loading
 * @param {string} originalText - Text gá»‘c Ä‘á»ƒ restore sau nÃ y
 */
function setButtonLoading(btn, loadingText = 'Äang xá»­ lÃ½...', originalText = null) {
  if (!btn) return;

  // LÆ°u text gá»‘c náº¿u chÆ°a cÃ³
  if (!btn.dataset.originalText) {
    btn.dataset.originalText = originalText || btn.innerHTML;
  }

  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
}

/**
 * Táº¯t loading state vÃ  restore button vá» tráº¡ng thÃ¡i ban Ä‘áº§u
 * @param {HTMLElement} btn - Button cáº§n restore
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
 * Hiá»ƒn thá»‹ modal xÃ¡c nháº­n Ä‘á»“ng bá»™ giao diá»‡n há»‡ thá»‘ng
 * @param {string} title - TiÃªu Ä‘á»
 * @param {string} message - Ná»™i dung xÃ¡c nháº­n
 * @param {string} confirmText - Text nÃºt xÃ¡c nháº­n
 * @param {string} cancelText - Text nÃºt há»§y
 * @returns {Promise<boolean>} - true náº¿u ngÆ°á»i dÃ¹ng xÃ¡c nháº­n
 */
async function confirmAction(title, message, confirmText = 'XÃ¡c nháº­n', cancelText = 'Há»§y') {
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

// ===== SHARED HELPERS (TIER-1 REFACTOR) =====

/**
 * ÄÃ³ng vÃ  cleanup Táº¤T Cáº¢ modal Bootstrap Ä‘ang má»Ÿ.
 * DÃ¹ng trong openRebookAsCreate khi cáº§n force close modal khÃ¡c trÆ°á»›c khi má»Ÿ modal táº¡o lá»‹ch.
 */
function _forceCloseAllModals() {
  document.querySelectorAll('.modal.show').forEach(el => {
    const inst = bootstrap.Modal.getInstance(el);
    if (inst) inst.hide();
  });
  document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
  document.body.classList.remove('modal-open');
  document.body.style.removeProperty('overflow');
  document.body.style.removeProperty('padding-right');
  document.body.removeAttribute('data-bs-overflow');
}

/**
 * Kiá»ƒm tra result API cÃ³ pháº£i lá»—i conflict khÃ´ng.
 * DÃ¹ng chung cho edit-batch, online-confirm, create-batch.
 * @param {Object} result - API response object
 * @param {boolean} [checkFlag=false] - cÃ³ kiá»ƒm tra result.conflict flag khÃ´ng
 * @returns {boolean}
 */
function _isConflictError(result, checkFlag = false) {
  const errLower = (result.error || '').toLowerCase();
  return (checkFlag && result.conflict === true) ||
    errLower.includes('trÃ¹ng') ||
    errLower.includes('Ä‘áº§y') ||
    errLower.includes('Ä‘á»§ chá»—') ||
    errLower.includes('kháº£ dá»¥ng') ||
    errLower.includes('capacity') ||
    errLower.includes('conflict');
}

/**
 * Láº¥y Bootstrap Modal instance hoáº·c táº¡o má»›i náº¿u chÆ°a cÃ³.
 * @param {HTMLElement} el
 * @returns {bootstrap.Modal|null}
 */


/**
 * Clone node Ä‘á»ƒ xÃ³a táº¥t cáº£ event listener cÅ©, gáº¯n láº¡i vÃ o DOM.
 * Tráº£ vá» node má»›i Ä‘Ã£ Ä‘Æ°á»£c gáº¯n vÃ o DOM.
 * @param {HTMLElement} el
 * @returns {HTMLElement}
 */
function _replaceWithClone(el) {
  const clone = el.cloneNode(true);
  el.parentNode.replaceChild(clone, el);
  return clone;
}

/**
 * Äiá»n thÃ´ng tin ngÆ°á»i Ä‘áº·t lá»‹ch vÃ o booker panel.
 * DÃ¹ng chung cho openCreateModal (rebook/online/pending) vÃ  openEditModalWithData.
 *
 * @param {Object} rb            - object chá»©a name, phone, email, source, note
 * @param {string} defaultSource - fallback khi rb.source rá»—ng (máº·c Ä‘á»‹nh 'DIRECT')
 */
function _fillBookerFields(rb, defaultSource = 'DIRECT') {
  document.getElementById('bookerName').value   = rb.name   || '';
  document.getElementById('bookerPhone').value  = rb.phone  || '';
  document.getElementById('bookerEmail').value  = rb.email  || '';
  document.getElementById('bookerSource').value = rb.source || defaultSource;
  const bookerNoteEl = document.getElementById('bookerNote');
  if (bookerNoteEl) bookerNoteEl.value = rb.note || '';
}

/**
 * Cáº­p nháº­t badge #webCount vá»›i sá»‘ lÆ°á»£ng pending.
 * @param {number} count
 */
function _setWebCountBadge(count) {
  const webCount = document.getElementById('webCount');
  if (!webCount) return;
  if (count === 0) {
    webCount.textContent = '';
    webCount.classList.add('d-none');
  } else {
    webCount.textContent = String(count);
    webCount.classList.remove('d-none');
  }
}

/**
 * Äiá»n options vÃ o má»™t <select> tá»« máº£ng items.
 * XÃ³a toÃ n bá»™ options cÅ© (trá»« placeholder náº¿u cÃ³) rá»“i append má»›i.
 *
 * @param {HTMLSelectElement} selectEl   - pháº§n tá»­ <select> cáº§n Ä‘iá»n
 * @param {Array}             items      - máº£ng dá»¯ liá»‡u
 * @param {string|Function}   valueKey   - tÃªn field láº¥y value, hoáº·c hÃ m (item) => value
 * @param {string|Function}   labelFn    - tÃªn field láº¥y label, hoáº·c hÃ m (item) => label
 * @param {string}            [placeholder] - text option Ä‘áº§u tiÃªn (value=""), bá» qua náº¿u null
 */
function _populateSelect(selectEl, items, valueKey, labelFn, placeholder = null) {
  if (!selectEl) return;
  selectEl.innerHTML = placeholder !== null
    ? `<option value="">${placeholder}</option>`
    : '';
  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value       = typeof valueKey === 'function' ? valueKey(item) : item[valueKey];
    opt.textContent = typeof labelFn  === 'function' ? labelFn(item)  : item[labelFn];
    selectEl.appendChild(opt);
  });
}

/**
 * Refresh cáº£ grid lá»‹ch vÃ  tab yÃªu cáº§u Ä‘áº·t lá»‹ch.
 * DÃ¹ng á»Ÿ nhá»¯ng nÆ¡i luÃ´n cáº§n cáº£ 2 sau khi thay Ä‘á»•i dá»¯ liá»‡u.
 */
async function _refreshAll() {
  await refreshData();
  await renderWebRequests();
}

// ===== LOADING SKELETON CHO GRID =====
function showGridLoading(){
  const grid = document.getElementById("grid");
  if (!grid) return;
  // Hiá»‡n 5 dÃ²ng skeleton Ä‘á»ƒ layout khÃ´ng bá»‹ trá»‘ng trong lÃºc fetch
  const rowH = getComputedStyle(document.documentElement).getPropertyValue('--rowH') || '72px';
  grid.innerHTML = Array.from({length: 5}, (_, i) => `
    <div class="lane-row" style="opacity:.45;">
      <div class="roomcell"><span class="dot"></span>â€”</div>
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
 * Kiá»ƒm tra slot cÃ³ náº±m trong quÃ¡ khá»© khÃ´ng.
 * day: 'YYYY-MM-DD', time: 'HH:MM'
 */
function _isSlotInPast(day, time) {
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  if (day > todayStr) return false;
  if (day < todayStr) return true;
  // CÃ¹ng ngÃ y hÃ´m nay â€” so sÃ¡nh giá»
  const [h, m] = time.split(':').map(Number);
  const slotMinutes = h * 60 + m;
  const nowMinutes  = now.getHours() * 60 + now.getMinutes();
  return slotMinutes <= nowMinutes;
}

/**
 * Toggle slot: click Ã´ trá»‘ng â†’ chá»n, click láº¡i block xanh â†’ bá» chá»n.
 * ÄÃ¢y lÃ  hÃ m duy nháº¥t xá»­ lÃ½ add/remove pending block.
 */
function handleToggleSlot({ roomId, laneIndex, day, time, slotsEl }) {
  const duration = DEFAULT_DURATION;
  const endTime  = addMinutesToTime(time, duration);
  const startMin = minutesFromStart(time);
  const endMin   = minutesFromStart(endTime);

  // Kiá»ƒm tra ngoÃ i giá»
  if (startMin < 0 || endMin > totalTimelineMinutes()) {
    showToast("warning", "NgoÃ i giá» hoáº¡t Ä‘á»™ng", `Spa hoáº¡t Ä‘á»™ng tá»« ${START_HOUR}:00 Ä‘áº¿n ${END_HOUR}:00`);
    return;
  }

  // Cháº·n slot trong quÃ¡ khá»©
  if (_isSlotInPast(day, time)) {
    showToast("warning", "KhÃ´ng thá»ƒ chá»n slot nÃ y", "KhÃ´ng thá»ƒ táº¡o lá»‹ch háº¹n trong quÃ¡ khá»©");
    return;
  }

  // TÃ¬m pending block trÃ¹ng slot nÃ y (cÃ¹ng room + lane + day + time)
  const existing = pendingBlocks.find(pb =>
    pb.roomId === roomId &&
    pb.laneIndex === laneIndex &&
    pb.day === day &&
    pb.time === time
  );

  if (existing) {
    // â”€â”€ TOGGLE OFF: bá» chá»n â”€â”€
    pendingBlocks = pendingBlocks.filter(pb => pb.id !== existing.id);
    document.querySelectorAll(`.appt-pending[data-pending-id="${existing.id}"]`).forEach(el => el.remove());
    _syncActionBar();
    return;
  }

  // â”€â”€ TOGGLE ON: kiá»ƒm tra conflict rá»“i thÃªm â”€â”€

  // Conflict vá»›i appointment Ä‘Ã£ cÃ³
  const dayAppts = APPOINTMENTS.filter(a =>
    a.roomCode === roomId && a.date === day && !["CANCELLED", "REJECTED"].includes((a.apptStatus || "").toUpperCase())
  );
  const { placements } = allocateRoomLanes(roomId, day, dayAppts);
  const laneAppts = placements.filter(p => p.laneIndex === laneIndex).map(p => p.appt);
  const conflictAppt = laneAppts.find(a =>
    overlaps(startMin, endMin, minutesFromStart(a.start), minutesFromStart(a.end))
  );
  if (conflictAppt) {
    showToast("warning", "Slot Ä‘Ã£ cÃ³ lá»‹ch", "Khung giá» Ä‘Ã£ cÃ³ lá»‹ch, vui lÃ²ng chá»n thá»i gian khÃ¡c");
    if (slotsEl) {
      slotsEl.classList.add("conflict-flash");
      setTimeout(() => slotsEl.classList.remove("conflict-flash"), 450);
    }
    return;
  }

  // Conflict vá»›i pending block khÃ¡c trong cÃ¹ng lane
  const conflictPending = pendingBlocks.find(pb =>
    pb.roomId === roomId && pb.laneIndex === laneIndex && pb.day === day &&
    overlaps(startMin, endMin, minutesFromStart(pb.time), minutesFromStart(pb.endTime))
  );
  if (conflictPending) {
    showToast("warning", "TrÃ¹ng vá»›i slot Ä‘ang chá»n", `Lane nÃ y Ä‘Ã£ cÃ³ slot Ä‘ang chá»n lÃºc ${conflictPending.time}â€“${conflictPending.endTime}`);
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
  if (label) label.textContent = count === 1 ? "1 khÃ¡ch Ä‘Ã£ chá»n" : `${count} khÃ¡ch Ä‘Ã£ chá»n`;

  // Khi Ä‘ang á»Ÿ cháº¿ Ä‘á»™ thÃªm slot, Ä‘á»•i label nÃºt Tiáº¿p tá»¥c
  if (btnContinue) {
    if (_addingSlotMode) {
      btnContinue.innerHTML = '<i class="fas fa-arrow-right me-1"></i>Quay láº¡i & thÃªm khÃ¡ch';
    } else {
      btnContinue.innerHTML = '<i class="fas fa-arrow-right me-1"></i>Tiáº¿p tá»¥c';
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

  // XÃ³a block cÅ© náº¿u Ä‘Ã£ tá»“n táº¡i
  slotsEl.querySelector(`.appt-pending[data-pending-id="${pb.id}"]`)?.remove();

  const block = document.createElement("div");
  block.className = "appt appt-pending";
  block.dataset.pendingId = String(pb.id);

  // Chá»‰ cÃ³ top-bar xanh + hint giá» â€” khÃ´ng cÃ³ nÃºt X
  block.innerHTML = `
    <div class="pb-selection-bar"></div>
    <div class="pb-time-hint">${pb.time} â€“ ${pb.endTime}</div>
  `;

  block.style.cssText = "position:absolute;top:0;height:var(--rowH);z-index:30;cursor:pointer;";

  const leftMin = minutesFromStart(pb.time);
  const durMin  = Math.max(SLOT_MIN, minutesFromStart(pb.endTime) - leftMin);
  block.style.left  = `calc(${minutesToPercent(leftMin)}% + 1px)`;
  block.style.width = `calc(${minutesToPercent(durMin)}% - 2px)`;

  // Click vÃ o block xanh â†’ toggle off (bá» chá»n)
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
// SECTION 8: TAB 1 - Lá»ŠCH THEO PHÃ’NG (GRID)
// ============================================================
function renderHeader(){
  const timeHeader = document.getElementById("timeHeader");
  const totalSlots = ((END_HOUR-START_HOUR)*60)/SLOT_MIN;
  document.documentElement.style.setProperty("--totalSlots", totalSlots);
  let html = `<div class="leftcell">PhÃ²ng</div><div class="slots">`;
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
    // TÃ­nh end: Æ°u tiÃªn a.end, fallback vá» durationMin
    const rawE = a.end ? minutesFromStart(a.end) : NaN;
    const e = (!isNaN(rawE) && rawE > s) ? rawE : s + Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
    // Äáº£m báº£o end > start (trÃ¡nh block width = 0)
    const eFixed = e > s ? e : s + SLOT_MIN;
    for(let g=0; g<need; g++){
      let foundLane = -1;
      for(let li=0; li<cap; li++){
        if(!laneIntervals[li].some(it => overlaps(s, eFixed, it.startMin, it.endMin))){ foundLane = li; break; }
      }
      if(foundLane === -1) foundLane = 0; // fallback: lane 0 náº¿u háº¿t chá»—
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

  // UC 14.2 exception flow 5a â€” hiá»ƒn thá»‹ error state thay vÃ¬ grid rá»—ng im láº·ng
  if (_gridLoadError) {
    grid.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;padding:3rem 1rem;gap:.75rem;color:#b91c1c;">
        <i class="fas fa-exclamation-circle" style="font-size:1.25rem;flex-shrink:0;"></i>
        <span style="font-size:.9rem;font-weight:500;">${MSG_LOAD_APPT_ERROR}</span>
      </div>`;
    return;
  }

  ROOMS.forEach((r)=>{
    // Lá»c lá»‹ch theo phÃ²ng â€” chá»‰ hiá»ƒn thá»‹ lá»‹ch Ä‘Ã£ CONFIRMED
    // PENDING khÃ´ng hiá»ƒn thá»‹ trÃªn grid (chá»‰ á»Ÿ tab YÃªu cáº§u Ä‘áº·t lá»‹ch)
    let appts = APPOINTMENTS.filter(a =>
      a.date === day &&
      a.roomCode === r.id &&
      (a.bookingStatus || '').toUpperCase() === 'CONFIRMED' &&
      !['CANCELLED', 'REJECTED'].includes((a.apptStatus || '').toUpperCase())
    );

    // PhÃ¢n bá»• Lane (dÃ²ng) cho tá»«ng khÃ¡ch
    const { cap, placements } = allocateRoomLanes(r.id, day, appts);
    for(let lane=0; lane<cap; lane++){
      const laneRow = document.createElement("div");
      laneRow.className = "lane-row";
      laneRow.dataset.roomId = r.id;
      laneRow.dataset.lane = lane;

      // tÃªn phÃ²ng
      laneRow.innerHTML = `${lane===0?`<div class="roomcell"><span class="dot"></span>${r.name}</div>`:`<div class="roomcell muted"><span class="dot"></span>${r.name}</div>`}<div class="slots" data-room="${r.id}" data-lane="${lane}"></div>`;
      const slotsEl = laneRow.querySelector(".slots");

      // click vÃ o Ã´ trá»‘ng â†’ toggle slot (chá»n hoáº·c bá» chá»n)
      slotsEl.addEventListener("click", (e) => {
        if (e.target.closest('.appt') || e.target.closest('.appt-pending')) return;

        const rect        = slotsEl.getBoundingClientRect();
        const ratio       = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const minutes     = Math.floor(ratio * totalTimelineMinutes() / SLOT_MIN) * SLOT_MIN;
        const clickedTime = `${pad2(START_HOUR + Math.floor(minutes / 60))}:${pad2(minutes % 60)}`;

        handleToggleSlot({ roomId: r.id, laneIndex: lane, day: dayPicker.value, time: clickedTime, slotsEl });
      });

      // váº½ block lá»‹ch háº¹n
      placements.filter(p => p.laneIndex === lane).forEach(p=>{
        const a = p.appt;
        const block = document.createElement("div");

        // Tab Lá»‹ch theo phÃ²ng chá»‰ hiá»ƒn thá»‹ CONFIRMED â€” khÃ´ng cÃ³ pending á»Ÿ Ä‘Ã¢y ná»¯a
        block.className = `appt ${statusClass(a.apptStatus)}`;
        block.dataset.id = a.id;

        const leftMin = minutesFromStart(a.start);
        // TÃ­nh durMin: Æ°u tiÃªn end - start, fallback vá» durationMin, tá»‘i thiá»ƒu SLOT_MIN
        const endMin  = a.end ? minutesFromStart(a.end) : NaN;
        const durMin  = (!isNaN(endMin) && endMin > leftMin)
          ? endMin - leftMin
          : Math.max(SLOT_MIN, Number(a.durationMin) || SLOT_MIN);
        const endLabel = a.end || addMinutesToTime(a.start, durMin);
        // DÃ¹ng % thay vÃ¬ px â†’ tá»± co giÃ£n theo chiá»u rá»™ng thá»±c táº¿ cá»§a vÃ¹ng slots
        const leftPct  = minutesToPercent(leftMin);
        const widthPct = minutesToPercent(durMin);
        block.style.left  = `calc(${leftPct}% + 2px)`;
        block.style.width = `calc(${widthPct}% - 4px)`;

        const paidIcon = (a.payStatus || '').toUpperCase() === 'PAID'
          ? `<span class="appt-paid-icon" title="ÄÃ£ thanh toÃ¡n"><i class="fas fa-receipt"></i></span>`
          : '';
        const svcText   = a.serviceCode || a.service || '';
        const custText  = a.customerName || '';

        const titleText = svcText && custText ? `${svcText} Â· ${custText}` : (svcText || custText || 'ChÆ°a chá»n DV');
        block.innerHTML = `<div class="appt-content"><div class="t1">${titleText}</div><div class="t2">${a.start}â€“${endLabel}</div></div>${paidIcon}`;
        // click vÃ o lá»‹ch ==> sá»­a
        block.addEventListener("click", (ev)=>{
          ev.stopPropagation();
          openEditModal(a.id).catch(err => console.error('[openEditModal] threw:', err));
        });

        slotsEl.appendChild(block);
      });

      // Váº½ pending blocks Ä‘Ãºng theo lane
      renderPendingBlocks(slotsEl, r.id, lane, day);

      grid.appendChild(laneRow);
    }
  });

  // Váº½ Ä‘Æ°á»ng dá»c thá»i Ä‘iá»ƒm hiá»‡n táº¡i â€” element Ä‘Æ°á»£c táº¡o 1 láº§n, cáº­p nháº­t bá»Ÿi updateCurrentTimeLine()
  updateCurrentTimeLine();
}

// â”€â”€ Current time line â€” realtime, khÃ´ng phá»¥ thuá»™c reload â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/**
 * Táº¡o hoáº·c cáº­p nháº­t vá»‹ trÃ­ Ä‘Æ°á»ng Ä‘á» thá»i gian hiá»‡n táº¡i.
 * Gá»i khi: renderGrid, Ä‘á»•i ngÃ y, resize, setInterval.
 */
function updateCurrentTimeLine() {
  const grid = document.getElementById("grid");
  const dayPicker = document.getElementById("dayPicker");
  if (!grid) return;

  // Láº¥y hoáº·c táº¡o element (chá»‰ táº¡o 1 láº§n duy nháº¥t)
  let line = grid.querySelector('.current-time-line');

  const viewDay  = dayPicker ? dayPicker.value : '';
  const now      = new Date();
  const todayStr = `${now.getFullYear()}-${pad2(now.getMonth()+1)}-${pad2(now.getDate())}`;

  // Chá»‰ hiá»‡n khi Ä‘ang xem Ä‘Ãºng ngÃ y hÃ´m nay
  if (viewDay !== todayStr) {
    if (line) line.style.display = 'none';
    return;
  }

  const nowMinutes = now.getHours() * 60 + now.getMinutes() - START_HOUR * 60;
  const pct        = (nowMinutes / totalTimelineMinutes()) * 100;

  // NgoÃ i khung giá» â†’ áº©n
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

  // Cáº­p nháº­t vá»‹ trÃ­ vÃ  label
  line.style.display = '';
  line.style.left    = `calc(var(--leftCol) + ${pct} * (100% - var(--leftCol)) / 100)`;
  const labelEl = line.querySelector('.ctl-label');
  if (labelEl) labelEl.textContent = label;
}

// Khá»Ÿi Ä‘á»™ng interval realtime â€” cáº­p nháº­t má»—i 30 giÃ¢y
function startCurrentTimeLineInterval() {
  if (_ctlInterval) clearInterval(_ctlInterval);
  _ctlInterval = setInterval(updateCurrentTimeLine, 30_000);
}

// ============================================================
// SECTION 9: TAB 2 - YÃŠU Cáº¦U Äáº¶T Lá»ŠCH (WEB REQUESTS)
// ============================================================
// váº½ báº£ng yÃªu cáº§u Ä‘áº·t lá»‹ch online (CHá»ˆ PENDING - chá» xÃ¡c nháº­n)
async function renderWebRequests(){
  const dateFilter    = (document.getElementById("webDateFilter")     || {}).value || '';
  const searchTerm    = ((document.getElementById("webSearchInput")   || {}).value || '').trim();
  const serviceFilter = (document.getElementById("webServiceFilter")  || {}).value || '';

  let rows = await loadBookingRequests(dateFilter, searchTerm, serviceFilter);

  updateBookingBadges(rows);
  window._webAppts = rows;

  const webTbody = document.getElementById("webTbody");
  if(rows.length === 0){
    webTbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">${MSG_WEB_EMPTY}</td></tr>`;
    return;
  }
  webTbody.innerHTML = rows.map(a => {
    // Backend chá»‰ tráº£ vá» PENDINGS bookings - khÃ´ng cáº§n check status
    const apptId = a.id;
    // Chá»‰ cÃ³ action XÃ¡c nháº­n vÃ  Tá»« chá»‘i cho PENDING bookings
    const actionBtn = `<div class="action-buttons">
      <button type="button" class="web-action-btn web-action-btn-approve" data-id="${apptId}" onclick="approveWeb('${apptId}')"><i class="fas fa-check"></i><span>XÃ¡c nháº­n</span></button>
      <button type="button" class="web-action-btn web-action-btn-reject" data-id="${apptId}" onclick="rejectWeb('${apptId}')"><i class="fas fa-xmark"></i><span>Tá»« chá»‘i</span></button>
    </div>`;

    return `<tr>
      <td class="fw-semibold">${apptId}</td>
      <td>${a.customerName}</td>
      <td>${a.phone}</td>
      <td>${a.service}</td>
      <td>${a.date}</td>
      <td>${a.start} - ${a.end}</td>
      <td>${a.durationMin||""} phÃºt</td>
      <td class="action-cell">${actionBtn}</td>
    </tr>`;
  }).join("");
}

//Flow: Click "XÃ¡c nháº­n" â†’ TÃ¬m appt data â†’ Má»Ÿ modal vá»›i prefill â†’ Staff chá»n phÃ²ng/giá» â†’ Submit
window.approveWeb = async function(id){
  // TÃ¬m appointment data tá»« cache
  const appt = (window._webAppts || []).find(a => a.id === id);
  if (!appt) {
    showToast('error', 'Lá»—i', MSG_WEB_GENERIC_ERR);
    return;
  }
  openConfirmOnlineRequestModal(appt);
}


function openConfirmOnlineRequestModal(appt) {
  // â”€â”€ STEP 1: Validate input â”€â”€
  if (!appt) {
    showToast('error', 'Lá»—i', 'KhÃ´ng tÃ¬m tháº¥y thÃ´ng tin Ä‘áº·t lá»‹ch');
    return;
  }

  // â”€â”€ STEP 2: Get modal elements â”€â”€
  const modalEl = document.getElementById("apptModal");
  const modalTitle = document.getElementById("modalTitle");
  const btnSaveText = document.getElementById("btnSaveText");

  if (!modalEl || !modalTitle) {
    showToast('error', 'Lá»—i', 'KhÃ´ng tÃ¬m tháº¥y modal form');
    return;
  }

  // â”€â”€ STEP 3: Reset modal state â”€â”€
  resetModalError();
  modalTitle.textContent = "XÃ¡c nháº­n yÃªu cáº§u Ä‘áº·t lá»‹ch";
  if (btnSaveText) btnSaveText.textContent = "XÃ¡c nháº­n & Táº¡o lá»‹ch";

  document.getElementById("apptId").value = "";
  document.getElementById("btnDelete").classList.add("d-none");
  document.getElementById('btnRebook')?.classList.add('d-none');

  // Set online request mode flag
  window._pendingOnlineRequestCode = appt.bookingCode || ''; // lÆ°u bookingCode cá»§a online request Ä‘ang Ä‘Æ°á»£c xÃ¡c nháº­n

  // Show form
  _showSharedForm(); // hiá»ƒn thá»‹ form lÃªn 
  _setAddGuestBtnVisible(false);

  // â”€â”€ STEP 4: Fill booker info (ngÆ°á»i Ä‘áº·t) â”€â”€
  document.getElementById('bookerName').value = appt.bookerName || appt.customerName || '';
  document.getElementById('bookerPhone').value = appt.bookerPhone || appt.phone || '';
  document.getElementById('bookerEmail').value = appt.bookerEmail || appt.email || '';
  document.getElementById('bookerSource').value = 'ONLINE';
  const bookerNoteEl = document.getElementById('bookerNote');
  if (bookerNoteEl) bookerNoteEl.value = appt.bookerNotes || '';

  // â”€â”€ STEP 5: Set booking date (ngÃ y háº¹n) â”€â”€
  const bookingDateEl = document.getElementById('bookingDate');
  if (bookingDateEl) {
    bookingDateEl.value = appt.date || '';
  }

  // â”€â”€ STEP 6: Clear old guests & Add new guest card â”€â”€
  _guestCount = 0;
  document.getElementById('guestList').innerHTML = '';

  addOnlineRequestGuestCard(appt);

  // â”€â”€ STEP 7: áº¨n nÃºt ba cháº¥m (gc-expand-btn) â”€â”€
  // Trong mode xÃ¡c nháº­n, khÃ´ng cáº§n nÃºt expand detail
  const expandBtns = document.querySelectorAll('.gc-expand-btn');
  expandBtns.forEach(btn => btn.classList.add('d-none'));

  // â”€â”€ STEP 7.5: áº¨n khá»‘i Tráº¡ng thÃ¡i & Thanh toÃ¡n â”€â”€
  // Tab "YÃªu cáº§u Ä‘áº·t lá»‹ch" chá»‰ xá»­ lÃ½ PENDING â†’ khÃ´ng cáº§n status dropdown
  _applyModalMode('request');

  // â”€â”€ STEP 8: Show modal â”€â”€
  const existing = bootstrap.Modal.getInstance(modalEl);
  const modal = existing || new bootstrap.Modal(modalEl);
  modal.show();

  // Show info toast
  showToast('info', 'XÃ¡c nháº­n yÃªu cáº§u', 'Vui lÃ²ng chá»n phÃ²ng vÃ  kiá»ƒm tra thÃ´ng tin trÆ°á»›c khi lÆ°u');
}


function addOnlineRequestGuestCard(onlineAppt) {
  const list = document.getElementById('guestList');
  if (!list) return;

  // Táº¡o guest item má»›i
  const idx = _guestCount++;
  const item = _buildGuestItem(idx, {});
  list.appendChild(item);

  // Fill info khÃ¡ch hÃ ng
  const nameInp = item.querySelector('.gc-name');
  if (nameInp) nameInp.value = onlineAppt.customerName || onlineAppt.bookerName || '';

  const phoneInp = item.querySelector('.gc-phone');
  if (phoneInp) phoneInp.value = onlineAppt.phone || onlineAppt.bookerPhone || '';

  const emailInp = item.querySelector('.gc-email');
  if (emailInp) emailInp.value = onlineAppt.email || onlineAppt.bookerEmail || '';

  // Fill service + variant
  if (onlineAppt.serviceId) {
    const svcSel = item.querySelector('.gc-service');
    if (svcSel) {
      svcSel.value = onlineAppt.serviceId;
      _loadGuestVariants(item, onlineAppt.serviceId, onlineAppt.variantId);
    }
  }

  // Fill date/time
  if (onlineAppt.date) {
    item.dataset.slotDate = onlineAppt.date;
    const dateInp = item.querySelector('.gc-date');
    if (dateInp) dateInp.value = onlineAppt.date;
  }

  if (onlineAppt.start) {
    item.dataset.slotTime = onlineAppt.start;
    const timeHid = item.querySelector('.gc-time');
    if (timeHid) timeHid.value = onlineAppt.start;
    const startInp = item.querySelector('.gc-time-input');
    if (startInp) startInp.value = onlineAppt.start;

    // Update time-range display Ä‘á»ƒ user tháº¥y giá» Ä‘Ã£ Ä‘áº·t
    const disp = item.querySelector('.gc-time-range-display');
    if (disp) {
      // TÃ­nh giá» káº¿t thÃºc (náº¿u cÃ³ duration tá»« variant thÃ¬ dÃ¹ng, default 60 phÃºt)
      let duration = 60; // default 60 phÃºt
      if (onlineAppt.variantId) {
        // Try to get duration from variant
        const variant = SERVICES.find(s => s.id === onlineAppt.serviceId)
          ?.variants?.find(v => v.id === onlineAppt.variantId);
        if (variant && variant.duration_minutes) {
          duration = variant.duration_minutes;
        }
      }
      const endTime = addMinutesToTime(onlineAppt.start, duration);
      // Extract HH:MM from start time in case it contains extra info
      const startTimeMatch = onlineAppt.start.match(/(\d{1,2}:\d{2})/);
      const startTimeDisplay = startTimeMatch ? startTimeMatch[1] : onlineAppt.start;
      disp.innerHTML = startTimeDisplay + '<span class="gc-time-range-sep"> â€“ </span>' + (endTime || '--:--');
    }
  }

  // Cáº­p nháº­t UI
  // Online request chá»‰ cÃ³ 1 khÃ¡ch â†’ khÃ´ng cáº§n Ä‘Ã¡nh sá»‘, progress bar (bá»‹ áº©n), delete button
  _markRowValidity(item);  // Highlight border Ä‘á»ƒ user biáº¿t dÃ²ng Ä‘Ã£ Ä‘á»§ info chÆ°a
}

window.rejectWeb = async function(id){
  const appt = (window._webAppts || []).find(a => a.id === id);
  const info = appt ? `${appt.customerName || appt.bookerName || ''} â€” ${appt.date} ${appt.start}` : id;

  const infoEl = document.getElementById('rejectWebInfo');
  if (infoEl) infoEl.textContent = info;

  const modalEl = document.getElementById('rejectWebModal');
  modalEl.addEventListener('shown.bs.modal', () => {
    document.querySelectorAll('.modal-backdrop').forEach(el => el.classList.add('reject-web-backdrop'));
  }, { once: true });
  modalEl.addEventListener('hidden.bs.modal', () => {
    document.querySelectorAll('.modal-backdrop').forEach(el => el.classList.remove('reject-web-backdrop'));
  }, { once: true });
  const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);

  // Gáº¯n handler má»™t láº§n, trÃ¡nh duplicate
  const btn = document.getElementById('confirmRejectWebBtn');
  const newBtn = _replaceWithClone(btn);

  newBtn.addEventListener('click', async () => {
    modal.hide();
    try {
      const result = await apiPost(`${API_BASE}/appointments/${id}/status/`, { status: 'REJECTED' });
      if (result.success) {
        showToast("success", "ThÃ nh cÃ´ng", MSG_REJECT_SUCCESS);
        await renderWebRequests();
        await refreshData();
      } else {
        showToast("error", "Lá»—i", MSG_WEB_GENERIC_ERR);
      }
    } catch (err) {
      showToast("error", "Lá»—i", MSG_WEB_GENERIC_ERR);
    }
  });

  modal.show();
}

window.rebookAppointment = async function(id) {
  // Guard: trÃ¡nh double-click má»Ÿ nhiá»u modal trong khi Ä‘ang fetch
  if (window._rebookInProgress) {
    console.warn('[Rebook] Äang xá»­ lÃ½, bá» qua click thá»«a â€” náº¿u bá»‹ káº¹t, reload trang');
    // Reset Ä‘á»ƒ khÃ´ng bá»‹ káº¹t mÃ£i
    window._rebookInProgress = false;
    return;
  }
  window._rebookInProgress = true;
  try {
    const result = await apiGet(`${API_BASE}/appointments/${id}/`);
    if (!result || !result.success || !result.appointment) {
      console.error('[Rebook] API tháº¥t báº¡i:', result);
      showToast('error', 'Lá»—i', MSG_WEB_GENERIC_ERR);
      return;
    }
    openRebookAsCreate(result.appointment);
  } catch (err) {
    console.error('[Rebook] Lá»—i fetch:', err);
    showToast('error', 'Lá»—i', MSG_WEB_GENERIC_ERR);
  } finally {
    window._rebookInProgress = false;
  }
};

/**
 * Má»Ÿ modal Táº O lá»‹ch má»›i, pre-fill tá»« lá»‹ch cÅ©.
 * KhÃ´ng copy ngÃ y/giá»/phÃ²ng â€” admin pháº£i chá»n láº¡i.
 *
 * Strategy: force-cleanup má»i modal/backdrop Ä‘ang má»Ÿ, sau Ä‘Ã³ má»Ÿ modal má»›i.
 * DÃ¹ng requestAnimationFrame Ä‘á»ƒ Ä‘áº£m báº£o DOM Ä‘Ã£ cleanup trÆ°á»›c khi Bootstrap
 * khá»Ÿi táº¡o modal má»›i.
 */
function openRebookAsCreate(a) {
  const prefill = {
    _fromRebook: true,
    _booker: {
      name:   a.bookerName  || '',
      phone:  a.bookerPhone || '',
      email:  a.bookerEmail || '',
      // Rebook luÃ´n lÃ  admin táº¡o trá»±c tiáº¿p â†’ source DIRECT, khÃ´ng copy source cÅ©
      // (trÃ¡nh trÆ°á»ng há»£p booking gá»‘c lÃ  ONLINE â†’ booking má»›i bá»‹ coi lÃ  online pending)
      source: 'DIRECT',
      note:   a.bookerNotes || '',
    },
    _guest: {
      name:      a.customerName || '',
      phone:     a.phone        || '',
      email:     a.email        || '',
      serviceId: a.serviceId    || null,
      variantId: a.variantId    || null,
      // KhÃ´ng copy: roomId, date, time, status, appointment_code, booking_code, invoice
    },
  };

  // BÆ°á»›c 2: Má»Ÿ modal táº¡o má»›i
  const _doOpen = () => {
    openCreateModal(prefill);
  };

  const modalEl = document.getElementById('apptModal');
  const isAnyModalOpen = !!document.querySelector('.modal.show') || !!document.querySelector('.modal-backdrop');

  if (isAnyModalOpen) {
    // CÃ³ modal Ä‘ang má»Ÿ â†’ Ä‘á»£i apptModal hidden rá»“i má»Ÿ láº¡i
    // Náº¿u apptModal Ä‘ang show, Ä‘Äƒng kÃ½ hidden event
    if (modalEl && modalEl.classList.contains('show')) {
      modalEl.addEventListener('hidden.bs.modal', () => {
        setTimeout(_doOpen, 50);
      }, { once: true });
      const inst = bootstrap.Modal.getInstance(modalEl);
      if (inst) inst.hide();
    } else {
      // Modal khÃ¡c Ä‘ang má»Ÿ (khÃ´ng pháº£i apptModal) â†’ force close táº¥t cáº£ rá»“i má»Ÿ ngay
      _forceCloseAllModals();
      setTimeout(_doOpen, 100);
    }
  } else {
    // KhÃ´ng cÃ³ modal nÃ o má»Ÿ â†’ má»Ÿ ngay
    _doOpen();
  }
}

// Äiá»n dropdown dá»‹ch vá»¥ cho filter bar scheduler
function fillServiceFilter(){
  const sel = document.getElementById('serviceFilter');
  if (sel) {
    _populateSelect(sel, SERVICES, 'id', 'name', 'Táº¥t cáº£ dá»‹ch vá»¥');
  }
  // Äiá»n dropdown dá»‹ch vá»¥ cho tab YÃªu cáº§u Ä‘áº·t lá»‹ch
  const webSel = document.getElementById('webServiceFilter');
  if (webSel) {
    _populateSelect(webSel, SERVICES, 'id', 'name', 'Táº¥t cáº£ dá»‹ch vá»¥');
  }
}

// ============================================================
// SECTION 10: CUSTOMER LOOKUP
// ============================================================
// Autofill thÃ´ng tin tá»« CustomerProfile khi nháº­p SÄT ngÆ°á»i Ä‘áº·t hoáº·c tá»«ng khÃ¡ch.
// KhÃ´ng tá»± fill ghi chÃº lá»‹ch háº¹n (bookerNote).
// KhÃ´ng ghi Ä‘Ã¨ dá»¯ liá»‡u user Ä‘Ã£ sá»­a tay, trá»« khi SÄT thay Ä‘á»•i.

/**
 * Lookup CustomerProfile theo SÄT qua API /api/customers/search/?q=<phone>
 * Tráº£ vá» customer object hoáº·c null náº¿u khÃ´ng tÃ¬m tháº¥y.
 */
async function _lookupCustomerByPhone(phone) {
  const digits = (phone || '').replace(/\D/g, '');
  if (digits.length < 10) return null;
  try {
    const result = await apiGet(`${API_BASE}/customers/search/?q=${encodeURIComponent(digits)}`);
    if (!result.success || !result.customers?.length) return null;
    // TÃ¬m exact match theo phone
    const exact = result.customers.find(c => (c.phone || '').replace(/\D/g, '') === digits);
    return exact || null;
  } catch (e) {
    return null;
  }
}

function initCustomerSearch() {
  // Bind blur trÃªn bookerPhone â†’ autofill booker info
  const bookerPhoneEl = document.getElementById('bookerPhone');
  if (!bookerPhoneEl) return;

  let _lastBookerPhone = '';

  bookerPhoneEl.addEventListener('blur', async function() {
    const phone = bookerPhoneEl.value.trim();
    const digits = phone.replace(/\D/g, '');
    // KhÃ´ng lookup náº¿u SÄT khÃ´ng Ä‘á»•i hoáº·c quÃ¡ ngáº¯n
    if (digits === _lastBookerPhone || digits.length < 10) return;
    _lastBookerPhone = digits;

    const customer = await _lookupCustomerByPhone(digits);
    if (!customer) {
      // KhÃ´ng tÃ¬m tháº¥y â†’ clear customerId, giá»¯ nguyÃªn dá»¯ liá»‡u user Ä‘ang nháº­p
      document.getElementById('selectedCustomerId').value = '';
      return;
    }

    // TÃ¬m tháº¥y â†’ autofill booker
    // Ghi Ä‘Ã¨ náº¿u profile má»›i khÃ¡c profile cÅ© (Ä‘á»•i SÄT sang khÃ¡ch khÃ¡c)
    const nameEl    = document.getElementById('bookerName');
    const emailEl   = document.getElementById('bookerEmail');
    const prevCustId = document.getElementById('selectedCustomerId').value || '';
    const isNewProfile = String(customer.id) !== prevCustId;

    // Fill tÃªn/email: ghi Ä‘Ã¨ khi profile má»›i khÃ¡c, hoáº·c Ã´ Ä‘ang trá»‘ng
    if (nameEl  && (isNewProfile || !nameEl.value.trim()))  nameEl.value  = customer.fullName || '';
    if (emailEl && (isNewProfile || !emailEl.value.trim())) emailEl.value = customer.email    || '';

    // LÆ°u customerId cá»§a booker
    document.getElementById('selectedCustomerId').value = String(customer.id);

    // Náº¿u cÃ³ guest card nÃ o Ä‘ang tick "= ngÆ°á»i Ä‘áº·t" â†’ sync xuá»‘ng + fill customer note
    _getGuestItems().forEach(item => {
      const chk = item.querySelector('.gc-same-as-booker');
      if (!chk || !chk.checked) return;
      const nameI   = item.querySelector('.gc-name');
      const emailI  = item.querySelector('.gc-email');
      const custIdI = item.querySelector('.gc-customer-id');
      const noteI   = item.querySelector('.gc-customer-note');
      const prevGuestCustId = (custIdI?.value || item.dataset.customerId || '');
      const isNewGuestProfile = String(customer.id) !== prevGuestCustId;
      if (nameI)  nameI.value  = customer.fullName || '';
      if (emailI) emailI.value = customer.email    || '';
      if (custIdI) custIdI.value = String(customer.id);
      item.dataset.customerId = String(customer.id);
      // Ghi Ä‘Ã¨ ghi chÃº há»“ sÆ¡ khÃ¡ch khi profile má»›i khÃ¡c, hoáº·c Ã´ Ä‘ang trá»‘ng
      if (noteI && (isNewGuestProfile || !noteI.value.trim())) {
        noteI.value = customer.notes || '';
        item.dataset.originalNote = (customer.notes || '').trim();
      }
    });
  });

  // â”€â”€ Sync 2 chiá»u: khi booker fields thay Ä‘á»•i â†’ cáº­p nháº­t guest cards Ä‘ang tick â”€â”€
  // DÃ¹ng 'input' Ä‘á»ƒ pháº£n há»“i ngay khi user gÃµ, khÃ´ng cáº§n blur
  function _syncCheckedGuests() {
    const newName  = document.getElementById('bookerName')?.value.trim()  || '';
    const newPhone = document.getElementById('bookerPhone')?.value.trim() || '';
    const newEmail = document.getElementById('bookerEmail')?.value.trim() || '';
    _getGuestItems().forEach(item => {
      const chk = item.querySelector('.gc-same-as-booker');
      if (!chk || !chk.checked) return;
      const nameI  = item.querySelector('.gc-name');
      const phoneI = item.querySelector('.gc-phone');
      const emailI = item.querySelector('.gc-email');
      if (nameI)  nameI.value  = newName;
      if (phoneI) phoneI.value = newPhone;
      if (emailI) emailI.value = newEmail;
    });
  }

  ['bookerName', 'bookerPhone', 'bookerEmail'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', _syncCheckedGuests);
  });
}

// Customer lookup stubs Ä‘Ã£ xÃ³a â€” chá»‰ giá»¯ _resetAllCustomerState dÃ¹ng trong modal reset
function _resetAllCustomerState() {
  document.getElementById('selectedCustomerId').value = '';
}

// ============================================================
// SECTION 11: MODAL & FORM HELPERS
// ============================================================
// Escape HTML Ä‘á»ƒ trÃ¡nh XSS
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

// â”€â”€ Helpers â”€â”€
function _getGuestItems() {
  return Array.from(document.querySelectorAll('#guestList .gc-item'));
}

function _getGuestItem(idx) {
  return document.querySelector(`#guestList .gc-item[data-idx="${idx}"]`);
}

/** Kiá»ƒm tra 1 guest row Ä‘Ã£ Ä‘á»§ trÆ°á»ng báº¯t buá»™c chÆ°a */
function _isGuestComplete(item) {
  if (!item) return false;
  const svc  = item.querySelector('.gc-service')?.value;
  const vari = item.querySelector('.gc-variant')?.value;
  const room = item.dataset.slotRoom || item.querySelector('.gc-room')?.value;
  const date = document.getElementById('bookingDate')?.value || item.dataset.slotDate || item.querySelector('.gc-date')?.value;
  const time = item.dataset.slotTime || item.querySelector('.gc-time')?.value;
  return !!(svc && vari && room && date && time);
}

/** Highlight Ã´ thiáº¿u trong 1 row */
function _markRowValidity(item) {
  if (!item) return;
  const row = item.querySelector('.gc-row');
  if (row) {
    const complete = _isGuestComplete(item);
    row.style.background      = '#fff';
    row.style.borderLeftColor = complete ? '#86efac' : '#fca5a5';
  }
}

/** Highlight lá»—i khi submit â€” chá»‰ gá»i khi user báº¥m LÆ°u */
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

/** Cáº­p nháº­t progress bar */
function _updateGuestProgress() {
  _updateCreatePayBtn();
}

/** Load variants cho 1 guest card */
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

/** Load variants cho 1 guest card */
function _loadGuestVariants(item, serviceId, selectedVariantId) {
  const varSel = item.querySelector('.gc-variant');
  if (!varSel) return;
  varSel.innerHTML = '<option value="">-- Chá»n gÃ³i --</option>';
  varSel.disabled  = true;
  varSel.style.color      = '#9ca3af';
  varSel.style.background = '#f9fafb';

  const svc = SERVICES.find(s => s.id === parseInt(serviceId, 10));
  if (!svc || !svc.variants?.length) {
    // KhÃ´ng cÃ³ variant â†’ giá»¯ disabled nhÆ°ng placeholder rÃµ rÃ ng
    varSel.innerHTML = '<option value="">-- Chá»n dá»‹ch vá»¥ trÆ°á»›c --</option>';
    return;
  }

  svc.variants.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = variantLabel(v);
    opt.dataset.duration = v.duration_minutes;
    if (selectedVariantId && v.id === parseInt(selectedVariantId, 10)) opt.selected = true;
    varSel.appendChild(opt);
  });

  // Enable + reset style vá» bÃ¬nh thÆ°á»ng
  varSel.disabled         = false;
  varSel.style.color      = '#111827';
  varSel.style.background = '#fff';
  varSel.style.opacity    = '1';

  if (!selectedVariantId && svc.variants.length === 1) {
    varSel.value = svc.variants[0].id;
  }
  _updateGuestEndTime(item);
  _updateCreatePayBtn();
}

/** TÃ­nh vÃ  lÆ°u end_time vÃ o dataset + cáº­p nháº­t hiá»ƒn thá»‹ (giá» káº¿t thÃºc auto-tÃ­nh) */
function _updateGuestEndTime(item) {
  const varSel = item.querySelector('.gc-variant');
  const timeVal = item.dataset.slotTime;
  if (!varSel || !timeVal) return;
  const opt = varSel.options[varSel.selectedIndex];
  const dur = opt?.dataset?.duration ? Number(opt.dataset.duration) : 60;
  const newEnd = addMinutesToTime(timeVal, dur);
  item.dataset.endTime = newEnd;
  // Cáº­p nháº­t hidden input
  const endHidden = item.querySelector('.gc-time-end');
  if (endHidden) endHidden.value = newEnd;
  // Cáº­p nháº­t time-range display (giá» káº¿t thÃºc readonly)
  const disp = item.querySelector('.gc-time-range-display');
  if (disp) {
    const startVal = item.dataset.slotTime || '--:--';
    disp.innerHTML = startVal + '<span class="gc-time-range-sep"> â€“ </span>' + newEnd;
  }
  // Cáº­p nháº­t legacy gc-slot-time náº¿u cÃ²n
  const endEl = item.querySelector('.gc-slot-time');
  if (endEl && item.dataset.slotTime) {
    endEl.textContent = `${item.dataset.slotTime}â€“${newEnd}`;
  }
}

/**
 * Validate thá»i Ä‘iá»ƒm chuyá»ƒn tráº¡ng thÃ¡i ARRIVED / COMPLETED.
 *
 * @param {string} dateStr   - "YYYY-MM-DD"
 * @param {string} timeStr   - "HH:MM"
 * @param {number} durationMin - sá»‘ phÃºt (máº·c Ä‘á»‹nh 60)
 * @param {string} newStatus - "ARRIVED" | "COMPLETED" | ...
 * @returns {{ ok: boolean, error: string }}
 */
function _validateStatusTiming(dateStr, timeStr, durationMin, newStatus) {
  if (newStatus !== 'ARRIVED' && newStatus !== 'COMPLETED') return { ok: true, error: '' };

  const dur = parseInt(durationMin, 10) || 60;

  // Parse start datetime (local)
  const [y, mo, d]  = (dateStr || '').split('-').map(Number);
  const [h, mi]     = (timeStr || '00:00').split(':').map(Number);
  if (!y || !mo || !d) return { ok: true, error: '' }; // khÃ´ng Ä‘á»§ data â†’ bá» qua

  const startMs = new Date(y, mo - 1, d, h, mi, 0).getTime();
  const endMs   = startMs + dur * 60 * 1000;
  const nowMs   = Date.now();

  if (newStatus === 'ARRIVED' && nowMs < startMs) {
    return { ok: false, error: 'ChÆ°a Ä‘áº¿n giá» háº¹n, khÃ´ng thá»ƒ chuyá»ƒn sang ÄÃ£ Ä‘áº¿n' };
  }
  if (newStatus === 'COMPLETED' && nowMs < endMs) {
    return { ok: false, error: 'ChÆ°a káº¿t thÃºc giá» háº¹n, khÃ´ng thá»ƒ hoÃ n thÃ nh lá»‹ch' };
  }
  return { ok: true, error: '' };
}

/**
 * Cáº­p nháº­t badge tráº¡ng thÃ¡i thanh toÃ¡n vÃ  label nÃºt invoice trong edit modal.
 * KhÃ´ng cÃ²n hiá»ƒn thá»‹ Tá»•ng/ÄÃ£ tráº£/CÃ²n láº¡i trong modal chá»‰nh lá»‹ch.
 */
function _updatePaymentSummary() {
  const apptId = document.getElementById('apptId');
  const isEdit = !!(apptId && apptId.value.trim());
  if (!isEdit) return;

  const payStatus = document.getElementById('sharedPayStatus')?.value || 'UNPAID';

  // Cáº­p nháº­t badge
  _setPayStatusBadge(payStatus);

  // Cáº­p nháº­t label + style nÃºt invoice
  const btnLabel = document.getElementById('btnInvoiceLabel');
  const btn      = document.getElementById('btnOpenInvoice');
  if (payStatus === 'PAID') {
    if (btnLabel) btnLabel.textContent = 'Xem hÃ³a Ä‘Æ¡n';
    if (btn) btn.className = 'btn-invoice-action btn-invoice-view';
  } else if (payStatus === 'REFUNDED') {
    if (btnLabel) btnLabel.textContent = 'Xem hÃ³a Ä‘Æ¡n';
    if (btn) btn.className = 'btn-invoice-action btn-invoice-view';
  } else if (payStatus === 'PARTIAL') {
    if (btnLabel) btnLabel.textContent = 'Thu thÃªm';
    if (btn) btn.className = 'btn-invoice-action btn-invoice-more';
  } else {
    if (btnLabel) btnLabel.textContent = 'Thanh toÃ¡n';
    if (btn) btn.className = 'btn-invoice-action';
  }
}

/**
 * Cáº­p nháº­t badge hiá»ƒn thá»‹ tráº¡ng thÃ¡i thanh toÃ¡n (readonly).
 */
function _setPayStatusBadge(payStatus) {
  const badge = document.getElementById('payStatusBadge');
  if (!badge) return;

  const MAP = {
    UNPAID:   { text: 'ChÆ°a thanh toÃ¡n', cls: 'pay-status-unpaid'   },
    PARTIAL:  { text: 'Má»™t pháº§n',         cls: 'pay-status-partial'  },
    PAID:     { text: 'ÄÃ£ thanh toÃ¡n',    cls: 'pay-status-paid'     },
    REFUNDED: { text: 'ÄÃ£ hoÃ n tiá»n',     cls: 'pay-status-refunded' },
  };
  const info = MAP[payStatus] || MAP.UNPAID;
  badge.textContent = info.text;
  badge.className   = `pay-status-badge ${info.cls}`;
}

/** Format sá»‘ tiá»n VNÄ */
function _fmtVND(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) return 'â€”';
  return Number(amount).toLocaleString('vi-VN') + 'Ä‘';
}

function _setSelectValue(sel, value, fallback) {
  if (!sel) return;
  const wanted = value || fallback || '';
  // <input type="hidden"> khÃ´ng cÃ³ .options â€” set value trá»±c tiáº¿p
  if (!sel.options) {
    sel.value = wanted;
    return;
  }
  const hasOption = Array.from(sel.options).some(opt => opt.value === wanted);
  sel.value = hasOption ? wanted : (fallback || '');
}

/**
 * Ãp dá»¥ng mode cho modal lá»‹ch háº¹n â€” pháº£i gá»i TRÆ¯á»šC modal.show().
 *
 * mode = 'request' : áº©n block Tráº¡ng thÃ¡i & Thanh toÃ¡n (xÃ¡c nháº­n online / Ä‘áº·t láº¡i tá»« request)
 * mode = 'normal'  : hiá»‡n láº¡i block Tráº¡ng thÃ¡i & Thanh toÃ¡n (táº¡o má»›i / chá»‰nh sá»­a bÃ¬nh thÆ°á»ng)
 *
 * Reset hoÃ n toÃ n tráº¡ng thÃ¡i áº©n/hiá»‡n cÅ© trÆ°á»›c khi apply mode má»›i,
 * trÃ¡nh tráº¡ng thÃ¡i tá»« láº§n má»Ÿ trÆ°á»›c bá»‹ giá»¯ láº¡i.
 */
function _applyModalMode(mode) {
  const sharedStatusBlock = document.getElementById('sharedStatusBlock');
  if (!sharedStatusBlock) return;

  if (mode === 'request') {
    // request-mode: áº©n Tráº¡ng thÃ¡i & Thanh toÃ¡n
    sharedStatusBlock.style.display = 'none';
    sharedStatusBlock.classList.add('d-none');
  } else {
    // normal-mode: hiá»‡n láº¡i â€” xÃ³a má»i class/style áº©n tá»« láº§n trÆ°á»›c
    sharedStatusBlock.style.display = 'block';
    sharedStatusBlock.classList.remove('d-none');
    sharedStatusBlock.classList.remove('hidden');
    sharedStatusBlock.removeAttribute('hidden');
  }
}

function _showSharedStatusBlock(statusValue, payValue, isEditMode) {
  const sharedStatusSel = document.getElementById('sharedApptStatus');
  const sharedPaySel    = document.getElementById('sharedPayStatus');
  _setSelectValue(sharedStatusSel, statusValue, 'NOT_ARRIVED');
  _setSelectValue(sharedPaySel,    payValue,    'UNPAID');

  const readonlyWrap  = document.getElementById('payStatusReadonlyWrap');
  const btnWrap       = document.getElementById('btnInvoiceWrap');

  // Shared status dropdown â€” hiá»‡n cáº£ create vÃ  edit mode
  const apptStatusWrap = sharedStatusSel ? sharedStatusSel.closest('.status-form-group') : null;

  if (apptStatusWrap) apptStatusWrap.style.display = '';
  if (readonlyWrap) readonlyWrap.classList.remove('d-none');
  if (btnWrap)      btnWrap.classList.remove('d-none');
  if (sharedPaySel) sharedPaySel.onchange = null;

  if (isEditMode) {
    // EDIT MODE: Ä‘Ã¡nh giÃ¡ láº¡i tráº¡ng thÃ¡i nÃºt dá»±a trÃªn dá»‹ch vá»¥ Ä‘Ã£ chá»n
    _updateCreatePayBtn();
    _updatePaymentSummary();
  } else {
    // CREATE MODE: badge readonly + nÃºt invoice
    // KhÃ´ng nháº­p thanh toÃ¡n trá»±c tiáº¿p, dÃ¹ng invoice modal sau khi táº¡o lá»‹ch
    // Badge luÃ´n "ChÆ°a thanh toÃ¡n" khi táº¡o má»›i
    _setPayStatusBadge('UNPAID');
    // ÄÃ¡nh giÃ¡ tráº¡ng thÃ¡i nÃºt dá»±a trÃªn dá»‹ch vá»¥ Ä‘Ã£ chá»n
    _updateCreatePayBtn();
    const btnInvoiceLabel = document.getElementById('btnInvoiceLabel');
    if (btnInvoiceLabel) btnInvoiceLabel.textContent = 'Thanh toÃ¡n';
  }
}

/** Build 1 compact guest row â€” detail panel áº©n máº·c Ä‘á»‹nh, toggle báº±ng JS */
function _buildGuestItem(idx, prefill) {
  prefill = prefill || {};
  const dayPicker = document.getElementById("dayPicker");
  var dateVal  = prefill.date || document.getElementById('bookingDate')?.value || dayPicker.value;
  var timeVal  = prefill.time || '';
  var endTime  = (timeVal && prefill.pendingDuration) ? addMinutesToTime(timeVal, prefill.pendingDuration) : '';

  var svcOpts = '<option value="">Dá»‹ch vá»¥</option>' +
    SERVICES.map(function(s){ return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');

  var inp = 'width:100%;height:36px;padding:0 12px;font-size:14px;border:1px solid #d1d5db;border-radius:6px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;';
  var sel = 'width:100%;height:36px;padding:0 10px;font-size:14px;border:1px solid #d1d5db;border-radius:6px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#111827;display:block;appearance:auto;';
  var roomSelectCss = sel.replace('width:100%;', 'width:112px;max-width:100%;');
  var sInp = 'width:100%;height:32px;padding:0 10px;font-size:13px;border:1px solid #e5e7eb;border-radius:5px;outline:none;background:#fff;box-sizing:border-box;font-family:inherit;color:#374151;display:block;';
  var lbl  = 'font-size:13px;font-weight:600;color:#6b7280;display:block;margin-bottom:4px;white-space:nowrap;';
  var selectedRoomId = prefill.roomId || '';

  // Slot badge: phÃ²ng dropdown + time-range field gá»n Ä‘áº¹p
  var roomOpts = '<option value="" disabled' + (selectedRoomId ? '' : ' selected') + ' hidden>Chá»n phÃ²ng</option>' +
    ROOMS.map(function(r){
      var roomId = r.id || r.code || '';
      var isSel = (String(roomId) === String(selectedRoomId)) ? ' selected' : '';
      var label = _roomShortLabel(r);
      var capacity = r.capacity || '';
      var title = label + (capacity ? ' - ' + capacity + ' giÆ°á»ng' : '');
      return '<option value="' + _esc(roomId) + '"' + isSel + ' data-capacity="' + _esc(capacity) + '" title="' + _esc(title) + '">' + _esc(label) + '</option>';
    }).join('');

  var slotBadge = '<div class="gc-slot-badge">'
    + '<select class="gc-room-select" required style="' + roomSelectCss + '">' + roomOpts + '</select>'
    + '<div class="gc-time-range-field" title="Click Ä‘á»ƒ chá»‰nh giá»">'
      + '<i class="far fa-clock gc-time-range-icon"></i>'
      + '<span class="gc-time-range-display">'
        + (timeVal ? _esc(timeVal) : '--:--')
        + '<span class="gc-time-range-sep"> â€“ </span>'
        + (endTime ? _esc(endTime) : '--:--')
      + '</span>'
      + '<div class="gc-time-range-inputs">'
        + '<input type="time" class="gc-time-input" value="' + _esc(timeVal) + '" title="Giá» báº¯t Ä‘áº§u" />'
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
  + '<input type="hidden" class="gc-customer-id" value="' + _esc(prefill.customerId || '') + '" />'

  // â”€â”€ DÃ’NG CHÃNH â”€â”€
  // Grid: # | PhÃ²ngÂ·Giá» | TÃªn khÃ¡ch (+ checkbox) | SÄT | Dá»‹ch vá»¥ | GÃ³i | Actions
  + '<div class="gc-row gc-row-grid">'

    // Col 1 â€” sá»‘ thá»© tá»±
    + '<div class="gc-num" style="text-align:center;font-size:13px;font-weight:700;color:#94a3b8;">â€”</div>'

    // Col 2 â€” phÃ²ng Â· giá»
    + '<div class="gc-slot-cell">' + slotBadge + '</div>'

    // Col 3 â€” tÃªn khÃ¡ch + checkbox "= ngÆ°á»i Ä‘áº·t"
    + '<div class="gc-name-cell">'
      + '<div class="gc-name-inline">'
        + '<input class="gc-name" style="' + inp + 'flex:1 1 220px;min-width:0;" placeholder="TÃªn khÃ¡ch *" value="' + _esc(prefill.name || '') + '" />'
        + '<label class="gc-same-booker-label" title="Äiá»n tá»« ngÆ°á»i Ä‘áº·t">'
          + '<input type="checkbox" class="gc-same-as-booker" style="width:14px;height:14px;cursor:pointer;accent-color:#1d4ed8;margin:0;" />'
          + '<span>= ngÆ°á»i Ä‘áº·t</span>'
        + '</label>'
      + '</div>'
    + '</div>'

    // Col 4 â€” SÄT
    + '<div class="gc-phone-cell"><input class="gc-phone" style="' + inp + '" placeholder="SÄT" inputmode="numeric" value="' + _esc(prefill.phone || '') + '" /></div>'

    // Col 5 â€” dá»‹ch vá»¥
    + '<div class="gc-service-cell"><select class="gc-service" style="' + sel + '">' + svcOpts + '</select></div>'

    // Col 6 â€” gÃ³i
    + '<div class="gc-variant-cell"><select class="gc-variant" style="' + sel + '" disabled><option value="">-- Chá»n dá»‹ch vá»¥ trÆ°á»›c --</option></select></div>'

    // Col 7 â€” actions
    + '<div class="gc-actions-cell" style="display:flex;align-items:center;justify-content:center;gap:6px;">'
      + '<button type="button" class="gc-expand-btn" onclick="toggleGuestCard(' + idx + ')" title="Email & ghi chÃº"'
      + ' style="height:36px;width:36px;padding:0;font-size:15px;background:#f1f5f9;border:1px solid #e2e8f0;color:#64748b;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;">'
      + '<i class="fas fa-ellipsis-h"></i></button>'
      + '<button type="button" class="gc-delete-btn" onclick="removeGuestCard(' + idx + ')" title="XÃ³a khÃ¡ch"'
      + ' style="height:36px;width:36px;padding:0;font-size:15px;background:#fff5f5;border:1px solid #fecaca;color:#ef4444;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s,opacity .15s;">'
      + '<i class="fas fa-trash-alt"></i></button>'
    + '</div>'

  + '</div>'

  // gc-sub-row Ä‘Ã£ chuyá»ƒn thÃ nh block chung á»Ÿ footer â€” khÃ´ng render per-guest anymore

  // â”€â”€ PHáº¦N Má»ž Rá»˜NG â€” Email + Ghi chÃº há»“ sÆ¡ khÃ¡ch + Tráº¡ng thÃ¡i (toggle báº±ng dáº¥u 3 cháº¥m) â”€â”€
  + '<div class="gc-detail-wrap">'
    + '<div class="gc-detail">'
      + '<div style="display:flex;flex-direction:column;gap:2px;min-width:150px;flex:1;">'
        + '<label style="' + lbl + '">Email</label>'
        + '<input type="email" class="gc-email" style="' + sInp + '" placeholder="Email (náº¿u cÃ³)" value="' + _esc(prefill.email || '') + '" />'
      + '</div>'
      // Dropdown tráº¡ng thÃ¡i riÃªng tá»«ng khÃ¡ch â€” Ä‘Ã£ chuyá»ƒn lÃªn gc-row-grid (col 7) Ä‘á»ƒ hiá»‡n rÃµ trong edit mode
      // Trong create mode, tráº¡ng thÃ¡i dÃ¹ng sharedApptStatus á»Ÿ footer
      + '<div style="display:flex;flex-direction:column;gap:2px;flex:3;min-width:180px;">'
        + '<label style="' + lbl + '">Ghi chÃº há»“ sÆ¡ khÃ¡ch <span style="font-weight:400;color:#9ca3af;font-size:12px;">(lÆ°u vÃ o há»“ sÆ¡ náº¿u khÃ¡ch cÃ³ há»“ sÆ¡)</span></label>'
        + '<input class="gc-customer-note" style="' + sInp + '" placeholder="Ghi chÃº lÃ¢u dÃ i tá»« há»“ sÆ¡ khÃ¡ch..." value="' + _esc(prefill.customerNote || '') + '" title="Ghi chÃº lÃ¢u dÃ i tá»« há»“ sÆ¡ khÃ¡ch â€” sáº½ Ä‘Æ°á»£c cáº­p nháº­t vÃ o há»“ sÆ¡ khi lÆ°u (náº¿u khÃ¡ch cÃ³ há»“ sÆ¡)" />'
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

  var svcSel = item.querySelector('.gc-service');
  var varSel = item.querySelector('.gc-variant');
  if (svcSel) {
    svcSel.addEventListener('change', function() {
      svcSel.style.borderColor = svcSel.value ? '#d1d5db' : '';
      svcSel.style.background  = '#fff';
      _loadGuestVariants(item, svcSel.value, null);
      _markRowValidity(item);
      _updateGuestProgress();
      _updateCreatePayBtn();
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
      _updateCreatePayBtn();
    });
  }
  var nameInp = item.querySelector('.gc-name');
  if (nameInp) nameInp.addEventListener('input', function() {
    nameInp.style.borderColor = nameInp.value.trim() ? '#d1d5db' : '';
    nameInp.style.background  = '#fff';
    _updateGuestProgress();
  });

  // â”€â”€ Autofill tá»« CustomerProfile khi blur khá»i Ã´ SÄT khÃ¡ch â”€â”€
  var phoneInp = item.querySelector('.gc-phone');
  if (phoneInp) {
    let _lastGuestPhone = '';
    phoneInp.addEventListener('blur', async function() {
      const phone  = phoneInp.value.trim();
      const digits = phone.replace(/\D/g, '');
      if (digits === _lastGuestPhone || digits.length < 10) return;
      _lastGuestPhone = digits;

      const customer = await _lookupCustomerByPhone(digits);
      if (!customer) {
        // KhÃ´ng tÃ¬m tháº¥y â†’ clear customerId, giá»¯ nguyÃªn dá»¯ liá»‡u user Ä‘ang nháº­p
        const custIdI = item.querySelector('.gc-customer-id');
        if (custIdI) custIdI.value = '';
        item.dataset.customerId = '';
        return;
      }

      // TÃ¬m tháº¥y â†’ autofill Ä‘Ãºng dÃ²ng nÃ y
      // Ghi Ä‘Ã¨ náº¿u profile má»›i khÃ¡c profile cÅ© (Ä‘á»•i SÄT sang khÃ¡ch khÃ¡c)
      const nameI   = item.querySelector('.gc-name');
      const emailI  = item.querySelector('.gc-email');
      const custIdI = item.querySelector('.gc-customer-id');
      const noteI   = item.querySelector('.gc-customer-note');
      const prevCustId = custIdI?.value || item.dataset.customerId || '';
      const isNewProfile = String(customer.id) !== prevCustId;

      if (nameI  && (isNewProfile || !nameI.value.trim()))  nameI.value  = customer.fullName || '';
      if (emailI && (isNewProfile || !emailI.value.trim())) emailI.value = customer.email    || '';

      // LÆ°u customerId vÃ o hidden field vÃ  dataset
      if (custIdI) custIdI.value = String(customer.id);
      item.dataset.customerId = String(customer.id);

      // Ghi Ä‘Ã¨ ghi chÃº há»“ sÆ¡ khÃ¡ch khi profile má»›i khÃ¡c, hoáº·c Ã´ Ä‘ang trá»‘ng
      if (noteI && (isNewProfile || !noteI.value.trim())) {
        noteI.value = customer.notes || '';
        item.dataset.originalNote = (customer.notes || '').trim();
      }

      _updateGuestProgress();
    });
  }

  // Checkbox "= ngÆ°á»i Ä‘áº·t" â€” sync tÃªn + SÄT + email tá»« booker khi tick
  var sameChk = item.querySelector('.gc-same-as-booker');
  if (sameChk) {
    sameChk.addEventListener('change', function() {
      var nameI  = item.querySelector('.gc-name');
      var phoneI = item.querySelector('.gc-phone');
      var emailI = item.querySelector('.gc-email');
      var custIdI = item.querySelector('.gc-customer-id');
      if (sameChk.checked) {
        if (nameI)  nameI.value  = document.getElementById('bookerName')?.value.trim()  || '';
        if (phoneI) phoneI.value = document.getElementById('bookerPhone')?.value.trim() || '';
        if (emailI) emailI.value = document.getElementById('bookerEmail')?.value.trim() || '';
        if (nameI)  nameI.readOnly  = true;
        if (phoneI) phoneI.readOnly = true;
        // Khi tick "= ngÆ°á»i Ä‘áº·t": copy customerId cá»§a booker vÃ o guest
        // (booker customerId Ä‘Æ°á»£c lÆ°u trong #selectedCustomerId)
        const bookerCustId = document.getElementById('selectedCustomerId')?.value || '';
        if (custIdI) custIdI.value = bookerCustId;
        item.dataset.customerId = bookerCustId;
        // Ghi chÃº há»“ sÆ¡ khÃ¡ch: fill tá»« CustomerProfile cá»§a booker náº¿u cÃ³ vÃ  Ã´ Ä‘ang trá»‘ng
        if (bookerCustId) {
          const noteI = item.querySelector('.gc-customer-note');
          if (noteI && !noteI.value.trim()) {
            // Lookup async â€” khÃ´ng block UI
            _lookupCustomerByPhone(document.getElementById('bookerPhone')?.value || '').then(c => {
              if (c && noteI && !noteI.value.trim()) {
                noteI.value = c.notes || '';
                item.dataset.originalNote = (c.notes || '').trim();
              }
            });
          }
        }
      } else {
        if (nameI)  { nameI.value  = ''; nameI.readOnly  = false; }
        if (phoneI) { phoneI.value = ''; phoneI.readOnly = false; }
        if (emailI) emailI.readOnly = false;
        // Bá» tick â†’ khÃ¡ch lÃ  ngÆ°á»i khÃ¡c, xÃ³a customerId Ä‘á»ƒ trÃ¡nh update nháº§m profile ngÆ°á»i Ä‘áº·t
        if (custIdI) custIdI.value = '';
        item.dataset.customerId = '';
        // XÃ³a ghi chÃº há»“ sÆ¡ vÃ¬ chÆ°a biáº¿t profile cá»§a khÃ¡ch nÃ y
        const noteI = item.querySelector('.gc-customer-note');
        if (noteI) noteI.value = '';
        item.dataset.originalNote = '';
      }
      _updateGuestProgress();
    });
  }

  // â”€â”€ Bind time inputs â€” sync vá» hidden fields + dataset â”€â”€
  var startInp = item.querySelector('.gc-time-input');
  var timeHid  = item.querySelector('.gc-time');
  var endHid   = item.querySelector('.gc-time-end');

  function _syncTimeDisplay() {
    var disp = item.querySelector('.gc-time-range-display');
    if (!disp) return;
    var s = startInp ? startInp.value : '';
    // Giá» káº¿t thÃºc luÃ´n tÃ­nh tá»« giá» báº¯t Ä‘áº§u + duration
    var varSel = item.querySelector('.gc-variant');
    var dur = 60;
    if (varSel && varSel.selectedIndex >= 0) {
      var opt = varSel.options[varSel.selectedIndex];
      dur = opt?.dataset?.duration ? Number(opt.dataset.duration) : 60;
    }
    var e = s ? addMinutesToTime(s, dur) : '--:--';
    disp.innerHTML = (s || '--:--') + '<span class="gc-time-range-sep"> â€“ </span>' + e;
  }

  if (startInp) {
    startInp.addEventListener('change', function() {
      var v = startInp.value;
      item.dataset.slotTime = v;
      if (timeHid) timeHid.value = v;
      // TÃ­nh láº¡i end tá»« variant duration (luÃ´n luÃ´n tÃ­nh)
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

  // â”€â”€ Click vÃ o cá»¥m time-range â†’ toggle editing mode â”€â”€
  var timeRangeField = item.querySelector('.gc-time-range-field');
  if (timeRangeField) {
    timeRangeField.addEventListener('click', function(e) {
      if (e.target.tagName === 'INPUT') return; // Ä‘ang trong input thÃ¬ khÃ´ng toggle
      var isEditing = timeRangeField.classList.contains('is-editing');
      if (!isEditing) {
        timeRangeField.classList.add('is-editing');
        // Focus vÃ o input giá» báº¯t Ä‘áº§u
        setTimeout(function() {
          var inp = timeRangeField.querySelector('.gc-time-input');
          if (inp) inp.focus();
        }, 30);
      }
    });
    // Click ra ngoÃ i â†’ Ä‘Ã³ng editing (dÃ¹ng AbortController Ä‘á»ƒ trÃ¡nh leak khi card bá»‹ xÃ³a)
    var _trAbort = new AbortController();
    document.addEventListener('click', function(e) {
      if (!timeRangeField.contains(e.target)) {
        timeRangeField.classList.remove('is-editing');
      }
    }, { signal: _trAbort.signal });
    // Cleanup khi card bá»‹ remove khá»i DOM
    new MutationObserver(function(_, obs) {
      if (!document.contains(item)) { _trAbort.abort(); obs.disconnect(); }
    }).observe(document.body, { childList: true, subtree: true });
    // Enter tá»« input â†’ Ä‘Ã³ng editing
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

  // LÆ°u appointment_code vÃ o dataset Ä‘á»ƒ submit handler biáº¿t update Ä‘Ãºng appt
  if (prefill._apptId) {
    item.dataset.apptId = prefill._apptId;
  }

  // LÆ°u customerId vÃ  originalNote Ä‘á»ƒ so sÃ¡nh khi update note
  if (prefill.customerId) {
    item.dataset.customerId = String(prefill.customerId);
  }
  // originalNote: lÆ°u note gá»‘c tá»« profile Ä‘á»ƒ so sÃ¡nh trÆ°á»›c khi gá»i API
  item.dataset.originalNote = (prefill.customerNote || '').trim();

  // LÆ°u date/time/room gá»‘c Ä‘á»ƒ edit submit chá»‰ gá»­i khi thá»±c sá»± thay Ä‘á»•i
  if (prefill._editMode) {
    item.dataset.originalDate    = prefill.date    || '';
    item.dataset.originalTime    = prefill.time    || '';
    item.dataset.originalRoom    = prefill.roomId  || '';
    // LÆ°u variantId gá»‘c Ä‘á»ƒ detect khi variant Ä‘á»•i â†’ gá»­i kÃ¨m roomId cho BE validate overlap
    item.dataset.originalVariantId = prefill.variantId ? String(prefill.variantId) : '';
    // LÆ°u status gá»‘c Ä‘á»ƒ _hasUnsavedGuestChanges detect thay Ä‘á»•i (so sÃ¡nh vá»›i sharedApptStatus)
    item.dataset.originalApptStatus = prefill.apptStatus || 'NOT_ARRIVED';
  }

  if (prefill.serviceId) {
    const svcSel = item.querySelector('.gc-service');
    if (svcSel) {
      svcSel.value = prefill.serviceId;
      _loadGuestVariants(item, prefill.serviceId, prefill.variantId);
    }
  }

  // Set room/date/time tá»« prefill náº¿u cÃ³ (edit mode)
  if (prefill.roomId) {
    item.dataset.slotRoom = prefill.roomId;
    const roomInp = item.querySelector('.gc-room');
    if (roomInp) roomInp.value = prefill.roomId;
    // Cáº­p nháº­t select phÃ²ng
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

window.removeGuestCard = async function(idx) {
  const items = _getGuestItems();
  const item  = _getGuestItem(idx);
  if (!item) return;

  // Láº¥y _apptId tá»« dataset (Ä‘Æ°á»£c set khi build guest card trong edit mode)
  const targetApptId = item.dataset.apptId || '';

  // Náº¿u chá»‰ cÃ²n 1 dÃ²ng â†’ khÃ´ng cho xÃ³a, yÃªu cáº§u dÃ¹ng nÃºt XÃ³a lá»‹ch
  if (items.length <= 1) {
    showToast('warning', 'KhÃ´ng thá»ƒ xÃ³a', 'Booking chá»‰ cÃ²n 1 khÃ¡ch. DÃ¹ng nÃºt "XÃ³a" Ä‘á»ƒ xÃ³a toÃ n bá»™ lá»‹ch háº¹n.');
    return;
  }

  // Náº¿u card chÆ°a cÃ³ appointment_id (card má»›i thÃªm chÆ°a lÆ°u) â†’ chá»‰ remove DOM
  if (!targetApptId) {
    item.remove();
    _renumberGuests();
    _updateGuestProgress();
    _updateDeleteBtnState();
    return;
  }

  // Card Ä‘Ã£ cÃ³ appointment_id â†’ há»i confirm rá»“i gá»i API delete
  const customerName = item.querySelector('.gc-name')?.value.trim() || 'khÃ¡ch nÃ y';
  const confirmed = await confirmAction(
    'XÃ³a khÃ¡ch khá»i booking?',
    `XÃ³a "${customerName}" khá»i booking nÃ y? HÃ nh Ä‘á»™ng khÃ´ng thá»ƒ hoÃ n tÃ¡c.`,
    'XÃ³a',
    'Há»§y'
  );
  if (!confirmed) return;

  // Disable nÃºt xÃ³a trong lÃºc Ä‘ang gá»i API
  const deleteBtn = item.querySelector('.gc-delete-btn');
  if (deleteBtn) { deleteBtn.disabled = true; deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }

  try {
    const result = await apiPost(`${API_BASE}/appointments/${targetApptId}/delete/`, {});
    if (result.success) {
      item.remove();
      _renumberGuests();
      _updateGuestProgress();
      _updateDeleteBtnState();
      showToast('success', 'ÄÃ£ xÃ³a', `ÄÃ£ xÃ³a ${customerName} khá»i booking`);
    } else {
      // Restore nÃºt náº¿u tháº¥t báº¡i
      if (deleteBtn) { deleteBtn.disabled = false; deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>'; }
      showToast('error', 'KhÃ´ng thá»ƒ xÃ³a', result.error || 'XÃ³a tháº¥t báº¡i, vui lÃ²ng thá»­ láº¡i.');
    }
  } catch (err) {
    if (deleteBtn) { deleteBtn.disabled = false; deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>'; }
    showToast('error', 'Lá»—i', 'XÃ³a tháº¥t báº¡i, vui lÃ²ng thá»­ láº¡i.');
  }
};

function _renumberGuests() {
  _getGuestItems().forEach((item, i) => {
    const numEl = item.querySelector('.gc-num');
    if (numEl) numEl.textContent = i + 1;
  });
}

/** Disable nÃºt xÃ³a khi chá»‰ cÃ²n 1 dÃ²ng, enable láº¡i khi cÃ³ nhiá»u hÆ¡n */
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

function _collectGuestCards() {
  const bookerNote = document.getElementById('bookerNote')?.value.trim() || '';
  // NgÃ y háº¹n chung cho toÃ n booking â€” Ä‘á»c tá»« field #bookingDate á»Ÿ booker section
  const sharedDate = document.getElementById('bookingDate')?.value || '';
  // Äá»c tráº¡ng thÃ¡i tá»« block footer (dÃ¹ng cho CREATE mode)
  const sharedStatus  = document.getElementById('sharedApptStatus')?.value  || 'NOT_ARRIVED';
  return _getGuestItems().map(item => {
    const variantSel = item.querySelector('.gc-variant');
    const selectedVariantOpt = variantSel?.options[variantSel.selectedIndex];
    // Tráº¡ng thÃ¡i láº¥y tá»« sharedApptStatus chung â€” Ã¡p dá»¥ng cho táº¥t cáº£ guests (cáº£ create vÃ  edit mode)
    const perCardDate = item.dataset.slotDate || item.querySelector('.gc-date')?.value || '';
    // BUG-006 FIX: Cáº£ edit mode vÃ  create mode Ä‘á»u Æ°u tiÃªn per-card date.
    // sharedDate chá»‰ dÃ¹ng lÃ m fallback khi per-card date rá»—ng.
    const resolvedDate = perCardDate || sharedDate;
    return {
      name:               item.querySelector('.gc-name')?.value.trim() || '',
      phone:              item.querySelector('.gc-phone')?.value.trim() || '',
      email:              item.querySelector('.gc-email')?.value.trim() || '',
      serviceId:          item.querySelector('.gc-service')?.value || '',
      variantId:          variantSel?.value || '',
      roomId:             item.dataset.slotRoom || item.querySelector('.gc-room')?.value || '',
      date:               resolvedDate,
      time:               item.querySelector('.gc-time-input')?.value || item.dataset.slotTime || item.querySelector('.gc-time')?.value || '',
      apptStatus:         sharedStatus,
      note:               bookerNote,
      customerNote:       item.querySelector('.gc-customer-note')?.value.trim() || '',
      customerId:         item.querySelector('.gc-customer-id')?.value || item.dataset.customerId || '',
      originalNote:       item.dataset.originalNote || '',
      originalDate:       item.dataset.originalDate || '',
      originalTime:       item.dataset.originalTime || '',
      originalRoom:       item.dataset.originalRoom || '',
      _originalVariantId: item.dataset.originalVariantId || '',
      _duration:          selectedVariantOpt?.dataset?.duration || 60,
      _finalAmount:       item.dataset.finalAmount || 0,
      _apptId:            item.dataset.apptId || '',   // appointment_code náº¿u lÃ  edit mode
    };
  });
}

/**
 * Cáº­p nháº­t ghi chÃº há»“ sÆ¡ khÃ¡ch cho tá»«ng guest cÃ³ thay Ä‘á»•i note.
 *
 * Quy táº¯c:
 * 1. Chá»‰ update khi guest cÃ³ customerId â€” khÃ´ng dÃ¹ng phone Ä‘á»ƒ xÃ¡c Ä‘á»‹nh profile
 * 2. KhÃ´ng cÃ³ customerId â†’ bá» qua (toast nháº¹ náº¿u note cÃ³ thay Ä‘á»•i)
 * 3. Chá»‰ gá»i API khi note thá»±c sá»± thay Ä‘á»•i (so sÃ¡nh originalNote vs newNote)
 * 4. Náº¿u xÃ³a note (originalNote â‰  '' vÃ  newNote = '') â†’ há»i confirm trÆ°á»›c
 * 5. API lá»—i â†’ hiá»ƒn thá»‹ toast cáº£nh bÃ¡o (khÃ´ng silent fail)
 *
 * @param {Array} cards - máº£ng guest card data tá»« _collectGuestCards()
 * @param {boolean} [skipConfirm=false] - bá» qua confirm xÃ³a note (dÃ¹ng khi Ä‘Ã£ confirm trÆ°á»›c)
 */
async function _updateCustomerNotes(cards, skipConfirm = false) {
  for (const g of cards) {
    const newNote      = (g.customerNote || '').trim();
    const originalNote = (g.originalNote || '').trim();
    const customerId   = (g.customerId || '').toString().trim();
    const guestLabel   = g.name ? ` (${g.name})` : '';

    // KhÃ´ng thay Ä‘á»•i â†’ khÃ´ng gá»i API
    if (newNote === originalNote) continue;

    // KhÃ´ng cÃ³ customerId â†’ khÃ´ng update, toast nháº¹ náº¿u ngÆ°á»i dÃ¹ng Ä‘Ã£ nháº­p note
    if (!customerId) {
      if (newNote) {
        showToast('warning', 'LÆ°u Ã½', `KhÃ¡ch${guestLabel} chÆ°a cÃ³ há»“ sÆ¡ nÃªn ghi chÃº chÆ°a Ä‘Æ°á»£c lÆ°u vÃ o há»“ sÆ¡ khÃ¡ch.`);
      }
      continue;
    }

    // XÃ³a note (originalNote cÃ³ giÃ¡ trá»‹, newNote rá»—ng) â†’ há»i confirm
    if (!skipConfirm && originalNote !== '' && newNote === '') {
      const nameLabel = g.name ? `"${g.name}"` : 'khÃ¡ch nÃ y';
      const confirmed = await confirmAction(
        'XÃ³a ghi chÃº há»“ sÆ¡ khÃ¡ch',
        `Báº¡n cÃ³ cháº¯c muá»‘n xÃ³a ghi chÃº há»“ sÆ¡ khÃ¡ch cá»§a ${nameLabel}?`,
        'XÃ³a ghi chÃº',
        'Giá»¯ láº¡i'
      );
      if (!confirmed) continue;
    }

    // CÃ³ customerId â†’ update theo ID
    try {
      const result = await apiPost(`${API_BASE}/customers/id/${customerId}/note/`, { note: newNote });
      if (!result.success) {
        showToast('warning', 'Cáº£nh bÃ¡o', `KhÃ´ng cáº­p nháº­t Ä‘Æ°á»£c ghi chÃº há»“ sÆ¡ khÃ¡ch${guestLabel}`);
      }
    } catch (e) {
      console.warn('_updateCustomerNotes: failed for customerId', customerId, e);
      showToast('warning', 'Cáº£nh bÃ¡o', `KhÃ´ng cáº­p nháº­t Ä‘Æ°á»£c ghi chÃº há»“ sÆ¡ khÃ¡ch${guestLabel}`);
    }
  }
}

/** Ãp dá»¥ng service/variant cho táº¥t cáº£ guest rows */
function _initApplyAllBar() {
  const applyAllSvc = document.getElementById('applyAllService');
  if (applyAllSvc) {
    _populateSelect(applyAllSvc, SERVICES, 'id', 'name', 'Dá»‹ch vá»¥');
    applyAllSvc.onchange = function() {
      const varSel = document.getElementById('applyAllVariant');
      if (!varSel) return;
      varSel.innerHTML = '<option value="">-- GÃ³i --</option>';
      varSel.disabled  = true;
      varSel.style.color      = '#9ca3af';
      varSel.style.background = '#f9fafb';
      const svc = SERVICES.find(s => String(s.id) === this.value);
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
      const apptIdEl = document.getElementById('apptId');
      const bookingCode = apptIdEl?.dataset.bookingCode || '';
      const allApptIds  = apptIdEl?.dataset.allApptIds  || '';

      _savedBookerInfo = {
        name:        document.getElementById('bookerName')?.value   || '',
        phone:       document.getElementById('bookerPhone')?.value  || '',
        email:       document.getElementById('bookerEmail')?.value  || '',
        source:      document.getElementById('bookerSource')?.value || 'DIRECT',
        note:        document.getElementById('bookerNote')?.value   || '',
        bookingDate: document.getElementById('bookingDate')?.value  || '',
      };

      // LÆ°u context edit mode (náº¿u cÃ³ bookingCode thÃ¬ Ä‘ang á»Ÿ edit)
      _addingSlotEditBookingCode = bookingCode || null;
      if (bookingCode) {
        // LÆ°u láº¡i toÃ n bá»™ guest cards hiá»‡n táº¡i Ä‘á»ƒ restore sau
        _savedBookerInfo._allApptIds  = allApptIds;
        _savedBookerInfo._bookingCode = bookingCode;
        // Snapshot cÃ¡c guest card hiá»‡n táº¡i
        _savedBookerInfo._existingGuests = _getGuestItems().map(item => ({
          name:       item.querySelector('.gc-name')?.value       || '',
          phone:      item.querySelector('.gc-phone')?.value      || '',
          email:      item.querySelector('.gc-email')?.value      || '',
          serviceId:  item.querySelector('.gc-service')?.value    || '',
          variantId:  item.querySelector('.gc-variant')?.value    || '',
          roomId:     item.querySelector('.gc-room')?.value       || '',
          date:       item.querySelector('.gc-date')?.value       || '',
          time:       item.querySelector('.gc-time')?.value       || '',
          apptStatus: item.dataset.originalApptStatus             || 'NOT_ARRIVED',
          customerId: item.dataset.customerId                     || '',
          _editMode:  true,
          _apptId:    item.dataset.apptId                         || '',
        }));
      } else {
        _addingSlotEditBookingCode = null;
      }

      _addingSlotMode = true;
      const modalEl = document.getElementById("apptModal");
      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.hide();
      showToast('info', 'Chá»n thÃªm slot', 'HÃ£y chá»n thÃªm 1 slot trÃªn lá»‹ch Ä‘á»ƒ thÃªm khÃ¡ch má»›i, rá»“i báº¥m "Tiáº¿p tá»¥c"');
    };
  }

  // KhÃ´ng auto-fill booker â†’ guest: dá»¯ liá»‡u khÃ¡ch vÃ  ngÆ°á»i Ä‘áº·t hoÃ n toÃ n Ä‘á»™c láº­p
}

// â”€â”€ Helpers Ä‘á»ƒ show/hide shared form â”€â”€
function _showSharedForm() {
  const f = document.getElementById('apptForm');
  if (f) { f.style.display = 'flex'; }
}
function _setAddGuestBtnVisible(visible) {
  // "createOnlyBar" chá»©a nÃºt "ThÃªm khÃ¡ch" â€” hiá»‡n trong cáº£ create láº«n edit mode.
  // visible=false chá»‰ dÃ¹ng cho rebook vÃ  online-confirm (khÃ´ng cho thÃªm khÃ¡ch má»›i).
  // Edit mode thÃ´ng thÆ°á»ng KHÃ”NG gá»i hÃ m nÃ y vá»›i false ná»¯a â€” xem openEditModalWithData.
  const bar = document.getElementById('createOnlyBar');
  if (bar) bar.style.display = 'flex';
  const btnAdd = document.getElementById('btnAddGuest');
  if (btnAdd) btnAdd.style.display = visible ? '' : 'none';
}

function openCreateModal(prefill={}){
  try {
  const modalEl = document.getElementById("apptModal");
  const modalTitle = document.getElementById("modalTitle");
  const apptId = document.getElementById("apptId");
  const btnDelete = document.getElementById("btnDelete");
  const dayPicker = document.getElementById("dayPicker");

  resetModalError();
  modalTitle.textContent = "Táº¡o lá»‹ch háº¹n";
  apptId.value = "";
  btnDelete.classList.add("d-none");
  document.getElementById('btnRebook')?.classList.add('d-none');
  // Reset online request state
  window._pendingOnlineRequestCode = '';

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "Táº¡o lá»‹ch háº¹n";

  // Hiá»‡n shared form, báº­t create-only bar
  _showSharedForm();
  _setAddGuestBtnVisible(true);

  // Label panel
  const lbl = document.getElementById('bookerPanelLabel');
  if (lbl) lbl.textContent = 'NgÆ°á»i Ä‘áº·t lá»‹ch';

  // Reset ngÆ°á»i Ä‘áº·t
  document.getElementById('bookerName').value   = '';
  document.getElementById('bookerPhone').value  = '';
  document.getElementById('bookerEmail').value  = '';
  document.getElementById('bookerSource').value = 'DIRECT';
  const bookerNoteEl = document.getElementById('bookerNote');
  if (bookerNoteEl) bookerNoteEl.value = '';
  // Set ngÃ y háº¹n chung â€” máº·c Ä‘á»‹nh lÃ  ngÃ y Ä‘ang xem trÃªn grid
  const bookingDateEl = document.getElementById('bookingDate');
  if (bookingDateEl) bookingDateEl.value = prefill.day || dayPicker.value || '';

  // Reset danh sÃ¡ch khÃ¡ch
  _guestCount = 0;
  document.getElementById('guestList').innerHTML = '';

  if (prefill._fromRebook && prefill._booker) {
    _isRebookMode = true;
    const rb = prefill._booker;
    _fillBookerFields(rb);
    addGuestCard({
      name:        prefill._guest?.name      || '',
      phone:       prefill._guest?.phone     || '',
      email:       prefill._guest?.email     || '',
      serviceId:   prefill._guest?.serviceId || null,
      variantId:   prefill._guest?.variantId || null,
      date:        dayPicker.value,
    });
    modalTitle.textContent = 'Äáº·t láº¡i lá»‹ch háº¹n';
    _setAddGuestBtnVisible(false);
    showToast('info', 'Äáº·t láº¡i', 'Vui lÃ²ng chá»n ngÃ y, giá» vÃ  phÃ²ng má»›i');
  } else if (prefill._fromOnlineRequest && prefill._booker) {
    _isRebookMode = false;
    // LÆ°u booking request code Ä‘á»ƒ submit sau
    window._pendingOnlineRequestCode = prefill._bookingRequestCode || '';
    const rb = prefill._booker;
    _fillBookerFields(rb, 'ONLINE');
    // Set ngÃ y háº¹n tá»« request
    const reqDate = prefill._guest?.date || '';
    if (reqDate && bookingDateEl) bookingDateEl.value = reqDate;
    addGuestCard({
      name:        prefill._guest?.name      || '',
      phone:       prefill._guest?.phone     || '',
      email:       prefill._guest?.email     || '',
      serviceId:   prefill._guest?.serviceId || null,
      variantId:   prefill._guest?.variantId || null,
      date:        reqDate || dayPicker.value || '',
      time:        prefill._guest?.time      || '',
      // roomId sáº½ Ä‘á»ƒ trá»‘ng â€” staff pháº£i chá»n
    });
    modalTitle.textContent = 'XÃ¡c nháº­n yÃªu cáº§u Ä‘áº·t lá»‹ch';
    if (btnSaveText) btnSaveText.textContent = 'XÃ¡c nháº­n & Táº¡o lá»‹ch';
    _setAddGuestBtnVisible(false);
    showToast('info', 'XÃ¡c nháº­n yÃªu cáº§u', 'Vui lÃ²ng chá»n phÃ²ng vÃ  kiá»ƒm tra thÃ´ng tin trÆ°á»›c khi lÆ°u');
  } else if (prefill._fromPending && prefill._blocks && prefill._blocks.length > 0) {
    _isRebookMode = false;
    if (prefill._restoreBooker) {
      const rb = prefill._restoreBooker;
      _fillBookerFields(rb);
      // KhÃ´i phá»¥c ngÃ y háº¹n Ä‘Ã£ lÆ°u
      const bookingDateEl3 = document.getElementById('bookingDate');
      if (bookingDateEl3 && rb.bookingDate) bookingDateEl3.value = rb.bookingDate;
    }
    // Set ngÃ y háº¹n chung tá»« block Ä‘áº§u tiÃªn
    const bookingDateEl2 = document.getElementById('bookingDate');
    if (bookingDateEl2 && prefill._blocks[0]?.day) bookingDateEl2.value = prefill._blocks[0].day;
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
  _resetAllCustomerState();

  // XÃ¡c Ä‘á»‹nh mode vÃ  apply TRÆ¯á»šC KHI show modal â€” khÃ´ng bá»‹ nhÃ¡ UI
  const _isOnlineRequestMode = !!(prefill._fromOnlineRequest);
  const _isRebookModeLocal   = !!(prefill._fromRebook);
  const _shouldHideStatus    = _isOnlineRequestMode || _isRebookModeLocal;

  if (_shouldHideStatus) {
    _applyModalMode('request');
  } else {
    _applyModalMode('normal');
    _showSharedStatusBlock('NOT_ARRIVED', 'UNPAID', false);
  }
  // Reset payment táº¡m má»—i láº§n má»Ÿ modal táº¡o má»›i
  _createModePayment = { payStatus: 'UNPAID', paymentMethod: '', paymentAmount: 0 };

  let modal = null;
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (!modal) {
    console.error('[openCreateModal] KhÃ´ng khá»Ÿi táº¡o Ä‘Æ°á»£c Bootstrap Modal instance');
    return;
  }
  modalEl.addEventListener('shown.bs.modal', () => {

    // XÃ“A nÃºt ba cháº¥m vÃ  XÃ“A HOÃ€N TOÃ€N Email + Ghi chÃº trong form "XÃ¡c nháº­n" vÃ  "Äáº·t láº¡i"
    if (_shouldHideStatus) {
      const guestItems = document.querySelectorAll('.gc-item');
      guestItems.forEach(item => {
        const expandBtn = item.querySelector('.gc-expand-btn');
        if (expandBtn) expandBtn.remove();
        const detailWrap = item.querySelector('.gc-detail-wrap');
        if (detailWrap) detailWrap.remove();
      });
    }
  }, { once: true });
  modal.show();
  } catch (err) {
    console.error('[openCreateModal] Lá»–I EXCEPTION:', err);
  }
}

/** Má»Ÿ modal táº¡o lá»‹ch tá»« pending blocks Ä‘Ã£ chá»n trÃªn grid */
function openCreateModalFromPending() {
  if (!pendingBlocks.length) return;

  if (_addingSlotMode && _savedBookerInfo) {
    _addingSlotMode = false;

    if (_addingSlotEditBookingCode && _savedBookerInfo._existingGuests) {
      // â”€â”€ EDIT MODE: restore edit modal + append slot má»›i â”€â”€
      const booker = _savedBookerInfo;
      const existingGuests = booker._existingGuests || [];
      const bookingCode    = booker._bookingCode;
      const allApptIds     = booker._allApptIds;

      _savedBookerInfo = null;
      _addingSlotEditBookingCode = null;

      // Rebuild edit modal vá»›i guests cÅ© + pending blocks má»›i
      const modalEl    = document.getElementById("apptModal");
      const modalTitle = document.getElementById("modalTitle");
      const apptId     = document.getElementById("apptId");

      resetModalError();
      modalTitle.textContent = `Chá»‰nh sá»­a â€¢ ${bookingCode}`;
      apptId.value = existingGuests[0]?._apptId || '';
      apptId.dataset.bookingCode = bookingCode;
      apptId.dataset.allApptIds  = allApptIds;

      _showSharedForm();
      _setAddGuestBtnVisible(true);
      _applyModalMode('normal');

      const lbl = document.getElementById('bookerPanelLabel');
      if (lbl) lbl.textContent = 'NgÆ°á»i Ä‘áº·t lá»‹ch';

      _guestCount = 0;
      document.getElementById('guestList').innerHTML = '';
      _resetAllCustomerState();

      _fillBookerFields({
        name:   booker.name,
        phone:  booker.phone,
        email:  booker.email,
        source: booker.source || 'DIRECT',
        note:   booker.note,
      });
      const bookingDateEl = document.getElementById('bookingDate');
      if (bookingDateEl) bookingDateEl.value = booker.bookingDate || '';

      // Restore cÃ¡c guest cÅ©
      existingGuests.forEach(g => addGuestCard(g));

      // Append guest má»›i tá»« pending blocks
      pendingBlocks.forEach(pb => {
        addGuestCard({
          date:   pb.day,
          time:   pb.time,
          roomId: pb.roomId,
          pendingDuration: pb.duration,
          _editMode: false,  // guest má»›i â€” chÆ°a cÃ³ apptId
        });
      });

      _initApplyAllBar();
      _updateGuestProgress();

      const btnSaveText = document.getElementById("btnSaveText");
      if (btnSaveText) btnSaveText.textContent = "LÆ°u lá»‹ch háº¹n";

      // Hiá»‡n status block (dÃ¹ng status cá»§a guest Ä‘áº§u tiÃªn)
      _showSharedStatusBlock(
        existingGuests[0]?.apptStatus || 'NOT_ARRIVED',
        'UNPAID',
        true
      );

      clearPendingBlocks();

      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.show();

    } else {
      // â”€â”€ CREATE MODE: quay láº¡i modal sau khi user chá»n thÃªm slot â”€â”€
      openCreateModal({ _fromPending: true, _blocks: [...pendingBlocks], _restoreBooker: _savedBookerInfo });
      _savedBookerInfo = null;
    }
  } else {
    openCreateModal({ _fromPending: true, _blocks: [...pendingBlocks] });
  }
}

async function openEditModal(id){
  try {
  const modalError = document.getElementById("modalError");
  resetModalError();

  // BÆ°á»›c 1: fetch appointment Ä‘Æ¡n Ä‘á»ƒ láº¥y bookingCode
  const result = await apiGet(`${API_BASE}/appointments/${id}/`);
  if (!result.success || !result.appointment) {
    // Fallback: tÃ¬m trong APPOINTMENTS cache
    const cached = APPOINTMENTS.find(x => x.id === id);
    if (cached) {
      await _openEditModalByBooking(cached.bookingCode, id);
    } else {
      _showModalError("KhÃ´ng tÃ¬m tháº¥y lá»‹ch háº¹n");
    }
    return;
  }

  const bookingCode = result.appointment.bookingCode;
  await _openEditModalByBooking(bookingCode, id);
  } catch(err) {
    console.error('[openEditModal] threw:', err);
  }
}

/**
 * Fetch toÃ n bá»™ appointments trong booking rá»“i má»Ÿ modal edit.
 * @param {string} bookingCode - mÃ£ booking
 * @param {string} clickedApptId - appointment_code Ä‘Æ°á»£c click (Ä‘á»ƒ set apptId)
 */
async function _openEditModalByBooking(bookingCode, clickedApptId) {
  const modalError = document.getElementById("modalError");

  if (!bookingCode) {
    // KhÃ´ng cÃ³ bookingCode â†’ fallback edit Ä‘Æ¡n láº»
    const result = await apiGet(`${API_BASE}/appointments/${clickedApptId}/`);
    if (result.success && result.appointment) openEditModalWithData([result.appointment], clickedApptId);
    else { _showModalError("KhÃ´ng tÃ¬m tháº¥y lá»‹ch háº¹n"); }
    return;
  }

  const bkResult = await apiGet(`${API_BASE}/bookings/${bookingCode}/`);
  if (bkResult.success && bkResult.appointments && bkResult.appointments.length > 0) {
    openEditModalWithData(bkResult.appointments, clickedApptId);
  } else {
    // Fallback: chá»‰ load appointment Ä‘Æ°á»£c click
    const result = await apiGet(`${API_BASE}/appointments/${clickedApptId}/`);
    if (result.success && result.appointment) openEditModalWithData([result.appointment], clickedApptId);
    else { _showModalError("KhÃ´ng tÃ¬m tháº¥y lá»‹ch háº¹n"); }
  }
}

/**
 * Má»Ÿ modal chá»‰nh sá»­a vá»›i danh sÃ¡ch appointments thuá»™c cÃ¹ng 1 booking.
 * @param {Array} appointments - máº£ng appointment objects (tá»« API)
 * @param {string} clickedApptId - appointment_code Ä‘Æ°á»£c click (dÃ¹ng Ä‘á»ƒ set apptId chÃ­nh)
 */
function openEditModalWithData(appointments, clickedApptId) {
  try {
  // Láº¥y appointment Ä‘áº§u tiÃªn lÃ m "primary" Ä‘á»ƒ láº¥y booker info
  const primary = appointments.find(a => a.id === clickedApptId) || appointments[0];
  if (!primary) return;

  const modalEl    = document.getElementById("apptModal");
  const modalTitle = document.getElementById("modalTitle");
  const apptId     = document.getElementById("apptId");
  const btnDelete  = document.getElementById("btnDelete");

  resetModalError();

  // Title hiá»ƒn thá»‹ booking code náº¿u cÃ³ nhiá»u khÃ¡ch
  if (appointments.length > 1) {
    modalTitle.textContent = `Chá»‰nh sá»­a â€¢ ${primary.bookingCode || primary.id} (${appointments.length} khÃ¡ch)`;
  } else {
    modalTitle.textContent = `Chá»‰nh sá»­a â€¢ ${primary.id}`;
  }

  // apptId lÆ°u appointment_code Ä‘Æ°á»£c click (dÃ¹ng khi submit 1 appt)
  // Vá»›i multi-appt, lÆ°u thÃªm bookingCode Ä‘á»ƒ submit handler biáº¿t
  apptId.value = primary.id;
  apptId.dataset.bookingCode  = primary.bookingCode || '';
  apptId.dataset.allApptIds   = JSON.stringify(appointments.map(a => a.id));
  // LÆ°u date/time/duration Ä‘á»ƒ validate timing khi submit
  apptId.dataset.apptDate     = primary.date  || '';
  apptId.dataset.apptTime     = primary.start || '';
  apptId.dataset.apptDuration = primary.durationMin || '60';

  // NÃºt Rebook / XÃ³a â€” dá»±a trÃªn primary
  const btnRebook = document.getElementById('btnRebook');
  const st   = (primary.apptStatus  || '').toUpperCase();
  const bkSt = (primary.bookingStatus || '').toUpperCase();

  if (st === 'COMPLETED') {
    btnDelete.classList.add("d-none");
  } else {
    btnDelete.classList.remove("d-none");
  }
  if (btnRebook) {
    if (st === 'CANCELLED' || bkSt === 'CANCELLED' || bkSt === 'REJECTED') {
      btnRebook.classList.remove('d-none');
    } else {
      btnRebook.classList.add('d-none');
    }
  }

  const btnSaveText = document.getElementById("btnSaveText");
  if (btnSaveText) btnSaveText.textContent = "LÆ°u lá»‹ch háº¹n";

  _showSharedForm();
  _setAddGuestBtnVisible(true);  // edit mode Ä‘Æ°á»£c thÃªm khÃ¡ch má»›i

  // Tráº¡ng thÃ¡i & thanh toÃ¡n dÃ¹ng cá»§a primary (hoáº·c appointment Ä‘Æ°á»£c click)
  // LuÃ´n apply normal-mode trÆ°á»›c Ä‘á»ƒ reset má»i tráº¡ng thÃ¡i áº©n tá»« request-mode
  _applyModalMode('normal');
  _showSharedStatusBlock(primary.apptStatus || 'NOT_ARRIVED', primary.payStatus || 'UNPAID', true);

  const lbl = document.getElementById('bookerPanelLabel');
  if (lbl) lbl.textContent = 'NgÆ°á»i Ä‘áº·t lá»‹ch';

  // Reset guest list
  _guestCount = 0;
  document.getElementById('guestList').innerHTML = '';
  _resetAllCustomerState();
  document.getElementById('selectedCustomerId').value = primary.customerId || '';

  // Äiá»n booker panel tá»« primary (booker info chung cho cáº£ booking)
  _fillBookerFields({
    name:   primary.bookerName  || '',
    phone:  primary.bookerPhone || '',
    email:  primary.bookerEmail || '',
    source: primary.source      || 'DIRECT',
    note:   primary.bookerNotes || '',
  });
  // Set ngÃ y háº¹n chung â€” láº¥y tá»« appointment Ä‘áº§u tiÃªn
  const bookingDateEl = document.getElementById('bookingDate');
  if (bookingDateEl) bookingDateEl.value = primary.date || appointments[0]?.date || '';

  // ThÃªm 1 guest card cho Má»–I appointment trong booking
  appointments.forEach(a => {
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
      note:         a.bookerNotes || '',
      customerNote: a.customerNote || '',
      customerId:   a.customerId || '',
      _editMode:    true,
      _apptId:      a.id,   // lÆ°u appointment_code vÃ o card Ä‘á»ƒ submit Ä‘Ãºng
    });
  });

  // Populate dropdown "Ãp dá»¥ng táº¥t cáº£" trong edit mode
  _initApplyAllBar();

  let modal = null;
  if (modalEl) {
    const existing = bootstrap.Modal.getInstance(modalEl);
    modal = existing || new bootstrap.Modal(modalEl);
  }
  if (modal) modal.show();

  // Load invoice summary sau khi modal má»Ÿ (Ä‘á»ƒ cáº­p nháº­t paid amount)
  if (primary.bookingCode) {
    _loadInvoiceSummary(primary.bookingCode);
  }
  } catch(err) {
    console.error('[openEditModalWithData] threw:', err);
  }
}

/**
 * Load invoice summary tá»« API vÃ  cáº­p nháº­t payment summary trong edit modal.
 * Disable nÃºt XÃ³a vÃ  Thanh toÃ¡n trong lÃºc load Ä‘á»ƒ trÃ¡nh race condition.
 */
async function _loadInvoiceSummary(bookingCode) {
  if (!bookingCode) return;

  // Disable cÃ¡c nÃºt nháº¡y cáº£m trong lÃºc load
  const btnDelete   = document.getElementById('btnDelete');
  const btnInvoice  = document.getElementById('btnOpenInvoice');
  if (btnDelete)  { btnDelete._invoiceLoading  = true; btnDelete.disabled  = true; }
  if (btnInvoice) { btnInvoice._invoiceLoading = true; btnInvoice.disabled = true; }

  try {
    const result = await apiGet(`${API_BASE}/bookings/${bookingCode}/invoice/`);
    if (result.success && result.invoice) {
      const inv = result.invoice;
      // Cáº­p nháº­t hidden select (dÃ¹ng khi submit) vÃ  badge hiá»ƒn thá»‹
      const payStatusSel = document.getElementById('sharedPayStatus');
      if (payStatusSel && inv.paymentStatus) {
        _setSelectValue(payStatusSel, inv.paymentStatus, 'UNPAID');
      }
      _updatePaymentSummary();
    }
  } catch (e) {
    // KhÃ´ng cÃ³ invoice â†’ giá»¯ nguyÃªn tráº¡ng thÃ¡i máº·c Ä‘á»‹nh
  } finally {
    // Re-enable nÃºt sau khi load xong (chá»‰ náº¿u chÃ­nh hÃ m nÃ y Ä‘Ã£ disable)
    if (btnDelete && btnDelete._invoiceLoading) {
      delete btnDelete._invoiceLoading;
      // Chá»‰ enable láº¡i náº¿u payStatus cho phÃ©p xÃ³a
      const payStatus = document.getElementById('sharedPayStatus')?.value || '';
      btnDelete.disabled = ['PAID', 'PARTIAL', 'REFUNDED'].includes(payStatus);
    }
    if (btnInvoice && btnInvoice._invoiceLoading) {
      // Gá»i láº¡i _updateCreatePayBtn Ä‘á»ƒ set Ä‘Ãºng tráº¡ng thÃ¡i enable/disable theo dá»‹ch vá»¥
      _updateCreatePayBtn();
      delete btnInvoice._invoiceLoading;
    }
  }
}

const btnSave = document.getElementById("btnSave");
btnSave.addEventListener("click", ()=> {
  // Trigger submit trÃªn form
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

  // â”€â”€ Validate booker â€” chung cho cáº£ CREATE vÃ  EDIT â”€â”€
  const nameVal  = document.getElementById('bookerName')?.value.trim() || '';
  const phoneVal = document.getElementById('bookerPhone')?.value.trim() || '';
  const emailVal = document.getElementById('bookerEmail')?.value.trim() || '';
  const bookerCheck = _validateBookerFields(nameVal, phoneVal, emailVal);
  if (!bookerCheck.ok) { _showModalError(bookerCheck.error); return; }

  // â”€â”€ EDIT MODE â€” gá»­i 1 request batch atomic thay vÃ¬ loop â”€â”€
  if (id) {
    const cards = _collectGuestCards();
    if (!cards.length) { _showModalError("Lá»—i: khÃ´ng tÃ¬m tháº¥y dá»¯ liá»‡u"); return; }

    // Validate tá»«ng guest card (FE-side, trÆ°á»›c khi gá»­i)
    for (let i = 0; i < cards.length; i++) {
      const g = cards[i];
      const label = cards.length > 1 ? `KhÃ¡ch ${i + 1}: ` : '';
      const gItem = _getGuestItems()[i];
      // Validate date / time / room
      const dtrCheck = _validateGuestDateTimeRoom(g, i, cards.length);
      if (!dtrCheck.ok) {
        if (gItem && (dtrCheck.type === 'time' || dtrCheck.type === 'room')) _markRowError(gItem);
        _showModalError(dtrCheck.error); return;
      }
      // Kiá»ƒm tra thá»i gian quÃ¡ khá»© â€” chá»‰ cháº·n khi ngÃ y/giá» thá»±c sá»± thay Ä‘á»•i
      if (g.time && (g.date !== g.originalDate || g.time !== g.originalTime) && _isSlotInPast(g.date, g.time)) {
        _showModalError(`${label}KhÃ´ng thá»ƒ táº¡o lá»‹ch háº¹n vÃ o thá»i gian nÃ y (giá» Ä‘Ã£ qua)`); return;
      }
      const basicCheck = _validateGuestBasic(g, i, cards.length);
      if (!basicCheck.ok) { _showModalError(basicCheck.error); return; }
    }
    const editNoteVal = document.getElementById('bookerNote')?.value || '';
    const noteCheck = _validateBookerNote(editNoteVal);
    if (!noteCheck.ok) { _showModalError(noteCheck.error); return; }

    const bookingCode = apptId.dataset.bookingCode || '';
    if (!bookingCode) {
      _showModalError("KhÃ´ng tÃ¬m tháº¥y mÃ£ booking. Vui lÃ²ng Ä‘Ã³ng vÃ  má»Ÿ láº¡i."); return;
    }

    // BUG-007 FIX: Validate COMPLETED + PAID cho tá»«ng guest card riÃªng láº»
    // (khÃ´ng dÃ¹ng sharedApptStatus ná»¯a â€” má»—i khÃ¡ch cÃ³ tráº¡ng thÃ¡i riÃªng)
    const editPayStatus = document.getElementById('sharedPayStatus')?.value || '';
    for (let i = 0; i < cards.length; i++) {
      const g = cards[i];
      const label = cards.length > 1 ? `KhÃ¡ch ${i + 1}: ` : '';
      const completedCheck = _validateCompletedStatus(g.apptStatus, editPayStatus);
      if (!completedCheck.ok) { _showModalError(`${label}${completedCheck.error}`); return; }
    }

    // BUG-007 FIX: Validate thá»i Ä‘iá»ƒm ARRIVED / COMPLETED cho tá»«ng card
    const editTimingCheck = _validateAllCardsTiming(
      cards,
      (g)    => g.apptStatus,
      (g)    => g.date || apptId.dataset.apptDate || '',
      (g)    => g.time || apptId.dataset.apptTime || '',
      (g)    => Number(g._duration || apptId.dataset.apptDuration || 60),
    );
    if (!editTimingCheck.ok) { _showModalError(editTimingCheck.error); return; }

    // XÃ¢y dá»±ng payload batch â€” BUG-02: 1 request duy nháº¥t, atomic
    const batchPayload = {
      bookerName:  nameVal,
      bookerPhone: phoneVal.replace(/\D/g, ''),
      bookerEmail: emailVal,
      bookerNotes: document.getElementById('bookerNote')?.value.trim() || '',
      guests: cards.map(g => {
        const guest = {
          appointmentCode: g._apptId || '',
          customerName:    g.name || '',
          phone:           (g.phone || '').replace(/\D/g, ''),
          email:           g.email || '',
          variantId:       g.variantId || null,
          serviceId:       g.serviceId || null,
          customerId:      g.customerId || null,
          apptStatus:      g.apptStatus || 'NOT_ARRIVED',
        };
        // Chá»‰ gá»­i date/time/roomId khi thá»±c sá»± thay Ä‘á»•i
        // Ngoáº¡i lá»‡: náº¿u variantId thay Ä‘á»•i, luÃ´n gá»­i roomId hiá»‡n táº¡i Ä‘á»ƒ backend
        // validate overlap vá»›i duration má»›i (dÃ¹ room khÃ´ng Ä‘á»•i)
        // Ngoáº¡i lá»‡ 2: guest má»›i (khÃ´ng cÃ³ _apptId) â†’ luÃ´n gá»­i Ä‘á»§ date/time/roomId
        const isNewGuest = !g._apptId;
        const variantChanged = (g.variantId || null) !== (g._originalVariantId || null);
        if (isNewGuest || g.date !== g.originalDate) guest.date = g.date;
        if (isNewGuest || g.time !== g.originalTime) guest.time = g.time;
        if (isNewGuest || g.roomId !== g.originalRoom || variantChanged) guest.roomId = g.roomId;
        return guest;
      }),
    };

    isSubmitting = true;
    setButtonLoading(btnSave, 'Äang cáº­p nháº­t...');

    try {
      // BUG-02: 1 request duy nháº¥t â†’ atomic trÃªn backend
      const result = await apiPost(`${API_BASE}/bookings/${bookingCode}/update-batch/`, batchPayload);

      if (!result.success) {
        _showModalError(_isConflictError(result) ? (result.error || MSG_APPROVE_CONFLICT) : (result.error || MSG_WEB_GENERIC_ERR));
        return;
      }

      // ThÃ nh cÃ´ng â€” cáº­p nháº­t ghi chÃº há»“ sÆ¡ khÃ¡ch
      await _updateCustomerNotes(cards);

      const modalEl = document.getElementById("apptModal");
      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.hide();
      const firstDate = cards[0]?.date;
      if (firstDate && dayPicker.value !== firstDate) dayPicker.value = firstDate;
      await _refreshAll();
      showToast("success", "ThÃ nh cÃ´ng", "Cáº­p nháº­t lá»‹ch háº¹n thÃ nh cÃ´ng");

    } catch(err) {
      _showModalError(MSG_WEB_GENERIC_ERR);
    } finally {
      isSubmitting = false;
      resetButton(btnSave);
    }
    return;
  }

  // â”€â”€ CREATE MODE (batch) â”€â”€
  const bookerName  = nameVal;
  const bookerPhone = phoneVal;
  const bookerEmail = emailVal;

  const guestCards = _collectGuestCards();
  if (!guestCards.length) {
    _showModalError("Vui lÃ²ng thÃªm Ã­t nháº¥t 1 khÃ¡ch");
    return;
  }

  // UC 14.3 â€” khi xÃ¡c nháº­n request online, báº¯t buá»™c pháº£i chá»n phÃ²ng
  if (window._pendingOnlineRequestCode) {
    const missingRoom = guestCards.some(g => !g.roomId);
    if (missingRoom) {
      _showModalError('Vui lÃ²ng chá»n phÃ²ng trÆ°á»›c khi xÃ¡c nháº­n yÃªu cáº§u Ä‘áº·t lá»‹ch');
      return;
    }
  }

  // Validate thanh toÃ¡n Ä‘Ã£ bá»‹ bá» khá»i create mode â€” thanh toÃ¡n qua invoice modal sau khi táº¡o lá»‹ch

  // Validate ghi chÃº lá»‹ch háº¹n (max 1000 kÃ½ tá»± theo DB)
  const bookerNoteVal = document.getElementById('bookerNote')?.value || '';
  const noteCheck = _validateBookerNote(bookerNoteVal);
  if (!noteCheck.ok) { _showModalError(noteCheck.error); return; }

  // Láº¥y ngÃ y hÃ´m nay Ä‘á»ƒ check quÃ¡ khá»©
  const _todayStr = (() => { const t = new Date(); return `${t.getFullYear()}-${pad2(t.getMonth()+1)}-${pad2(t.getDate())}`; })();

  for (let i = 0; i < guestCards.length; i++) {
    const g = guestCards[i];
    const label = `KhÃ¡ch ${i + 1}`;
    const gItem = _getGuestItems()[i];

    // Validate date / time / room
    const dtrCheck = _validateGuestDateTimeRoom(g, i, guestCards.length);
    if (!dtrCheck.ok) {
      if (gItem && (dtrCheck.type === 'time' || dtrCheck.type === 'room')) _markRowError(gItem);
      _showModalError(dtrCheck.error); return;
    }
    // Validate ngÃ y quÃ¡ khá»© (CREATE mode) â€” bá» qua khi xÃ¡c nháº­n online request
    if (!window._pendingOnlineRequestCode && g.date < _todayStr) {
      const prefix = guestCards.length > 1 ? `${label}: ` : '';
      _showModalError(`${prefix}NgÃ y háº¹n khÃ´ng Ä‘Æ°á»£c nhá» hÆ¡n ngÃ y hÃ´m nay`); return;
    }
    // Kiá»ƒm tra thá»i gian quÃ¡ khá»© â€” bá» qua khi xÃ¡c nháº­n online request (staff chá»‰ confirm, khÃ´ng táº¡o má»›i)
    if (!window._pendingOnlineRequestCode && _isSlotInPast(g.date, g.time)) {
      const prefix = guestCards.length > 1 ? `${label}: ` : '';
      _showModalError(`${prefix}KhÃ´ng thá»ƒ táº¡o lá»‹ch háº¹n vÃ o thá»i gian nÃ y (giá» Ä‘Ã£ qua)`); return;
    }
    const basicCheck = _validateGuestBasic(g, i, guestCards.length);
    if (!basicCheck.ok) {
      if (gItem) _markRowError(gItem);
      _showModalError(basicCheck.error); return;
    }
  }

  // V-11: Check cross-guest conflict â€” 2 khÃ¡ch cÃ¹ng phÃ²ng cÃ¹ng giá» overlap
  if (guestCards.length > 1) {
    for (let i = 0; i < guestCards.length; i++) {
      for (let j = i + 1; j < guestCards.length; j++) {
        const a = guestCards[i], b = guestCards[j];
        if (!a.roomId || !b.roomId || a.roomId !== b.roomId) continue;
        if (!a.time || !b.time) continue;
        // TÃ­nh duration tá»« variant (fallback 60)
        const durA = Number(a._duration) || 60;
        const durB = Number(b._duration) || 60;
        const aStart = minutesFromStart(a.time);
        const aEnd   = aStart + durA;
        const bStart = minutesFromStart(b.time);
        const bEnd   = bStart + durB;
        if (overlaps(aStart, aEnd, bStart, bEnd)) {
          _showModalError(`KhÃ¡ch ${i+1} vÃ  KhÃ¡ch ${j+1} trÃ¹ng phÃ²ng vÃ  thá»i gian. Vui lÃ²ng chá»n phÃ²ng hoáº·c giá» khÃ¡c.`); return;
        }
      }
    }
  }

  // Validate tráº¡ng thÃ¡i "HoÃ n thÃ nh"
  const createApptStatus = document.getElementById('sharedApptStatus')?.value || '';
  if (createApptStatus === 'COMPLETED') {
    const hasService = guestCards.some(g => g.serviceId);
    if (!hasService) {
      _showModalError("KhÃ´ng thá»ƒ hoÃ n thÃ nh lá»‹ch háº¹n khi chÆ°a cÃ³ dá»‹ch vá»¥"); return;
    }
    // BUG-001: COMPLETED pháº£i Ä‘i kÃ¨m PAID â€” kiá»ƒm tra _createModePayment trÆ°á»›c khi submit
    const completedCheck = _validateCompletedStatus('COMPLETED', _createModePayment.payStatus);
    if (!completedCheck.ok) {
      _showModalError(completedCheck.error + '. Vui lÃ²ng thanh toÃ¡n trÆ°á»›c.'); return;
    }
  }

  // Validate thá»i Ä‘iá»ƒm chuyá»ƒn tráº¡ng thÃ¡i ARRIVED / COMPLETED (create mode)
  // Loop táº¥t cáº£ guestCards â€” má»—i khÃ¡ch cÃ³ thá»ƒ khÃ¡c giá»/duration
  if (createApptStatus === 'ARRIVED' || createApptStatus === 'COMPLETED') {
    const createTimingCheck = _validateAllCardsTiming(
      guestCards,
      ()     => createApptStatus,
      (g)    => g.date,
      (g)    => g.time,
      (g)    => Number(g._duration) || 60,
    );
    if (!createTimingCheck.ok) { _showModalError(createTimingCheck.error); return; }
  }

  // UC 14.3 â€” TÃ¡ch luá»“ng: xÃ¡c nháº­n request online vs táº¡o lá»‹ch thÆ°á»ng
  const _onlineRequestCode = window._pendingOnlineRequestCode || '';

  if (_onlineRequestCode) {
    // â”€â”€ LUá»’NG XÃC NHáº¬N REQUEST ONLINE â”€â”€
    // Gá»i endpoint riÃªng: update appointment gá»‘c + confirm booking gá»‘c (khÃ´ng táº¡o booking má»›i)
    const confirmPayload = {
      guests: guestCards.map(g => ({
        name:      g.name,
        phone:     g.phone,
        email:     g.email,
        serviceId: g.serviceId || null,
        variantId: g.variantId || null,
        roomId:    g.roomId,
        date:      g.date,
        time:      g.time,
        customerId: g.customerId || null,
      })),
    };

    isSubmitting = true;
    setButtonLoading(btnSave, 'Äang xÃ¡c nháº­n...');
    try {
      const result = await apiPost(`${API_BASE}/booking-requests/${_onlineRequestCode}/confirm/`, confirmPayload);
      if (result.success) {
        await _updateCustomerNotes(guestCards);
        const modalEl = document.getElementById("apptModal");
        const existing = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
        const modal = existing || (modalEl ? new bootstrap.Modal(modalEl) : null);
        if (modal) modal.hide();
        _addingSlotMode = false;
        _savedBookerInfo = null;
        _addingSlotEditBookingCode = null;
        window._pendingOnlineRequestCode = '';
        _isRebookMode = false;
        const firstDate = guestCards[0]?.date;
        if (firstDate && dayPicker.value !== firstDate) dayPicker.value = firstDate;
        clearPendingBlocks();
        await _refreshAll();
        showToast('success', 'ThÃ nh cÃ´ng', MSG_APPROVE_SUCCESS);
      } else {
        _showModalError(_isConflictError(result, true) ? (result.error || MSG_WEB_CONFLICT) : (result.error || MSG_WEB_GENERIC_ERR));
      }
    } catch (err) {
      _showModalError(MSG_WEB_GENERIC_ERR);
    } finally {
      isSubmitting = false;
      resetButton(btnSave);
    }
    return;
  }

  // â”€â”€ LUá»’NG Táº O Lá»ŠCH THÆ¯á»œNG â”€â”€
  const batchPayload = {
    booker: {
      name:          bookerName,
      phone:         bookerPhone.replace(/\D/g, ''),
      email:         bookerEmail,
      source:        document.getElementById('bookerSource')?.value || 'DIRECT',
      notes:         document.getElementById('bookerNote')?.value.trim() || '',
      payStatus:     _createModePayment.payStatus     || 'UNPAID',
      paymentMethod: _createModePayment.paymentMethod || '',
      paymentAmount: _createModePayment.paymentAmount || 0,
      // BUG-001 FIX: Gá»­i discount Ä‘á»ƒ backend Ã¡p dá»¥ng khi táº¡o invoice
      discountType:  _createModePayment.discountType  || 'NONE',
      discountValue: _createModePayment.discountValue || 0,
      fromAdmin:     true,  // Admin táº¡o/rebook â†’ backend set CONFIRMED, khÃ´ng cáº§n xÃ¡c nháº­n
    },
    guests: guestCards,
  };

  isSubmitting = true;
  setButtonLoading(btnSave, 'Äang táº¡o lá»‹ch...');
  try {
    const result = await apiPost(`${API_BASE}/appointments/create-batch/`, batchPayload);
    if (result.success) {
      // Cáº­p nháº­t ghi chÃº há»“ sÆ¡ khÃ¡ch (await Ä‘á»ƒ xá»­ lÃ½ confirm xÃ³a note)
      await _updateCustomerNotes(guestCards);

      const modalEl = document.getElementById("apptModal");
      let modal = null;
      if (modalEl) {
        const existing = bootstrap.Modal.getInstance(modalEl);
        modal = existing || new bootstrap.Modal(modalEl);
      }
      if (modal) modal.hide();      _addingSlotMode = false;
      _savedBookerInfo = null;
      _addingSlotEditBookingCode = null;
      const firstDate = guestCards[0]?.date;
      if (firstDate && dayPicker.value !== firstDate) dayPicker.value = firstDate;
      clearPendingBlocks();
      await _refreshAll();
      const successMsg = _isRebookMode ? MSG_REBOOK_SUCCESS : (result.message || 'Táº¡o lá»‹ch háº¹n thÃ nh cÃ´ng');
      _isRebookMode = false;
      showToast("success", "ThÃ nh cÃ´ng", successMsg);
      if (result.errors?.length) {
        setTimeout(() => showToast("warning", "Má»™t sá»‘ lá»—i", result.errors.join(' | ')), 1500);
      }
    } else {
      _showModalError(_isConflictError(result) ? (result.error || MSG_WEB_CONFLICT) : (result.error || MSG_WEB_GENERIC_ERR));
    }
    } catch(err) {
      _showModalError(MSG_WEB_GENERIC_ERR);
  } finally {
    isSubmitting = false;
    resetButton(btnSave);
  }
});

// ===== NÃšT Äáº¶T Láº I trong modal =====
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

  // Kiá»ƒm tra hÃ³a Ä‘Æ¡n Ä‘Ã£ thanh toÃ¡n hoáº·c Ä‘Ã£ hoÃ n tiá»n â€” khÃ´ng cho phÃ©p xÃ³a
  const payStatus = document.getElementById('sharedPayStatus')?.value || '';
  if (payStatus === 'PAID' || payStatus === 'PARTIAL' || payStatus === 'REFUNDED') {
    const payMsg = payStatus === 'PARTIAL'
      ? 'Lá»‹ch háº¹n Ä‘ang cÃ³ thanh toÃ¡n má»™t pháº§n, khÃ´ng thá»ƒ xÃ³a.'
      : 'Lá»‹ch háº¹n Ä‘Ã£ thanh toÃ¡n, khÃ´ng thá»ƒ xÃ³a.';
    showToast('error', 'KhÃ´ng thá»ƒ xÃ³a', payMsg);
    return;
  }

  // Äá»c info tá»« guest card duy nháº¥t (edit mode)
  const firstCard = _getGuestItems()[0];
  const customerNameVal = firstCard?.querySelector('.gc-name')?.value.trim()
    || document.getElementById('bookerName')?.value.trim() || '';
  const timeVal = firstCard?.dataset.slotTime || '';

  const infoEl = document.getElementById('deleteAppointmentInfo');
  if (infoEl) {
    const parts = [];
    if (customerNameVal) parts.push(customerNameVal);
    if (timeVal) parts.push(timeVal);
    infoEl.textContent = parts.join(' Â· ');
    infoEl.style.display = parts.length ? '' : 'none';
  }

  // DÃ¹ng instance Ä‘Ã£ khá»Ÿi táº¡o sáºµn â€” trÃ¡nh lá»—i Bootstrap táº¡o nhiá»u instance
  const deleteModal = window.deleteAppointmentModal
    || new bootstrap.Modal(document.getElementById('deleteAppointmentModal'));

  const confirmDeleteBtn = document.getElementById('confirmDeleteAppointmentBtn');
  if (confirmDeleteBtn) {
    // XÃ³a listener cÅ© báº±ng cÃ¡ch clone node Ä‘á»ƒ trÃ¡nh duplicate
    const newBtn = _replaceWithClone(confirmDeleteBtn);

    newBtn.addEventListener('click', async () => {
      deleteModal.hide();

      isSubmitting = true;
      setButtonLoading(btnDelete, 'Äang xÃ³a...');

      try {
        const result = await apiPost(`${API_BASE}/appointments/${id}/delete/`, {});
        if (result.success) {
          const modalEl = document.getElementById("apptModal");
          if (modalEl) {
            const existing = bootstrap.Modal.getInstance(modalEl);
            if (existing) existing.hide();
          }
          await _refreshAll();
          showToast("success", "ThÃ nh cÃ´ng", result.message || "ÄÃ£ xÃ³a lá»‹ch háº¹n");
        } else {
          showToast("error", "Lá»—i", result.error || "KhÃ´ng thá»ƒ xÃ³a lá»‹ch háº¹n");
        }
      } catch (err) {
        console.error('Delete error:', err);
        showToast("error", "Lá»—i", "XÃ³a tháº¥t báº¡i, vui lÃ²ng thá»­ láº¡i sau.");
      } finally {
        isSubmitting = false;
        resetButton(btnDelete);
      }
    });
  }

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
    // Network lá»—i hoÃ n toÃ n (offline, DNS fail...) â€” UC 14.2 exception flow 5a
    console.error('refreshData error:', err);
    APPOINTMENTS = [];
    _gridLoadError = true;
    showToast('error', 'Lá»—i', MSG_LOAD_APPT_ERROR);
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

  // NÃºt má»Ÿ modal
  const btnOpen = document.getElementById('btnOpenSearch');
  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      _fillSearchDropdowns();
      searchModal.show();
    });
  }

  // NÃºt TÃ¬m kiáº¿m
  const btnDo = document.getElementById('btnDoSearch');
  if (btnDo) btnDo.addEventListener('click', () => _doSearch());

  // NÃºt Äáº·t láº¡i
  const btnReset = document.getElementById('btnResetSearch');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      _resetSearchModalState(searchModalEl);
      refreshData();        // Refresh grid lá»‹ch theo phÃ²ng vá» toÃ n bá»™ danh sÃ¡ch
      renderWebRequests();  // Refresh tab YÃªu cáº§u Ä‘áº·t lá»‹ch
    });
  }

  // Enter trong cÃ¡c input â†’ trigger search
  ['srchName','srchPhone','srchEmail','srchCode','srchDateFrom','srchDateTo'].forEach(id => {
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
        Nháº­p Ä‘iá»u kiá»‡n vÃ  báº¥m TÃ¬m kiáº¿m
      </div>`;
  }
}

function _fillSearchDropdowns() {
  // Äiá»n dropdown dá»‹ch vá»¥
  const srchSvc = document.getElementById('srchService');
  if (srchSvc && srchSvc.options.length <= 1 && SERVICES.length) {
    _populateSelect(srchSvc, SERVICES, 'id', 'name', 'Táº¥t cáº£ dá»‹ch vá»¥');
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
  const dateFrom  = (document.getElementById('srchDateFrom') || {}).value || '';
  const dateTo    = (document.getElementById('srchDateTo')   || {}).value || '';

  const hasCondition = name || phone || email || code || service || status || source || dateFrom || dateTo;
  if (!hasCondition) {
    _setSearchWarning(true, 'Vui lÃ²ng nháº­p Ä‘iá»u kiá»‡n tÃ¬m kiáº¿m');
    return;
  }

  if (dateFrom && dateTo && dateFrom > dateTo) {
    _setSearchWarning(true, 'Khoáº£ng ngÃ y tÃ¬m kiáº¿m khÃ´ng há»£p lá»‡.');
    return;
  }

  _setSearchWarning(false);

  const resultsEl = document.getElementById('srchResults');
  if (resultsEl) {
    resultsEl.innerHTML = `<div class="text-center text-muted py-5"><i class="fas fa-spinner fa-spin fa-2x mb-2 d-block"></i>Äang tÃ¬m kiáº¿m...</div>`;
  }

  const params = new URLSearchParams();
  if (name)     params.append('name', name);
  if (phone)    params.append('phone', phone);
  if (email)    params.append('email', email);
  if (code)     params.append('code', code);
  if (service)  params.append('service', service);
  if (status)   params.append('status', status);
  if (source)   params.append('source', source);
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo)   params.append('date_to', dateTo);

  const searchModalEl = document.getElementById('searchModal');
  if (searchModalEl) searchModalEl.dataset.currentFilters = params.toString();

  const result = await apiGet(`${API_BASE}/appointments/search/?${params.toString()}`);

  if (!result.success) {
    if (resultsEl) resultsEl.innerHTML = `<div class="alert alert-danger m-3"><i class="fas fa-exclamation-circle me-2"></i>KhÃ´ng thá»ƒ tÃ¬m kiáº¿m lá»‹ch háº¹n. Vui lÃ²ng thá»­ láº¡i sau.</div>`;
    return;
  }

  const appts = result.appointments || [];
  if (!appts.length) {
    if (resultsEl) resultsEl.innerHTML = `<div class="text-center text-muted py-5"><i class="fas fa-inbox fa-2x mb-2 d-block opacity-25"></i>KhÃ´ng tÃ¬m tháº¥y lá»‹ch háº¹n phÃ¹ há»£p.</div>`;
    return;
  }

  const rows = appts.map(a => {
    // REJECTED lÃ  booking-level â€” náº¿u booking bá»‹ tá»« chá»‘i thÃ¬ badge luÃ´n hiá»‡n "ÄÃ£ tá»« chá»‘i"
    // báº¥t ká»ƒ appointment.status lÃ  gÃ¬ (CANCELLED / NOT_ARRIVED do cascade).
    // CÃ¡c status cÃ²n láº¡i dÃ¹ng apptStatus lÃ  nguá»“n sá»± tháº­t chÃ­nh.
    const displayStatus = (a.bookingStatus || '').toUpperCase() === 'REJECTED'
      ? 'REJECTED'
      : a.apptStatus;
    const statusBadge = `<span class="badge ${_srchStatusBadgeClass(displayStatus)}">${statusLabel(displayStatus)}</span>`;
    const svcDisplay = a.serviceCode
      ? `<span class="fw-semibold">${_esc(a.serviceCode)}</span>${a.service ? ` <span class="text-muted small">â€” ${_esc(a.service)}</span>` : ''}`
      : (a.service ? _esc(a.service) : '<span class="text-muted fst-italic">ChÆ°a chá»n DV</span>');
    return `
      <div class="srch-result-item d-flex align-items-center gap-3 px-3 py-2 border-bottom"
           style="cursor:pointer;transition:background .15s;"
           onmouseenter="this.style.background='#f0f7ff'" onmouseleave="this.style.background=''"
           onclick="window._srchGoToAppt('${_esc(a.id)}', '${_esc(a.date)}')">
        <div style="min-width:80px;">
          <div class="fw-semibold small">${_esc(a.date)}</div>
          <div class="text-muted small">${_esc(a.start)}${a.end ? 'â€“'+_esc(a.end) : ''}</div>
        </div>
        <div style="min-width:70px;" class="text-muted small">
          <i class="fas fa-door-open me-1"></i>${_esc(a.roomName || a.roomCode || 'â€”')}
        </div>
        <div style="flex:1;min-width:0;">
          <div class="fw-semibold text-truncate">${_esc(a.customerName || a.bookerName || 'â€”')}</div>
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
        <span class="small text-muted"><i class="fas fa-list me-1"></i>TÃ¬m tháº¥y <strong>${appts.length}</strong> káº¿t quáº£${appts.length === 100 ? ' (hiá»ƒn thá»‹ tá»‘i Ä‘a 100)' : ''}</span>
        <span class="small text-muted">Click vÃ o káº¿t quáº£ Ä‘á»ƒ xem trÃªn lá»‹ch</span>
      </div>
      ${rows}`;
  }
}

function _srchStatusBadgeClass(s) {
  const sl = (s || '').toLowerCase();
  if (sl === 'pending')   return 'bg-warning text-dark';
  if (sl === 'confirmed') return 'bg-info text-dark';
  if (sl === 'not_arrived') return 'bg-secondary';
  if (sl === 'arrived')   return 'bg-info text-dark';
  if (sl === 'completed') return 'bg-success';
  if (sl === 'cancelled') return 'bg-secondary';
  if (sl === 'rejected')  return 'bg-danger';
  return 'bg-secondary';
}

window._srchGoToAppt = async function(apptId, apptDate) {
  // ÄÃ³ng modal tÃ¬m kiáº¿m
  const searchModalEl = document.getElementById('searchModal');
  if (searchModalEl) {
    const searchModal = bootstrap.Modal.getInstance(searchModalEl);
    if (searchModal) searchModal.hide();
  }

  // Chuyá»ƒn grid sang Ä‘Ãºng ngÃ y
  if (apptDate && dayPicker) {
    dayPicker.value = apptDate;
    await refreshData();
  }

  // Highlight block trÃªn grid
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
  // LÆ°u cÃ¡c mÃ£ lá»‹ch Ä‘Ã£ toast Ä‘á»ƒ khÃ´ng hiá»‡n láº¡i
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
        <div style="font-size:13px;font-weight:700;color:#111827;margin-bottom:2px;">KhÃ¡ch vá»«a há»§y lá»‹ch</div>
        <div style="font-size:12px;color:#6b7280;">
          <span style="font-weight:600;color:#374151;">${customerName}</span>
          Ä‘Ã£ há»§y lá»‹ch <span style="font-weight:600;color:#ef4444;">${code}</span>
        </div>
      </div>
      <button onclick="document.getElementById('${id}').remove()"
              style="flex-shrink:0;background:none;border:none;cursor:pointer;color:#9ca3af;font-size:16px;line-height:1;padding:0;">Ã—</button>
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

  // Cháº¡y láº§n Ä‘áº§u sau 5s (trÃ¡nh spam khi má»›i load), sau Ä‘Ã³ má»—i 30s
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

  // Initialize customer search (stub â€” badges Ä‘Ã£ bá»)
  initCustomerSearch();

  // Initialize delete modal
  const deleteModalEl = document.getElementById('deleteAppointmentModal');
  if (deleteModalEl) {
    window.deleteAppointmentModal = new bootstrap.Modal(deleteModalEl);
  }

  if(sidebarToggle) sidebarToggle.addEventListener("click", ()=> sidebar.classList.toggle("show"));

  // â”€â”€ Render header timeline NGAY Láº¬P Tá»¨C trÆ°á»›c khi fetch â”€â”€
  // Äá»ƒ layout á»•n Ä‘á»‹nh, khÃ´ng bá»‹ trá»‘ng trong lÃºc chá» API
  dayPicker.value = todayISO();
  renderHeader();
  showGridLoading();   // hiá»‡n skeleton trong vÃ¹ng grid

  // â”€â”€ Fetch song song rooms + services Ä‘á»ƒ giáº£m thá»i gian chá» â”€â”€
  await Promise.all([loadRooms(), loadServices()]);

  fillServiceFilter();

  // â”€â”€ Fetch appointments + web requests song song â”€â”€
  await Promise.all([
    refreshData(),
    renderWebRequests(),
  ]);

  // ===== POLLING: cáº­p nháº­t badge pending count má»—i 15 giÃ¢y =====
  // Track count láº§n trÆ°á»›c Ä‘á»ƒ phÃ¡t hiá»‡n thay Ä‘á»•i
  let _lastPendingCount = -1;
  // Store interval reference Ä‘á»ƒ cleanup khi rá»i trang
  const _pendingCountInterval = setInterval(async () => {
    try {
      const res = await apiGet(`${API_BASE}/booking/pending-count/`);
      if (res.success && typeof res.count === 'number') {
        // Cáº­p nháº­t badge
        _setWebCountBadge(res.count);

        // Náº¿u count thay Ä‘á»•i so vá»›i láº§n trÆ°á»›c â†’ reload danh sÃ¡ch yÃªu cáº§u
        // (khÃ´ng reset filter, chá»‰ gá»i láº¡i renderWebRequests vá»›i filter hiá»‡n táº¡i)
        if (_lastPendingCount !== -1 && res.count !== _lastPendingCount) {
          renderWebRequests();
        }
        _lastPendingCount = res.count;
      }
    } catch(e) { /* silent */ }
  }, 15000);

  // Cleanup khi rá»i trang Ä‘á»ƒ trÃ¡nh memory leak
  window.addEventListener('beforeunload', () => {
    clearInterval(_pendingCountInterval);
    clearInterval(_ctlInterval);
  });

  if(btnToday) btnToday.addEventListener("click", ()=> setDay(todayISO()));
  if(btnPrev) btnPrev.addEventListener("click", ()=> shiftDay(-1));
  if(btnNext) btnNext.addEventListener("click", ()=> shiftDay(1));
  if(dayPicker) dayPicker.addEventListener("change", ()=> { clearPendingBlocks(); refreshData(); updateCurrentTimeLine(); });

  // â”€â”€ Current time line: interval realtime + resize â”€â”€
  startCurrentTimeLineInterval();
  window.addEventListener('resize', updateCurrentTimeLine);

  // ===== ACTION BAR â€” Pending blocks =====
  const btnCancelPending   = document.getElementById('btnCancelPending');
  const btnContinuePending = document.getElementById('btnContinuePending');

  if (btnCancelPending) {
    btnCancelPending.addEventListener('click', () => {
      _addingSlotMode = false;
      _savedBookerInfo = null;
      _addingSlotEditBookingCode = null;
      clearPendingBlocks();
      showToast('info', 'ÄÃ£ há»§y', 'ÄÃ£ xÃ³a toÃ n bá»™ slot Ä‘ang chá»n');
    });
  }

  if (btnContinuePending) {
    btnContinuePending.addEventListener('click', () => {
      if (!pendingBlocks.length) return;
      try {
        openCreateModalFromPending();
      } catch(err) {
        console.error('[btnContinuePending] openCreateModalFromPending threw:', err);
      }
    });
  }

  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', () => {
      if (!isSubmitting && !_addingSlotMode) {
        clearPendingBlocks();
      }
      // Reset online request state khi modal Ä‘Ã³ng (ká»ƒ cáº£ khi cancel)
      window._pendingOnlineRequestCode = '';
    });
  }

  // Filter bar â€” tab YÃªu cáº§u Ä‘áº·t lá»‹ch (dÃ¹ng FilterManager chung)
  const webFM = new FilterManager({
    fields:   ['webSearchInput', 'webServiceFilter', 'webDateFilter'],
    btnId:    'webFilterBtn',
    searchId: 'webSearchInput',
    onApply:  () => renderWebRequests(),
  });

  // ===== SEARCH MODAL =====
  initSearchModal();

  // ===== INVOICE MODAL =====
  _initInvoiceModal();

  // XÃ³a pending blocks khi chuyá»ƒn tab (trÃ¡nh orphaned blocks khÃ´ng nhÃ¬n tháº¥y)
  // Guard: khÃ´ng xÃ³a khi Ä‘ang trong flow thÃªm khÃ¡ch tá»« edit mode (_addingSlotMode)
  document.querySelectorAll('[data-bs-toggle="pill"]').forEach(tab => {
    tab.addEventListener('shown.bs.tab', () => {
      if (!_addingSlotMode) {
        clearPendingBlocks();
      }
    });
  });
});

// ============================================================
// SECTION 16: INVOICE MODAL
// ============================================================

/** State cá»§a invoice modal */
let _invoiceData = null; // dá»¯ liá»‡u invoice hiá»‡n táº¡i

/**
 * LÆ°u tráº¡ng thÃ¡i thanh toÃ¡n táº¡m thá»i cho create mode.
 * ÄÆ°á»£c set khi user xÃ¡c nháº­n trong _openCreatePayModal(),
 * Ä‘Æ°á»£c Ä‘á»c khi submit batchPayload.
 */
let _createModePayment = {
  payStatus:     'UNPAID',
  paymentMethod: '',
  paymentAmount: 0,
};

/**
 * Cáº­p nháº­t tráº¡ng thÃ¡i enable/disable nÃºt "Thanh toÃ¡n" trong create mode.
 * Chá»‰ enable khi Ã­t nháº¥t 1 khÃ¡ch Ä‘Ã£ chá»n Ä‘á»§ dá»‹ch vá»¥ + gÃ³i.
 * Gá»i má»—i khi variant thay Ä‘á»•i hoáº·c guest card thÃªm/xÃ³a.
 */
function _updateCreatePayBtn() {
  const btnOpen = document.getElementById('btnOpenInvoice');
  if (!btnOpen) return;

  const items = _getGuestItems();
  const hasReadyGuest = items.some(item => {
    const svcVal = item.querySelector('.gc-service')?.value || '';
    const varVal = item.querySelector('.gc-variant')?.value || '';
    return svcVal && varVal;
  });

  btnOpen.disabled = !hasReadyGuest;
  btnOpen.title    = hasReadyGuest
    ? 'Nháº­p thÃ´ng tin thanh toÃ¡n'
    : 'Vui lÃ²ng chá»n dá»‹ch vá»¥ vÃ  gÃ³i dá»‹ch vá»¥ trÆ°á»›c khi thanh toÃ¡n';

  // Hiá»ƒn thá»‹ rÃµ tráº¡ng thÃ¡i disabled/enabled
  if (hasReadyGuest) {
    btnOpen.style.opacity        = '';
    btnOpen.style.filter         = '';
    btnOpen.style.cursor         = '';
    btnOpen.style.pointerEvents  = '';
  } else {
    btnOpen.style.opacity        = '0.5';
    btnOpen.style.filter         = '';
    btnOpen.style.cursor         = 'not-allowed';
    btnOpen.style.pointerEvents  = 'none';
  }
}

/**
 * Má»Ÿ modal thanh toÃ¡n táº¡m cho create mode.
 * TÃ­nh tiá»n tá»« guestCards hiá»‡n táº¡i (dá»±a trÃªn SERVICES data),
 * cho phÃ©p nháº­p phÆ°Æ¡ng thá»©c + sá»‘ tiá»n, lÆ°u vÃ o _createModePayment.
 */
function _openCreatePayModal() {
  // Kiá»ƒm tra láº¡i â€” pháº£i cÃ³ Ã­t nháº¥t 1 khÃ¡ch Ä‘á»§ dá»‹ch vá»¥ + gÃ³i
  const liveData = _buildLinesFromGuestCards();
  if (!liveData || !liveData.lines.length) {
    showToast('warning', 'ChÆ°a Ä‘á»§ thÃ´ng tin', 'Vui lÃ²ng chá»n dá»‹ch vá»¥ vÃ  gÃ³i dá»‹ch vá»¥ trÆ°á»›c khi thanh toÃ¡n.');
    return;
  }

  const { lines, subtotal } = liveData;

  // DÃ¹ng láº¡i invoiceModal vá»›i data táº¡m â€” khÃ´ng cáº§n bookingCode
  _invoiceData = {
    _bookingCode:   '',   // rá»—ng = create mode
    _createMode:    true,
    invoiceCode:    '',
    bookingCode:    '',
    bookerName:     document.getElementById('bookerName')?.value.trim() || '',
    bookerPhone:    document.getElementById('bookerPhone')?.value.trim() || '',
    lines,
    subtotal:       String(subtotal),
    discountType:   'NONE',
    discountValue:  '0',
    discountAmount: '0',
    finalAmount:    String(subtotal),
    paidAmount:     String(_createModePayment.paymentAmount || 0),
    remaining:      String(Math.max(subtotal - (_createModePayment.paymentAmount || 0), 0)),
    paymentStatus:  _createModePayment.payStatus || 'UNPAID',
  };

  _renderInvoiceModal(_invoiceData);

  // Äá»•i label nÃºt xÃ¡c nháº­n cho create mode
  const btnLbl = document.getElementById('btnConfirmPaymentLabel');
  if (btnLbl) btnLbl.textContent = 'XÃ¡c nháº­n';

  const invoiceModalEl = document.getElementById('invoiceModal');
  const invoiceModal   = bootstrap.Modal.getInstance(invoiceModalEl) || new bootstrap.Modal(invoiceModalEl);
  invoiceModal.show();
}

/**
 * BUG-008 FIX: Kiá»ƒm tra xem cÃ³ guest card nÃ o trong edit mode cÃ³ thay Ä‘á»•i chÆ°a lÆ°u khÃ´ng.
 *
 * So sÃ¡nh giÃ¡ trá»‹ hiá»‡n táº¡i cá»§a variant, room, date, time vá»›i giÃ¡ trá»‹ gá»‘c
 * Ä‘Æ°á»£c lÆ°u trong dataset khi modal má»Ÿ (originalVariantId, originalRoom,
 * originalDate, originalTime).
 *
 * CÅ©ng kiá»ƒm tra booker info (name, phone, email, notes) so vá»›i giÃ¡ trá»‹
 * Ä‘Æ°á»£c load tá»« API khi má»Ÿ modal.
 *
 * @returns {boolean} true náº¿u cÃ³ thay Ä‘á»•i chÆ°a lÆ°u
 */
function _hasUnsavedGuestChanges() {
  const apptIdEl = document.getElementById('apptId');
  // Chá»‰ Ã¡p dá»¥ng trong edit mode (cÃ³ bookingCode)
  if (!apptIdEl?.dataset.bookingCode) return false;

  const items = _getGuestItems();
  for (const item of items) {
    const currentVariant = item.querySelector('.gc-variant')?.value || '';
    const originalVariant = item.dataset.originalVariantId || '';
    if (currentVariant !== originalVariant) return true;

    const currentRoom = item.dataset.slotRoom || item.querySelector('.gc-room')?.value || '';
    const originalRoom = item.dataset.originalRoom || '';
    if (currentRoom !== originalRoom) return true;

    // NgÃ y háº¹n â€” BUG-A08 FIX: Æ°u tiÃªn per-card slotDate thay vÃ¬ bookingDate (shared).
    // bookingDate chá»‰ pháº£n Ã¡nh ngÃ y khÃ¡ch Ä‘áº§u tiÃªn â€” dÃ¹ng nÃ³ cho táº¥t cáº£ cards
    // sáº½ luÃ´n tráº£ true cho cÃ¡c khÃ¡ch cÃ³ ngÃ y khÃ¡c nhau dÃ¹ khÃ´ng cÃ³ thay Ä‘á»•i thá»±c sá»±.
    const currentDate = item.dataset.slotDate
      || item.querySelector('.gc-date')?.value
      || document.getElementById('bookingDate')?.value
      || '';
    const originalDate = item.dataset.originalDate || '';
    if (originalDate && currentDate !== originalDate) return true;

    const currentTime = item.querySelector('.gc-time-input')?.value
      || item.dataset.slotTime
      || item.querySelector('.gc-time')?.value
      || '';
    const originalTime = item.dataset.originalTime || '';
    if (originalTime && currentTime !== originalTime) return true;

    // Check tráº¡ng thÃ¡i chung â€” so sÃ¡nh sharedApptStatus vá»›i originalApptStatus cá»§a card Ä‘áº§u tiÃªn
    const currentStatus = document.getElementById('sharedApptStatus')?.value || '';
    const originalStatus = item.dataset.originalApptStatus || '';
    if (originalStatus && currentStatus !== originalStatus) return true;
  }

  return false;
}

function _initInvoiceModal() {
  // NÃºt má»Ÿ invoice modal â€” phÃ¢n biá»‡t create mode vÃ  edit mode
  const btnOpen = document.getElementById('btnOpenInvoice');
  if (btnOpen) {
    btnOpen.addEventListener('click', async () => {
      const apptIdEl    = document.getElementById('apptId');
      const bookingCode = apptIdEl?.dataset.bookingCode || '';

      if (bookingCode) {
        // EDIT MODE: BUG-008 FIX â€” kiá»ƒm tra form cÃ³ thay Ä‘á»•i chÆ°a lÆ°u khÃ´ng
        // Náº¿u cÃ³ â†’ yÃªu cáº§u lÆ°u trÆ°á»›c Ä‘á»ƒ BE vÃ  FE dÃ¹ng cÃ¹ng 1 nguá»“n dá»¯ liá»‡u
        const unsavedChanges = _hasUnsavedGuestChanges();
        if (unsavedChanges) {
          _showModalError('Vui lÃ²ng lÆ°u lá»‹ch háº¹n trÆ°á»›c khi má»Ÿ hÃ³a Ä‘Æ¡n (cÃ³ thay Ä‘á»•i chÆ°a Ä‘Æ°á»£c lÆ°u).');
          // Scroll lÃªn Ä‘á»ƒ user tháº¥y thÃ´ng bÃ¡o
          document.getElementById('modalError')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          return;
        }
        await _openInvoiceModal(bookingCode);
      } else {
        // CREATE MODE: má»Ÿ modal thanh toÃ¡n táº¡m dá»±a trÃªn guestCards hiá»‡n táº¡i
        _openCreatePayModal();
      }
    });
  }

  // Tá»± Ä‘á»™ng tÃ­nh láº¡i khi thay Ä‘á»•i discount
  const discountInput = document.getElementById('invDiscountValue');
  const discountType  = document.getElementById('invDiscountType');
  if (discountInput) discountInput.addEventListener('input', () => _recalcInvoiceTotals());
  if (discountType)  discountType.addEventListener('change', () => _recalcInvoiceTotals());

  // NÃºt xÃ¡c nháº­n thanh toÃ¡n
  const btnConfirm = document.getElementById('btnConfirmPayment');
  if (btnConfirm) {
    btnConfirm.addEventListener('click', async () => {
      await _submitInvoicePayment();
    });
  }

  // NÃºt hoÃ n tiá»n
  const btnRefundInit = document.getElementById('btnRefundPayment');
  if (btnRefundInit) {
    btnRefundInit.addEventListener('click', async () => {
      await _submitInvoiceRefund();
    });
  }
}

/**
 * Build danh sÃ¡ch lines tá»« guest cards hiá»‡n táº¡i trÃªn form.
 * Tráº£ vá» { lines, subtotal } hoáº·c null náº¿u khÃ´ng cÃ³ guest nÃ o há»£p lá»‡.
 */
function _buildLinesFromGuestCards() {
  const items = _getGuestItems();
  const readyGuests = items.filter(item => {
    return (item.querySelector('.gc-service')?.value || '') &&
           (item.querySelector('.gc-variant')?.value || '');
  });
  if (!readyGuests.length) return null;

  let subtotal = 0;
  const lines = [];
  readyGuests.forEach(item => {
    const svcSel  = item.querySelector('.gc-service');
    const varSel  = item.querySelector('.gc-variant');
    const svc     = SERVICES.find(s => String(s.id) === svcSel?.value);
    const variant = svc?.variants?.find(v => String(v.id) === varSel?.value);
    const price   = parseFloat(variant?.price || svc?.price || 0);
    const name    = item.querySelector('.gc-name')?.value.trim() || 'â€”';
    subtotal += price;
    lines.push({
      customerName: name,
      serviceName:  svc?.name || '',
      variantLabel: variant?.label || '',
      durationMin:  variant?.duration_minutes || null,
      unitPrice:    String(price),
      quantity:     1,
      lineTotal:    String(price),
    });
  });
  return { lines, subtotal };
}

/**
 * Má»Ÿ Invoice Modal vÃ  load dá»¯ liá»‡u hÃ³a Ä‘Æ¡n.
 */
async function _openInvoiceModal(bookingCode) {
  const invoiceModalEl = document.getElementById('invoiceModal');
  if (!invoiceModalEl) return;

  // Reset error
  const errEl = document.getElementById('invoiceModalError');
  if (errEl) { errEl.textContent = ''; errEl.classList.add('d-none'); }

  // Show loading state
  const btnConfirm = document.getElementById('btnConfirmPayment');
  if (btnConfirm) btnConfirm.disabled = true;

  // Load invoice data
  const result = await apiGet(`${API_BASE}/bookings/${bookingCode}/invoice/`);
  if (!result.success || !result.invoice) {
    showToast('error', 'Lá»—i', 'KhÃ´ng thá»ƒ táº£i dá»¯ liá»‡u hÃ³a Ä‘Æ¡n');
    return;
  }

  _invoiceData = result.invoice;
  _invoiceData._bookingCode = bookingCode;

  // BUG-008 FIX: KhÃ´ng override lines/subtotal tá»« form chÆ°a lÆ°u ná»¯a.
  // Caller (_initInvoiceModal) Ä‘Ã£ Ä‘áº£m báº£o khÃ´ng cÃ³ unsaved changes trÆ°á»›c khi gá»i hÃ m nÃ y.
  // DÃ¹ng hoÃ n toÃ n dá»¯ liá»‡u tá»« API (Ä‘Ã£ pháº£n Ã¡nh Ä‘Ãºng DB sau khi lÆ°u).

  // Render modal
  _renderInvoiceModal(_invoiceData);

  // Má»Ÿ modal
  const invoiceModal = bootstrap.Modal.getInstance(invoiceModalEl) || new bootstrap.Modal(invoiceModalEl);
  invoiceModal.show();

  if (btnConfirm) btnConfirm.disabled = false;
}

/**
 * Render ná»™i dung Invoice Modal tá»« dá»¯ liá»‡u invoice.
 */
function _renderInvoiceModal(inv) {
  // Header
  const titleEl = document.getElementById('invoiceModalTitle');
  if (titleEl) {
    titleEl.textContent = inv.invoiceCode ? `HÃ³a Ä‘Æ¡n ${inv.invoiceCode}` : `HÃ³a Ä‘Æ¡n â€” ${inv.bookingCode}`;
  }

  // Booking info
  const bcEl = document.getElementById('invBookingCode');
  const bnEl = document.getElementById('invBookerName');
  const bpEl = document.getElementById('invBookerPhone');
  if (bcEl) bcEl.textContent = inv.bookingCode || '';
  if (bnEl) bnEl.textContent = inv.bookerName  || '';
  if (bpEl) bpEl.textContent = inv.bookerPhone || '';

  // Lines
  const tbody = document.getElementById('invLinesTbody');
  if (tbody) {
    if (!inv.lines || inv.lines.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">ChÆ°a cÃ³ dá»‹ch vá»¥</td></tr>';
    } else {
      tbody.innerHTML = inv.lines.map(line => {
        const hasService = line.serviceName || line.variantLabel;
        const svcCell = hasService
          ? `<td>${_esc(line.serviceName || '')}</td>`
          : `<td class="invoice-no-service">ChÆ°a chá»n dá»‹ch vá»¥</td>`;
        const variantCell = hasService
          ? `<td>${_esc(line.variantLabel || '')}${line.durationMin ? ` â€” ${line.durationMin} phÃºt` : ''}</td>`
          : `<td class="invoice-no-service">â€”</td>`;
        const priceCell = hasService
          ? `<td class="text-end">${_fmtVND(parseFloat(line.unitPrice))}</td>`
          : `<td class="text-end invoice-no-service">0Ä‘</td>`;
        const totalCell = hasService
          ? `<td class="text-end">${_fmtVND(parseFloat(line.lineTotal))}</td>`
          : `<td class="text-end invoice-no-service">0Ä‘</td>`;
        return `<tr>
          <td>${_esc(line.customerName || '')}</td>
          ${svcCell}
          ${variantCell}
          ${priceCell}
          <td class="text-center">${line.quantity || 1}</td>
          ${totalCell}
        </tr>`;
      }).join('');
    }
  }

  // Reset discount fields â€” khÃ´i phá»¥c tá»« invoice Ä‘Ã£ lÆ°u
  const discountInput = document.getElementById('invDiscountValue');
  const discountType  = document.getElementById('invDiscountType');
  if (discountInput) {
    const dv = parseFloat(inv.discountValue) || 0;
    discountInput.value = dv > 0 ? dv : '';
  }
  if (discountType) {
    // Map model value â†’ select option: NONE/AMOUNT/PERCENT
    const dtMap = { NONE: 'NONE', AMOUNT: 'AMOUNT', PERCENT: 'PERCENT' };
    discountType.value = dtMap[inv.discountType] || 'NONE';
  }

  // Totals
  _updateInvoiceTotalsDisplay(
    parseFloat(inv.subtotal)       || 0,
    parseFloat(inv.discountAmount) || 0,
    parseFloat(inv.finalAmount)    || 0,
    parseFloat(inv.paidAmount)     || 0,
    parseFloat(inv.remaining)      || 0,
  );

  // Pay input section
  const payStatus  = inv.paymentStatus || 'UNPAID';
  const paidAmount = parseFloat(inv.paidAmount) || 0;
  const payInputWrap = document.getElementById('invPayInputWrap');
  const btnConfirm   = document.getElementById('btnConfirmPayment');
  const btnLabel     = document.getElementById('btnConfirmPaymentLabel');
  const btnRefund    = document.getElementById('btnRefundPayment');
  const refundedMsg  = document.getElementById('invRefundedMsg');

  // Reset tráº¡ng thÃ¡i trÆ°á»›c
  if (payInputWrap) payInputWrap.style.display = 'none';
  if (btnConfirm)   btnConfirm.style.display   = 'none';
  if (btnRefund)    btnRefund.style.display     = 'none';
  if (refundedMsg)  refundedMsg.style.display   = 'none';

  if (payStatus === 'REFUNDED') {
    // ÄÃ£ hoÃ n tiá»n â†’ chá»‰ hiá»‡n thÃ´ng bÃ¡o, áº©n táº¥t cáº£ nÃºt
    if (refundedMsg) refundedMsg.style.display = '';
  } else if (payStatus === 'PAID') {
    // ÄÃ£ thanh toÃ¡n Ä‘á»§ â†’ hiá»‡n nÃºt HoÃ n tiá»n chá»‰ khi paidAmount > 0
    if (paidAmount > 0) {
      if (btnRefund) btnRefund.style.display = '';
    }
  } else {
    // UNPAID / PARTIAL â†’ hiá»‡n form nháº­p thanh toÃ¡n
    // BUG-002 FIX: PARTIAL cÃ³ tiá»n Ä‘Ã£ thu â†’ hiá»‡n thÃªm nÃºt HoÃ n tiá»n
    const finalAmount = parseFloat(inv.finalAmount) || 0;
    const remaining   = parseFloat(inv.remaining)   || 0;

    // Náº¿u final = 0 (chÆ°a cÃ³ dá»‹ch vá»¥) â†’ áº©n form, hiá»‡n thÃ´ng bÃ¡o
    if (finalAmount === 0 && payStatus === 'UNPAID') {
      const errEl = document.getElementById('invoiceModalError');
      if (errEl) {
        errEl.textContent = 'ChÆ°a cÃ³ dá»‹ch vá»¥ nÃ o Ä‘Æ°á»£c chá»n. Vui lÃ²ng lÆ°u lá»‹ch háº¹n vá»›i dá»‹ch vá»¥ trÆ°á»›c khi thanh toÃ¡n.';
        errEl.classList.remove('d-none');
      }
      // áº¨n nÃºt xÃ¡c nháº­n â€” khÃ´ng thá»ƒ thanh toÃ¡n 0Ä‘
      if (btnConfirm) btnConfirm.style.display = 'none';
    } else {
      if (payInputWrap) payInputWrap.style.display = 'block';
      if (btnConfirm)   btnConfirm.style.display   = '';
      if (payStatus === 'PARTIAL' && paidAmount > 0) {
        if (btnRefund) btnRefund.style.display = '';
      }
      const payAmountInput = document.getElementById('invPayAmount');
      if (payAmountInput) {
        payAmountInput.value = remaining > 0 ? Math.round(remaining) : '';
      }
      if (btnLabel) {
        btnLabel.textContent = payStatus === 'PARTIAL' ? 'Thu thÃªm' : 'XÃ¡c nháº­n thanh toÃ¡n';
      }
    }
  }
}

/**
 * TÃ­nh láº¡i tá»•ng tiá»n khi thay Ä‘á»•i chiáº¿t kháº¥u.
 */
function _recalcInvoiceTotals() {
  if (!_invoiceData) return;

  const subtotal      = parseFloat(_invoiceData.subtotal) || 0;
  const discountInput = document.getElementById('invDiscountValue');
  const discountType  = document.getElementById('invDiscountType');
  const paidAmount    = parseFloat(_invoiceData.paidAmount) || 0;

  let discountValue = parseFloat(discountInput?.value || 0) || 0;
  const dtype = discountType?.value || 'NONE';  // NONE | AMOUNT | PERCENT

  // Clamp: 0 â‰¤ discount â‰¤ subtotal
  const discountAmount = _calcDiscountAmount(subtotal, dtype, discountValue);
  const finalAmount = subtotal - discountAmount;
  const remaining   = Math.max(finalAmount - paidAmount, 0);

  _updateInvoiceTotalsDisplay(subtotal, discountAmount, finalAmount, paidAmount, remaining);

  // Cáº­p nháº­t pre-fill sá»‘ tiá»n
  const payAmountInput = document.getElementById('invPayAmount');
  if (payAmountInput && remaining > 0) {
    payAmountInput.value = Math.round(remaining);
  }
}

/**
 * Cáº­p nháº­t hiá»ƒn thá»‹ cÃ¡c dÃ²ng tá»•ng trong invoice modal.
 */
function _updateInvoiceTotalsDisplay(subtotal, discount, final, paid, remaining) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = _fmtVND(val);
  };
  set('invSubtotal',  subtotal);
  set('invDiscount',  discount);
  set('invFinal',     final);
  set('invPaid',      paid);
  set('invRemaining', remaining);
}

/**
 * Submit thanh toÃ¡n tá»« Invoice Modal.
 */
async function _submitInvoicePayment() {
  if (!_invoiceData) return;

  const errEl = document.getElementById('invoiceModalError');
  if (errEl) { errEl.textContent = ''; errEl.classList.add('d-none'); }

  const discountInput = document.getElementById('invDiscountValue');
  const discountType  = document.getElementById('invDiscountType');
  const payAmountInput = document.getElementById('invPayAmount');
  const payMethodSel   = document.getElementById('invPayMethod');
  const btnConfirm     = document.getElementById('btnConfirmPayment');

  const discountValue = parseFloat(discountInput?.value || 0) || 0;
  const dtype         = discountType?.value || 'NONE';  // NONE | AMOUNT | PERCENT
  const payAmount     = parseFloat(payAmountInput?.value || 0) || 0;
  const payMethod     = payMethodSel?.value || '';

  // Validate
  if (payAmount > 0 && !payMethod) {
    if (errEl) { errEl.textContent = 'Vui lÃ²ng chá»n phÆ°Æ¡ng thá»©c thanh toÃ¡n'; errEl.classList.remove('d-none'); }
    return;
  }
  if (payAmount < 0) {
    if (errEl) { errEl.textContent = 'Sá»‘ tiá»n khÃ´ng Ä‘Æ°á»£c Ã¢m'; errEl.classList.remove('d-none'); }
    return;
  }
  if (dtype === 'PERCENT' && discountValue > 100) {
    if (errEl) { errEl.textContent = 'Chiáº¿t kháº¥u % khÃ´ng Ä‘Æ°á»£c vÆ°á»£t quÃ¡ 100'; errEl.classList.remove('d-none'); }
    return;
  }

  // Validate remaining (tÃ­nh tá»« _invoiceData + discount hiá»‡n táº¡i)
  if (payAmount > 0 && !(_invoiceData._createMode)) {
    const subtotalCheck = parseFloat(_invoiceData.subtotal) || 0;
    const paidCheck     = parseFloat(_invoiceData.paidAmount) || 0;
    const discountAmountCheck = _calcDiscountAmount(subtotalCheck, dtype, discountValue);
    const finalCheck     = Math.max(subtotalCheck - discountAmountCheck, 0);
    const remainingCheck = Math.max(finalCheck - paidCheck, 0);
    if (finalCheck === 0) {
      if (errEl) { errEl.textContent = 'ChÆ°a cÃ³ dá»‹ch vá»¥ nÃ o Ä‘Æ°á»£c chá»n. Vui lÃ²ng lÆ°u lá»‹ch háº¹n vá»›i dá»‹ch vá»¥ trÆ°á»›c khi thanh toÃ¡n.'; errEl.classList.remove('d-none'); }
      return;
    }
    if (payAmount > remainingCheck) {
      if (errEl) { errEl.textContent = `Sá»‘ tiá»n thanh toÃ¡n (${_fmtVND(payAmount)}) vÆ°á»£t quÃ¡ sá»‘ tiá»n cÃ²n láº¡i (${_fmtVND(remainingCheck)}). Vui lÃ²ng kiá»ƒm tra láº¡i.`; errEl.classList.remove('d-none'); }
      return;
    }
  }

  const bookingCode = _invoiceData._bookingCode;

  // â”€â”€ CREATE MODE: lÆ°u payment data táº¡m, khÃ´ng gá»i API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  if (_invoiceData._createMode || !bookingCode) {
    // TÃ­nh final sau discount
    const subtotal = parseFloat(_invoiceData.subtotal) || 0;
    const discountAmount = _calcDiscountAmount(subtotal, dtype, discountValue);
    const finalAmount = subtotal - discountAmount;

    // XÃ¡c Ä‘á»‹nh payStatus
    const hasAnyService = ((_invoiceData.lines || []).some(l => parseFloat(l.unitPrice) > 0));
    const payStatus = _calcPayStatus(finalAmount, payAmount, hasAnyService);

    // LÆ°u vÃ o state táº¡m
    _createModePayment = {
      payStatus,
      paymentMethod: payMethod,
      paymentAmount: payAmount,
      discountType:  dtype,
      discountValue,
      discountAmount,
      finalAmount,
    };

    // Cáº­p nháº­t badge trong create modal
    _setPayStatusBadge(payStatus);
    const btnInvoiceLabel = document.getElementById('btnInvoiceLabel');
    if (btnInvoiceLabel) {
      if (payStatus === 'PAID')         btnInvoiceLabel.textContent = 'Xem hÃ³a Ä‘Æ¡n';
      else if (payStatus === 'PARTIAL') btnInvoiceLabel.textContent = 'Thu thÃªm';
      else                              btnInvoiceLabel.textContent = 'Thanh toÃ¡n';
    }

    // ÄÃ³ng invoice modal
    const invoiceModalEl = document.getElementById('invoiceModal');
    const invoiceModal   = bootstrap.Modal.getInstance(invoiceModalEl);
    if (invoiceModal) invoiceModal.hide();

    showToast('success', 'ÄÃ£ ghi nháº­n', `Thanh toÃ¡n: ${_fmtVND(payAmount)} â€” sáº½ lÆ°u khi táº¡o lá»‹ch`);
    return;
  }

  // â”€â”€ EDIT MODE: gá»i API nhÆ° cÅ© â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  // Loading state â€” chá»‰ Ä‘á»•i text trong span, khÃ´ng ghi Ä‘Ã¨ innerHTML nÃºt
  const btnLbl = document.getElementById('btnConfirmPaymentLabel');
  if (btnConfirm) btnConfirm.disabled = true;
  if (btnLbl) btnLbl.textContent = 'Äang xá»­ lÃ½...';

  try {
    const result = await apiPost(`${API_BASE}/bookings/${bookingCode}/invoice/pay/`, {
      discountType:  dtype,
      discountValue: discountValue,
      payAmount:     payAmount,
      paymentMethod: payMethod,
    });

    if (!result.success) {
      if (errEl) { errEl.textContent = result.error || 'CÃ³ lá»—i xáº£y ra'; errEl.classList.remove('d-none'); }
      return;
    }

    // ÄÃ³ng invoice modal
    const invoiceModalEl = document.getElementById('invoiceModal');
    const invoiceModal = bootstrap.Modal.getInstance(invoiceModalEl);
    if (invoiceModal) invoiceModal.hide();

    // Cáº­p nháº­t hidden select + badge trong edit modal
    const payStatusSel = document.getElementById('sharedPayStatus');
    if (payStatusSel) _setSelectValue(payStatusSel, result.paymentStatus, 'UNPAID');
    _updatePaymentSummary();

    // Refresh grid
    await _refreshAll();

    const statusLabels = { UNPAID: 'ChÆ°a thanh toÃ¡n', PARTIAL: 'Thanh toÃ¡n má»™t pháº§n', PAID: 'ÄÃ£ thanh toÃ¡n' };
    showToast('success', 'Thanh toÃ¡n thÃ nh cÃ´ng', statusLabels[result.paymentStatus] || result.paymentStatus);

  } catch (e) {
    if (errEl) { errEl.textContent = 'CÃ³ lá»—i xáº£y ra, vui lÃ²ng thá»­ láº¡i'; errEl.classList.remove('d-none'); }
  } finally {
    if (btnConfirm) {
      btnConfirm.disabled = false;
      const lbl = document.getElementById('btnConfirmPaymentLabel');
      if (lbl) lbl.textContent = 'XÃ¡c nháº­n thanh toÃ¡n';
    }
  }
}

/**
 * HoÃ n tiá»n hÃ³a Ä‘Æ¡n â€” Ä‘á»•i táº¥t cáº£ InvoicePayment SUCCESS â†’ REFUNDED.
 */
async function _submitInvoiceRefund() {
  if (!_invoiceData) return;

  const bookingCode = _invoiceData._bookingCode;
  if (!bookingCode) return;

  const errEl    = document.getElementById('invoiceModalError');
  const btnRefund = document.getElementById('btnRefundPayment');
  const btnLbl    = document.getElementById('btnRefundPaymentLabel');

  if (errEl) { errEl.textContent = ''; errEl.classList.add('d-none'); }

  // Confirm trÆ°á»›c khi hoÃ n tiá»n
  const confirmed = await confirmAction(
    'XÃ¡c nháº­n hoÃ n tiá»n',
    'Báº¡n cÃ³ cháº¯c muá»‘n hoÃ n tiá»n hÃ³a Ä‘Æ¡n nÃ y? Táº¥t cáº£ giao dá»‹ch thanh toÃ¡n sáº½ bá»‹ Ä‘Ã¡nh dáº¥u lÃ  Ä‘Ã£ hoÃ n.',
    'HoÃ n tiá»n',
    'Há»§y'
  );
  if (!confirmed) return;

  if (btnRefund) btnRefund.disabled = true;
  if (btnLbl)    btnLbl.textContent = 'Äang xá»­ lÃ½...';

  try {
    const result = await apiPost(`${API_BASE}/bookings/${bookingCode}/invoice/refund/`, {});

    if (!result.success) {
      if (errEl) { errEl.textContent = result.error || 'CÃ³ lá»—i xáº£y ra'; errEl.classList.remove('d-none'); }
      return;
    }

    // ÄÃ³ng invoice modal
    const invoiceModalEl = document.getElementById('invoiceModal');
    const invoiceModal = bootstrap.Modal.getInstance(invoiceModalEl);
    if (invoiceModal) invoiceModal.hide();

    // Cáº­p nháº­t tráº¡ng thÃ¡i thanh toÃ¡n trong edit modal
    const payStatusSel = document.getElementById('sharedPayStatus');
    if (payStatusSel) _setSelectValue(payStatusSel, 'REFUNDED', 'UNPAID');
    _updatePaymentSummary();

    // Refresh grid
    await _refreshAll();

    showToast('success', 'HoÃ n tiá»n thÃ nh cÃ´ng', 'ÄÃ£ hoÃ n tiá»n hÃ³a Ä‘Æ¡n');

  } catch (e) {
    if (errEl) { errEl.textContent = 'CÃ³ lá»—i xáº£y ra, vui lÃ²ng thá»­ láº¡i'; errEl.classList.remove('d-none'); }
  } finally {
    if (btnRefund) btnRefund.disabled = false;
    if (btnLbl)    btnLbl.textContent = 'HoÃ n tiá»n';
  }
}



