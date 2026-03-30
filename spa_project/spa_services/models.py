from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Service(models.Model):
    """
    Dịch vụ spa

    INDEXES & CONSTRAINTS:
    - code: UNIQUE - mã dịch vụ không trùng
    - slug: UNIQUE - cho URL thân thiện SEO
    - category: INDEX - filter theo danh mục (rất hay dùng)
    - status: INDEX - filter theo trạng thái active/inactive
    - name: INDEX (giản lược) - hỗ trợ search tên dịch vụ
    - created_at: INDEX (descending) - sắp xếp mới nhất trước

    DATABASE CONSTRAINTS:
    - price >= 0: Đảm bảo giá không âm
    - duration_minutes > 0: Thời lượng phải dương
    """
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

    code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Mã dịch vụ',
        help_text='Mã dịch vụ tự sinh (DV0001, DV0002, ...)'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Tên dịch vụ',
        help_text='Tên dịch vụ, tối đa 200 ký tự'
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name='Slug',
        help_text='URL thân thiện cho SEO'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='skincare',
        verbose_name='Danh mục',
        db_index=True,  # INDEX: Filter theo danh mục rất hay dùng
    )
    short_description = models.CharField(max_length=300, blank=True, verbose_name='Mô tả ngắn')
    description = models.TextField(verbose_name='Mô tả chi tiết')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='Giá (VNĐ)'
    )
    duration_minutes = models.PositiveIntegerField(
        verbose_name='Thời lượng (phút)',
        help_text='Thời gian thực hiện dịch vụ (phút)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Trạng thái',
        db_index=True,  # INDEX: Filter active/inactive
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
            # Index cho slug (URL lookup)
            models.Index(fields=['slug'], name='service_slug_idx'),
            # Index cho active status (filter chính)
            models.Index(fields=['is_active'], name='service_active_idx'),
            # Index cho code (lookup nhanh)
            models.Index(fields=['code'], name='service_code_idx'),
            # Index cho created_at descending (sắp xếp mới nhất)
            models.Index(fields=['-created_at'], name='service_created_idx'),
            # Index cho tên dịch vụ (search)
            models.Index(fields=['name'], name='service_name_idx'),
            # COMPOSITE INDEX: category + status (filter theo danh mục và trạng thái)
            models.Index(fields=['category', 'status'], name='service_category_status_idx'),
        ]
        constraints = [
            # Đảm bảo giá không âm (database-level)
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='service_price_non_negative'
            ),
            # Đảm bảo thời lượng dương
            models.CheckConstraint(
                check=models.Q(duration_minutes__gt=0),
                name='service_duration_positive'
            ),
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

        RACE CONDITION FIX:
        - Dùng transaction.atomic() để đảm bảo atomicity
        - Dùng select_for_update() để lock row (không cho request khác đọc cùng lúc)
        - Nếu code đã tồn tại thì tăng số tiếp cho đến khi tìm được code trống

        GIẢI THÍCH SELECT_FOR_UPDATE:
        - Khi 2 request cùng lúc gọi hàm này, request đầu tiên sẽ lock row
        - Request thứ 2 phải đợi request 1 commit xong mới được đọc
        - Nhờ đó tránh sinh trùng mã
        """
        prefix = 'DV'
        max_attempts = 100  # Số lần thử tối đa (tránh infinite loop)

        for attempt in range(max_attempts):
            with transaction.atomic():
                # Lấy bản ghi cuối cùng và LOCK nó
                # select_for_update() sẽ block các request khác cho đến khi transaction này xong
                last_service = cls.objects.select_for_update().order_by('-id').first()

                if last_service and last_service.code and last_service.code.startswith(prefix):
                    try:
                        last_number = int(last_service.code[len(prefix):])
                        new_number = last_number + 1 + attempt  # +attempt để tránh trùng nếu có lỗi trước đó
                    except (ValueError, IndexError):
                        new_number = 1 + attempt
                else:
                    new_number = 1 + attempt

                new_code = f"{prefix}{new_number:04d}"

                # Kiểm tra xem code đã tồn tại chưa
                # (có thể do request trước đã tạo nhưng chưa commit)
                if not cls.objects.filter(code=new_code).exists():
                    return new_code

        # Fallback: Nếu vẫn không tìm được, dùng timestamp để đảm bảo unique
        import time
        return f"{prefix}{int(time.time()) % 100000:05d}"

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
