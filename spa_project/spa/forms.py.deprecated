"""
Django Forms cho Spa ANA

Updated for Phase 6: Booking form with guest/authenticated support
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import Service, CustomerProfile, Appointment, Complaint, ComplaintReply
from .services import validate_appointment_date, validate_appointment_time


# =====================================================
# Admin Authentication Forms
# =====================================================

class AdminLoginForm(AuthenticationForm):
    """
    Form đăng nhập Admin

    Kế thừa từ Django's AuthenticationForm để:
    - Tự động validate username/password
    - Hỗ trợ CSRF protection
    - Tương thích với Django auth system
    """
    username = forms.CharField(
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })
    )

    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu',
            'autocomplete': 'current-password'
        })
    )

    remember_me = forms.BooleanField(
        label='Ghi nhớ đăng nhập',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    error_messages = {
        'invalid_login': 'Tên đăng nhập hoặc mật khẩu không chính xác.',
        'inactive': 'Tài khoản này đã bị vô hiệu hóa.',
    }


# =====================================================
# Service Forms
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
            ('active', 'Đang hoạt động'),
            ('inactive', 'Ngừng hoạt động'),
        ],
        initial='active',
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
        from PIL import Image
        try:
            img = Image.open(image)
            width, height = img.size
            if width < 300 or height < 300:
                raise forms.ValidationError('Kích thước ảnh tối thiểu là 300x300px')
        except Exception as e:
            raise forms.ValidationError('Có lỗi khi đọc hình ảnh')

        return image

    def clean_category_number(self):
        """Validate và map category number sang category code"""
        category_num = self.cleaned_data.get('category_number')
        if not category_num:
            raise forms.ValidationError('Vui lòng chọn danh mục')
        return Service.CATEGORY_MAP.get(category_num, 'skincare')

    def save(self, commit=True):
        """Override save để xử lý mapping và sinh mã"""
        service = super().save(commit=False)

        # Map category_number to category
        category_num = self.cleaned_data.get('category_number')
        service.category = Service.CATEGORY_MAP.get(category_num, 'skincare')

        # Map status to is_active
        service.status = self.cleaned_data.get('status', 'active')
        service.is_active = (service.status == 'active')

        # Generate code if not exists
        if not service.code:
            service.code = Service.generate_service_code()

        if commit:
            service.save()

        return service



# =====================================================
# CustomerProfile Forms
# =====================================================

class CustomerProfileForm(forms.ModelForm):
    """Form cập nhật thông tin profile khách hàng"""

    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'phone', 'email', 'gender', 'dob', 'address', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ và tên đầy đủ'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Số điện thoại (dùng để đăng nhập)',
                'pattern': '[0-9]{10,11}',
                'title': 'Số điện thoại 10-11 số'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email của bạn'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Địa chỉ của bạn'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú thêm (nếu có)'
            })
        }

    def clean_full_name(self):
        """Validate họ tên"""
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise forms.ValidationError('Vui lòng nhập họ và tên.')
        if len(full_name) < 2:
            raise forms.ValidationError('Họ và tên phải có ít nhất 2 ký tự.')
        return full_name

    def clean_phone(self):
        """Validate số điện thoại"""
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Vui lòng nhập số điện thoại.')
        # Chỉ giữ lại số
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 10 or len(phone) > 11:
            raise forms.ValidationError('Số điện thoại phải có 10-11 chữ số.')
        # Kiểm tra trùng (trừ user hiện tại)
        if CustomerProfile.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Số điện thoại này đã được sử dụng.')
        return phone

    def clean_email(self):
        """Validate email"""
        email = self.cleaned_data.get('email', '').strip()
        if email:
            # Kiểm tra định dạng email cơ bản
            if '@' not in email or '.' not in email.split('@')[-1]:
                raise forms.ValidationError('Email không hợp lệ.')
        return email


class ChangePasswordForm(forms.Form):
    """Form đổi mật khẩu khách hàng"""
    
    current_password = forms.CharField(
        label='Mật khẩu hiện tại',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu hiện tại',
            'autocomplete': 'current-password'
        })
    )
    new_password = forms.CharField(
        label='Mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu mới',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        label='Xác nhận mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu mới',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """Kiểm tra mật khẩu hiện tại đúng không"""
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Mật khẩu hiện tại không đúng.')
        return current_password

    def clean_new_password(self):
        """Validate mật khẩu mới"""
        new_password = self.cleaned_data.get('new_password')
        if not new_password:
            raise forms.ValidationError('Vui lòng nhập mật khẩu mới.')
        if len(new_password) < 6:
            raise forms.ValidationError('Mật khẩu mới phải có ít nhất 6 ký tự.')
        return new_password

    def clean_confirm_password(self):
        """Kiểm tra mật khẩu xác nhận khớp"""
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Mật khẩu xác nhận không khớp.')
        return confirm_password

    def save(self):
        """Lưu mật khẩu mới"""
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user


class CustomerRegistrationForm(forms.ModelForm):
    """
    Form đăng ký khách hàng mới

    NOTE: Login bằng số điện thoại
    - Username = Phone
    - Email có thể bỏ trống
    """
    password1 = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu'
        })
    )
    password2 = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu'
        })
    )

    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'phone', 'gender', 'dob', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ và tên đầy đủ'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Số điện thoại (dùng đăng nhập)',
                'pattern': '[0-9]{10,11}'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Địa chỉ của bạn'
            })
        }

    def clean_phone(self):
        """Validate số điện thoại"""
        phone = self.cleaned_data.get('phone')
        if CustomerProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Số điện thoại này đã được đăng ký.')
        return phone

    def clean_password2(self):
        """Validate mật khẩu khớp nhau"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Mật khẩu không khớp nhau.')

        return password2

    def save(self, commit=True):
        """Tạo User và CustomerProfile"""
        user = User.objects.create_user(
            username=self.cleaned_data['phone'],
            password=self.cleaned_data['password1']
        )

        profile = super().save(commit=False)
        profile.user = user

        if commit:
            profile.save()

        return profile


