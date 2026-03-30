"""
URL configuration for spa app.

PHASE 8.6: DEPRECATED ROUTES - Đã chuyển sang các app riêng
=============================================================

File này chỉ giữ lại fallback routes để tránh lỗi.
Tất cả routes chính đã được chuyển sang các app:
- admin_panel (login, logout, profile)
- customers (manage customers)
- staff (manage staff)
- chat (live chat)
- appointments (booking)

Author: Spa ANA Team
"""
from django.urls import path
from . import views

app_name = 'spa'

urlpatterns = [
    # ============================================================
    # PHASE 8.6: MOVED → admin_panel/urls.py
    # ============================================================
    # path('manage/login/', views.admin_login, name='admin_login'),         # MOVED → admin_panel/
    # path('manage/logout/', views.admin_logout, name='admin_logout'),       # MOVED → admin_panel/
    # path('manage/profile/', views.admin_profile, name='admin_profile'),    # MOVED → admin_panel/

    # ============================================================
    # PHASE 8.6: MOVED → customers/urls.py
    # ============================================================
    # path('manage/customers/', views.admin_customers, name='admin_customers'),  # MOVED → customers/

    # ============================================================
    # PHASE 8.6: MOVED → staff/urls.py
    # ============================================================
    # path('manage/staff/', views.admin_staff, name='admin_staff'),  # MOVED → staff/

    # ============================================================
    # PHASE 8.6: MOVED → chat/urls.py
    # ============================================================
    # path('manage/live-chat/', views.admin_live_chat, name='admin_live_chat'),  # MOVED → chat/

    # ============================================================
    # PHASE 6: MOVED → appointments/urls.py
    # ============================================================
    # path('booking/', views.booking, name='booking'),  # MOVED → appointments/

    # ============================================================
    # LEGACY: Các routes cũ đã deprecated từ các phase trước
    # ============================================================
    # PHASE 3: Moved to pages/urls.py
    # PHASE 4: Moved to accounts/urls.py
    # PHASE 5: Moved to spa_services/urls.py
    # PHASE 6: Moved to appointments/urls.py
    # PHASE 7: Moved to complaints/urls.py

    # ============================================================
    # FALLBACK: Không còn route nào ở đây
    # ============================================================
    # Tất cả routes đã được chuyển sang apps riêng
    # File này chỉ còn lại để giữ cấu trúc project
]
