// Admin Services Page JavaScript

// Category Names mapping
const categoryNames = {
    1: 'Chăm sóc da',
    2: 'Massage',
    3: 'Phun thêu',
    4: 'Triệt lông'
};

// Status Names
const statusNames = {
    'active': 'Đang hoạt động',
    'inactive': 'Ngừng hoạt động'
};

// Track edit mode
let isEditMode = false;
let editingServiceId = null;
let existingImageUrl = null;

// ===== LOADING STATE HELPER =====
// Biến theo dõi trạng thái đang submit để tránh submit lặp
let isSubmitting = false;

/**
 * Bật loading state cho button
 * @param {HTMLElement} btn - Button cần set loading
 * @param {string} loadingText - Text hiển thị khi loading
 */
function setButtonLoading(btn, loadingText = 'Đang xử lý...') {
    if (!btn) return;
    
    // Lưu text gốc nếu chưa có
    if (!btn.dataset.originalText) {
        btn.dataset.originalText = btn.innerHTML;
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

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadServicesTable();
    setupFilters();
    setupFormValidation();

    // Show Django messages as toast
    showDjangoMessagesAsToast();
});

// Load Services Table (for AJAX calls)
function loadServicesTable() {
    // This function is kept for compatibility but not used in traditional flow
    const tbody = document.getElementById('servicesTableBody');
    if (!tbody) return;

    // Check if we need to reload via AJAX
    // For now, we use traditional Django rendering
}

// Setup Filters
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Auto-submit form for instant filtering
            const form = searchInput.closest('form');
            if (form) {
                form.submit();
            }
        });
    }
}

// Setup Form Validation
function setupFormValidation() {
    const form = document.getElementById('addServiceForm');
    if (!form) return;

    const nameInput = form.querySelector('[name="name"]');
    const priceInput = form.querySelector('[name="price"]');
    const durationInput = form.querySelector('[name="duration_minutes"]');
    const categoryInput = form.querySelector('[name="category_number"]');
    const imageInput = form.querySelector('[name="image"]');

    if (nameInput) {
        nameInput.addEventListener('blur', function() {
            validateServiceName(this);
        });
    }

    if (priceInput) {
        priceInput.addEventListener('blur', function() {
            validatePrice(this);
        });
    }

    if (durationInput) {
        durationInput.addEventListener('blur', function() {
            validateDuration(this);
        });
    }

    if (categoryInput) {
        categoryInput.addEventListener('blur', function() {
            validateCategory(this);
        });
    }

    if (imageInput) {
        imageInput.addEventListener('change', function() {
            validateImage(this);
        });
    }
}

// Validation Functions
function validateServiceName(input) {
    const value = input.value.trim();

    clearFieldError(input);

    if (!value) {
        showFieldError(input, 'Tên dịch vụ không được để trống');
        return false;
    }

    if (value.length < 5) {
        showFieldError(input, 'Tên dịch vụ phải có ít nhất 5 ký tự');
        return false;
    }

    if (value.length > 200) {
        showFieldError(input, 'Tên dịch vụ không được quá 200 ký tự');
        return false;
    }

    if (value.match(/^\d+$/)) {
        showFieldError(input, 'Tên dịch vụ không hợp lệ');
        return false;
    }

    return true;
}

function validateCategory(input) {
    const value = input.value;

    clearFieldError(input);

    if (!value) {
        showFieldError(input, 'Vui lòng chọn danh mục');
        return false;
    }

    return true;
}

function validatePrice(input) {
    const value = parseFloat(input.value);

    clearFieldError(input);

    if (isNaN(value) || input.value === '') {
        showFieldError(input, 'Giá dịch vụ không hợp lệ');
        return false;
    }

    if (value <= 0) {
        showFieldError(input, 'Giá dịch vụ phải lớn hơn 0');
        return false;
    }

    if (value > 999999999) {
        showFieldError(input, 'Giá dịch vụ không được quá 999,999,999 VNĐ');
        return false;
    }

    return true;
}

function validateDuration(input) {
    const value = parseInt(input.value);

    clearFieldError(input);

    if (isNaN(value) || input.value === '') {
        showFieldError(input, 'Thời gian không hợp lệ');
        return false;
    }

    if (value <= 0) {
        showFieldError(input, 'Thời gian phải lớn hơn 0');
        return false;
    }

    if (value > 480) {
        showFieldError(input, 'Thời gian không được quá 480 phút (8 tiếng)');
        return false;
    }

    return true;
}

