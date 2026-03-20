from django.contrib import admin
from .models import Service, CustomerProfile, Appointment, ConsultationRequest, SupportRequest


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin cho dịch vụ"""
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    list_editable = ['is_active', 'price']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'category')
        }),
        ('Mô tả', {
            'fields': ('short_description', 'description', 'image')
        }),
        ('Thông tin dịch vụ', {
            'fields': ('price', 'duration_minutes', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin cho profile khách hàng"""
    list_display = ['full_name', 'phone', 'user', 'gender', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['full_name', 'phone', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Thông tin tài khoản', {
            'fields': ('user', 'phone')
        }),
        ('Thông tin cá nhân', {
            'fields': ('full_name', 'gender', 'dob', 'address')
        }),
        ('Thông tin khác', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    """Admin cho yêu cầu tư vấn"""
    list_display = ['full_name', 'phone', 'request_type', 'status', 'agree_contact', 'created_at']
    list_filter = ['request_type', 'status', 'agree_contact', 'created_at']
    search_fields = ['full_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Thông tin liên hệ', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Nội dung tư vấn', {
            'fields': ('request_type', 'content', 'preferred_contact_time')
        }),
        ('Xử lý', {
            'fields': ('status', 'agree_contact', 'staff_notes')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    """Admin cho góp ý/khiếu nại"""
    list_display = ['full_name', 'phone', 'support_type', 'status', 'appointment_code', 'created_at']
    list_filter = ['support_type', 'status', 'created_at']
    search_fields = ['full_name', 'phone', 'appointment_code', 'content']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Thông tin liên hệ', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Nội dung yêu cầu', {
            'fields': ('support_type', 'support_date', 'appointment_code', 'related_service')
        }),
        ('Chi tiết', {
            'fields': ('content', 'expected_solution', 'agree_processing')
        }),
        ('Xử lý', {
            'fields': ('status', 'staff_notes', 'resolution')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )