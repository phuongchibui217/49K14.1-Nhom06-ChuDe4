from django.db import models
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
