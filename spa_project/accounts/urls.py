from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('quen-mat-khau/', views.password_reset_request, name='password_reset'),
    path('reset-mat-khau/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]
