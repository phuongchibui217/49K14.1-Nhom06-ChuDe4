"""
Forms cho Appointment — booking online từ phía khách hàng.

Author: Spa ANA Team
"""

import re
from django import forms
from .models import Appointment
from spa_services.models import Service, ServiceVariant
from .services import validate_appointment_date, validate_appointment_time


class AppointmentForm(forms.ModelForm):
    """
    Form đặt lịch hẹn cho khách hàng (booking online).

    Phân tách rõ:
    - booker_name / booker_phone: lấy từ account đang đăng nhập (hidden field)
    - customer_name_snapshot / customer_phone_snapshot: khách sử dụng dịch vụ
      (mặc định = thông tin account, nhưng user có thể sửa nếu đặt dùm người khác)
    - service: chọn dịch vụ để lọc variant — không lưu vào DB
    - service_variant: gói dịch vụ (tuỳ chọn)
    """

    # Chọn dịch vụ để lọc variant — không lưu vào DB
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(status='ACTIVE'),
        required=False,
        empty_label='-- Chọn dịch vụ (tuỳ chọn) --',
        label='Dịch vụ',
        widget=forms.Select(attrs={'class': 'lux-select'})
    )

    class Meta:
        model = Appointment
        fields = [
            'booker_name',
            'booker_phone',
            'service_variant',
            'appointment_date',
            'appointment_time',
            'notes',
        ]
        widgets = {
            # booker fields — hidden, tự điền từ account
            'booker_name':  forms.HiddenInput(),
            'booker_phone': forms.HiddenInput(),
            # các field hiển thị
            'service_variant': forms.Select(attrs={'class': 'lux-select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'lux-input', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'lux-input', 'type': 'time'}),
            'notes': forms.Textarea(attrs={
                'class': 'lux-textarea',
                'rows': 4,
                'placeholder': 'Ghi chú thêm về yêu cầu đặc biệt, dị ứng, hoặc thông tin khác...',
            }),
        }
        labels = {
            'service_variant': 'Gói dịch vụ',
            'appointment_date': 'Ngày hẹn',
            'appointment_time': 'Giờ hẹn',
            'notes': 'Ghi chú',
        }

    def __init__(self, *args, **kwargs):
        # Nhận customer_profile để pre-fill booker fields
        self.customer_profile = kwargs.pop('customer_profile', None)
        super().__init__(*args, **kwargs)

        self.fields['service_variant'].required = True
        self.fields['service_variant'].empty_label = '-- Chọn gói dịch vụ --'

        # Pre-fill booker từ profile — áp dụng cả GET lẫn POST
        # (POST data có thể không chứa hidden fields nếu bị strip)
        if self.customer_profile:
            profile_name  = self.customer_profile.full_name or ''
            profile_phone = self.customer_profile.phone or ''
            self.initial['booker_name']  = profile_name
            self.initial['booker_phone'] = profile_phone
            # Nếu POST data thiếu booker fields thì inject vào data
            if self.data:
                data = self.data.copy()
                if not data.get('booker_name'):
                    data['booker_name'] = profile_name
                if not data.get('booker_phone'):
                    data['booker_phone'] = profile_phone
                self.data = data

        # Load variants theo service đã chọn
        service_id = self.data.get('service') if self.data else None
        if service_id:
            self.fields['service_variant'].queryset = ServiceVariant.objects.filter(
                service_id=service_id
            ).order_by('sort_order', 'duration_minutes')
        else:
            self.fields['service_variant'].queryset = ServiceVariant.objects.select_related('service').order_by(
                'service__name', 'sort_order', 'duration_minutes'
            )

    def clean_booker_phone(self):
        phone = self.cleaned_data.get('booker_phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if not digits:
            raise forms.ValidationError('Không xác định được số điện thoại người đặt.')
        return digits

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date:
            try:
                validate_appointment_date(appointment_date)
            except Exception as e:
                raise forms.ValidationError(str(e.message))
        return appointment_date

    def clean_appointment_time(self):
        appointment_time = self.cleaned_data.get('appointment_time')
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_time and appointment_date:
            try:
                validate_appointment_time(appointment_time, appointment_date)
            except Exception as e:
                raise forms.ValidationError(str(e.message))
        return appointment_time

    def clean_service_variant(self):
        service_variant = self.cleaned_data.get('service_variant')
        if not service_variant:
            raise forms.ValidationError('Vui lòng chọn gói dịch vụ để đặt lịch.')
        return service_variant
