"""
URL configuration cho appointments app

Phân tách rõ ràng:
- views.py  → Trang web (HTML)   → import views
- api.py    → API endpoints (JSON) → import api

Author: Spa ANA Team
"""

from django.urls import path
from . import views
from . import api

app_name = 'appointments'

urlpatterns = [
    # ============================================================
    # TRANG WEB (views.py) - Trả về HTML
    # ============================================================
    path('booking/', views.booking, name='booking'),
    path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),
    path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('manage/appointments/', views.admin_appointments, name='admin_appointments'),

    # ============================================================
    # API ENDPOINTS (api.py) - Trả về JSON
    # ============================================================
    path('api/rooms/', api.api_rooms_list, name='api_rooms_list'),
    path('api/appointments/', api.api_appointments_list, name='api_appointments_list'),
    path('api/appointments/create/', api.api_appointment_create, name='api_appointment_create'),
    path('api/appointments/<str:appointment_code>/', api.api_appointment_detail, name='api_appointment_detail'),
    path('api/appointments/<str:appointment_code>/update/', api.api_appointment_update, name='api_appointment_update'),
    path('api/appointments/<str:appointment_code>/status/', api.api_appointment_status, name='api_appointment_status'),
    path('api/appointments/<str:appointment_code>/delete/', api.api_appointment_delete, name='api_appointment_delete'),
    path('api/booking-requests/', api.api_booking_requests, name='api_booking_requests'),
]