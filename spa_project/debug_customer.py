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

from django.contrib.auth import authenticate
from accounts.models import CustomerProfile

print('=== DEBUG CUSTOMER LOGIN ===\n')

# Test authenticate customer
phone = '0901234567'
password = 'customer123'

print(f'1. Testing authenticate for {phone}...')
user = authenticate(username=phone, password=password)

if user:
    print(f'   ✅ Authenticate SUCCESS')
    print(f'   Username: {user.username}')
    print(f'   Email: {user.email}')
    print(f'   is_staff: {user.is_staff}')
    print(f'   is_superuser: {user.is_superuser}')
    print(f'   is_active: {user.is_active}')
    print(f'   is_authenticated: {user.is_authenticated}')

    print(f'\n2. Checking CustomerProfile...')
    try:
        profile = CustomerProfile.objects.get(user=user)
        print(f'   ✅ CustomerProfile EXISTS')
        print(f'   ID: {profile.id}')
        print(f'   Full Name: {profile.full_name}')
        print(f'   Phone: {profile.phone}')
        print(f'   Email: {profile.email}')
        print(f'   Address: {profile.address}')
        print(f'   Gender: {profile.gender}')
    except CustomerProfile.DoesNotExist:
        print(f'   ❌ CustomerProfile DOES NOT EXIST')
        print(f'   This is the problem!')

    # Test accessing via user.customer_profile
    print(f'\n3. Testing hasattr(user, "customer_profile")...')
    has_attr = hasattr(user, 'customer_profile')
    print(f'   hasattr result: {has_attr}')

    if has_attr:
        print(f'   Trying to access user.customer_profile...')
        try:
            profile = user.customer_profile
            print(f'   ✅ SUCCESS: {profile.full_name}')
        except Exception as e:
            print(f'   ❌ ERROR: {type(e).__name__}: {e}')
    else:
        print(f'   ❌ hasattr returned False')

    # Test alternate method
    print(f'\n4. Testing CustomerProfile.objects.filter(user=user).exists()...')
    exists = CustomerProfile.objects.filter(user=user).exists()
    print(f'   Result: {exists}')

else:
    print(f'   ❌ Authenticate FAILED')
    print(f'   Check username/password again')
