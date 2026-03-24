import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from spa.models import Service

# Check if services exist
if Service.objects.count() == 0:
    # Create sample services
    Service.objects.create(
        name='Cham Soc Da Chuyen Sau',
        category='skincare',
        short_description='Dieu tri mun, tai tao da, tre hoa da',
        description='Lieu trinh cham soc da chuyen sau voi cac san pham cao cap',
        price=1500000,
        duration_minutes=90,
        is_active=True
    )
    Service.objects.create(
        name='Massage Body Thu Gian',
        category='massage',
        short_description='Giam cang thang, thu gian co the',
        description='Massage toan body voi tinh dau nhien nhien',
        price=800000,
        duration_minutes=60,
        is_active=True
    )
    Service.objects.create(
        name='Phun Thew Moi & May',
        category='tattoo',
        short_description='Ky thuat 3D tu nhien, ben mau',
        description='Phun thew moi va may voi ky thuat 3D tu nhien',
        price=2500000,
        duration_minutes=120,
        is_active=True
    )
    Service.objects.create(
        name='Tiet Long Vinh Vien',
        category='hair',
        short_description='Cong nghie Diode Laser hien dai',
        description='Tiet long vinh vien voi cong nghie Diode Laser',
        price=800000,
        duration_minutes=45,
        is_active=True
    )
    print('Da tao 4 dich vu mau')
else:
    count = Service.objects.count()
    print(f'Da co {count} dich vu trong database')
    for s in Service.objects.all()[:5]:
        print(f' - {s.name}')
