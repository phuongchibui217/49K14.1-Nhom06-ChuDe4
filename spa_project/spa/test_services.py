"""
Tests cho Services Layer - Logic nghiệp vụ quan trọng

Chạy test: python manage.py test spa.test_services

Mục đích:
- Đảm bảo validation hoạt động đúng
- Đảm bảo logic tạo lịch hẹn không bị lỗi
- Đảm bảo check phòng trống hoạt động
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date, time, timedelta

from .models import Service, CustomerProfile, Appointment, Room
from .services import (
    validate_appointment_date,
    validate_appointment_time,
    check_room_availability,
    calculate_end_time,
    validate_appointment_create,
)
from .service_services import (
    validate_service_name,
    validate_service_price,
    validate_service_duration,
    validate_service_data,
)


# =====================================================
# TEST: VALIDATE NGÀY GIỜ LỊCH HẸN
# =====================================================

class AppointmentDateValidationTest(TestCase):
    """
    Test validation ngày giờ đặt lịch
    
    QUAN TRỌNG: Ngày quá khứ không được phép đặt
    """
    
    def test_khong_cho_dat_lich_qua_khu(self):
        """Không cho đặt lịch ở ngày quá khứ"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Expect ValidationError khi đặt ngày quá khứ
        with self.assertRaises(ValidationError) as context:
            validate_appointment_date(yesterday)
        
        # Kiểm tra message lỗi có chứa từ "quá khứ"
        self.assertIn('quá khứ', str(context.exception.message).lower())
    
    def test_cho_phep_dat_lich_hom_nay(self):
        """Cho phép đặt lịch hôm nay"""
        today = timezone.now().date()
        
        # Không raise error khi đặt hôm nay
        try:
            validate_appointment_date(today)
        except ValidationError:
            self.fail("Không nên raise error khi đặt lịch hôm nay")
    
    def test_cho_phep_dat_lich_tuong_lai(self):
        """Cho phép đặt lịch trong tương lai"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Không raise error khi đặt tương lai
        try:
            validate_appointment_date(tomorrow)
        except ValidationError:
            self.fail("Không nên raise error khi đặt lịch tương lai")


class AppointmentTimeValidationTest(TestCase):
    """
    Test validation giờ đặt lịch
    
    QUAN TRỌNG: 
    - Đặt hôm nay phải trước ít nhất 30 phút
    - Giờ làm việc: 8:00 - 20:00
    """
    
    def test_gio_qua_som_sang_hom_nay(self):
        """Giờ quá sớm (trước 8:00) không được phép"""
        # Sử dụng ngày mai để tránh lỗi "30 phút trước"
        tomorrow = timezone.now().date() + timedelta(days=1)
        early_time = time(7, 0)  # 7:00 AM
        
        with self.assertRaises(ValidationError) as context:
            validate_appointment_time(early_time, tomorrow)
        
        self.assertIn('08:00', str(context.exception.message))
    
    def test_gio_qua_muon_toi_hom_nay(self):
        """Giờ quá muộn (sau 20:00) không được phép"""
        today = timezone.now().date()
        late_time = time(20, 30)  # 20:30
        
        with self.assertRaises(ValidationError) as context:
            validate_appointment_time(late_time, today)
        
        self.assertIn('20:00', str(context.exception.message))
    
    def test_gio_hop_le(self):
        """Giờ trong khung làm việc (8:00-20:00) được phép"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        valid_time = time(10, 0)  # 10:00 AM
        
        try:
            validate_appointment_time(valid_time, tomorrow)
        except ValidationError:
            self.fail("Giờ 10:00 nên được phép đặt")


# =====================================================
# TEST: CHECK PHÒNG TRỐNG
# =====================================================

