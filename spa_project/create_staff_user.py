import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import User

# Check existing staff users
staff_users = User.objects.filter(is_staff=True)
print(f'Total staff users: {staff_users.count()}')

for u in staff_users:
    print(f'- Username: {u.username}')
    print(f'  Superuser: {u.is_superuser}')
    print(f'  Active: {u.is_active}')
    print(f'  Email: {u.email}')
    print()

# If no staff users, create one
if staff_users.count() == 0:
    print('No staff users found. Creating a new staff user...')

    # Create staff user
    staff_user = User.objects.create_user(
        username='admin',
        email='admin@spaana.vn',
        password='admin123',  # Change this after first login!
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    print(f'Created staff user: {staff_user.username}')
    print(f'Password: admin123')
    print('Please change password after first login!')
else:
    print('Staff users already exist.')
