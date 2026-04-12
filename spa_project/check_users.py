import os
import sys
import django

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import CustomerProfile

print('=== USERS IN DATABASE ===')
users = User.objects.all()

if not users:
    print('Chưa có user nào trong database!')
else:
    for u in users:
        has_profile = hasattr(u, 'customer_profile')
        profile_info = ''
        if has_profile:
            profile_info = f', Profile: {u.customer_profile.full_name}'

        print(f'Username: {u.username}, Email: {u.email}, is_staff: {u.is_staff}, is_superuser: {u.is_superuser}{profile_info}')

print(f'\nTotal users: {users.count()}')
