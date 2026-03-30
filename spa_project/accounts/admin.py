from django.contrib import admin
from .models import CustomerProfile


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
