from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


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

    STATUS_CHOICES = [
        ('active', 'Đang hoạt động'),
        ('inactive', 'Ngừng hoạt động'),
    ]

    # Mapping category number to category code
    CATEGORY_MAP = {
        '1': 'skincare',
        '2': 'massage',
        '3': 'tattoo',
        '4': 'hair',
    }

    # Reverse mapping for display
    CATEGORY_DISPLAY_MAP = {
        'skincare': 1,
        'massage': 2,
        'tattoo': 3,
        'hair': 4,
        'nails': 5,
        'other': 6,
    }

    code = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='Mã dịch vụ')
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
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='Giá (VNĐ)'
    )
    duration_minutes = models.PositiveIntegerField(verbose_name='Thời lượng (phút)')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Trạng thái'
    )
    image = models.ImageField(upload_to='services/', null=True, blank=True, verbose_name='Hình ảnh')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services_created',
        verbose_name='Người tạo'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services_updated',
        verbose_name='Người cập nhật'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        verbose_name = 'Dịch vụ'
        verbose_name_plural = 'Dịch vụ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['code']),
            models.Index(fields=['-created_at']),
        ]

    def save(self, *args, **kwargs):
        # Generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Generate code if not provided
        if not self.code:
            self.code = self.generate_service_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_category_name(self):
        """Lấy tên danh mục dạng text"""
        return dict(self.CATEGORY_CHOICES).get(self.category, 'Khác')

    def get_category_number(self):
        """Lấy số thứ tự danh mục (cho frontend)"""
        return self.CATEGORY_DISPLAY_MAP.get(self.category, 1)

    @classmethod
    def generate_service_code(cls):
        """
        Sinh mã dịch vụ tự động theo rule: DV + số thứ tự 4 chữ số
        Ví dụ: DV0001, DV0002, ...
        """
        prefix = 'DV'

        # Get the last service code
        last_service = cls.objects.order_by('-id').first()

        if last_service and last_service.code and last_service.code.startswith(prefix):
            # Extract number from last code
            try:
                last_number = int(last_service.code[len(prefix):])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    def clean(self):
        """Validation logic"""
        # Validate name not only numbers
        if self.name and self.name.strip().isdigit():
            raise ValidationError({'name': 'Tên dịch vụ không hợp lệ'})

        # Validate name uniqueness (case-insensitive, ignore extra spaces)
        if self.name:
            normalized_name = ' '.join(self.name.strip().split())
            existing_services = Service.objects.filter(
                name__iexact=normalized_name
            )

            if self.pk:
                existing_services = existing_services.exclude(pk=self.pk)

            if existing_services.exists():
                raise ValidationError({'name': 'Dịch vụ đã tồn tại'})

        # Validate description
        if not self.description or not self.description.strip():
            raise ValidationError({'description': 'Vui lòng nhập mô tả dịch vụ'})

        # Validate price
        if self.price is None or self.price <= 0:
            raise ValidationError({'price': 'Giá dịch vụ không hợp lệ'})

        # Validate duration
        if self.duration_minutes is None or self.duration_minutes <= 0:
            raise ValidationError({'duration_minutes': 'Thời gian không hợp lệ'})

        # Validate status
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError({'status': 'Vui lòng chọn trạng thái dịch vụ'})

    def get_image_url(self):
        """Get image URL or default placeholder"""
        if self.image and self.image.name:
            return self.image.url
        return 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=100'


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


