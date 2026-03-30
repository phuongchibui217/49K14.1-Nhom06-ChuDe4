from django.contrib import admin
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin cho phòng dịch vụ"""
    list_display = ['code', 'name', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    list_editable = ['is_active', 'capacity']
    readonly_fields = ['created_at', 'updated_at']
