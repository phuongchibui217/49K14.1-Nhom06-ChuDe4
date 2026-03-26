from django.contrib import admin
from .models import (
    Service, CustomerProfile, Room, Appointment, 
    Complaint, ComplaintReply, ComplaintHistory
)


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


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin cho phòng dịch vụ"""
    list_display = ['code', 'name', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    list_editable = ['is_active', 'capacity']
    readonly_fields = ['created_at', 'updated_at']


class ComplaintReplyInline(admin.TabularInline):
    """Inline cho phản hồi khiếu nại"""
    model = ComplaintReply
    extra = 0
    readonly_fields = ['sender', 'sender_role', 'sender_name', 'message', 'created_at']
    fields = ['sender_name', 'sender_role', 'message', 'is_internal', 'created_at']


class ComplaintHistoryInline(admin.TabularInline):
    """Inline cho lịch sử khiếu nại"""
    model = ComplaintHistory
    extra = 0
    readonly_fields = ['action', 'old_value', 'new_value', 'note', 'performed_by', 'performed_at']
    fields = ['action', 'old_value', 'new_value', 'note', 'performed_by', 'performed_at']
    

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin cho khiếu nại - Quản lý đầy đủ"""
    list_display = ['code', 'title', 'customer', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['code', 'title', 'customer__full_name', 'customer__phone', 'content']
    readonly_fields = ['code', 'created_at', 'updated_at', 'resolved_at']
    inlines = [ComplaintReplyInline, ComplaintHistoryInline]
    date_hierarchy = 'created_at'
    list_select_related = ['customer', 'assigned_to']
    fieldsets = (
        ('Thông tin khiếu nại', {
            'fields': ('code', 'customer', 'title', 'content')
        }),
        ('Thông tin liên hệ', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Thông tin liên quan', {
            'fields': ('incident_date', 'appointment_code', 'related_service', 'expected_solution')
        }),
        ('Xử lý', {
            'fields': ('status', 'assigned_to', 'resolution', 'resolved_at')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'assigned_to')


@admin.register(ComplaintReply)
class ComplaintReplyAdmin(admin.ModelAdmin):
    """Admin cho phản hồi khiếu nại"""
    list_display = ['complaint', 'sender_name', 'sender_role', 'is_internal', 'created_at']
    list_filter = ['sender_role', 'is_internal', 'created_at']
    search_fields = ['complaint__code', 'sender_name', 'message']
    readonly_fields = ['sender_name', 'created_at']


@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    """Admin cho lịch sử khiếu nại"""
    list_display = ['complaint', 'action', 'old_value', 'new_value', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['complaint__code', 'note']
    readonly_fields = ['complaint', 'action', 'old_value', 'new_value', 'note', 'performed_by', 'performed_at']