class Room(models.Model):
    """Phòng dịch vụ"""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Mã phòng'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Tên phòng'
    )
    capacity = models.PositiveIntegerField(
        default=1,
        verbose_name='Sức chứa (số khách cùng lúc)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Phòng'
        verbose_name_plural = 'Phòng'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Appointment(models.Model):
    """Lịch hẹn đặt dịch vụ"""
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('not_arrived', 'Chưa đến'),
        ('arrived', 'Đã đến'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Chưa thanh toán'),
        ('partial', 'Thanh toán một phần'),
        ('paid', 'Đã thanh toán'),
    ]

    SOURCE_CHOICES = [
        ('web', 'Khách đặt online'),
        ('admin', 'Lễ tân tạo'),
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
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Phòng'
    )
    appointment_date = models.DateField(
        verbose_name='Ngày hẹn'
    )
    appointment_time = models.TimeField(
        verbose_name='Giờ bắt đầu'
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Giờ kết thúc'
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Thời lượng (phút)'
    )
    guests = models.PositiveIntegerField(
        default=1,
        verbose_name='Số khách'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        verbose_name='Trạng thái thanh toán'
    )
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='web',
        verbose_name='Nguồn đặt lịch'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú của khách hàng'
    )
    staff_notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú của nhân viên'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments_created',
        verbose_name='Người tạo'
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
            models.Index(fields=['room', 'appointment_date']),
            models.Index(fields=['source', 'status']),
        ]

    def __str__(self):
        return f"{self.appointment_code} - {self.customer.full_name} - {self.service.name}"

    def save(self, *args, **kwargs):
        # Generate appointment code
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

        # Auto calculate duration and end_time
        if self.appointment_time and self.service:
            if not self.duration_minutes:
                self.duration_minutes = self.service.duration_minutes
            
            # Calculate end_time
            if self.duration_minutes:
                from datetime import datetime, timedelta
                start_dt = datetime.combine(datetime.today(), self.appointment_time)
                end_dt = start_dt + timedelta(minutes=self.duration_minutes)
                self.end_time = end_dt.time()

        super().save(*args, **kwargs)

    def get_end_time_display(self):
        """Get end time as string"""
        if self.end_time:
            return self.end_time.strftime('%H:%M')

        # Get duration - fallback to service duration if not set
        duration = self.duration_minutes
        if duration is None and hasattr(self, 'service'):
            duration = self.service.duration_minutes

        # Calculate from duration
        if self.appointment_time and duration:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(datetime.today(), self.appointment_time)
            end_dt = start_dt + timedelta(minutes=duration)
            return end_dt.strftime('%H:%M')
        return ''


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


class Complaint(models.Model):
    """
    Khiếu nại từ khách hàng
    
    Hỗ trợ các loại: Khiếu nại, Góp ý, Hỏi đáp
    """
    COMPLAINT_TYPE_CHOICES = [
        ('complaint', 'Khiếu nại'),
        ('feedback', 'Góp ý'),
        ('inquiry', 'Hỏi đáp'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ]

    STATUS_CHOICES = [
        ('new', 'Mới tạo'),
        ('pending', 'Chờ tiếp nhận'),
        ('assigned', 'Đã tiếp nhận'),
        ('processing', 'Đang xử lý'),
        ('waiting_customer', 'Chờ khách phản hồi'),
        ('resolved', 'Đã hoàn thành'),
        ('closed', 'Đã đóng'),
    ]

    # Mã khiếu nại tự sinh
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name='Mã khiếu nại'
    )
    # Khách hàng (nếu đã đăng nhập)
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name='Khách hàng'
    )
    # Thông tin liên hệ (có thể khác với thông tin khách hàng)
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
    # Nội dung khiếu nại
    title = models.CharField(
        max_length=200,
        verbose_name='Tiêu đề khiếu nại'
    )
    content = models.TextField(
        verbose_name='Nội dung khiếu nại'
    )
    complaint_type = models.CharField(
        max_length=20,
        choices=COMPLAINT_TYPE_CHOICES,
        default='complaint',
        verbose_name='Loại khiếu nại'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Mức độ ưu tiên'
    )
    # Thông tin liên quan
    incident_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ngày xảy ra vấn đề'
    )
    appointment_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Mã lịch hẹn liên quan'
    )
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Dịch vụ liên quan'
    )
    expected_solution = models.TextField(
        blank=True,
        verbose_name='Giải pháp mong muốn'
    )
    # Xử lý
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Trạng thái'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        verbose_name='Người phụ trách'
    )
    resolution = models.TextField(
        blank=True,
        verbose_name='Kết quả xử lý'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày hoàn thành'
    )
    # Thời gian
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lần cuối'
    )

    class Meta:
        verbose_name = 'Khiếu nại'
        verbose_name_plural = 'Khiếu nại'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['complaint_type', 'status']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_complaint_code()
        super().save(*args, **kwargs)

    @classmethod
    def generate_complaint_code(cls):
        """Sinh mã khiếu nại: KN + 6 chữ số (KN000001)"""
        prefix = 'KN'
        last_complaint = cls.objects.order_by('-id').first()
        if last_complaint and last_complaint.code and last_complaint.code.startswith(prefix):
            try:
                last_number = int(last_complaint.code[len(prefix):])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        return f"{prefix}{new_number:06d}"

    def get_status_badge_class(self):
        """Trả về CSS class cho badge trạng thái"""
        status_classes = {
            'new': 'badge-new',
            'pending': 'badge-pending',
            'assigned': 'badge-assigned',
            'processing': 'badge-processing',
            'waiting_customer': 'badge-warning',
            'resolved': 'badge-success',
            'closed': 'badge-secondary',
        }
        return status_classes.get(self.status, 'badge-secondary')


