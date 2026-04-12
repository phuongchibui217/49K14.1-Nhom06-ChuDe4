from django.db import models, transaction
from django.contrib.auth.models import User


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

    def get_active_rooms(self):
        """Lấy danh sách phòng đang hoạt động"""
        return Room.objects.filter(is_active=True)


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

    # Mã lịch hẹn - dạng: APP + 4 digits (ví dụ: APP0001, APP0002, ...)
    appointment_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name='Mã lịch hẹn',
        help_text='Mã tự sinh: APP + số thứ tự'
    )
    customer = models.ForeignKey(
        'accounts.CustomerProfile',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Khách hàng'
    )
    service = models.ForeignKey(
        'spa_services.Service',
        on_delete=models.CASCADE,
        verbose_name='Dịch vụ'
    )
    room = models.ForeignKey(
        'appointments.Room',
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
        Sinh mã lịch hẹn tự động: APP + 4 chữ số
        Ví dụ: APP0001, APP0002, ...

        RACE CONDITION FIX:
        - Dùng transaction.atomic() + select_for_update()
        - Check trùng và tăng số cho đến khi tìm được mã trống
        """
        prefix = 'APP'
        max_attempts = 100

        for attempt in range(max_attempts):
            with transaction.atomic():
                # Lấy lịch hẹn cuối cùng (mã lớn nhất) và LOCK
                last_appointment = cls.objects.select_for_update().filter(
                    appointment_code__startswith=prefix
                ).order_by('-appointment_code').first()

                if last_appointment:
                    try:
                        last_number = int(last_appointment.appointment_code[-4:])
                        new_number = last_number + 1 + attempt
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt

                new_code = f'{prefix}{new_number:04d}'

                # Kiểm tra trùng
                if not cls.objects.filter(appointment_code=new_code).exists():
                    return new_code

        # Fallback: Dùng timestamp
        import time
        return f'{prefix}{int(time.time()) % 10000:04d}'
