new_create_mode = '''      {# CREATE MODE — 3-panel redesign: Người đặt | Slot summary | Accordion khách #}
      <div id="createModeBody" style="display:none;flex-direction:column;overflow:hidden;flex:1;min-height:0;">

        {# ── PANEL 1: Người đặt (sticky top) ── #}
        <div class="cm-booker-panel">
          <div class="cm-section-label">
            <span class="cm-section-icon" style="background:#1f3a5f;">
              <i class="fas fa-user"></i>
            </span>
            <span>Người đặt lịch</span>
          </div>
          <div class="row g-2">
            <div class="col-md-3">
              <label class="cm-label">Họ tên <span class="text-danger">*</span></label>
              <input class="form-control form-control-sm" id="bookerName" placeholder="Họ tên người đặt" autocomplete="off" />
            </div>
            <div class="col-md-2">
              <label class="cm-label">Số điện thoại <span class="text-danger">*</span></label>
              <input class="form-control form-control-sm" id="bookerPhone" placeholder="SĐT" inputmode="numeric" autocomplete="off" />
            </div>
            <div class="col-md-3">
              <label class="cm-label">Email</label>
              <input type="email" class="form-control form-control-sm" id="bookerEmail" placeholder="Email" autocomplete="off" />
            </div>
            <div class="col-md-2">
              <label class="cm-label">Nguồn</label>
              <select class="form-select form-select-sm" id="bookerSource">
                <option value="DIRECT">Trực tiếp</option>
                <option value="PHONE">Điện thoại</option>
                <option value="FACEBOOK">Facebook</option>
                <option value="ZALO">Zalo</option>
                <option value="ONLINE">Online</option>
              </select>
            </div>
            <div class="col-md-2 d-flex align-items-end">
              <div class="form-check mb-1">
                <input class="form-check-input" type="checkbox" id="chkFillFromBooker" checked />
                <label class="form-check-label cm-label" for="chkFillFromBooker" style="white-space:nowrap;">
                  Dùng cho khách trống
                </label>
              </div>
            </div>
          </div>
        </div>

        {# ── PANEL 2 + 3: Scroll area ── #}
        <div class="cm-scroll-area">

          {# ── PANEL 2: Slot summary ── #}
          <div class="cm-slot-summary" id="slotSummaryPanel">
            <div class="cm-section-label mb-2">
              <span class="cm-section-icon" style="background:#0891b2;">
                <i class="fas fa-calendar-check"></i>
              </span>
              <span id="slotSummaryTitle">Các slot đã chọn</span>
            </div>
            <div id="slotSummaryList" class="cm-slot-list"></div>
          </div>

          {# ── PANEL 3: Áp dụng chung + Accordion khách ── #}
          <div class="cm-guests-panel">
            <div class="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-2">
              <div class="cm-section-label mb-0">
                <span class="cm-section-icon" style="background:#c9a96e;">
                  <i class="fas fa-spa"></i>
                </span>
                <span style="font-weight:600;font-size:.875rem;color:#1f2937;">Thông tin từng khách</span>
              </div>
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <button type="button" id="btnAddGuest" class="cm-btn-add-guest">
                  <i class="fas fa-plus me-1"></i>Thêm khách
                </button>
              </div>
            </div>

            {# Toolbar áp dụng cho tất cả #}
            <div class="cm-apply-bar" id="applyAllBar">
              <span class="cm-apply-label"><i class="fas fa-magic me-1"></i>Áp dụng cho tất cả:</span>
              <select class="form-select form-select-sm cm-apply-select" id="applyAllService" style="max-width:160px;">
                <option value="">-- Dịch vụ --</option>
              </select>
              <select class="form-select form-select-sm cm-apply-select" id="applyAllVariant" style="max-width:160px;" disabled>
                <option value="">-- Gói --</option>
              </select>
              <select class="form-select form-select-sm cm-apply-select" id="applyAllStatus" style="max-width:130px;">
                <option value="">-- Trạng thái --</option>
                <option value="NOT_ARRIVED">Chưa đến</option>
                <option value="PENDING">Chờ xác nhận</option>
                <option value="ARRIVED">Đã đến</option>
                <option value="COMPLETED">Hoàn thành</option>
              </select>
              <select class="form-select form-select-sm cm-apply-select" id="applyAllPay" style="max-width:140px;">
                <option value="">-- Thanh toán --</option>
                <option value="UNPAID">Chưa thanh toán</option>
                <option value="PARTIAL">Một phần</option>
                <option value="PAID">Đã thanh toán</option>
              </select>
              <button type="button" class="cm-btn-apply" id="btnApplyAll">
                <i class="fas fa-check me-1"></i>Áp dụng
              </button>
            </div>

            {# Accordion danh sách khách #}
            <div id="guestList" class="cm-guest-accordion"></div>
          </div>

        </div>
      </div>

'''

content = open('templates/manage/pages/admin_appointments.html', 'r', encoding='utf-8').read()

start_marker = '      {# CREATE MODE'
end_marker = '      <div class="modal-footer"'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

new_content = content[:start_idx] + new_create_mode + content[end_idx:]
open('templates/manage/pages/admin_appointments.html', 'w', encoding='utf-8').write(new_content)
print('Done. New length:', len(new_content))
