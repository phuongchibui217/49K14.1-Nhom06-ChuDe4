from django.contrib import admin
from .models import Room, Appointment


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    search_fields = ['code', 'name']
    list_display = ['code', 'name', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['is_active', 'capacity']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'appointment_code', 'customer', 'service_variant',
        'room', 'appointment_date', 'appointment_time', 'status', 'payment_status'
    ]
    list_filter = ['status', 'payment_status', 'source', 'appointment_date']
    search_fields = [
        'appointment_code', 'customer__full_name', 'customer__phone',
        'booker_name', 'booker_phone', 'customer_name_snapshot'
    ]
    readonly_fields = ['appointment_code', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Mã lịch hẹn', {
            'fields': ('appointment_code',)
        }),
        ('Người đặt lịch', {
            'fields': ('booker_name', 'booker_phone', 'booker_email', 'source')
        }),
        ('Khách sử dụng dịch vụ', {
            'fields': ('customer', 'customer_name_snapshot', 'customer_phone_snapshot', 'customer_email_snapshot')
        }),
        ('Dịch vụ & Phòng', {
            'fields': ('service_variant', 'room')
        }),
        ('Thời gian', {
            'fields': ('appointment_date', 'appointment_time')
        }),
        ('Trạng thái', {
            'fields': ('status', 'payment_status')
        }),
        ('Ghi chú', {
            'fields': ('notes', 'staff_notes')
        }),
        ('Check-in / Check-out', {
            'fields': ('check_in_at', 'check_out_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at', 'deleted_by_user'),
            'classes': ('collapse',)
        }),
    )
