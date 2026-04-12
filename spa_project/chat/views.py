"""
Views cho Live Chat

File này chứa các views cho:
- Chat trực tuyến từ Admin Panel

Author: Spa ANA Team
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# =====================================================
# ADMIN LIVE CHAT VIEWS
# =====================================================

@login_required(login_url='accounts:login')
def admin_live_chat(request):
    """Chat trực tuyến"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')
    return render(request, 'chat/admin_live_chat.html')
