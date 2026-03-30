from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin cho lịch hẹn"""
    list_display = ['appointment_code', 'customer', 'service', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date', 'service']
    search_fields = ['appointment_code', 'customer__full_name', 'customer__phone', 'service__name']
    readonly_fields = ['appointment_code', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Thông tin lịch hẹn', {
            'fields': ('appointment_code', 'customer', 'service', 'appointment_date', 'appointment_time', 'status')
        }),
        ('Ghi chú', {
            'fields': ('notes', 'staff_notes')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