function validateImage(input) {
    const file = input.files[0];
    const previewDiv = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');

    clearFieldError(input);

    // Check if file exists or if editing (no new file)
    if (!file) {
        // For edit mode, allow no new image (will keep existing image)
        if (isEditMode) {
            // Show existing image if available
            if (existingImageUrl && previewDiv && previewImg) {
                previewImg.src = existingImageUrl;
                previewDiv.style.display = 'block';
            }
            return true;
        } else {
            // Require image when creating new service
            showFieldError(input, 'Vui lòng chọn hình ảnh dịch vụ');
            if (previewDiv) previewDiv.style.display = 'none';
            return false;
        }
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showFieldError(input, 'Hình ảnh không được quá 5MB');
        if (previewDiv) previewDiv.style.display = 'none';
        input.value = '';
        return false;
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showFieldError(input, 'Chỉ chấp nhận file ảnh (JPG, PNG, WebP)');
        if (previewDiv) previewDiv.style.display = 'none';
        input.value = '';
        return false;
    }

    return true;
}

function showFieldError(input, message) {
    const formGroup = input.closest('.mb-3, .col-md-4, .col-md-6');
    if (!formGroup) return;

    // Remove existing error
    const existingError = formGroup.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }

    // Add error class to input
    input.classList.add('is-invalid');

    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    formGroup.appendChild(errorDiv);
}

function clearFieldError(input) {
    input.classList.remove('is-invalid');

    const formGroup = input.closest('.mb-3, .col-md-4, .col-md-6');
    if (!formGroup) return;

    const errorMsg = formGroup.querySelector('.field-error');
    if (errorMsg) {
        errorMsg.remove();
    }
}

// Clear all field errors
function clearAllFieldErrors() {
    const fields = document.querySelectorAll('#addServiceForm .is-invalid');
    fields.forEach(field => {
        field.classList.remove('is-invalid');
    });

    const errorMessages = document.querySelectorAll('#addServiceForm .field-error');
    errorMessages.forEach(msg => msg.remove());
}

// Traditional Form Submit
function submitServiceForm(event) {
    event.preventDefault();

    // ===== NGĂN SUBMIT LẶP =====
    if (isSubmitting) {
        console.log('Đang xử lý, bỏ qua submit lặp');
        return false;
    }

    const form = document.getElementById('addServiceForm');
    if (!form) return false;

    // Validate all fields
    const nameInput = form.querySelector('[name="name"]');
    const categoryInput = form.querySelector('[name="category_number"]');
    const priceInput = form.querySelector('[name="price"]');
    const durationInput = form.querySelector('[name="duration_minutes"]');
    const imageInput = form.querySelector('[name="image"]');

    let isValid = true;

    isValid = validateServiceName(nameInput) && isValid;
    isValid = validateCategory(categoryInput) && isValid;
    isValid = validatePrice(priceInput) && isValid;
    isValid = validateDuration(durationInput) && isValid;
    isValid = validateImage(imageInput) && isValid;

    if (!isValid) {
        showToast('error', 'Vui lòng kiểm tra lại các thông tin!');
        return false;
    }

    // ===== BẬT LOADING STATE =====
    isSubmitting = true;
    const submitBtn = document.querySelector('#addServiceModal .modal-footer .btn-primary');
    const loadingText = isEditMode ? 'Đang cập nhật...' : 'Đang thêm...';
    setButtonLoading(submitBtn, loadingText);

    // Create FormData for AJAX submission
    const formData = new FormData(form);

    // Determine URL based on mode
    const url = isEditMode ? `/api/services/${editingServiceId}/update/` : '/api/services/create/';

    // Submit via AJAX
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', data.message);
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addServiceModal'));
            if (modal) {
                modal.hide();
            }
            // Reload page after success
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('error', data.error || 'Có lỗi xảy ra!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('error', 'Có lỗi xảy ra khi lưu dữ liệu!');
    })
    .finally(() => {
        // ===== TẮT LOADING STATE =====
        isSubmitting = false;
        resetButton(submitBtn);
    });

    return false;
}

