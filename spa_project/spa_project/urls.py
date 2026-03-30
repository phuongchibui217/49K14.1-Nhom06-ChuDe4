"""
URL configuration for spa_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Phase 3: Pages app (static pages: home, about)
    path('', include('pages.urls')),
    # Phase 4: Accounts app (authentication, customer profile)
    path('', include('accounts.urls')),
    # Phase 5: Spa Services app (dịch vụ spa) có API
    path('', include('spa_services.urls')),
    # Phase 6: Appointments app (đặt lịch)  có API
    path('', include('appointments.urls')),
    # Phase 7: Complaints app (quản lý khiếu nại)
    path('', include('complaints.urls')),
    # Phase 8.5: Admin Panel (login, logout, profile)
    path('', include('admin_panel.urls')),
    # Phase 8.6: Customer Management (admin manage customers)
    path('', include('customers.urls')),
    # Phase 8.7: Staff Management (admin manage staff)
    path('', include('staff.urls')),
    # Phase 8.8: Live Chat (admin live chat)
    path('', include('chat.urls')),
    # Original spa app (keeping for now - will be deprecated)
    path('', include('spa.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)