"""
URL configuration cho appointments app

Chứa URL patterns cho appointment management:
- Public appointment pages (booking, my appointments, cancel)
- Admin appointment management (scheduler)
- API endpoints for appointments and rooms

Author: Spa ANA Team
"""

from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # ============================================================
    # Public Appointment Pages
    # ============================================================
    path('booking/', views.booking, name='booking'),
    path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),
    path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment,
         name='cancel_appointment'),

    # ============================================================
    # Admin Appointment Management
    # ============================================================
    path('manage/appointments/', views.admin_appointments, name='admin_appointments'),

    # ============================================================
    # API endpoints
    # ============================================================
    path('api/rooms/', views.api_rooms_list, name='api_rooms_list'),
    path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),
    path('api/appointments/create/', views.api_appointment_create, name='api_appointment_create'),
    path('api/appointments/<str:appointment_code>/', views.api_appointment_detail,
         name='api_appointment_detail'),
    path('api/appointments/<str:appointment_code>/update/', views.api_appointment_update,
         name='api_appointment_update'),
    path('api/appointments/<str:appointment_code>/status/', views.api_appointment_status,
         name='api_appointment_status'),
    path('api/appointments/<str:appointment_code>/delete/', views.api_appointment_delete,
         name='api_appointment_delete'),
    path('api/booking-requests/', views.api_booking_requests, name='api_booking_requests'),
]
