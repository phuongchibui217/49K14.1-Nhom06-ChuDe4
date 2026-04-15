"""
User Service - Helper tạo tài khoản theo nghiệp vụ

Luồng:
- create_customer_user(): khách tự đăng ký -> group "Khách hàng" + CustomerProfile
- create_staff_user():    admin tạo nhân viên -> group "Lễ tân" + StaffProfile
- ensure_staff_profile(): đảm bảo user staff luôn có StaffProfile (idempotent)
"""

from django.contrib.auth.models import User, Group
from django.db import transaction


GROUP_CUSTOMER = 'Khách hàng'
GROUP_RECEPTIONIST = 'Lễ tân'
GROUP_MANAGER = 'Quản lí'


def get_display_name(user: User) -> str:
    """
    Lấy tên hiển thị của user theo thứ tự ưu tiên:
    1. StaffProfile.full_name (nếu là staff)
    2. CustomerProfile.full_name (nếu là customer)
    3. User.get_full_name() (first_name + last_name)
    4. Fallback: username

    Dùng ở mọi nơi cần hiển thị tên nhân viên/người dùng ra ngoài.
    """
    if user is None:
        return 'Hệ thống'

    # Ưu tiên StaffProfile
    try:
        name = user.staff_profile.full_name
        if name and name.strip():
            return name.strip()
    except Exception:
        pass

    # Ưu tiên CustomerProfile
    try:
        name = user.customer_profile.full_name
        if name and name.strip():
            return name.strip()
    except Exception:
        pass

    # Django built-in full name
    name = user.get_full_name()
    if name and name.strip():
        return name.strip()

    return user.username


def _get_group(name: str) -> Group:
    """Lấy group theo tên, raise rõ ràng nếu không tồn tại."""
    try:
        return Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise ValueError(
            f"Group '{name}' chưa tồn tại trong database. "
            f"Vui lòng chạy: python manage.py sync_user_groups --init-groups"
        )


def ensure_staff_profile(user: User) -> 'StaffProfile':
    """
    Đảm bảo user staff luôn có đúng 1 StaffProfile. Idempotent — gọi nhiều lần an toàn.

    - Nếu đã có StaffProfile → trả về profile hiện tại, không tạo trùng.
    - Nếu chưa có → tạo mới với thông tin cơ bản từ User.

    Dùng ở:
    - staff/views.py khi update user thành staff
    - sync_user_groups khi backfill
    - Django admin save_model hook

    Args:
        user: User instance đã có is_staff=True hoặc is_superuser=True

    Returns:
        StaffProfile instance (mới hoặc đã tồn tại)
    """
    from staff.models import StaffProfile

    try:
        return user.staff_profile
    except StaffProfile.DoesNotExist:
        pass

    # Tạo profile với thông tin fallback từ User
    full_name = user.get_full_name() or user.username
    # Phone phải unique — dùng username làm placeholder nếu chưa có
    # (superuser/admin thường có username là tên, không phải SĐT)
    phone_candidate = user.username[:15]

    # Tránh trùng phone với profile khác
    if StaffProfile.objects.filter(phone=phone_candidate).exists():
        phone_candidate = f"staff_{user.pk}"[:15]

    profile = StaffProfile.objects.create(
        user=user,
        full_name=full_name,
        phone=phone_candidate,
    )
    return profile


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
