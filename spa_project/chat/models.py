import os
import uuid

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone


def chat_attachment_upload_to(instance, filename):
    """Lưu file chat theo ngày với tên UUID để tránh lộ tên gốc."""
    ext = os.path.splitext(filename or "")[1].lower()
    date_path = timezone.now().strftime("%Y/%m/%d")
    return f"chat/attachments/{date_path}/{uuid.uuid4().hex}{ext}"


class ChatSession(models.Model):
    """Phiên chat giữa khách hàng và đội ngũ admin."""

    CUSTOMER_TYPE_CHOICES = [
        ("guest", "Khách vãng lai"),
        ("authenticated", "Khách đã đăng nhập"),
    ]

    STATUS_CHOICES = [
        ("open", "Đang mở"),
        ("closed", "Đã đóng"),
    ]

    chat_code = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Mã phiên chat",
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default="guest",
        db_index=True,
        verbose_name="Loại khách hàng",
    )
    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
        verbose_name="Khách hàng",
    )
    guest_session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        verbose_name="Khóa phiên khách vãng lai",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        db_index=True,
        verbose_name="Trạng thái",
    )
    source_page = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Trang bắt đầu chat",
    )
    last_message_preview = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Xem trước tin nhắn cuối",
    )
    last_sender_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Loại người gửi cuối",
    )
    admin_unread_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Số tin nhắn khách chưa đọc phía admin",
    )
    customer_unread_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Số tin nhắn admin chưa đọc phía khách",
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Thời gian tin nhắn cuối",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Thời gian đóng phiên chat",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        verbose_name = "Phiên chat"
        verbose_name_plural = "Phiên chat"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["chat_code"], name="chat_session_code_idx"),
            models.Index(fields=["customer", "status"], name="chat_customer_status_idx"),
            models.Index(fields=["customer_type", "status"], name="chat_type_status_idx"),
            models.Index(fields=["-last_message_at"], name="chat_last_message_idx"),
        ]

    def __str__(self):
        return f"{self.chat_code} - {self.get_customer_display_name()}"

    def save(self, *args, **kwargs):
        if not self.chat_code:
            self.chat_code = self.generate_chat_code()
        super().save(*args, **kwargs)

    def get_customer_display_name(self):
        """Tên hiển thị ở danh sách chat."""
        if self.customer and self.customer.full_name:
            return self.customer.full_name
        if self.customer and self.customer.phone:
            return self.customer.phone
        return "Khách vãng lai"

    def get_customer_contact(self):
        """Thông tin liên hệ phụ cho admin."""
        if self.customer and self.customer.phone:
            return self.customer.phone
        return ""

    def get_last_message_label(self):
        """Nhãn xem trước tin nhắn cuối."""
        return self.last_message_preview or "Chưa có tin nhắn"

    @classmethod
    def generate_chat_code(cls):
        """
        Sinh mã chat: CHAT + YYYYMMDD + 4 chữ số.

        Ví dụ: CHAT202604120001
        """
        prefix = "CHAT"
        today = timezone.now().strftime("%Y%m%d")
        full_prefix = f"{prefix}{today}"
        max_attempts = 100

        for attempt in range(max_attempts):
            with transaction.atomic():
                last_session = cls.objects.select_for_update().filter(
                    chat_code__startswith=full_prefix
                ).order_by("-chat_code").first()

                if last_session:
                    try:
                        last_number = int(last_session.chat_code[-4:])
                        new_number = last_number + 1 + attempt
                    except (TypeError, ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt

                new_code = f"{full_prefix}{new_number:04d}"
                if not cls.objects.filter(chat_code=new_code).exists():
                    return new_code

        return f"{full_prefix}{int(timezone.now().timestamp()) % 10000:04d}"


class ChatMessage(models.Model):
    """Tin nhắn trong một phiên chat."""

    SENDER_TYPE_CHOICES = [
        ("customer", "Khách hàng"),
        ("admin", "Nhân viên"),
        ("system", "Hệ thống"),
    ]

    MESSAGE_TYPE_CHOICES = [
        ("text", "Văn bản"),
        ("image", "Hình ảnh"),
        ("file", "Tệp tin"),
    ]

    STATUS_CHOICES = [
        ("sent", "Đã gửi"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Phiên chat",
    )
    sender_type = models.CharField(
        max_length=20,
        choices=SENDER_TYPE_CHOICES,
        db_index=True,
        verbose_name="Loại người gửi",
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_messages_sent",
        verbose_name="Người gửi",
    )
    sender_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Tên người gửi",
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default="text",
        verbose_name="Loại tin nhắn",
    )
    content = models.TextField(
        blank=True,
        verbose_name="Nội dung",
    )
    attachment = models.FileField(
        upload_to=chat_attachment_upload_to,
        null=True,
        blank=True,
        verbose_name="Tệp đính kèm",
    )
    attachment_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Tên file gốc",
    )
    attachment_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Kích thước file",
    )
    attachment_content_type = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Kiểu nội dung file",
    )
    client_message_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Mã tin nhắn phía client",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="sent",
        verbose_name="Trạng thái",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        verbose_name = "Tin nhắn chat"
        verbose_name_plural = "Tin nhắn chat"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["session", "created_at"], name="chat_message_session_idx"),
            models.Index(fields=["sender_type", "created_at"], name="chat_message_sender_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "client_message_id"],
                condition=models.Q(client_message_id__isnull=False),
                name="chat_message_client_unique",
            ),
        ]

    def __str__(self):
        return f"{self.session.chat_code} - {self.sender_name or self.sender_type}"

    def save(self, *args, **kwargs):
        if not self.sender_name and self.sender:
            if hasattr(self.sender, "customer_profile"):
                self.sender_name = self.sender.customer_profile.full_name or self.sender.username
            else:
                self.sender_name = self.sender.get_full_name() or self.sender.username

        if self.attachment:
            self.attachment_name = self.attachment_name or os.path.basename(self.attachment.name)
            self.attachment_size = self.attachment_size or getattr(self.attachment, "size", 0) or 0
            self.attachment_content_type = (
                self.attachment_content_type
                or getattr(self.attachment, "content_type", "")
                or self.attachment_content_type
            )

        super().save(*args, **kwargs)

    def is_image(self):
        return self.message_type == "image"

    def get_preview_text(self):
        if self.message_type == "image":
            return self.attachment_name or "Hình ảnh"
        if self.message_type == "file":
            return self.attachment_name or "Tệp đính kèm"
        return (self.content or "").strip()