# =====================================================
# Appointment Forms
# =====================================================

class AppointmentForm(forms.ModelForm):
    """
    Form đặt lịch hẹn

    QUYẾT THIẾT DESIGN:
    - Nếu user đã đăng nhập: Tự động lấy thông tin từ CustomerProfile
    - Nếu user chưa đăng nhập: Yêu cầu đăng nhập TRƯỚC (không cho guest booking)

    LÝ DO:
    - Giảm spam booking
    - Đảm bảo có thông tin liên hệ
    - Dễ quản lý lịch hẹn
    - Theo dõi lịch sử khách hàng
    """
    appointment_date = forms.DateField(
        label='Ngày hẹn',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    appointment_time = forms.TimeField(
        label='Giờ hẹn',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    class Meta:
        model = Appointment
        fields = ['service', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'service': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú thêm (nếu có)'
            })
        }

    def __init__(self, *args, **kwargs):
        """Filter only active services"""
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['service'].empty_label = "-- Chọn dịch vụ --"
        self.fields['service'].required = True

    def clean_appointment_date(self):
        """
        Validate ngày hẹn - sử dụng timezone
        
        QUAN TRỌNG: Dùng timezone.now().date() thay vì date.today()
        để đảm bảo đúng múi giờ configured trong settings.TIME_ZONE
        """
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date:
            # Dùng service để validate (đã xử lý timezone đúng)
            try:
                validate_appointment_date(appointment_date)
            except Exception as e:
                raise forms.ValidationError(str(e.message))
        return appointment_date

    def clean_appointment_time(self):
        """
        Validate giờ hẹn
        
        - Nếu đặt hôm nay: phải trước ít nhất 30 phút
        - Giờ làm việc: 8:00 - 20:00
        """
        appointment_time = self.cleaned_data.get('appointment_time')
        appointment_date = self.cleaned_data.get('appointment_date')
        
        if appointment_time and appointment_date:
            try:
                validate_appointment_time(appointment_time, appointment_date)
            except Exception as e:
                raise forms.ValidationError(str(e.message))
        
        return appointment_time

    def clean(self):
        """
        Validate tổng hợp cho form đặt lịch
        
        Kiểm tra:
        - Ngày hợp lệ
        - Giờ hợp lệ
        """
        cleaned_data = super().clean()
        
        # Lấy dữ liệu đã validate
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        service = cleaned_data.get('service')
        
        # Nếu đã có lỗi ở field riêng thì không check thêm
        if not appointment_date or not appointment_time or not service:
            return cleaned_data
        
        # Các validation bổ sung có thể thêm ở đây
        # Ví dụ: check phòng trống (nếu form có chọn phòng)
        
        return cleaned_data


