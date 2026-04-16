from django.contrib.auth.models import User
from django.db import models, transaction


class ChatSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Dang mo'),
        ('PENDING', 'Cho xu ly'),
        ('CLOSED', 'Da dong'),
    ]

    customer = models.ForeignKey(
        'customers.CustomerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        verbose_name='Khach hang',
    )
    guest_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ten khach vang lai')
    guest_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='SDT khach vang lai')
    guest_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Email khach vang lai')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name='Trang thai')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Thoi diem bat dau phien')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Thoi diem dong phien')
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name='Thoi diem tin nhan cuoi')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thoi diem tao')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='Thoi diem cap nhat')

    chat_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Ma phien chat')
    customer_type = models.CharField(max_length=20, default='guest', verbose_name='Loai khach')
    guest_session_key = models.CharField(max_length=64, null=True, blank=True, unique=True, verbose_name='Khoa phien khach')
    source_page = models.CharField(max_length=255, blank=True, verbose_name='Trang bat dau chat')
    last_message_preview = models.CharField(max_length=255, blank=True, verbose_name='Xem truoc tin nhan cuoi')
    last_sender_type = models.CharField(max_length=20, blank=True, verbose_name='Loai nguoi gui cuoi')
    admin_unread_count = models.PositiveIntegerField(default=0, verbose_name='Tin chua doc phia admin')
    customer_unread_count = models.PositiveIntegerField(default=0, verbose_name='Tin chua doc phia khach')

    class Meta:
        db_table = 'chat_sessions'
        verbose_name = 'Phien chat'
        verbose_name_plural = 'Phien chat'
        ordering = ['-last_message_at', '-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['OPEN', 'PENDING', 'CLOSED']),
                name='chatsession_status_valid',
            ),
            models.CheckConstraint(
                check=models.Q(closed_at__isnull=True) | models.Q(closed_at__gte=models.F('started_at')),
                name='chatsession_closed_at_valid',
            ),
            models.CheckConstraint(
                check=models.Q(last_message_at__isnull=True) | models.Q(last_message_at__gte=models.F('started_at')),
                name='chatsession_last_message_at_valid',
            ),
        ]

    def __str__(self):
        return f"{self.chat_code or self.pk} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.chat_code:
            self.chat_code = self._generate_chat_code()
        super().save(*args, **kwargs)

    def get_customer_display_name(self):
        if self.customer and self.customer.full_name:
            return self.customer.full_name
        if self.customer and self.customer.phone:
            return self.customer.phone
        if self.guest_name:
            return self.guest_name
        return 'Khach vang lai'

    def get_customer_contact(self):
        if self.customer and self.customer.phone:
            return self.customer.phone
        return self.guest_phone or ''

    def get_last_message_label(self):
        return self.last_message_preview or 'Chua co tin nhan'

    @classmethod
    def _generate_chat_code(cls):
        prefix = 'CHAT'
        for attempt in range(100):
            with transaction.atomic():
                last = cls.objects.select_for_update().filter(
                    chat_code__startswith=prefix,
                ).order_by('-id').first()
                if last and last.chat_code:
                    try:
                        new_number = int(last.chat_code[len(prefix):]) + 1 + attempt
                    except (TypeError, ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt
                new_code = f'{prefix}{new_number:04d}'
                if not cls.objects.filter(chat_code=new_code).exists():
                    return new_code
        import time
        return f'{prefix}{int(time.time()) % 10000:04d}'


class ChatMessage(models.Model):
    SENDER_TYPE_CHOICES = [
        ('CUSTOMER', 'Khach hang'),
        ('STAFF', 'Nhan vien'),
        ('SYSTEM', 'He thong'),
        ('customer', 'Khach hang (legacy)'),
        ('admin', 'Nhan vien (legacy)'),
        ('system', 'He thong (legacy)'),
    ]
    DELIVERY_STATUS_CHOICES = [
        ('SENT', 'Da gui'),
        ('DELIVERED', 'Da nhan'),
        ('READ', 'Da doc'),
        ('FAILED', 'That bai'),
        ('sent', 'Da gui (legacy)'),
    ]
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Van ban'),
        ('image', 'Hinh anh'),
        ('file', 'Tep tin'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Phien chat',
    )
    sender_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages_sent',
        verbose_name='Nguoi gui',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages_sent_legacy',
        verbose_name='Nguoi gui (legacy)',
    )
    sender_type = models.CharField(max_length=20, verbose_name='Loai nguoi gui')
    sender_name = models.CharField(max_length=200, blank=True, verbose_name='Ten nguoi gui')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text', verbose_name='Loai tin nhan')
    content = models.TextField(blank=True, null=True, verbose_name='Noi dung tin nhan')
    attachment_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='URL tep dinh kem')
    attachment = models.FileField(upload_to='chat/attachments/', null=True, blank=True, verbose_name='Tep dinh kem')
    attachment_name = models.CharField(max_length=255, blank=True, verbose_name='Ten file')
    attachment_size = models.PositiveBigIntegerField(default=0, verbose_name='Kich thuoc file')
    attachment_content_type = models.CharField(max_length=120, blank=True, verbose_name='Kieu file')
    client_message_id = models.CharField(max_length=64, null=True, blank=True, verbose_name='Ma tin nhan client')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Thoi diem gui')
    delivery_status = models.CharField(max_length=20, default='SENT', verbose_name='Trang thai gui')
    status = models.CharField(max_length=20, default='sent', verbose_name='Trang thai (legacy)')
    is_read = models.BooleanField(default=False, verbose_name='Da doc')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thoi diem tao')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='Thoi diem cap nhat')

    class Meta:
        db_table = 'chat_messages'
        verbose_name = 'Tin nhan chat'
        verbose_name_plural = 'Tin nhan chat'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f"Session #{self.session_id} - {self.sender_type}"

    def is_image(self):
        return self.message_type == 'image'

    def get_preview_text(self):
        if self.message_type == 'image':
            return self.attachment_name or 'Hinh anh'
        if self.message_type == 'file':
            return self.attachment_name or 'Tep dinh kem'
        return (self.content or '').strip()


class SessionStaff(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='session_staff',
        verbose_name='Phien chat',
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions_joined',
        verbose_name='Nhan vien',
    )
    join_at = models.DateTimeField(auto_now_add=True, verbose_name='Thoi diem tham gia')

    class Meta:
        db_table = 'session_staff'
        verbose_name = 'Nhan vien phien chat'
        verbose_name_plural = 'Nhan vien phien chat'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'staff'],
                name='sessionstaff_session_staff_unique',
            ),
        ]

    def __str__(self):
        return f"Session #{self.session_id} - Staff #{self.staff_id}"
