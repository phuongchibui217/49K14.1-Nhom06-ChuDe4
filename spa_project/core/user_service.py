"""
User Service - Helper tạo tài khoản theo nghiệp vụ

Luồng:
- create_customer_user(): khách tự đăng ký -> group "Khách hàng" + CustomerProfile
- create_staff_user():    admin tạo nhân viên -> group "Lễ tân" + StaffProfile
"""

from django.contrib.auth.models import User, Group
from django.db import transaction


GROUP_CUSTOMER = 'Khách hàng'
GROUP_RECEPTIONIST = 'Lễ tân'
GROUP_MANAGER = 'Quản lí'


def _get_group(name: str) -> Group:
    """Lấy group theo tên, raise rõ ràng nếu không tồn tại."""
    try:
        return Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise ValueError(
            f"Group '{name}' chưa tồn tại trong database. "
            f"Vui lòng chạy: python manage.py sync_user_groups --init-groups"
        )


@transaction.atomic
def create_customer_user(username: str, password: str, full_name: str,
                         phone: str, email: str = '',
                         gender=None, dob=None, address=None) -> 'CustomerProfile':
    """
    Tạo tài khoản khách hàng:
    - User với is_staff=False, is_superuser=False
    - Gán group 'Khách hàng'
    - Tạo CustomerProfile
    """
    from customers.models import CustomerProfile

    group = _get_group(GROUP_CUSTOMER)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or '',
        is_staff=False,
        is_superuser=False,
    )
    user.groups.add(group)

    profile = CustomerProfile.objects.create(
        user=user,
        full_name=full_name,
        phone=phone,
        gender=gender,
        dob=dob,
        address=address or '',
    )
    return profile


@transaction.atomic
def create_staff_user(username: str, password: str, full_name: str,
                      phone: str, email: str = '',
                      is_superuser: bool = False) -> 'StaffProfile':
    """
    Tạo tài khoản nhân viên:
    - User với is_staff=True
    - Gán group 'Lễ tân' (mặc định) hoặc 'Quản lí' nếu is_superuser
    - Tạo StaffProfile
    """
    from staff.models import StaffProfile

    group_name = GROUP_MANAGER if is_superuser else GROUP_RECEPTIONIST
    group = _get_group(group_name)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or '',
        is_staff=True,
        is_superuser=is_superuser,
    )
    user.groups.add(group)

    profile = StaffProfile.objects.create(
        user=user,
        full_name=full_name,
        phone=phone,
    )
    return profile
