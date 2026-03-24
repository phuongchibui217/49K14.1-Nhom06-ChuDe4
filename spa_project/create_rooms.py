"""
Script tạo Rooms cho Spa ANA
Chạy: python manage.py shell < create_rooms.py
HOẶC: python manage.py shell
>>> from create_rooms import *
>>> create_rooms()
"""

from spa.models import Room


def create_rooms():
    """Tạo 5 phòng mặc định cho Spa"""

    rooms_data = [
        {'code': 'P01', 'name': 'Phòng 1', 'capacity': 3},
        {'code': 'P02', 'name': 'Phòng 2', 'capacity': 2},
        {'code': 'P03', 'name': 'Phòng 3', 'capacity': 4},
        {'code': 'P04', 'name': 'Phòng 4', 'capacity': 2},
        {'code': 'P05', 'name': 'Phòng 5', 'capacity': 3},
    ]

    created_count = 0
    for room_data in rooms_data:
        code = room_data['code']
        # Check nếu room đã tồn tại
        if Room.objects.filter(code=code).exists():
            print(f"✓ Room {code} đã tồn tại, bỏ qua")
            continue

        Room.objects.create(**room_data)
        print(f"✓ Đã tạo room {code}")
        created_count += 1

    if created_count == 0:
        print("\n✓ Tất cả rooms đã tồn tại!")
    else:
        print(f"\n✓ Đã tạo {created_count} rooms mới!")

    # Hiển thị danh sách rooms
    print("\n=== DANH SÁCH PHÒNG ===")
    for room in Room.objects.all().order_by('code'):
        status = "✅ Hoạt động" if room.is_active else "❌ Ngừng hoạt động"
        print(f"{room.code} - {room.name} (Sức chứa: {room.capacity}) - {status}")


if __name__ == "__main__":
    create_rooms()
