"""
Forms cho Authentication và Customer Profile

File này chứa các forms cho:
- Đăng ký khách hàng mới
- Cập nhật thông tin profile
- Đổi mật khẩu

Author: Spa ANA Team
"""

from django import forms
from django.contrib.auth.models import User

# Tạm import từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import CustomerProfile


# =====================================================
# CUSTOMER PROFILE FORMS
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
