"""
URL configuration for spa app.
"""
from django.urls import path
from . import views

app_name = 'spa'

urlpatterns = [
    # Customer pages
    path('', views.home, name='index'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('booking/', views.booking, name='booking'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset
    path('quen-mat-khau/', views.password_reset_request, name='password_reset'),
    path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Customer Account
    path('tai-khoan/', views.customer_profile, name='customer_profile'),
    path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),
    path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),

    # Admin pages (using /manage/ prefix to avoid conflict with Django admin)
    path('manage/login/', views.admin_login, name='admin_login'),
    path('manage/appointments/', views.admin_appointments, name='admin_appointments'),
    path('manage/services/', views.admin_services, name='admin_services'),
    path('manage/services/<int:service_id>/edit/', views.admin_service_edit, name='admin_service_edit'),
    path('manage/services/<int:service_id>/delete/', views.admin_service_delete, name='admin_service_delete'),
    path('manage/customers/', views.admin_customers, name='admin_customers'),
    path('manage/staff/', views.admin_staff, name='admin_staff'),
    # Admin Complaint Management
    path('manage/complaints/', views.admin_complaints, name='admin_complaints'),
    path('manage/complaints/<int:complaint_id>/', views.admin_complaint_detail, name='admin_complaint_detail'),
    path('manage/complaints/<int:complaint_id>/take/', views.admin_complaint_take, name='admin_complaint_take'),
    path('manage/complaints/<int:complaint_id>/assign/', views.admin_complaint_assign, name='admin_complaint_assign'),
    path('manage/complaints/<int:complaint_id>/reply/', views.admin_complaint_reply, name='admin_complaint_reply'),
    path('manage/complaints/<int:complaint_id>/status/', views.admin_complaint_status, name='admin_complaint_status'),
    path('manage/complaints/<int:complaint_id>/complete/', views.admin_complaint_complete, name='admin_complaint_complete'),

    # Customer Complaint
    path('gui-khieu-nai/', views.customer_complaint_create, name='customer_complaint_create'),
    path('khieu-nai-cua-toi/', views.customer_complaint_list, name='customer_complaint_list'),
    path('khieu-nai-cua-toi/<int:complaint_id>/', views.customer_complaint_detail, name='customer_complaint_detail'),
    path('khieu-nai-cua-toi/<int:complaint_id>/reply/', views.customer_complaint_reply, name='customer_complaint_reply'),
    path('manage/live-chat/', views.admin_live_chat, name='admin_live_chat'),
    path('manage/profile/', views.admin_profile, name='admin_profile'),
    path('manage/logout/', views.admin_logout, name='admin_logout'),

    # API endpoints for Services
    path('api/services/', views.api_services_list, name='api_services_list'),
    path('api/services/create/', views.api_service_create, name='api_service_create'),
    path('api/services/<int:service_id>/update/', views.api_service_update, name='api_service_update'),
    path('api/services/<int:service_id>/delete/', views.api_service_delete, name='api_service_delete'),

    # API endpoints for Appointments (Scheduler)
    path('api/rooms/', views.api_rooms_list, name='api_rooms_list'),
    path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),
    path('api/appointments/create/', views.api_appointment_create, name='api_appointment_create'),
    path('api/appointments/<str:appointment_code>/', views.api_appointment_detail, name='api_appointment_detail'),
    path('api/appointments/<str:appointment_code>/update/', views.api_appointment_update, name='api_appointment_update'),
    path('api/appointments/<str:appointment_code>/status/', views.api_appointment_status, name='api_appointment_status'),
    path('api/appointments/<str:appointment_code>/delete/', views.api_appointment_delete, name='api_appointment_delete'),
    path('api/booking-requests/', views.api_booking_requests, name='api_booking_requests'),
]
