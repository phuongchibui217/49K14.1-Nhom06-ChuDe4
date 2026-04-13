from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin cho dịch vụ"""
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'price']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'category')
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
