from django.db import models


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


# Create your models here.
