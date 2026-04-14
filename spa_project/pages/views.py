"""
Views cho trang tĩnh (Static Pages)

File này chứa các views cho:
- Trang chủ (home)
- Giới thiệu (about)

Author: Spa ANA Team
"""

from django.shortcuts import render
from spa_services.models import Service


def home(request):
    """
    Trang chủ - Hiển thị 6 dịch vụ active

    Args:
        request: HttpRequest

    Returns:
        HttpResponse: Render template spa/pages/home.html
    """
    # Lấy 6 dịch vụ active đầu tiên
    services = Service.objects.filter(status='ACTIVE')[:6]

    return render(request, 'pages/home.html', {'services': services})


def about(request):
    """
    Trang giới thiệu về Spa ANA

    Args:
        request: HttpRequest

    Returns:
        HttpResponse: Render template spa/pages/about.html
    """
    return render(request, 'pages/about.html')