class RoomAvailabilityTest(TestCase):
    """
    Test check phòng trống
    
    QUAN TRỌNG: Không cho đặt trùng phòng cùng khung giờ
    """
    
    def setUp(self):
        """Tạo dữ liệu test: service, room, customer, appointment"""
        # Tạo service
        self.service = Service.objects.create(
            name='Massage Test',
            slug='massage-test',
            price=100000,
            duration_minutes=60,
        )
        
        # Tạo room
        self.room = Room.objects.create(
            code='P001',
            name='Phòng Test 1',
            capacity=1,
        )
        
        # Tạo customer
        self.user = User.objects.create_user(username='0909123456')
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            phone='0909123456',
            full_name='Khách Test'
        )
        
        # Ngày mai (để tránh validation quá khứ)
        self.tomorrow = timezone.now().date() + timedelta(days=1)
    
    def test_phong_trong_khi_chua_co_lich(self):
        """Phòng trống khi chưa có lịch nào"""
        is_available, conflict, message = check_room_availability(
            room_code='P001',
            appointment_date=self.tomorrow,
            start_time=time(10, 0),
            duration_minutes=60
        )
        
        self.assertTrue(is_available)
        self.assertIsNone(conflict)
        self.assertEqual(message, '')
    
    def test_khong_cho_dat_trung_gio(self):
        """Không cho đặt trùng giờ với lịch đã có"""
        # Tạo lịch hẹn trước: 10:00 - 11:00
        Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            duration_minutes=60,
            status='pending'
        )
        
        # Thử đặt lịch trùng giờ: 10:30 - 11:30
        is_available, conflict, message = check_room_availability(
            room_code='P001',
            appointment_date=self.tomorrow,
            start_time=time(10, 30),
            duration_minutes=60
        )
        
        self.assertFalse(is_available)
        self.assertIsNotNone(conflict)
        self.assertIn('đã có lịch', message.lower())
    
    def test_cho_dat_gio_khac_cung_phong(self):
        """Cho đặt giờ khác cùng phòng"""
        # Tạo lịch hẹn: 10:00 - 11:00
        Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            duration_minutes=60,
            status='pending'
        )
        
        # Thử đặt lịch khác giờ: 14:00 - 15:00
        is_available, conflict, message = check_room_availability(
            room_code='P001',
            appointment_date=self.tomorrow,
            start_time=time(14, 0),
            duration_minutes=60
        )
        
        self.assertTrue(is_available)
    
    def test_lich_da_huy_khong_bi_tinh_trung(self):
        """Lịch đã hủy không bị tính là trùng"""
        # Tạo lịch hẹn đã hủy: 10:00 - 11:00
        Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            duration_minutes=60,
            status='cancelled'  # Đã hủy
        )
        
        # Thử đặt lịch cùng giờ
        is_available, conflict, message = check_room_availability(
            room_code='P001',
            appointment_date=self.tomorrow,
            start_time=time(10, 0),
            duration_minutes=60
        )
        
        # Phải available vì lịch cũ đã hủy
        self.assertTrue(is_available)
    
    def test_exclude_appointment_khi_sua_lich(self):
        """Khi sửa lịch, exclude lịch hiện tại khỏi check"""
        # Tạo lịch hẹn: 10:00 - 11:00
        appointment = Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            room=self.room,
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            duration_minutes=60,
            status='pending'
        )
        
        # Sửa lịch (giữ nguyên giờ) - phải cho phép
        is_available, conflict, message = check_room_availability(
            room_code='P001',
            appointment_date=self.tomorrow,
            start_time=time(10, 0),
            duration_minutes=60,
            exclude_appointment_code=appointment.appointment_code
        )
        
        # Phải available vì đang sửa chính lịch này
        self.assertTrue(is_available)


# =====================================================
# TEST: CALCULATE END TIME
# =====================================================

class CalculateEndTimeTest(TestCase):
    """Test tính giờ kết thúc"""
    
    def test_tinh_gio_ket_thuc(self):
        """Tính giờ kết thúc từ giờ bắt đầu + thời lượng"""
        start = time(10, 0)
        duration = 60
        
        end_time = calculate_end_time(start, duration)
        
        self.assertEqual(end_time.hour, 11)
        self.assertEqual(end_time.minute, 0)
    
    def test_tinh_gio_ket_thuc_90_phut(self):
        """Tính giờ kết thúc với 90 phút"""
        start = time(10, 30)
        duration = 90
        
        end_time = calculate_end_time(start, duration)
        
        self.assertEqual(end_time.hour, 12)
        self.assertEqual(end_time.minute, 0)


# =====================================================
# TEST: VALIDATE SERVICE DATA
# =====================================================

