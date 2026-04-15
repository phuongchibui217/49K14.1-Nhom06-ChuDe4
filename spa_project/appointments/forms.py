"""
Forms cho Appointment Management

File này chứa các forms cho:
- Đặt lịch hẹn

Author: Spa ANA Team
"""

from django import forms

from .models import Appointment
from spa_services.models import Service, ServiceVariant

from .services import validate_appointment_date, validate_appointment_time


# =====================================================
# APPOINTMENT FORMS
# =====================================================

class AppointmentForm(forms.ModelForm):
    """
    Form đặt lịch hẹn cho khách hàng (booking online).

    - service: bắt buộc
    - service_variant: optional — nếu service có variants thì khách chọn gói
    - Nếu không chọn variant → fallback về price/duration của service
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

    service_variant = forms.ModelChoiceField(
        queryset=ServiceVariant.objects.none(),
        required=False,
        empty_label='-- Chọn gói (nếu có) --',
        label='Gói dịch vụ',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['service', 'service_variant', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú thêm (nếu có)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['service'].empty_label = '-- Chọn dịch vụ --'
        self.fields['service'].required = True

        # Nếu đã có service (edit hoặc POST) → load variants của service đó
        service_id = None
        if self.data.get('service'):
            service_id = self.data.get('service')
        elif self.instance and self.instance.pk and self.instance.service_id:
            service_id = self.instance.service_id

        if service_id:
            self.fields['service_variant'].queryset = ServiceVariant.objects.filter(
                service_id=service_id, is_active=True
            ).order_by('sort_order', 'duration_minutes')

    def clean_appointment_date(self):
        """Validate ngày hẹn"""
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

        - Giờ làm việc: 9:00 - 21:00 (khách đặt từ 9h đến 20h)
        - Có thể đặt lịch cùng ngày, không cần trước 30 phút
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
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        service = cleaned_data.get('service')
        variant = cleaned_data.get('service_variant')

        if not appointment_date or not appointment_time or not service:
            return cleaned_data

        # Validate variant thuộc đúng service
        if variant and variant.service_id != service.id:
            self.add_error('service_variant', 'Gói dịch vụ không thuộc dịch vụ đã chọn')

        return cleaned_data
