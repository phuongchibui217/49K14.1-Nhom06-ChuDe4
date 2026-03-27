import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("=" * 50)
print("STAFF USERS LOGIN INFORMATION")
print("=" * 50)

staff_users = User.objects.filter(is_staff=True).order_by('-is_superuser', 'username')

for idx, user in enumerate(staff_users, 1):
    print(f"\nUser #{idx}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email or 'Not set'}")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Active: {user.is_active}")

    # Try to authenticate with common passwords
    test_passwords = ['admin123', '123456', 'password', 'nhanvien1', user.username]
    password_found = None

    for pwd in test_passwords:
        try:
            if authenticate(username=user.username, password=pwd):
                password_found = pwd
                break
        except:
            pass

    if password_found:
        print(f"Password: {password_found}")
    else:
        print("Password: [Already set - Try common passwords]")

print("\n" + "=" * 50)
print("LOGIN URL: http://127.0.0.1:8000/manage/login/")
print("=" * 50)
