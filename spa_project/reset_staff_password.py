import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import User

# Reset password for nhanvien1
try:
    user = User.objects.get(username='nhanvien1')
    user.set_password('nhanvien123')
    user.save()
    print("Password for 'nhanvien1' has been reset!")
    print("=" * 50)
    print("LOGIN INFORMATION:")
    print("=" * 50)
    print("Username: nhanvien1")
    print("Password: nhanvien123")
    print("Role: Staff (not superuser)")
    print("URL: http://127.0.0.1:8000/manage/login/")
    print("=" * 50)
except User.DoesNotExist:
    print("User 'nhanvien1' does not exist!")



# Truy cập: http://127.0.0.1:8000/manage/login/

# Đăng nhập với:

# Username: nhanvien1
# Password: nhanvien123
# Hoặc dùng admin:

# Username: admin
# Password: admin123