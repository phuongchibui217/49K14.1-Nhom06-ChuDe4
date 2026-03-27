import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("=" * 60)
print("DANH SACH TAI KHOAN NHAN VIEN")
print("=" * 60)

staff_users = User.objects.filter(is_staff=True).order_by('-is_superuser', 'username')

for idx, user in enumerate(staff_users, 1):
    print(f"\n{idx}. Username: {user.username}")
    print(f"   Email: {user.email or 'Chưa cập nhật'}")
    print(f"   Vai trò: {'Super Admin' if user.is_superuser else 'Nhân viên'}")
    print(f"   Trạng thái: {'Hoạt động' if user.is_active else 'Khóa'}")

    # Try to authenticate with common passwords
    test_passwords = ['admin123', '123456', 'password', 'nhanvien1', user.username]
    password_found = None

    for pwd in test_passwords:
        if authenticate(username=user.username, password=pwd):
            password_found = pwd
            break

    if password_found:
        print(f"   Password: {password_found}")
    else:
        print(f"   Password: [Đã đặt password - Không hiển thị]")

print("\n" + "=" * 60)
print("HUONG DAN DANG NHAP:")
print("=" * 60)
print("1. Truy cap: http://127.0.0.1:8000/manage/login/")
print("2. Dang nhap voi tai khoan ben tren")
print("3. Neu quen mat khau, lien he admin de reset")
