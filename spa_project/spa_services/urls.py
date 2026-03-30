"""
URL configuration cho spa_services app

Chứa URL patterns cho service management:
- Public service pages (list, detail)
- Admin service management
- API endpoints for services

Author: Spa ANA Team
"""

from django.urls import path
from . import views

app_name = 'spa_services'

urlpatterns = [
    # ============================================================
    # Public Service Pages
    # ============================================================
    path('services/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),

    # ============================================================
    # Admin Service Management
    # ============================================================
    path('manage/services/', views.admin_services, name='admin_services'),
    path('manage/services/<int:service_id>/edit/', views.admin_service_edit,
         name='admin_service_edit'),
    path('manage/services/<int:service_id>/delete/', views.admin_service_delete,
         name='admin_service_delete'),

    # ============================================================
    # API endpoints
    # ============================================================
    path('api/services/', views.api_services_list, name='api_services_list'),
    path('api/services/create/', views.api_service_create, name='api_service_create'),
    path('api/services/<int:service_id>/update/', views.api_service_update,
         name='api_service_update'),
    path('api/services/<int:service_id>/delete/', views.api_service_delete,
         name='api_service_delete'),
]