// Preview Image
function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');

    if (input.files && input.files[0]) {
        const file = input.files[0];

        // Quick validation
        if (file.size > 5 * 1024 * 1024) {
            showToast('error', 'Hình ảnh không được quá 5MB!');
            input.value = '';
            if (preview) preview.style.display = 'none';
            return;
        }

        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showToast('error', 'Chỉ chấp nhận file ảnh (JPG, PNG, WebP)!');
            input.value = '';
            if (preview) preview.style.display = 'none';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewImg) previewImg.src = e.target.result;
            if (preview) preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        // If no file selected and in edit mode, show existing image
        if (isEditMode && existingImageUrl) {
            if (previewImg) previewImg.src = existingImageUrl;
            if (preview) preview.style.display = 'block';
        } else {
            if (preview) preview.style.display = 'none';
        }
    }
}

// Clear Image Preview
function clearImagePreview() {
    const preview = document.getElementById('imagePreview');
    const imageInput = document.querySelector('[name="image"]');

    if (imageInput) {
        imageInput.value = '';
    }

    if (preview) {
        preview.style.display = 'none';
    }
}

// Edit Service (opens modal and pre-fills data via AJAX)
function editService(serviceId) {
    // Reset edit mode first
    isEditMode = false;
    editingServiceId = null;
    existingImageUrl = null;

    // Fetch service data
    fetch(`/api/services/?search=${serviceId}`)
        .then(response => response.json())
        .then(data => {
            if (data.services && data.services.length > 0) {
                const service = data.services[0];

                // Set edit mode
                isEditMode = true;
                editingServiceId = serviceId;
                existingImageUrl = service.image || null;

                // Fill form
                const form = document.getElementById('addServiceForm');

                form.querySelector('[name="service_code_preview"]').value = service.code || '';
                form.querySelector('[name="service_code_preview"]').readOnly = true;

                // Map category code to number
                const categoryMap = {
                    'skincare': '1',
                    'massage': '2',
                    'tattoo': '3',
                    'hair': '4',
                    'nails': '5',
                    'other': '6'
                };
                form.querySelector('[name="category_number"]').value = categoryMap[service.category] || '1';

                form.querySelector('[name="name"]').value = service.name || '';
                form.querySelector('[name="description"]').value = service.description || '';
                form.querySelector('[name="price"]').value = service.price || '';
                form.querySelector('[name="duration_minutes"]').value = service.duration_minutes || service.duration || '';
                form.querySelector('[name="status"]').value = service.status || 'active';

                // Show existing image preview
                const previewDiv = document.getElementById('imagePreview');
                const previewImg = document.getElementById('previewImg');
                if (existingImageUrl && previewDiv && previewImg) {
                    previewImg.src = existingImageUrl;
                    previewDiv.style.display = 'block';
                } else {
                    previewDiv.style.display = 'none';
                }

                // Make image not required in edit mode
                const imageInput = form.querySelector('[name="image"]');
                if (imageInput) {
                    imageInput.removeAttribute('required');
                }

                // Change modal title and button
                const modalTitle = document.querySelector('#addServiceModal .modal-title');
                modalTitle.innerHTML = `<i class="fas fa-edit" style="color: #d4a853; margin-right: 0.5rem;"></i> Chỉnh sửa dịch vụ`;

                const modalFooter = document.querySelector('#addServiceModal .modal-footer .btn-primary');
                modalFooter.innerHTML = `<i class="fas fa-save me-2"></i> Cập nhật`;

                // Clear all errors
                clearAllFieldErrors();

                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('addServiceModal'));
                modal.show();
            } else {
                showToast('error', 'Không tìm thấy dịch vụ!');
            }
        })
        .catch(error => {
            console.error('Error loading service:', error);
            showToast('error', 'Không thể tải thông tin dịch vụ!');
        });
}

