// ============================================
// Viện Thẩm Mỹ DIVA - Enhanced JavaScript Logic
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // Initialize Bootstrap Components
    // ============================================
    
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    
    // Initialize dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl)
    })
    
    // ============================================
    // Navbar Scroll Effect
    // ============================================
    
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('shadow');
            navbar.style.padding = '0.5rem 0';
        } else {
            navbar.classList.remove('shadow');
            navbar.style.padding = '1rem 0';
        }
    });
    
    // ============================================
    // Active Navigation Link
    // ============================================
    
    const currentPage = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPage.includes(href) || (currentPage === '/' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
    
    // ============================================
    // Smooth Scroll for Anchor Links
    // ============================================
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // ============================================
    // FORM VALIDATION FUNCTIONS
    // ============================================
    
    // Email Validation
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Phone Validation (Vietnam format)
    function validatePhone(phone) {
        const re = /(84|0[3|5|7|8|9])+([0-9]{8})\b/;
        return re.test(phone);
    }
    
    // Password Strength
    function validatePassword(password) {
        if (password.length < 6) {
            return { valid: false, message: 'Mật khẩu phải có ít nhất 6 ký tự!' };
        }
        return { valid: true, message: '' };
    }
    
    // Show inline error
    function showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (field) {
            let errorDiv = field.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('field-error')) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'field-error text-danger small mt-1';
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${message}`;
            field.classList.add('is-invalid');
            field.classList.add('border-danger');
        }
    }
    
    // Clear inline error
    function clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            let errorDiv = field.nextElementSibling;
            if (errorDiv && errorDiv.classList.contains('field-error')) {
                errorDiv.remove();
            }
            field.classList.remove('is-invalid');
            field.classList.remove('border-danger');
        }
    }
    
    // ============================================
    // LOGIN FORM VALIDATION
    // ============================================
    
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        
        // Real-time validation
        usernameInput.addEventListener('blur', function() {
            clearFieldError('username');
            if (!this.value.trim()) {
                showFieldError('username', 'Vui lòng nhập tên đăng nhập!');
            }
        });
        
        passwordInput.addEventListener('blur', function() {
            clearFieldError('password');
            if (!this.value) {
                showFieldError('password', 'Vui lòng nhập mật khẩu!');
            }
        });
        
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = usernameInput.value.trim();
            const password = passwordInput.value;
            let hasError = false;
            
            // Clear previous errors
            clearFieldError('username');
            clearFieldError('password');
            
            if (!username) {
                showFieldError('username', 'Vui lòng nhập tên đăng nhập!');
                hasError = true;
            }
            
            if (!password) {
                showFieldError('password', 'Vui lòng nhập mật khẩu!');
                hasError = true;
            }
            
            if (hasError) return;
            
            // Simulate login
            showLoading();
            setTimeout(() => {
                hideLoading();
                // Demo: redirect based on username
                if (username.toLowerCase() === 'admin') {
                    showAlert('success', 'Đăng nhập thành công! Chào Admin.');
                    window.location.href = 'admin/dashboard.html';
                } else {
                    showAlert('success', 'Đăng nhập thành công!');
                    window.location.href = 'index.html';
                }
            }, 1500);
        });
    }
    
    // ============================================
    // REGISTER FORM VALIDATION
    // ============================================
    
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const fullNameInput = document.getElementById('fullName');
        const emailInput = document.getElementById('email');
        const phoneInput = document.getElementById('phone');
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirmPassword');
        
        // Real-time validation
        fullNameInput.addEventListener('blur', function() {
            clearFieldError('fullName');
            if (!this.value.trim()) {
                showFieldError('fullName', 'Vui lòng nhập họ tên!');
            } else if (this.value.trim().length < 2) {
                showFieldError('fullName', 'Họ tên phải có ít nhất 2 ký tự!');
            }
        });
        
        emailInput.addEventListener('blur', function() {
            clearFieldError('email');
            if (!this.value) {
                showFieldError('email', 'Vui lòng nhập email!');
            } else if (!validateEmail(this.value)) {
                showFieldError('email', 'Email không hợp lệ!');
            }
        });
        
        phoneInput.addEventListener('blur', function() {
            clearFieldError('phone');
            if (!this.value) {
                showFieldError('phone', 'Vui lòng nhập số điện thoại!');
            } else if (!validatePhone(this.value)) {
                showFieldError('phone', 'Số điện thoại không hợp lệ!');
            }
        });
        
        passwordInput.addEventListener('blur', function() {
            clearFieldError('password');
            const result = validatePassword(this.value);
            if (!result.valid) {
                showFieldError('password', result.message);
            }
        });
        
        confirmPasswordInput.addEventListener('blur', function() {
            clearFieldError('confirmPassword');
            if (!this.value) {
                showFieldError('confirmPassword', 'Vui lòng xác nhận mật khẩu!');
            } else if (this.value !== passwordInput.value) {
                showFieldError('confirmPassword', 'Mật khẩu xác nhận không khớp!');
            }
        });
        
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fullName = fullNameInput.value.trim();
            const email = emailInput.value.trim();
            const phone = phoneInput.value.trim();
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            let hasError = false;
            
            // Clear previous errors
            clearFieldError('fullName');
            clearFieldError('email');
            clearFieldError('phone');
            clearFieldError('password');
            clearFieldError('confirmPassword');
            
            if (!fullName) {
                showFieldError('fullName', 'Vui lòng nhập họ tên!');
                hasError = true;
            } else if (fullName.length < 2) {
                showFieldError('fullName', 'Họ tên phải có ít nhất 2 ký tự!');
                hasError = true;
            }
            
            if (!email) {
                showFieldError('email', 'Vui lòng nhập email!');
                hasError = true;
            } else if (!validateEmail(email)) {
                showFieldError('email', 'Email không hợp lệ!');
                hasError = true;
            }
            
            if (!phone) {
                showFieldError('phone', 'Vui lòng nhập số điện thoại!');
                hasError = true;
            } else if (!validatePhone(phone)) {
                showFieldError('phone', 'Số điện thoại không hợp lệ!');
                hasError = true;
            }
            
            if (!password) {
                showFieldError('password', 'Vui lòng nhập mật khẩu!');
                hasError = true;
            } else if (password.length < 6) {
                showFieldError('password', 'Mật khẩu phải có ít nhất 6 ký tự!');
                hasError = true;
            }
            
            if (!confirmPassword) {
                showFieldError('confirmPassword', 'Vui lòng xác nhận mật khẩu!');
                hasError = true;
            } else if (password !== confirmPassword) {
                showFieldError('confirmPassword', 'Mật khẩu xác nhận không khớp!');
                hasError = true;
            }
            
            if (hasError) return;
            
            // Simulate registration
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Đăng ký thành công! Vui lòng đăng nhập.');
                registerForm.reset();
                window.location.href = 'login.html';
            }, 1500);
        });
    }
    
    // ============================================
    // BOOKING FORM & 24H CANCELLATION RULE
    // ============================================
    
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        const serviceInput = document.getElementById('service');
        const dateInput = document.getElementById('date');
        const timeInput = document.getElementById('time');
        const staffInput = document.getElementById('staff');
        
        // Initialize date picker - disable past dates
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
        
        // Real-time validation
        serviceInput.addEventListener('change', function() {
            clearFieldError('service');
            if (!this.value) {
                showFieldError('service', 'Vui lòng chọn dịch vụ!');
            }
        });
        
        dateInput.addEventListener('change', function() {
            clearFieldError('date');
            if (!this.value) {
                showFieldError('date', 'Vui lòng chọn ngày!');
            } else {
                // Validate date is not in the past
                const selectedDate = new Date(this.value);
                const now = new Date();
                now.setHours(0, 0, 0, 0);
                
                if (selectedDate < now) {
                    showFieldError('date', 'Vui lòng chọn ngày trong tương lai!');
                }
            }
        });
        
        timeInput.addEventListener('change', function() {
            clearFieldError('time');
            if (!this.value) {
                showFieldError('time', 'Vui lòng chọn giờ!');
            }
        });
        
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const service = serviceInput.value;
            const date = dateInput.value;
            const time = timeInput.value;
            let hasError = false;
            
            // Clear previous errors
            clearFieldError('service');
            clearFieldError('date');
            clearFieldError('time');
            
            if (!service) {
                showFieldError('service', 'Vui lòng chọn dịch vụ!');
                hasError = true;
            }
            
            if (!date) {
                showFieldError('date', 'Vui lòng chọn ngày!');
                hasError = true;
            } else {
                const selectedDate = new Date(date);
                const now = new Date();
                now.setHours(0, 0, 0, 0);
                
                if (selectedDate < now) {
                    showFieldError('date', 'Vui lòng chọn ngày trong tương lai!');
                    hasError = true;
                }
            }
            
            if (!time) {
                showFieldError('time', 'Vui lòng chọn giờ!');
                hasError = true;
            }
            
            if (hasError) return;
            
            // Simulate booking
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Đặt lịch thành công! Chúng tôi sẽ liên hệ sớm nhất.');
                bookingForm.reset();
            }, 1500);
        });
    }
    
    // ============================================
    // CANCEL APPOINTMENT WITH 24H RULE
    // ============================================
    
    window.cancelAppointment = function(appointmentId, appointmentDateStr) {
        const now = new Date();
        const appointmentDate = new Date(appointmentDateStr);
        
        // Calculate time difference in hours
        const timeDiff = (appointmentDate - now) / (1000 * 60 * 60);
        
        // Check 24-hour rule
        if (timeDiff < 24) {
            showAlert('error', 'Không thể hủy lịch hẹn! Bạn chỉ được hủy trước 24h theo quy định.');
            return false;
        }
        
        if (confirm('Bạn có chắc chắn muốn hủy lịch hẹn này?')) {
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Hủy lịch hẹn thành công!');
                
                // Remove appointment from UI
                const row = document.getElementById(`appointment-${appointmentId}`);
                if (row) {
                    const tbody = row.parentNode;
                    row.remove();
                    
                    // Update badge count if exists
                    const allTab = document.querySelector('#all-tab .badge');
                    const upcomingTab = document.querySelector('#upcoming-tab .badge');
                    const cancelledTab = document.querySelector('#cancelled-tab .badge');
                    
                    if (upcomingTab && cancelledTab) {
                        let upcomingCount = parseInt(upcomingTab.textContent);
                        let cancelledCount = parseInt(cancelledTab.textContent);
                        upcomingTab.textContent = upcomingCount - 1;
                        cancelledTab.textContent = cancelledCount + 1;
                    }
                }
            }, 1000);
        }
        return true;
    };
    
    // ============================================
    // CONSULTATION FORM VALIDATION
    // ============================================
    
    const consultationForm = document.getElementById('consultationForm');
    if (consultationForm) {
        const fullNameInput = document.getElementById('fullName');
        const emailInput = document.getElementById('email');
        const phoneInput = document.getElementById('phone');
        const messageInput = document.getElementById('message');
        
        // Real-time validation
        fullNameInput.addEventListener('blur', function() {
            clearFieldError('fullName');
            if (!this.value.trim()) {
                showFieldError('fullName', 'Vui lòng nhập họ tên!');
            }
        });
        
        emailInput.addEventListener('blur', function() {
            clearFieldError('email');
            if (!this.value) {
                showFieldError('email', 'Vui lòng nhập email!');
            } else if (!validateEmail(this.value)) {
                showFieldError('email', 'Email không hợp lệ!');
            }
        });
        
        phoneInput.addEventListener('blur', function() {
            clearFieldError('phone');
            if (!this.value) {
                showFieldError('phone', 'Vui lòng nhập số điện thoại!');
            } else if (!validatePhone(this.value)) {
                showFieldError('phone', 'Số điện thoại không hợp lệ!');
            }
        });
        
        messageInput.addEventListener('blur', function() {
            clearFieldError('message');
            if (!this.value.trim()) {
                showFieldError('message', 'Vui lòng nhập nội dung!');
            } else if (this.value.trim().length < 10) {
                showFieldError('message', 'Nội dung phải có ít nhất 10 ký tự!');
            }
        });
        
        consultationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fullName = fullNameInput.value.trim();
            const email = emailInput.value.trim();
            const phone = phoneInput.value.trim();
            const message = messageInput.value.trim();
            let hasError = false;
            
            // Clear previous errors
            clearFieldError('fullName');
            clearFieldError('email');
            clearFieldError('phone');
            clearFieldError('message');
            
            if (!fullName) {
                showFieldError('fullName', 'Vui lòng nhập họ tên!');
                hasError = true;
            }
            
            if (!email) {
                showFieldError('email', 'Vui lòng nhập email!');
                hasError = true;
            } else if (!validateEmail(email)) {
                showFieldError('email', 'Email không hợp lệ!');
                hasError = true;
            }
            
            if (!phone) {
                showFieldError('phone', 'Vui lòng nhập số điện thoại!');
                hasError = true;
            } else if (!validatePhone(phone)) {
                showFieldError('phone', 'Số điện thoại không hợp lệ!');
                hasError = true;
            }
            
            if (!message) {
                showFieldError('message', 'Vui lòng nhập nội dung!');
                hasError = true;
            } else if (message.length < 10) {
                showFieldError('message', 'Nội dung phải có ít nhất 10 ký tự!');
                hasError = true;
            }
            
            if (hasError) return;
            
            // Simulate submission
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Gửi yêu cầu tư vấn thành công!');
                consultationForm.reset();
            }, 1500);
        });
    }
    
    // ============================================
    // COMPLAINT FORM VALIDATION
    // ============================================
    
    const complaintForm = document.getElementById('complaintForm');
    if (complaintForm) {
        const typeInput = document.getElementById('complaintType');
        const dateInput = document.getElementById('complaintDate');
        const contentInput = document.getElementById('complaintContent');
        
        // Initialize complaint date - max today
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('max', today);
        
        // Real-time validation
        typeInput.addEventListener('change', function() {
            clearFieldError('complaintType');
            if (!this.value) {
                showFieldError('complaintType', 'Vui lòng chọn loại khiếu nại!');
            }
        });
        
        dateInput.addEventListener('change', function() {
            clearFieldError('complaintDate');
            if (!this.value) {
                showFieldError('complaintDate', 'Vui lòng chọn ngày xảy ra sự việc!');
            }
        });
        
        contentInput.addEventListener('blur', function() {
            clearFieldError('complaintContent');
            if (!this.value.trim()) {
                showFieldError('complaintContent', 'Vui lòng nhập nội dung!');
            } else if (this.value.trim().length < 20) {
                showFieldError('complaintContent', 'Nội dung phải có ít nhất 20 ký tự!');
            }
        });
        
        complaintForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const type = typeInput.value;
            const date = dateInput.value;
            const content = contentInput.value.trim();
            let hasError = false;
            
            // Clear previous errors
            clearFieldError('complaintType');
            clearFieldError('complaintDate');
            clearFieldError('complaintContent');
            
            if (!type) {
                showFieldError('complaintType', 'Vui lòng chọn loại khiếu nại!');
                hasError = true;
            }
            
            if (!date) {
                showFieldError('complaintDate', 'Vui lòng chọn ngày xảy ra sự việc!');
                hasError = true;
            }
            
            if (!content) {
                showFieldError('complaintContent', 'Vui lòng nhập nội dung!');
                hasError = true;
            } else if (content.length < 20) {
                showFieldError('complaintContent', 'Nội dung phải có ít nhất 20 ký tự!');
                hasError = true;
            }
            
            if (hasError) return;
            
            // Simulate submission
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Gửi khiếu nại thành công! Chúng tôi sẽ xử lý sớm nhất.');
                complaintForm.reset();
            }, 1500);
        });
    }
    
    // ============================================
    // CHAT SYSTEM SIMULATION
    // ============================================
    
    // Initialize chat if exists
    const chatContainer = document.getElementById('chatContainer');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendMessage');
    
    if (chatContainer && chatInput && sendButton) {
        // Auto-scroll to bottom
        function scrollToBottom() {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Add message to chat
        function addMessage(content, isUser = true) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${isUser ? 'user' : 'staff'}`;
            messageDiv.innerHTML = `
                <div class="message-content">
                    <strong>${isUser ? 'Bạn' : 'Nhân viên'}:</strong>
                    <p>${content}</p>
                    <small class="message-time">${new Date().toLocaleTimeString('vi-VN')}</small>
                </div>
            `;
            chatContainer.appendChild(messageDiv);
            scrollToBottom();
        }
        
        // Send message
        function sendMessage() {
            const content = chatInput.value.trim();
            if (!content) return;
            
            // Add user message
            addMessage(content, true);
            chatInput.value = '';
            
            // Simulate staff response after 2 seconds
            setTimeout(() => {
                const responses = [
                    'Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất.',
                    'Chào bạn, có thể bạn cung cấp thêm thông tin không?',
                    'Đã nhận được tin nhắn của bạn. Chuyên gia đang kiểm tra.',
                    'Vâng, chúng tôi hiểu. Bạn có thể đặt lịch hẹn trực tiếp không?'
                ];
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                addMessage(randomResponse, false);
            }, 2000);
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Scroll to bottom on load
        setTimeout(scrollToBottom, 100);
    }
    
    // ============================================
    // FILTER & SEARCH FUNCTIONALITY
    // ============================================
    
    // Filter appointments (Admin)
    window.filterAppointments = function() {
        const searchInput = document.getElementById('appointmentSearch');
        const serviceFilter = document.getElementById('serviceFilter');
        const statusFilter = document.getElementById('statusFilter');
        const dateFromFilter = document.getElementById('dateFrom');
        const dateToFilter = document.getElementById('dateTo');
        
        if (!searchInput) return;
        
        const searchText = searchInput.value.toLowerCase();
        const serviceValue = serviceFilter ? serviceFilter.value : '';
        const statusValue = statusFilter ? statusFilter.value : '';
        const dateFrom = dateFromFilter ? dateFromFilter.value : '';
        const dateTo = dateToFilter ? dateToFilter.value : '';
        
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            let showRow = true;
            
            // Filter by customer name
            if (searchText) {
                const nameCell = row.cells[1];
                if (nameCell && !nameCell.textContent.toLowerCase().includes(searchText)) {
                    showRow = false;
                }
            }
            
            // Filter by service
            if (serviceValue) {
                const serviceCell = row.cells[3];
                if (serviceCell && !serviceCell.textContent.toLowerCase().includes(serviceValue)) {
                    showRow = false;
                }
            }
            
            // Filter by status
            if (statusValue) {
                const statusCell = row.cells[6];
                if (statusCell) {
                    const statusText = statusCell.textContent.toLowerCase();
                    const statusMap = {
                        'pending': 'chờ xác nhận',
                        'confirmed': 'đã xác nhận',
                        'processing': 'đang xử lý',
                        'completed': 'hoàn thành',
                        'cancelled': 'đã hủy'
                    };
                    if (!statusText.includes(statusMap[statusValue])) {
                        showRow = false;
                    }
                }
            }
            
            // Filter by date range
            if (dateFrom || dateTo) {
                const dateCell = row.cells[4];
                if (dateCell) {
                    const cellDate = dateCell.textContent.split(' ')[0];
                    const dateParts = cellDate.split('/');
                    const rowDate = new Date(dateParts[2], dateParts[1] - 1, dateParts[0]);
                    
                    if (dateFrom && rowDate < new Date(dateFrom)) {
                        showRow = false;
                    }
                    if (dateTo && rowDate > new Date(dateTo)) {
                        showRow = false;
                    }
                }
            }
            
            row.style.display = showRow ? '' : 'none';
        });
    };
    
    // Add filter event listeners
    const appointmentSearchInput = document.getElementById('appointmentSearch');
    const appointmentServiceFilter = document.getElementById('serviceFilter');
    const appointmentStatusFilter = document.getElementById('statusFilter');
    const appointmentDateFrom = document.getElementById('dateFrom');
    const appointmentDateTo = document.getElementById('dateTo');
    
    if (appointmentSearchInput) {
        appointmentSearchInput.addEventListener('input', window.filterAppointments);
    }
    if (appointmentServiceFilter) {
        appointmentServiceFilter.addEventListener('change', window.filterAppointments);
    }
    if (appointmentStatusFilter) {
        appointmentStatusFilter.addEventListener('change', window.filterAppointments);
    }
    if (appointmentDateFrom) {
        appointmentDateFrom.addEventListener('change', window.filterAppointments);
    }
    if (appointmentDateTo) {
        appointmentDateTo.addEventListener('change', window.filterAppointments);
    }
    
    // ============================================
    // ALERT FUNCTIONS
    // ============================================
    
    function showAlert(type, message) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.custom-alert');
        existingAlerts.forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `custom-alert alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: fadeInUp 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-radius: 8px;
        `;
        
        const icon = type === 'success' ? '<i class="fas fa-check-circle me-2"></i>' : 
                    type === 'error' ? '<i class="fas fa-exclamation-circle me-2"></i>' : 
                    '<i class="fas fa-info-circle me-2"></i>';
        
        alertDiv.innerHTML = `
            ${icon}${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // ============================================
    // LOADING SPINNER
    // ============================================
    
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingOverlay';
        loadingDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,255,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;
        
        loadingDiv.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-warning" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-muted fw-bold">Đang xử lý...</p>
            </div>
        `;
        
        document.body.appendChild(loadingDiv);
    }
    
    function hideLoading() {
        const loadingDiv = document.getElementById('loadingOverlay');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
    
    // ============================================
    // ADMIN FUNCTIONS
    // ============================================
    
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.admin-sidebar');
            if (sidebar) {
                sidebar.classList.toggle('show');
            }
        });
    }
    
    // Delete service confirmation
    window.deleteService = function(serviceId) {
        if (confirm('Bạn có chắc chắn muốn xóa dịch vụ này?')) {
            showLoading();
            setTimeout(() => {
                hideLoading();
                showAlert('success', 'Xóa dịch vụ thành công!');
                const row = document.getElementById(`service-${serviceId}`);
                if (row) {
                    row.remove();
                }
            }, 1000);
        }
    };
    
    // ============================================
    // SCROLL TO TOP BUTTON
    // ============================================
    
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollBtn.className = 'scroll-top-btn';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
        color: white;
        border: none;
        cursor: pointer;
        display: none;
        z-index: 999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        font-size: 1.2rem;
    `;
    
    document.body.appendChild(scrollBtn);
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollBtn.style.display = 'block';
        } else {
            scrollBtn.style.display = 'none';
        }
    });
    
    scrollBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // ============================================
    // SERVICE FILTER (Services page)
    // ============================================
    
    window.filterServices = function(category) {
        const items = document.querySelectorAll('.service-item');
        const buttons = document.querySelectorAll('.btn-outline-warning, .btn-warning');
        
        // Update button styles
        buttons.forEach(btn => {
            if ((btn.textContent.includes('Tất cả') && category === 'all') ||
                (btn.textContent.includes('Chăm sóc da') && category === 'skincare') ||
                (btn.textContent.includes('Tiêm Filler') && category === 'filler') ||
                (btn.textContent.includes('Phun thêu') && category === 'tattoo') ||
                (btn.textContent.includes('Triệt lông') && category === 'hair')) {
                btn.classList.remove('btn-outline-warning');
                btn.classList.add('btn-warning');
            } else if (btn.classList.contains('btn-warning') && !btn.classList.contains('active')) {
                btn.classList.remove('btn-warning');
                btn.classList.add('btn-outline-warning');
            }
        });
        
        // Filter items
        items.forEach(item => {
            if (category === 'all' || item.dataset.category === category) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    };
    
    // ============================================
    // INITIALIZE
    // ============================================
    
    console.log('DIVA Website loaded successfully!');
    console.log('Features loaded: Form Validation, Booking Logic, Chat System, Filter/Search');
});