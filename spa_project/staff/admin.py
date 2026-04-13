from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'gender', 'dob', 'created_at')
    search_fields = ('full_name', 'phone')
    list_filter = ('gender', 'created_at')

