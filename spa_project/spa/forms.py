"""
Django Forms cho Spa ANA

Updated for Phase 6: Booking form with guest/authenticated support
"""

from django import forms
from django.contrib.auth.models import User
from .models import Service, CustomerProfile, Appointment, ConsultationRequest, SupportRequest


# =====================================================
# Service Forms
# =====================================================

class ServiceForm(forms.ModelForm):
    """Form tạo/cập nhật dịch vụ - dùng trong admin nếu cần"""

    class Meta:
        model = Service
        fields = ['name', 'slug', 'category', 'short_description', 'description',
                  'price', 'duration_minutes', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên dịch vụ'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tự động tạo từ tên'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mô tả ngắn (hiển thị trong card)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Mô tả chi tiết về dịch vụ'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Giá dịch vụ (VNĐ)'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Thời lượng (phút)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


# =====================================================
# CustomerProfile Forms
# =====================================================

class CustomerProfileForm(forms.ModelForm):
    """Form cập nhật thông tin profile khách hàng"""

    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'phone', 'gender', 'dob', 'address', 'notes']
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
        """Validate không chọn ngày quá khứ"""
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date:
            from datetime import date
            if appointment_date < date.today():
                raise forms.ValidationError('Không thể chọn ngày trong quá khứ.')
        return appointment_date


# =====================================================
# ConsultationRequest Forms
# =====================================================

class ConsultationRequestForm(forms.ModelForm):
    """Form đăng ký tư vấn"""

    class Meta:
        model = ConsultationRequest
        fields = ['full_name', 'phone', 'email', 'request_type',
                  'content', 'preferred_contact_time', 'agree_contact']
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
            'request_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nội dung cần tư vấn...',
                'required': 'required'
            }),
            'preferred_contact_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: Buổi sáng, Chiều, T2-T6...'
            }),
            'agree_contact': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'required': 'required'
            })
        }

    def clean_agree_contact(self):
        agree_contact = self.cleaned_data.get('agree_contact')
        if not agree_contact:
            raise forms.ValidationError('Bạn cần đồng ý để được liên hệ tư vấn.')
        return agree_contact


# =====================================================
# SupportRequest Forms
# =====================================================

class SupportRequestForm(forms.ModelForm):
    """Form gửi góp ý/khiếu nại"""

    class Meta:
        model = SupportRequest
        fields = ['full_name', 'phone', 'email', 'support_type',
                  'support_date', 'appointment_code', 'related_service',
                  'content', 'expected_solution', 'agree_processing']
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
            'support_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'support_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'appointment_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mã lịch hẹn (nếu có)'
            }),
            'related_service': forms.Select(attrs={
                'class': 'form-select'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Nội dung góp ý/khiếu nại...',
                'required': 'required'
            }),
            'expected_solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Bạn muốn được giải quyết như thế nào?'
            }),
            'agree_processing': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'required': 'required'
            })
        }

    def __init__(self, *args, **kwargs):
        """Filter only active services"""
        super().__init__(*args, **kwargs)
        self.fields['related_service'].queryset = Service.objects.filter(is_active=True)
        self.fields['related_service'].required = False
        self.fields['related_service'].empty_label = "-- Chọn dịch vụ (nếu có) --"

    def clean_agree_processing(self):
        agree_processing = self.cleaned_data.get('agree_processing')
        if not agree_processing:
            raise forms.ValidationError('Bạn cần đồng ý để chúng tôi xử lý yêu cầu.')
        return agree_processing
