"""
Forms cho Appointment Management

File này chứa các forms cho:
- Đặt lịch hẹn

Author: Spa ANA Team
"""

from django import forms

# Tạm import từ spa.models (CHƯA chuyển model trong phase này)
from spa.models import Appointment, Service

# Import validation services từ appointments/services
from .services import validate_appointment_date, validate_appointment_time


# =====================================================
# APPOINTMENT FORMS
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
