from django.db import models, transaction
from django.contrib.auth.models import User


class Room(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name='Mã phòng')
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên phòng')
    capacity = models.PositiveIntegerField(verbose_name='Sức chứa')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='Thời điểm cập nhật')

    class Meta:
        db_table = 'rooms'
        verbose_name = 'Phòng'
        verbose_name_plural = 'Phòng'
        ordering = ['code']
        constraints = [
            models.CheckConstraint(check=models.Q(capacity__gt=0), name='room_capacity_positive')
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xác nhận'),
        ('NOT_ARRIVED', 'Chưa đến'),
        ('ARRIVED', 'Đã đến'),
        ('COMPLETED', 'Đã hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PARTIAL', 'Thanh toán một phần'),
        ('PAID', 'Đã thanh toán'),
        ('REFUNDED', 'Đã hoàn tiền'),
    ]
    SOURCE_CHOICES = [
        ('DIRECT', 'Trực tiếp'),
        ('ONLINE', 'Đặt online'),
        ('PHONE', 'Điện thoại'),
        ('FACEBOOK', 'Facebook'),
        ('ZALO', 'Zalo'),
    ]

    appointment_code = models.CharField(max_length=10, unique=True, blank=True, verbose_name='Mã lịch hẹn')
    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE,
        related_name='appointments', verbose_name='Khách hàng'
    )
    service = models.ForeignKey(
        'spa_services.Service', on_delete=models.CASCADE, verbose_name='Dịch vụ'
    )
    service_variant = models.ForeignKey(
        'spa_services.ServiceVariant', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments', verbose_name='Gói dịch vụ'
    )
    room = models.ForeignKey(
        Room, on_delete=models.PROTECT, verbose_name='Phòng'
    )
    booker_name  = models.CharField(max_length=100, blank=True, default='', verbose_name='Tên người đặt')
    booker_phone = models.CharField(max_length=15,  blank=True, default='', verbose_name='SĐT người đặt')
    booker_email = models.CharField(max_length=255, blank=True, default='', verbose_name='Email người đặt')
    customer_name_snapshot = models.CharField(max_length=100, verbose_name='Tên khách (snapshot)')
    customer_phone_snapshot = models.CharField(max_length=15, blank=True, null=True, verbose_name='SĐT khách (snapshot)')
    customer_email_snapshot = models.CharField(max_length=255, blank=True, null=True, verbose_name='Email khách (snapshot)')
    appointment_date = models.DateField(db_index=True, verbose_name='Ngày hẹn')
    appointment_time = models.TimeField(verbose_name='Giờ bắt đầu')
    end_time = models.TimeField(verbose_name='Giờ kết thúc')
    duration_minutes = models.PositiveIntegerField(verbose_name='Thời lượng (phút)')
    guests = models.PositiveIntegerField(default=1, verbose_name='Số khách')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_ARRIVED', db_index=True, verbose_name='Trạng thái')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID', verbose_name='Trạng thái thanh toán')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='DIRECT', verbose_name='Nguồn đặt lịch')
    notes = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Ghi chú của khách')
    staff_notes = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Ghi chú nội bộ')
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='appointments_created', verbose_name='Người tạo'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='Thời điểm cập nhật')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm xóa')
    deleted_by_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments_deleted', verbose_name='Người xóa'
    )
    check_in_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm check-in')
    check_out_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm check-out')

    class Meta:
        db_table = 'appointments'
        verbose_name = 'Lịch hẹn'
        verbose_name_plural = 'Lịch hẹn'
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['appointment_code'], name='appt_code_idx'),
            models.Index(fields=['customer', 'appointment_date'], name='appt_customer_date_idx'),
            models.Index(fields=['status', 'appointment_date'], name='appt_status_date_idx'),
            models.Index(fields=['room', 'appointment_date'], name='appt_room_date_idx'),
            models.Index(fields=['source', 'status'], name='appt_source_status_idx'),
            models.Index(fields=['appointment_date', 'appointment_time'], name='appt_datetime_idx'),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(guests__gte=1), name='appointment_guests_positive'),
            models.CheckConstraint(check=models.Q(duration_minutes__gt=0), name='appointment_duration_positive'),
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('appointment_time')),
                name='appointment_end_time_after_start'
            ),
            models.CheckConstraint(
                check=models.Q(check_out_at__isnull=True) | models.Q(check_in_at__isnull=True) | models.Q(check_out_at__gte=models.F('check_in_at')),
                name='appointment_checkout_after_checkin'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['PENDING', 'NOT_ARRIVED', 'ARRIVED', 'COMPLETED', 'CANCELLED']),
                name='appointment_status_valid'
            ),
            models.CheckConstraint(
                check=models.Q(payment_status__in=['UNPAID', 'PARTIAL', 'PAID', 'REFUNDED']),
                name='appointment_payment_status_valid'
            ),
            models.CheckConstraint(
                check=models.Q(source__in=['DIRECT', 'ONLINE', 'PHONE', 'FACEBOOK', 'ZALO']),
                name='appointment_source_valid'
            ),
        ]

    # ------------------------------------------------------------------
    # Customer-facing status (khác với staff/internal status)
    # NOT_ARRIVED / ARRIVED → "Đã xác nhận" (spa đã xác nhận lịch)
    # PENDING               → "Chờ xác nhận"
    # COMPLETED             → "Hoàn thành"
    # CANCELLED             → "Đã hủy"
    # ------------------------------------------------------------------
    CUSTOMER_STATUS_LABELS = {
        'PENDING':     'Chờ xác nhận',
        'NOT_ARRIVED': 'Đã xác nhận',
        'ARRIVED':     'Đã xác nhận',
        'COMPLETED':   'Hoàn thành',
        'CANCELLED':   'Đã hủy',
    }
    # CSS key dùng trong template (class="status-badge status-<key>")
    CUSTOMER_STATUS_CSS = {
        'PENDING':     'pending',
        'NOT_ARRIVED': 'confirmed',
        'ARRIVED':     'confirmed',
        'COMPLETED':   'completed',
        'CANCELLED':   'cancelled',
    }

    @property
    def customer_status_label(self):
        """Label hiển thị cho khách hàng (không lộ trạng thái vận hành nội bộ)."""
        return self.CUSTOMER_STATUS_LABELS.get(self.status, self.get_status_display())

    @property
    def customer_status_css(self):
        """CSS key cho badge ở trang khách hàng."""
        return self.CUSTOMER_STATUS_CSS.get(self.status, 'pending')

    def __str__(self):
        return f"{self.appointment_code} - {self.customer_name_snapshot}"

    def save(self, *args, **kwargs):
        if not self.appointment_code:
            self.appointment_code = self._generate_code()
        if self.appointment_time and self.service and not self.duration_minutes:
            # Ưu tiên lấy từ variant nếu có, fallback về variant đầu tiên của service
            if self.service_variant:
                self.duration_minutes = self.service_variant.duration_minutes
            else:
                first_variant = self.service.variants.order_by('sort_order', 'duration_minutes').first()
                self.duration_minutes = first_variant.duration_minutes if first_variant else 60
        if self.appointment_time and self.duration_minutes and not self.end_time:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(datetime.today(), self.appointment_time)
            self.end_time = (start_dt + timedelta(minutes=self.duration_minutes)).time()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_code(cls):
        prefix = 'APP'
        for attempt in range(100):
            with transaction.atomic():
                last = cls.objects.select_for_update().filter(
                    appointment_code__startswith=prefix
                ).order_by('-appointment_code').first()
                if last:
                    try:
                        new_number = int(last.appointment_code[-4:]) + 1 + attempt
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt
                new_code = f'{prefix}{new_number:04d}'
                if not cls.objects.filter(appointment_code=new_code).exists():
                    return new_code
        import time
        return f'{prefix}{int(time.time()) % 10000:04d}'


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PARTIAL', 'Thanh toán một phần'),
        ('PAID', 'Đã thanh toán'),
        ('CANCELLED', 'Đã hủy'),
        ('REFUNDED', 'Đã hoàn tiền'),
    ]

    code = models.CharField(max_length=10, unique=True, blank=True, verbose_name='Mã hóa đơn')
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE,
        related_name='invoice', verbose_name='Lịch hẹn'
    )
    subtotal_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Tổng tiền trước chiết khấu')
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Số tiền chiết khấu')
    final_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='Thành tiền')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID', verbose_name='Trạng thái')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='invoices_created', verbose_name='Người tạo'
    )

    class Meta:
        db_table = 'invoices'
        verbose_name = 'Hóa đơn'
        verbose_name_plural = 'Hóa đơn'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=models.Q(subtotal_amount__gte=0), name='invoice_subtotal_non_negative'),
            models.CheckConstraint(check=models.Q(discount_amount__gte=0), name='invoice_discount_non_negative'),
            models.CheckConstraint(check=models.Q(final_amount__gte=0), name='invoice_final_non_negative'),
            models.CheckConstraint(
                check=models.Q(discount_amount__lte=models.F('subtotal_amount')),
                name='invoice_discount_lte_subtotal'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['UNPAID', 'PARTIAL', 'PAID', 'CANCELLED', 'REFUNDED']),
                name='invoice_status_valid'
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.appointment.appointment_code}"

    @classmethod
    def _generate_code(cls):
        prefix = 'INV'
        for attempt in range(100):
            with transaction.atomic():
                last = cls.objects.select_for_update().order_by('-id').first()
                if last and last.code and last.code.startswith(prefix):
                    try:
                        new_number = int(last.code[len(prefix):]) + 1 + attempt
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt
                new_code = f"{prefix}{new_number:05d}"
                if not cls.objects.filter(code=new_code).exists():
                    return new_code
        import time
        return f"{prefix}{int(time.time()) % 100000:05d}"


class InvoicePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Tiền mặt'),
        ('CARD', 'Thẻ'),
        ('BANK_TRANSFER', 'Chuyển khoản'),
        ('E_WALLET', 'Ví điện tử'),
    ]
    TRANSACTION_STATUS_CHOICES = [
        ('PENDING', 'Chờ xử lý'),
        ('SUCCESS', 'Thành công'),
        ('FAILED', 'Thất bại'),
        ('REFUNDED', 'Đã hoàn tiền'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='payments', verbose_name='Hóa đơn'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='Số tiền')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='Phương thức thanh toán')
    transaction_status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='SUCCESS', verbose_name='Trạng thái giao dịch')
    paid_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm thanh toán')
    recorded_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='payments_recorded', verbose_name='Người ghi nhận'
    )
    recorded_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='Mã giao dịch tham chiếu')
    note = models.CharField(max_length=500, blank=True, null=True, verbose_name='Ghi chú')

    class Meta:
        db_table = 'invoice_payments'
        verbose_name = 'Thanh toán'
        verbose_name_plural = 'Thanh toán'
        ordering = ['-paid_at']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='payment_amount_positive'),
            models.CheckConstraint(
                check=models.Q(payment_method__in=['CASH', 'CARD', 'BANK_TRANSFER', 'E_WALLET']),
                name='payment_method_valid'
            ),
            models.CheckConstraint(
                check=models.Q(transaction_status__in=['PENDING', 'SUCCESS', 'FAILED', 'REFUNDED']),
                name='payment_transaction_status_valid'
            ),
        ]

    def __str__(self):
        return f"{self.invoice.code} - {self.amount:,}đ"