class ServiceValidationTest(TestCase):
    """
    Test validation dữ liệu dịch vụ
    
    QUAN TRỌNG: 
    - Tên không trùng
    - Giá không âm
    - Thời lượng hợp lệ
    """
    
    def test_ten_khong_duoc_trong(self):
        """Tên dịch vụ không được để trống"""
        is_valid, error = validate_service_name('')
        
        self.assertFalse(is_valid)
        self.assertIn('Vui lòng nhập', error)
    
    def test_ten_qua_ngan(self):
        """Tên dịch vụ quá ngắn (< 5 ký tự)"""
        is_valid, error = validate_service_name('Abc')
        
        self.assertFalse(is_valid)
        self.assertIn('ít nhất 5 ký tự', error)
    
    def test_ten_qua_dai(self):
        """Tên dịch vụ quá dài (> 200 ký tự)"""
        long_name = 'A' * 201
        is_valid, error = validate_service_name(long_name)
        
        self.assertFalse(is_valid)
        self.assertIn('200 ký tự', error)
    
    def test_ten_trung(self):
        """Tên dịch vụ bị trùng"""
        # Tạo service trước
        Service.objects.create(
            name='Massage Test Unique',
            slug='massage-test-unique',
            price=100000,
            duration_minutes=60,
        )
        
        # Thử tạo service cùng tên
        is_valid, error = validate_service_name('Massage Test Unique')
        
        self.assertFalse(is_valid)
        self.assertIn('đã tồn tại', error)
    
    def test_ten_hop_le(self):
        """Tên dịch vụ hợp lệ"""
        is_valid, error = validate_service_name('Massage Thư Giãn Đặc Biệt')
        
        self.assertTrue(is_valid)
        self.assertEqual(error, '')
    
    def test_gia_khong_hop_le(self):
        """Giá không hợp lệ (không phải số)"""
        is_valid, price, error = validate_service_price('abc')
        
        self.assertFalse(is_valid)
        self.assertEqual(price, 0)
        self.assertIn('không hợp lệ', error)
    
    def test_gia_am(self):
        """Giá âm không được phép"""
        is_valid, price, error = validate_service_price(-100000)
        
        self.assertFalse(is_valid)
        self.assertIn('không được âm', error)
    
    def test_gia_qua_lon(self):
        """Giá quá lớn không được phép"""
        is_valid, price, error = validate_service_price(1000000000)  # 1 tỷ
        
        self.assertFalse(is_valid)
        self.assertIn('999,999,999', error)
    
    def test_gia_hop_le(self):
        """Giá hợp lệ"""
        is_valid, price, error = validate_service_price(100000)
        
        self.assertTrue(is_valid)
        self.assertEqual(price, 100000)
        self.assertEqual(error, '')
    
    def test_thoi_luong_qua_ngan(self):
        """Thời lượng quá ngắn (< 5 phút)"""
        is_valid, duration, error = validate_service_duration(3)
        
        self.assertFalse(is_valid)
        self.assertIn('ít nhất 5 phút', error)
    
    def test_thoi_luong_qua_dai(self):
        """Thời lượng quá dài (> 480 phút)"""
        is_valid, duration, error = validate_service_duration(500)
        
        self.assertFalse(is_valid)
        self.assertIn('480 phút', error)
    
    def test_thoi_luong_hop_le(self):
        """Thời lượng hợp lệ"""
        is_valid, duration, error = validate_service_duration(60)
        
        self.assertTrue(is_valid)
        self.assertEqual(duration, 60)
        self.assertEqual(error, '')


# =====================================================
# TEST: VALIDATE FULL APPOINTMENT
# =====================================================

class FullAppointmentValidationTest(TestCase):
    """
    Test validate_appointment_create - tổng hợp tất cả validation
    
    QUAN TRỌNG: Hàm này gom tất cả validation vào một chỗ
    """
    
    def setUp(self):
        self.service = Service.objects.create(
            name='Service Test',
            slug='service-test',
            price=100000,
            duration_minutes=60,
        )
        self.room = Room.objects.create(
            code='P002',
            name='Phòng Test 2',
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)
    
    def test_validate_thanh_cong(self):
        """Validate thành công khi tất cả hợp lệ"""
        result = validate_appointment_create(
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            duration_minutes=60,
            room_code='P002'
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], [])
    
    def test_validate_that_bai_ngay_qua_khu(self):
        """Validate thất bại khi ngày quá khứ"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        result = validate_appointment_create(
            appointment_date=yesterday,
            appointment_time=time(10, 0),
            duration_minutes=60,
        )
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)