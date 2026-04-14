"""
Forms cho Service Management

File này chứa các forms cho:
- Tạo/cập nhật dịch vụ spa

Author: Spa ANA Team
"""

from django import forms
from PIL import Image

# Tạm import từ spa.models (CHƯA chuyển model trong phase này)
from .models import Service


# =====================================================
# SERVICE FORMS
# =====================================================

class ServiceForm(forms.ModelForm):
    """
    Form tạo/cập nhật dịch vụ

    VALIDATION RULES:
    - Mã dịch vụ: tự động sinh (DV0001, DV0002, ...)
    - Danh mục: bắt buộc chọn
    - Tên dịch vụ: bắt buộc, không chỉ số, không trùng
    - Mô tả: bắt buộc
    - Giá: bắt buộc, số dương
    - Thời gian: bắt buộc, số nguyên dương
    - Trạng thái: mặc định active
    - Hình ảnh: bắt buộc, chỉ jpg/jpeg/png/webp, max 5MB, min 300x300px
    """
    category_number = forms.ChoiceField(
        label='Danh mục',
        choices=[
            ('1', 'Chăm sóc da'),
            ('2', 'Massage'),
            ('3', 'Phun thêu'),
            ('4', 'Triệt lông'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        error_messages={'required': 'Vui lòng chọn danh mục'}
    )

    name = forms.CharField(
        label='Tên dịch vụ',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên dịch vụ...'
        }),
        error_messages={'required': 'Tên dịch vụ không hợp lệ'}
    )

    description = forms.CharField(
        label='Mô tả',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Mô tả chi tiết về dịch vụ...'
        }),
        error_messages={'required': 'Vui lòng nhập mô tả dịch vụ'}
    )

    price = forms.IntegerField(
        label='Giá (VNĐ)',
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        error_messages={'min_value': 'Giá dịch vụ không hợp lệ'}
    )

    duration_minutes = forms.IntegerField(
        label='Thời gian (phút)',
        required=True,
        min_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '90',
            'min': '5'
        }),
        error_messages={'min_value': 'Thời gian không hợp lệ'}
    )

    status = forms.ChoiceField(
        label='Trạng thái',
        choices=[
            ('ACTIVE', 'Đang hoạt động'),
            ('INACTIVE', 'Ngừng hoạt động'),
        ],
        initial='ACTIVE',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        error_messages={'required': 'Vui lòng chọn trạng thái dịch vụ'}
    )

    image = forms.ImageField(
        label='Hình ảnh',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/jpg,image/png,image/webp'
        })
    )

    class Meta:
        model = Service
        fields = []
        # Không dùng trực tiếp fields từ model, ta đã định nghĩa ở trên

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set label for duration_minutes
        self.fields['duration_minutes'].label = 'Thời gian (phút)'

    def clean_name(self):
        """Validate tên dịch vụ"""
        name = self.cleaned_data.get('name', '').strip()

        # Check if name is not empty
        if not name:
            raise forms.ValidationError('Tên dịch vụ không hợp lệ')

        # Check if name contains only numbers
        if name.isdigit():
            raise forms.ValidationError('Tên dịch vụ không hợp lệ')

        # Check if name already exists (case-insensitive, ignore extra spaces)
        normalized_name = ' '.join(name.split())
        existing_services = Service.objects.filter(name__iexact=normalized_name)

        # If editing, exclude current instance
        if self.instance and self.instance.pk:
            existing_services = existing_services.exclude(pk=self.instance.pk)

        if existing_services.exists():
            raise forms.ValidationError('Dịch vụ đã tồn tại')

        return name

    def clean_description(self):
        """Validate mô tả"""
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise forms.ValidationError('Vui lòng nhập mô tả dịch vụ')
        return description

    def clean_price(self):
        """Validate giá"""
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError('Giá dịch vụ không hợp lệ')
        return price

    def clean_duration_minutes(self):
        """Validate thời gian"""
        duration = self.cleaned_data.get('duration_minutes')
        if duration is None or duration <= 0:
            raise forms.ValidationError('Thời gian không hợp lệ')
        return duration

    def clean_image(self):
        """Validate hình ảnh"""
        image = self.cleaned_data.get('image')

        # If no image is provided
        if not image:
            # If this is an edit and the instance already has an image, keep it
            if self.instance and self.instance.pk and self.instance.image:
                return self.instance.image
            # If creating new service, image is required
            raise forms.ValidationError('Vui lòng chọn hình ảnh dịch vụ')

        # Check file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Hình ảnh không được quá 5MB')

        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image.content_type not in allowed_types:
            raise forms.ValidationError('Chỉ chấp nhận file ảnh (JPG, PNG, WebP)')

        # Check image dimensions (min 300x300)
        try:
            img = Image.open(image)
            width, height = img.size
            if width < 300 or height < 300:
                raise forms.ValidationError('Kích thước ảnh tối thiểu là 300x300px')
        except Exception as e:
            raise forms.ValidationError('Có lỗi khi đọc hình ảnh')

        return image

    def clean_category_number(self):
        """Validate và map category number sang ServiceCategory object"""
        category_num = self.cleaned_data.get('category_number')
        if not category_num:
            raise forms.ValidationError('Vui lòng chọn danh mục')
        _code_map = {'1': 'CAT01', '2': 'CAT02', '3': 'CAT03', '4': 'CAT04'}
        code = _code_map.get(category_num)
        if not code:
            raise forms.ValidationError('Danh mục không hợp lệ')
        from .models import ServiceCategory
        try:
            return ServiceCategory.objects.get(code=code)
        except ServiceCategory.DoesNotExist:
            raise forms.ValidationError('Danh mục không tồn tại trong hệ thống')

    def save(self, commit=True):
        """Override save để xử lý mapping và sinh mã"""
        service = super().save(commit=False)

        # Map category_number to ServiceCategory object
        service.category = self.cleaned_data.get('category_number')  # already a ServiceCategory object from clean_category_number

        # Map status to is_active
        service.status = self.cleaned_data.get('status', 'ACTIVE')
        service.is_active = (service.status == 'ACTIVE')

        # Generate code if not exists
        if not service.code:
            service.code = Service._generate_code()

        if commit:
            service.save()

        return service