# =====================================================
# Complaint Forms
# =====================================================

class CustomerComplaintForm(forms.ModelForm):
    """Form khách hàng gửi khiếu nại"""

    class Meta:
        model = Complaint
        fields = ['title', 'content',
                  'incident_date', 'appointment_code', 'related_service',
                  'expected_solution']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề khiếu nại'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Mô tả chi tiết vấn đề của bạn...'
            }),
            'incident_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'appointment_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mã lịch hẹn (nếu có)'
            }),
            'expected_solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Bạn mong muốn được giải quyết như thế nào?'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_service'].queryset = Service.objects.filter(is_active=True)
        self.fields['related_service'].required = False
        self.fields['related_service'].empty_label = "-- Chọn dịch vụ liên quan (nếu có) --"
        self.fields['related_service'].widget.attrs.update({'class': 'form-select'})

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title or len(title) < 5:
            raise forms.ValidationError('Tiêu đề phải có ít nhất 5 ký tự.')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content or len(content) < 10:
            raise forms.ValidationError('Nội dung phải có ít nhất 10 ký tự.')
        return content


class GuestComplaintForm(forms.ModelForm):
    """Form khách chưa đăng nhập gửi khiếu nại"""

    class Meta:
        model = Complaint
        fields = ['full_name', 'phone', 'email', 'title', 'content',
                  'incident_date',
                  'appointment_code', 'related_service', 'expected_solution']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ và tên của bạn'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Số điện thoại',
                'pattern': '[0-9]{10,11}'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email (không bắt buộc)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề khiếu nại'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Mô tả chi tiết vấn đề của bạn...'
            }),
            'incident_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'appointment_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mã lịch hẹn (nếu có)'
            }),
            'expected_solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Bạn mong muốn được giải quyết như thế nào?'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_service'].queryset = Service.objects.filter(is_active=True)
        self.fields['related_service'].required = False
        self.fields['related_service'].empty_label = "-- Chọn dịch vụ liên quan (nếu có) --"
        self.fields['related_service'].widget.attrs.update({'class': 'form-select'})

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title or len(title) < 5:
            raise forms.ValidationError('Tiêu đề phải có ít nhất 5 ký tự.')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content or len(content) < 10:
            raise forms.ValidationError('Nội dung phải có ít nhất 10 ký tự.')
        return content

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Vui lòng nhập số điện thoại.')
        return phone


class ComplaintReplyForm(forms.ModelForm):
    """Form phản hồi khiếu nại"""

    class Meta:
        model = ComplaintReply
        fields = ['message', 'is_internal']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhập nội dung phản hồi...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message or len(message) < 3:
            raise forms.ValidationError('Nội dung phản hồi phải có ít nhất 3 ký tự.')
        return message


class ComplaintStatusForm(forms.ModelForm):
    """Form cập nhật trạng thái khiếu nại"""

    class Meta:
        model = Complaint
        fields = ['status', 'resolution']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'resolution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Kết quả xử lý (nếu hoàn thành)'
            }),
        }


class ComplaintAssignForm(forms.ModelForm):
    """Form phân công người phụ trách"""

    class Meta:
        model = Complaint
        fields = ['assigned_to']
        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ lấy staff users
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['assigned_to'].empty_label = "-- Chọn nhân viên --"
        self.fields['assigned_to'].required = True
