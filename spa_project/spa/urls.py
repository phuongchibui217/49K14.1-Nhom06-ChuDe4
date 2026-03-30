"""
URL configuration for spa app.
"""
from django.urls import path
from . import views

app_name = 'spa'

urlpatterns = [
    # ============================================================
    # PHASE 3: DEPRECATED - Moved to pages/urls.py
    # ============================================================
    # path('', views.home, name='index'),          # MOVED → pages/
    # path('home/', views.home, name='home'),      # MOVED → pages/
    # path('about/', views.about, name='about'),    # MOVED → pages/

    # ============================================================
    # PHASE 5: DEPRECATED - Moved to spa_services/urls.py
    # ============================================================
    # path('services/', views.service_list, name='service_list'),                    # MOVED → spa_services/
    # path('service/<int:service_id>/', views.service_detail, name='service_detail'),    # MOVED → spa_services/

    # Customer pages
    path('booking/', views.booking, name='booking'),

    # ============================================================
    # PHASE 4: DEPRECATED - Moved to accounts/urls.py
    # ============================================================
    # path('login/', views.login_view, name='login'),                             # MOVED → accounts/
    # path('register/', views.register, name='register'),                         # MOVED → accounts/
    # path('logout/', views.logout_view, name='logout'),                           # MOVED → accounts/
    # path('quen-mat-khau/', views.password_reset_request, name='password_reset'),    # MOVED → accounts/
    # path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm,         # MOVED → accounts/
    # path('tai-khoan/', views.customer_profile, name='customer_profile'),           # MOVED → accounts/

    # ============================================================
    # PHASE 6: DEPRECATED - Moved to appointments/urls.py
    # ============================================================
    # path('booking/', views.booking, name='booking'),                              # MOVED → appointments/
    # path('lich-hen-cua-toi/', views.my_appointments, name='my_appointments'),       # MOVED → appointments/
    # path('lich-hen/cancel/<int:appointment_id>/', views.cancel_appointment,        # MOVED → appointments/
    #      name='cancel_appointment'),                                               # MOVED → appointments/

    # Admin pages (using /manage/ prefix to avoid conflict with Django admin)
    path('manage/login/', views.admin_login, name='admin_login'),
    # Phase 6: Appointment management routes - MOVED → appointments/
    # path('manage/appointments/', views.admin_appointments, name='admin_appointments'),    # MOVED → appointments/
    # Phase 5: Service management routes - MOVED → spa_services/
    # path('manage/services/', views.admin_services, name='admin_services'),                # MOVED → spa_services/
    # path('manage/services/<int:service_id>/edit/', views.admin_service_edit,             # MOVED → spa_services/
    #      name='admin_service_edit'),                                                     # MOVED → spa_services/
    # path('manage/services/<int:service_id>/delete/', views.admin_service_delete,         # MOVED → spa_services/
    #      name='admin_service_delete'),                                                   # MOVED → spa_services/
    path('manage/customers/', views.admin_customers, name='admin_customers'),
    path('manage/staff/', views.admin_staff, name='admin_staff'),
    # ============================================================
    # PHASE 7: DEPRECATED - Moved to complaints/urls.py
    # ============================================================
    # Admin Complaint Management
    # path('manage/complaints/', views.admin_complaints, name='admin_complaints'),                # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/', views.admin_complaint_detail,                # MOVED → complaints/
    #      name='admin_complaint_detail'),                                                       # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/take/', views.admin_complaint_take,             # MOVED → complaints/
    #      name='admin_complaint_take'),                                                         # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/assign/', views.admin_complaint_assign,         # MOVED → complaints/
    #      name='admin_complaint_assign'),                                                       # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/reply/', views.admin_complaint_reply,           # MOVED → complaints/
    #      name='admin_complaint_reply'),                                                        # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/status/', views.admin_complaint_status,         # MOVED → complaints/
    #      name='admin_complaint_status'),                                                       # MOVED → complaints/
    # path('manage/complaints/<int:complaint_id>/complete/', views.admin_complaint_complete,     # MOVED → complaints/
    #      name='admin_complaint_complete'),                                                     # MOVED → complaints/
    # Customer Complaint
    # path('gui-khieu-nai/', views.customer_complaint_create, name='customer_complaint_create'),  # MOVED → complaints/
    # path('khieu-nai-cua-toi/', views.customer_complaint_list, name='customer_complaint_list'),  # MOVED → complaints/
    # path('khieu-nai-cua-toi/<int:complaint_id>/', views.customer_complaint_detail,             # MOVED → complaints/
    #      name='customer_complaint_detail'),                                                    # MOVED → complaints/
    # path('khieu-nai-cua-toi/<int:complaint_id>/reply/', views.customer_complaint_reply,         # MOVED → complaints/
    #      name='customer_complaint_reply'),                                                     # MOVED → complaints/

    path('manage/live-chat/', views.admin_live_chat, name='admin_live_chat'),
    path('manage/profile/', views.admin_profile, name='admin_profile'),
    path('manage/logout/', views.admin_logout, name='admin_logout'),

    # API endpoints for Services - MOVED → spa_services/
    # path('api/services/', views.api_services_list, name='api_services_list'),             # MOVED → spa_services/
    # path('api/services/create/', views.api_service_create, name='api_service_create'),    # MOVED → spa_services/
    # path('api/services/<int:service_id>/update/', views.api_service_update,               # MOVED → spa_services/
    #      name='api_service_update'),                                                      # MOVED → spa_services/
    # path('api/services/<int:service_id>/delete/', views.api_service_delete,               # MOVED → spa_services/
    #      name='api_service_delete'),                                                      # MOVED → spa_services/

    # API endpoints for Appointments (Scheduler) - MOVED → appointments/
    # path('api/rooms/', views.api_rooms_list, name='api_rooms_list'),                   # MOVED → appointments/
    # path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),# MOVED → appointments/
    # path('api/appointments/create/', views.api_appointment_create,                     # MOVED → appointments/
    #      name='api_appointment_create'),                                                # MOVED → appointments/
    # path('api/appointments/<str:appointment_code>/', views.api_appointment_detail,      # MOVED → appointments/
    #      name='api_appointment_detail'),                                               # MOVED → appointments/
    # path('api/appointments/<str:appointment_code>/update/', views.api_appointment_update,# MOVED → appointments/
    #      name='api_appointment_update'),                                               # MOVED → appointments/
    # path('api/appointments/<str:appointment_code>/status/', views.api_appointment_status,# MOVED → appointments/
    #      name='api_appointment_status'),                                              # MOVED → appointments/
    # path('api/appointments/<str:appointment_code>/delete/', views.api_appointment_delete,# MOVED → appointments/
    #      name='api_appointment_delete'),                                               # MOVED → appointments/
    # path('api/booking-requests/', views.api_booking_requests, name='api_booking_requests'),# MOVED → appointments/
]
