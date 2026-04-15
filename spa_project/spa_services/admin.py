from django.contrib import admin
from .models import Service, ServiceVariant


class ServiceVariantInline(admin.TabularInline):
    model = ServiceVariant
    extra = 1
    fields = ['label', 'duration_minutes', 'price', 'sort_order', 'is_active']
    ordering = ['sort_order', 'duration_minutes']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ServiceVariantInline]
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'category')
        }),
        ('Mô tả', {
            'fields': ('short_description', 'description', 'image')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceVariant)
class ServiceVariantAdmin(admin.ModelAdmin):
    list_display = ['service', 'label', 'duration_minutes', 'price', 'sort_order', 'is_active']
    list_filter = ['service', 'is_active']
    search_fields = ['service__name', 'label']
    list_editable = ['price', 'sort_order', 'is_active']
    ordering = ['service', 'sort_order', 'duration_minutes']
