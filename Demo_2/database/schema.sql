-- ============================================
-- Database Schema for Viện Thẩm Mỹ DIVA
-- SQLite3 Database
-- ============================================

-- Enable Foreign Keys
PRAGMA foreign_keys = ON;

-- ============================================
-- TABLE: USERS (Authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_joined DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login DATETIME
);

-- ============================================
-- TABLE: PROFILES
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    full_name VARCHAR(200) NOT NULL,
    phone_number VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    avatar VARCHAR(500),
    loyalty_points DECIMAL(10, 2) DEFAULT 0.00,
    is_locked BOOLEAN DEFAULT FALSE,
    lock_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE: SERVICES (DichVu)
-- ============================================
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(12, 2) NOT NULL,
    duration_minutes INTEGER,
    category VARCHAR(100),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE: APPOINTMENTS (LichHen)
-- ============================================
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    staff_id INTEGER,
    service_id INTEGER NOT NULL,
    appointment_date DATETIME NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancelled_at DATETIME,
    cancellation_reason TEXT,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT
);

-- Status values: 'pending', 'confirmed', 'processing', 'completed', 'cancelled'

-- ============================================
-- TABLE: CONSULTATIONS (YeuCauTuVan)
-- ============================================
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(254),
    service_id INTEGER,
    skin_type VARCHAR(50),
    concerns TEXT,
    preferred_time VARCHAR(50),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    staff_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Status values: 'pending', 'processing', 'completed'

-- ============================================
-- TABLE: COMPLAINTS (KhieuNai)
-- ============================================
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER,
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(254),
    complaint_type VARCHAR(50) NOT NULL,
    related_service_id INTEGER,
    related_appointment_id INTEGER,
    content TEXT NOT NULL,
    expected_solution TEXT,
    incident_date DATE,
    attachment_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',
    staff_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (related_service_id) REFERENCES services(id) ON DELETE SET NULL,
    FOREIGN KEY (related_appointment_id) REFERENCES appointments(id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Complaint type values: 'service', 'appointment', 'staff', 'price', 'facility', 'billing', 'other'
-- Status values: 'pending', 'processing', 'completed'

-- ============================================
-- TABLE: CONVERSATIONS (HoiThoai)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    staff_id INTEGER,
    subject VARCHAR(200),
    status VARCHAR(50) DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Status values: 'open', 'closed', 'archived'

-- ============================================
-- TABLE: MESSAGES (TinNhan)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================
-- SAMPLE DATA (Dữ liệu mẫu)
-- ============================================

-- Insert Users
INSERT INTO users (username, email, password, first_name, last_name, is_staff, is_superuser) VALUES
('admin', 'admin@diva.vn', 'hashed_password_1', 'Admin', 'DIVA', TRUE, TRUE),
('nurse1', 'nurse1@diva.vn', 'hashed_password_2', 'Nguyễn Thị', 'Mai', TRUE, FALSE),
('nurse2', 'nurse2@diva.vn', 'hashed_password_3', 'Trần Văn', 'Hùng', TRUE, FALSE);

-- Insert Profiles
INSERT INTO profiles (user_id, full_name, phone_number, address, loyalty_points) VALUES
(1, 'Admin DIVA', '1900 1234', '123 Nguyễn Huệ, Q.1, TP.HCM', 0),
(2, 'Bs. Nguyễn Thị Mai', '0901 234 567', '123 Nguyễn Huệ, Q.1, TP.HCM', 500),
(3, 'Bs. Trần Văn Hùng', '0902 345 678', '123 Nguyễn Huệ, Q.1, TP.HCM', 500);

-- Insert Services
INSERT INTO services (code, name, description, price, duration_minutes, category, is_active) VALUES
('DV001', 'Chăm Sóc Da Chuyên Sâu', 'Điều trị mụn, tái tạo da, trẻ hóa da chuyên sâu', 1500000, 90, 'skincare', TRUE),
('DV002', 'Tiêm Filler', 'Tạo hình mũi, cằm, môi tự nhiên', 3000000, 60, 'filler', TRUE),
('DV003', 'Phun Thêu Môi & Mày', 'Kỹ thuật 3D tự nhiên, bền màu', 2500000, 120, 'tattoo', TRUE),
('DV004', 'Triệt Lông Vĩnh Viễn', 'Công nghệ Diode Laser hiện đại', 800000, 45, 'hair', TRUE),
('DV005', 'Tẩy Tế Bào Chết', 'Làm sạch sâu, tái tạo', 600000, 60, 'skincare', TRUE),
('DV006', 'Điều Trị Mụn Chuyên Sâu', 'Điều trị mụn viêm, mụn đầu đen', 1200000, 75, 'skincare', TRUE),
('DV007', 'Trẻ Hóa Da', 'Công nghệ RF, laser, tái tạo collagen', 2000000, 90, 'skincare', TRUE),
('DV008', 'Phun Môi Công Nghệ Mới', 'Môi căng bóng, màu tự nhiên', 1800000, 90, 'tattoo', TRUE),
('DV009', 'Triệt Lông Toàn Thân', 'Gói triệt lông toàn thân', 2500000, 90, 'hair', TRUE);

-- Insert Sample Appointments
INSERT INTO appointments (code, customer_id, service_id, appointment_date, notes, status) VALUES
('LH001', 2, 1, datetime('now', '+1 day'), 'Khách hàng mong muốn điều trị mụn', 'pending'),
('LH002', 3, 2, datetime('now', '+2 days'), NULL, 'confirmed'),
('LH003', 2, 3, datetime('now', '+3 days'), 'Phun thêu môi 3D', 'processing');

-- Insert Sample Consultations
INSERT INTO consultations (code, customer_name, customer_phone, customer_email, service_id, message, status) VALUES
('TV001', 'Nguyễn Thị Lan', '0912 345 678', 'lan.nguyen@email.com', 1, 'Tôi muốn tư vấn về liệu trình điều trị mụn', 'pending'),
('TV002', 'Trần Văn Nam', '0934 567 890', 'nam.tran@email.com', 2, 'Tôi muốn biết thêm về tiêm Filler mũi', 'processing');

-- Insert Sample Complaints
INSERT INTO complaints (code, customer_name, customer_phone, customer_email, complaint_type, content, status) VALUES
('KN001', 'Phạm Thị Hương', '0956 789 012', 'huong.pham@email.com', 'service', 'Dịch vụ không đạt như kỳ vọng', 'pending');