"""
URL configuration cho appointments app

Phan tach ro rang:
- views.py  -> Trang web (HTML)   -> import views
- api.py    -> API endpoints (JSON) -> import api

Author: Spa ANA Team
"""

from django.urls import path

from . import api, views

app_name = 'appointments'

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),
    path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('manage/appointments/', views.admin_appointments, name='admin_appointments'),
    path('api/rooms/', api.api_rooms_list, name='api_rooms_list'),
    path('api/appointments/', api.api_appointments_list, name='api_appointments_list'),
    path('api/appointments/search/', api.api_appointments_search, name='api_appointments_search'),
    path('api/appointments/create/', api.api_appointment_create, name='api_appointment_create'),
    path('api/appointments/create-batch/', api.api_appointment_create_batch, name='api_appointment_create_batch'),
    path('api/appointments/<str:appointment_code>/', api.api_appointment_detail, name='api_appointment_detail'),
    path('api/appointments/<str:appointment_code>/update/', api.api_appointment_update, name='api_appointment_update'),
    path('api/appointments/<str:appointment_code>/rebook/', api.api_appointment_rebook, name='api_appointment_rebook'),
    path('api/appointments/<str:appointment_code>/status/', api.api_appointment_status, name='api_appointment_status'),
    path('api/appointments/<str:appointment_code>/delete/', api.api_appointment_delete, name='api_appointment_delete'),
    path('api/booking-requests/', api.api_booking_requests, name='api_booking_requests'),
    path('api/booking/pending-count/', api.api_booking_pending_count, name='api_booking_pending_count'),
    path('api/appointments/customer-cancelled-recent/', api.api_customer_cancelled_recent, name='api_customer_cancelled_recent'),
    path('api/customers/search/', api.api_customer_search, name='api_customer_search'),
]
