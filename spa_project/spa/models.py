from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Service(models.Model):
    """Dịch vụ spa"""
    CATEGORY_CHOICES = [
        ('skincare', 'Chăm sóc da'),
        ('massage', 'Massage'),
        ('tattoo', 'Phun thêu'),
        ('hair', 'Triệt lông'),
        ('nails', 'Làm móng'),
        ('other', 'Khác'),
    ]

    name = models.CharField(max_length=200, verbose_name='Tên dịch vụ')
    slug = models.SlugField(max_length=250, unique=True, verbose_name='Slug')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='skincare',
        verbose_name='Danh mục'
    )
    short_description = models.CharField(max_length=300, blank=True, verbose_name='Mô tả ngắn')
    description = models.TextField(verbose_name='Mô tả chi tiết')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Giá (VNĐ)')
    duration_minutes = models.PositiveIntegerField(verbose_name='Thời lượng (phút)')
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name='Hình ảnh')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        verbose_name = 'Dịch vụ'
        verbose_name_plural = 'Dịch vụ'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_category_name(self):
        """Lấy tên danh mục dạng text"""
        return dict(self.CATEGORY_CHOICES).get(self.category, 'Khác')


class CustomerProfile(models.Model):
    """
    Profile khách hàng - mở rộng Django User

    NOTE: Login bằng số điện thoại
    Hiện tại: Username = Phone (để đơn giản)
    Phase sau: Có thể custom User model hoặc dùng authentication backend
    """
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
        ('O', 'Khác'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name='User'
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Số điện thoại',
        help_text='Dùng cho login (username = phone)'
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name='Họ và tên đầy đủ',
        default=''
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name='Giới tính'
    )
    dob = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ngày sinh'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Địa chỉ'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày đăng ký'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Khách hàng'
        verbose_name_plural = 'Khách hàng'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.phone}"

    def get_appointments_count(self):
        """Đếm số lịch hẹn của khách hàng"""
        return self.appointments.count()


class Appointment(models.Model):
    """Lịch hẹn đặt dịch vụ"""
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
        ('no_show', 'Không đến'),
    ]

    # Mã lịch hẹn - dạng: APP + YYYYMMDD + 4 digits (ví dụ: APP202403150001)
    appointment_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name='Mã lịch hẹn'
    )
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Khách hàng'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name='Dịch vụ'
    )
    appointment_date = models.DateField(
        verbose_name='Ngày hẹn'
    )
    appointment_time = models.TimeField(
        verbose_name='Giờ hẹn'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú của khách hàng'
    )
    staff_notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú của nhân viên'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày đặt lịch'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Lịch hẹn'
        verbose_name_plural = 'Lịch hẹn'
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['appointment_code']),
            models.Index(fields=['customer', 'appointment_date']),
            models.Index(fields=['status', 'appointment_date']),
        ]

    def __str__(self):
        return f"{self.appointment_code} - {self.customer.full_name} - {self.service.name}"

    def save(self, *args, **kwargs):
        if not self.appointment_code:
            from django.utils import timezone
            today = timezone.now().strftime('%Y%m%d')
            last_appointment = Appointment.objects.filter(
                appointment_code__startswith=f'APP{today}'
            ).order_by('-appointment_code').first()

            if last_appointment:
                last_number = int(last_appointment.appointment_code[-4:])
                new_number = last_number + 1
            else:
                new_number = 1

            self.appointment_code = f'APP{today}{new_number:04d}'
        super().save(*args, **kwargs)


class ConsultationRequest(models.Model):
    """Yêu cầu tư vấn từ form đăng ký"""
    REQUEST_TYPE_CHOICES = [
        ('general', 'Tư vấn chung'),
        ('service', 'Tư vấn dịch vụ'),
        ('promotion', 'Hỏi về khuyến mãi'),
        ('other', 'Khác'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('contacted', 'Đã liên hệ'),
        ('resolved', 'Đã giải quyết'),
        ('cancelled', 'Đã hủy'),
    ]

    full_name = models.CharField(
        max_length=200,
        verbose_name='Họ và tên'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Số điện thoại'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='general',
        verbose_name='Loại yêu cầu'
    )
    content = models.TextField(
        verbose_name='Nội dung cần tư vấn',
        default=''
    )
    preferred_contact_time = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Thời gian liên hệ mong muốn',
        help_text='Ví dụ: Buổi sáng, Chiều, T2-T6...'
    )
    agree_contact = models.BooleanField(
        default=False,
        verbose_name='Đồng ý được liên hệ'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái'
    )
    staff_notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú xử lý'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày gửi'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Yêu cầu tư vấn'
        verbose_name_plural = 'Yêu cầu tư vấn'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_request_type_display()}"


class SupportRequest(models.Model):
    """
    Góp ý/Khiếu nại/Phản hồi

    Áp dụng cho khách hàng đã sử dụng dịch vụ hoặc có thắc mắc
    """
    SUPPORT_TYPE_CHOICES = [
        ('feedback', 'Góp ý'),
        ('complaint', 'Khiếu nại'),
        ('inquiry', 'Hỏi đáp'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết'),
        ('rejected', 'Đã từ chối'),
    ]

    full_name = models.CharField(
        max_length=200,
        verbose_name='Họ và tên'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Số điện thoại'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    support_type = models.CharField(
        max_length=20,
        choices=SUPPORT_TYPE_CHOICES,
        verbose_name='Loại yêu cầu'
    )
    support_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ngày xảy ra vấn đề',
        help_text='Nếu có'
    )
    appointment_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Mã lịch hẹn liên quan',
        help_text='Nếu vấn đề liên quan đến lịch hẹn cụ thể'
    )
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Dịch vụ liên quan'
    )
    content = models.TextField(
        verbose_name='Nội dung góp ý/khiếu nại',
        default=''
    )
    expected_solution = models.TextField(
        blank=True,
        verbose_name='Giải pháp mong muốn',
        help_text='Khách hàng muốn được giải quyết như thế nào'
    )
    agree_processing = models.BooleanField(
        default=False,
        verbose_name='Đồng意 xử lý thông tin'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái'
    )
    staff_notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú xử lý'
    )
    resolution = models.TextField(
        blank=True,
        verbose_name='Phương án giải quyết'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày gửi'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Góp ý/Khiếu nại'
        verbose_name_plural = 'Góp ý/Khiếu nại'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['support_type', 'status']),
            models.Index(fields=['appointment_code']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_support_type_display()}"