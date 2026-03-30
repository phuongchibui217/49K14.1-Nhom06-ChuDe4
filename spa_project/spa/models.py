from django.db import models, transaction
from django.contrib.auth.models import User


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
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
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
    """
    Lịch hẹn đặt dịch vụ
    
    INDEXES & CONSTRAINTS:
    - appointment_code: UNIQUE - mã lịch hẹn không trùng
    - appointment_date: INDEX - filter theo ngày (quan trọng nhất)
    - status: INDEX - filter theo trạng thái
    - room + appointment_date: COMPOSITE - check phòng trống
    - customer + appointment_date: COMPOSITE - xem lịch sử khách
    - source + status: COMPOSITE - filter yêu cầu từ web
    
    DATABASE CONSTRAINTS:
    - guests > 0: Số khách phải dương
    """
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
        verbose_name='Mã lịch hẹn',
        help_text='Mã tự sinh: APP + ngày + số thứ tự'
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
        verbose_name='Ngày hẹn',
        db_index=True,  # INDEX: Filter theo ngày - quan trọng nhất
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
        verbose_name='Số khách',
        help_text='Số lượng khách tham gia dịch vụ'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái',
        db_index=True,  # INDEX: Filter theo trạng thái
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
            # Index cho mã lịch hẹn (lookup nhanh)
            models.Index(fields=['appointment_code'], name='appt_code_idx'),
            # COMPOSITE: customer + date - xem lịch sử khách hàng
            models.Index(fields=['customer', 'appointment_date'], name='appt_customer_date_idx'),
            # COMPOSITE: status + date - filter lịch theo trạng thái và ngày
            models.Index(fields=['status', 'appointment_date'], name='appt_status_date_idx'),
            # COMPOSITE: room + date - check phòng trống theo ngày
            models.Index(fields=['room', 'appointment_date'], name='appt_room_date_idx'),
            # COMPOSITE: source + status - filter yêu cầu từ web
            models.Index(fields=['source', 'status'], name='appt_source_status_idx'),
            # COMPOSITE: date + time - sắp xếp và filter theo thời gian
            models.Index(fields=['appointment_date', 'appointment_time'], name='appt_datetime_idx'),
            # Index cho created_at (sắp xếp theo ngày tạo)
            models.Index(fields=['-created_at'], name='appt_created_idx'),
        ]
        constraints = [
            # Đảm bảo số khách > 0
            models.CheckConstraint(
                check=models.Q(guests__gte=1),
                name='appointment_guests_at_least_one'
            ),
        ]

    def __str__(self):
        return f"{self.appointment_code} - {self.customer.full_name} - {self.service.name}"

    def save(self, *args, **kwargs):
        # Generate appointment code (với race condition protection)
        if not self.appointment_code:
            self.appointment_code = self.generate_appointment_code()

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

    @classmethod
    def generate_appointment_code(cls):
        """
        Sinh mã lịch hẹn tự động: APP + YYYYMMDD + 4 chữ số
        Ví dụ: APP202403150001, APP202403150002, ...
        
        RACE CONDITION FIX:
        - Dùng transaction.atomic() + select_for_update()
        - Check trùng và tăng số cho đến khi tìm được mã trống
        """
        from django.utils import timezone
        
        prefix = 'APP'
        today = timezone.now().strftime('%Y%m%d')
        full_prefix = f'{prefix}{today}'
        max_attempts = 100
        
        for attempt in range(max_attempts):
            with transaction.atomic():
                # Lấy lịch hẹn cuối cùng của ngày hôm nay và LOCK
                last_appointment = cls.objects.select_for_update().filter(
                    appointment_code__startswith=full_prefix
                ).order_by('-appointment_code').first()
                
                if last_appointment:
                    try:
                        last_number = int(last_appointment.appointment_code[-4:])
                        new_number = last_number + 1 + attempt
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt
                
                new_code = f'{full_prefix}{new_number:04d}'
                
                # Kiểm tra trùng
                if not cls.objects.filter(appointment_code=new_code).exists():
                    return new_code
        
        # Fallback: Dùng timestamp
        import time
        return f'{full_prefix}{int(time.time()) % 10000:04d}'


class Complaint(models.Model):
    """
    Khiếu nại từ khách hàng
    
    Hỗ trợ các loại: Khiếu nại, Góp ý, Hỏi đáp
    """
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
        """
        Sinh mã khiếu nại: KN + 6 chữ số (KN000001)
        
        RACE CONDITION FIX:
        - Dùng transaction.atomic() + select_for_update()
        - Check trùng và tăng số cho đến khi tìm được mã trống
        """
        prefix = 'KN'
        max_attempts = 100
        
        for attempt in range(max_attempts):
            with transaction.atomic():
                # Lấy khiếu nại cuối cùng và LOCK
                last_complaint = cls.objects.select_for_update().order_by('-id').first()
                
                if last_complaint and last_complaint.code and last_complaint.code.startswith(prefix):
                    try:
                        last_number = int(last_complaint.code[len(prefix):])
                        new_number = last_number + 1 + attempt
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt
                
                new_code = f"{prefix}{new_number:06d}"
                
                # Kiểm tra trùng
                if not cls.objects.filter(code=new_code).exists():
                    return new_code
        
        # Fallback: Dùng timestamp
        import time
        return f"{prefix}{int(time.time()) % 1000000:06d}"

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


