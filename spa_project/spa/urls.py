"""
URL configuration for spa app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.service_list, name='service_list'),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),
    path('booking/', views.booking, name='booking'),
    path('consultation/', views.consultation, name='consultation'),
    path('complaint/', views.complaint, name='complaint'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]