class ComplaintReply(models.Model):
    """
    Phản hồi khiếu nại
    
    Lưu lịch sử phản hồi từ cả khách hàng và nhân viên
    """
    SENDER_ROLE_CHOICES = [
        ('customer', 'Khách hàng'),
        ('staff', 'Nhân viên CSKH'),
        ('manager', 'Quản lý'),
    ]

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name='Khiếu nại'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Người gửi'
    )
    sender_role = models.CharField(
        max_length=20,
        choices=SENDER_ROLE_CHOICES,
        default='staff',
        verbose_name='Vai trò người gửi'
    )
    sender_name = models.CharField(
        max_length=200,
        verbose_name='Tên người gửi',
        help_text='Lưu để hiển thị khi user bị xóa'
    )
    message = models.TextField(
        verbose_name='Nội dung phản hồi'
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name='Ghi chú nội bộ',
        help_text='Nếu true, khách hàng không thấy'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian'
    )

    class Meta:
        verbose_name = 'Phản hồi khiếu nại'
        verbose_name_plural = 'Phản hồi khiếu nại'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['complaint', 'created_at']),
        ]

    def __str__(self):
        return f"Phản hồi {self.complaint.code} - {self.sender_name}"

    def save(self, *args, **kwargs):
        # Lưu tên người gửi để hiển thị khi user bị xóa
        if not self.sender_name and self.sender:
            if hasattr(self.sender, 'customer_profile'):
                self.sender_name = self.sender.customer_profile.full_name
            else:
                self.sender_name = self.sender.get_full_name() or self.sender.username
        super().save(*args, **kwargs)


class ComplaintHistory(models.Model):
    """
    Lịch sử thay đổi khiếu nại
    
    Ghi nhận mọi thay đổi: trạng thái, người phụ trách, v.v.
    """
    ACTION_CHOICES = [
        ('created', 'Tạo khiếu nại'),
        ('status_changed', 'Đổi trạng thái'),
        ('assigned', 'Phân công'),
        ('took_ownership', 'Nhận xử lý'),
        ('replied', 'Phản hồi'),
        ('resolved', 'Hoàn thành'),
        ('closed', 'Đóng'),
        ('reopened', 'Mở lại'),
    ]

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Khiếu nại'
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Hành động'
    )
    old_value = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Giá trị cũ'
    )
    new_value = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Giá trị mới'
    )
    note = models.TextField(
        blank=True,
        verbose_name='Ghi chú'
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Người thực hiện'
    )
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian'
    )

    class Meta:
        verbose_name = 'Lịch sử khiếu nại'
        verbose_name_plural = 'Lịch sử khiếu nại'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['complaint', '-performed_at']),
        ]

    def __str__(self):
        return f"{self.complaint.code} - {self.get_action_display()}"

    @classmethod
    def log(cls, complaint, action, old_value='', new_value='', note='', performed_by=None):
        """Helper method để tạo log"""
        return cls.objects.create(
            complaint=complaint,
            action=action,
            old_value=old_value,
            new_value=new_value,
            note=note,
            performed_by=performed_by
        )


# Giữ lại SupportRequest để tương thích ngược với dữ liệu cũ
class SupportRequest(models.Model):
    """
    Góp ý/Khiếu nại/Phản hồi (DEPRECATED - dùng Complaint thay thế)
    
    Model này được giữ lại để tương thích với dữ liệu cũ.
    Sử dụng Complaint cho các tính năng mới.
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
        verbose_name='Đồng ý xử lý thông tin'
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
        verbose_name = 'Góp ý/Khiếu nại (Cũ)'
        verbose_name_plural = 'Góp ý/Khiếu nại (Cũ)'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['support_type', 'status']),
            models.Index(fields=['appointment_code']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_support_type_display()}"