// Delete Service
function deleteService(serviceId) {
    // ===== NGĂN XÓA LẶP =====
    if (isSubmitting) {
        console.log('Đang xử lý, bỏ qua click lặp');
        return;
    }

    // ===== MỞ MODAL XÁC NHẬN =====
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteServiceModal'));
    const confirmDeleteBtn = document.getElementById('confirmDeleteServiceBtn');

    // Lưu serviceId vào dataset của modal để sử dụng sau
    document.getElementById('deleteServiceModal').dataset.serviceId = serviceId;

    // Xử lý nút Xóa trong modal
    if (confirmDeleteBtn) {
        // Xóa event listener cũ (nếu có) để tránh trùng lặp
        const newBtn = confirmDeleteBtn.cloneNode(true);
        confirmDeleteBtn.parentNode.replaceChild(newBtn, confirmDeleteBtn);

        // Thêm event listener mới
        newBtn.addEventListener('click', function() {
            const modalServiceId = document.getElementById('deleteServiceModal').dataset.serviceId;

            // Đóng modal
            deleteModal.hide();

            // ===== BẬT LOADING STATE =====
            isSubmitting = true;
            showToast('warning', 'Đang xóa dịch vụ...');

            // Submit delete via API
            const csrfToken = getCookie('csrftoken');

            fetch(`/api/services/${modalServiceId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('success', data.message);
                    // Reload page after success
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', data.error || 'Có lỗi xảy ra khi xóa!');
                    isSubmitting = false; // Reset khi lỗi
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('error', 'Có lỗi xảy ra khi xóa dịch vụ!');
                isSubmitting = false; // Reset khi lỗi
            });
        });

        // Cập nhật reference
        document.getElementById('confirmDeleteServiceBtn').id = 'confirmDeleteServiceBtn';
    }

    // Mở modal
    deleteModal.show();
}

// Show Toast
function showToast(type, message) {
    const toast = document.getElementById('toast');
    const titleEl = document.getElementById('toastTitle');
    const bodyEl = document.getElementById('toastMessage');

    if (!toast) return;

    // Remove all existing classes
    toast.className = 'toast show ' + type;

    titleEl.textContent = type === 'success' ? 'Thành công' : type === 'warning' ? 'Đang xử lý...' : 'Lỗi';

    const icon = type === 'success' ? 'fa-check-circle' : type === 'warning' ? 'fa-spinner fa-spin' : 'fa-exclamation-circle';
    bodyEl.innerHTML = `<i class="fas ${icon}"></i> ${message}`;

    // Auto hide after 3 seconds for success, 5 seconds for others
    const hideTime = type === 'success' ? 3000 : 5000;
    setTimeout(function() {
        hideToast();
    }, hideTime);
}

// Hide Toast
function hideToast() {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.classList.remove('show');
    }
}

// Show Django Messages as Toast
function showDjangoMessagesAsToast() {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    // Find Django message toasts
    const djangoToasts = toastContainer.querySelectorAll('.toast:not(#toast)');
    djangoToasts.forEach(toast => {
        const isShow = toast.classList.contains('show');
        if (isShow) {
            const type = toast.classList.contains('success') ? 'success' :
                      toast.classList.contains('error') ? 'error' :
                      toast.classList.contains('warning') ? 'warning' : 'success';

            const titleEl = toast.querySelector('.toast-title');
            const bodyEl = toast.querySelector('.toast-body');

            if (titleEl && bodyEl) {
                const message = bodyEl.textContent || bodyEl.innerText;

                // Re-show as our custom toast
                setTimeout(() => {
                    showToast(type, message);
                }, 500);

                // Hide Django toast
                toast.classList.remove('show');
            }
        }
    });
}

// Get CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Close Modal helper
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
}

// Reset form to add mode
function resetFormToAddMode() {
    const form = document.getElementById('addServiceForm');
    if (!form) return;

    // Reset edit mode flags
    isEditMode = false;
    editingServiceId = null;
    existingImageUrl = null;

    // Reset form
    form.reset();

    // Reset modal title and button
    const modalTitle = document.querySelector('#addServiceModal .modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = `<i class="fas fa-plus" style="color: #d4a853; margin-right: 0.5rem;"></i> Thêm dịch vụ mới`;
    }

    const modalFooter = document.querySelector('#addServiceModal .modal-footer .btn-primary');
    if (modalFooter) {
        modalFooter.innerHTML = `<i class="fas fa-plus me-2"></i> Thêm dịch vụ`;
        modalFooter.disabled = false;
    }

    // Make image required again
    const imageInput = form.querySelector('[name="image"]');
    if (imageInput) {
        imageInput.setAttribute('required', 'required');
    }

    // Clear image preview
    clearImagePreview();

    // Clear all errors
    clearAllFieldErrors();

    // Reset readonly fields
    const codePreview = form.querySelector('[name="service_code_preview"]');
    if (codePreview) {
        codePreview.readOnly = false;
    }
}

// Modal hidden event - reset form
document.addEventListener('DOMContentLoaded', function() {
    const addServiceModal = document.getElementById('addServiceModal');
    if (addServiceModal) {
        addServiceModal.addEventListener('hidden.bs.modal', function() {
            resetFormToAddMode();
        });
    }
});