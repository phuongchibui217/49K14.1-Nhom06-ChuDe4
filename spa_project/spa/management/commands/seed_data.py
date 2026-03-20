from django.core.management.base import BaseCommand
from django.utils.text import slugify
from spa.models import Service
import sys


def safe_write(message):
    """Write message with UTF-8 encoding support"""
    try:
        sys.stdout.write(message + '\n')
    except UnicodeEncodeError:
        # Fallback to ASCII if UTF-8 fails
        sys.stdout.write(message.encode('ascii', 'ignore').decode('ascii') + '\n')
    sys.stdout.flush()


class Command(BaseCommand):
    help = 'Seed demo services data for Spa ANA'

    def handle(self, *args, **options):
        # Define demo services
        demo_services = [
            # CHĂM SÓC DA
            {
                'name': 'Chăm sóc da mặt cơ bản',
                'category': 'skincare',
                'short_description': 'Làm sạch sâu, dưỡng ẩm da mặt',
                'description': 'Dịch vụ chăm sóc da mặt cơ bản bao gồm: làm sạch sâu, tẩy da chết, xông hơi, massage nhẹ, đắp mặt nạ dưỡng ẩm. Giúp da mặt sạch sẽ, thông thoáng lỗ chân lông và căng mịn tức thì.',
                'price': 300000,
                'duration_minutes': 60,
            },
            {
                'name': 'Chăm sóc da mặt cao cấp',
                'category': 'skincare',
                'short_description': 'Điều trị mụn, dưỡng trắng chuyên sâu',
                'description': 'Liệu trình chăm sóc da chuyên sâu với công nghệ cao: soi da miễn phí, lấy nhân mụn, điện tím diệp đèn, điện di tinh chất vitamin C, collagen. Giúp điều trị mụn, dưỡng trắng, trẻ hóa da.',
                'price': 600000,
                'duration_minutes': 90,
            },
            {
                'name': 'Chăm sóc da toàn thân',
                'category': 'skincare',
                'short_description': 'Tắm trắng, dưỡng ẩm toàn thân',
                'description': 'Dịch vụ chăm sóc da toàn thân với: tắm trắng thiên nhiên, tẩy da chết toàn thân, ướp tinh bột nghệ, massage thư giãn, đắp mặt nạ dưỡng ẩm. Giúp da trắng hồng, mịn màng.',
                'price': 800000,
                'duration_minutes': 120,
            },

            # MASSAGE
            {
                'name': 'Massage body cổ truyền',
                'category': 'massage',
                'short_description': 'Massage thư giãn toàn thân',
                'description': 'Massage body theo phương pháp cổ truyền Việt Nam với tinh dầu thiên nhiên. Giúp thư giãn cơ bắp, giảm đau mỏi, tăng cường lưu thông máu. Các bộ phận được massage: đầu, vai, gáy, lưng, tay, chân.',
                'price': 350000,
                'duration_minutes': 60,
            },
            {
                'name': 'Massage đá nóng',
                'category': 'massage',
                'short_description': 'Massage với đá nóng thủy tinh',
                'description': 'Kết hợp massage truyền thống với đá nóng thủy tinh. Nhiệt từ đá giúp thư giãn sâu cơ bắp, giải độc tố, tăng cường trao đổi chất. Rất tốt cho người hay đau mỏi vai gáy, lưng.',
                'price': 500000,
                'duration_minutes': 90,
            },
            {
                'name': 'Massage chân trị liệu',
                'category': 'massage',
                'short_description': 'Massage chân và ấn huyệt đạo',
                'description': 'Massage chân chuyên sâu với kỹ thuật ấn huyệt đạo. Giúp giảm đau mỏi chân, cải thiện tuần hoàn, tốt cho giấc ngủ. Bao gồm: ngâm chân thảo dược, massage bàn chân, bắp chân, đầu gối.',
                'price': 250000,
                'duration_minutes': 45,
            },

            # TRIỆT LÔNG
            {
                'name': 'Triệt lông nách',
                'category': 'hair',
                'short_description': 'Triệt lông nách vĩnh viễn',
                'description': 'Triệt lông nách bằng công nghệ IPL tiên tiến. Giúp giảm lông nhanh chóng, an toàn, không đau, không viêm lỗ chân lông. Liệu trình 10 buổi đảm bảo lông mọc lại ít và thưa.',
                'price': 200000,
                'duration_minutes': 30,
            },
            {
                'name': 'Triệt lông toàn chân',
                'category': 'hair',
                'short_description': 'Triệt lông chân vĩnh viễn',
                'description': 'Triệt lông chân từ đùi đến mắt cá chân bằng công nghệ IPL. Hiệu quả triệt lông lên đến 95%, không đau, an toàn cho da. Lông mọc lại mềm và thưa hơn.',
                'price': 500000,
                'duration_minutes': 60,
            },
            {
                'name': 'Triệt lông bikini',
                'category': 'hair',
                'short_description': 'Triệt lông vùng bikini',
                'description': 'Triệt lông vùng bikini nhẹ nhàng, không đau, đảm bảo vệ sinh. Công nghệ IPL an toàn cho vùng da nhạy cảm, giúp tự tin hơn.',
                'price': 300000,
                'duration_minutes': 45,
            },

            # PHUN THÊU
            {
                'name': 'Phun mày Hàn Quốc',
                'category': 'tattoo',
                'short_description': 'Phun mày kiểu Hàn Quốc tự nhiên',
                'description': 'Phun mày theo công nghệ Hàn Quốc tạo dáng mày tự nhiên, mềm mại. Màu mày chuẩn, giữ màu lâu (3-5 năm). Kỹ thuật phun điệu đà, không sưng không pain.',
                'price': 800000,
                'duration_minutes': 90,
            },
            {
                'name': 'Phun môi hồng tự nhiên',
                'category': 'tattoo',
                'short_description': 'Phun môi căng mọng, hồng tươi',
                'description': 'Phun môi công nghệ mới giúp môi căng mọng, màu hồng tươi tự nhiên. Cam kết không sưng nề, không đau, ăn uống bình thường ngay sau khi phun. Màu giữ 3-5 năm.',
                'price': 1000000,
                'duration_minutes': 120,
            },
            {
                'name': 'Phun mí mắt hòa trộn',
                'category': 'tattoo',
                'short_description': 'Phun mí mắt tạo rõ đường mí',
                'description': 'Phun mí mắt công nghệ hòa trộn tạo đường mí mắt rõ, tự nhiên. Giúp mắt to tròn, có thần thái hơn. Không sưng nề, không đau, màu giữ 2-3 năm.',
                'price': 700000,
                'duration_minutes': 60,
            },

            # LÀM MÓNG
            {
                'name': 'Làm móng cơ bản',
                'category': 'nails',
                'short_description': 'Cắt, dũa, sơn phủ móng',
                'description': 'Dịch vụ làm móng cơ bản bao gồm: ngâm mềm da, cắt da, dũa tạo hình, sơn phủ. Giúp móng đẹp, sạch sẽ và khỏe mạnh.',
                'price': 100000,
                'duration_minutes': 45,
            },
            {
                'name': 'Gắn móng gel Hàn Quốc',
                'category': 'nails',
                'short_description': 'Gắn móng gel bền đẹp',
                'description': 'Gắn móng gel theo công nghệ Hàn Quốc. Móng bền, đẹp, tự nhiên, không bị ố vàng. Nhiều mẫu mã trang trí đa dạng: đính đá, vẽ hoa, sơn gradient...',
                'price': 250000,
                'duration_minutes': 90,
            },
            {
                'name': 'Trọn gói tay chân',
                'category': 'nails',
                'short_description': 'Làm móng cả tay và chân',
                'description': 'Combo làm đẹp cả tay và chân: ngâm mềm, cắt da, dũa, sơn gel. Giúp đôi tay chân đẹp, mềm mại, quyến rũ. Tặng kèm massage nhẹ.',
                'price': 400000,
                'duration_minutes': 150,
            },
        ]

        # Count created/updated
        created_count = 0
        updated_count = 0

        safe_write('Seeding demo services data...')

        for service_data in demo_services:
            # Generate slug from name
            slug = slugify(service_data['name'])

            # Check if service exists
            existing_service = Service.objects.filter(slug=slug).first()

            if existing_service:
                # Update existing service
                for key, value in service_data.items():
                    setattr(existing_service, key, value)
                existing_service.save()
                updated_count += 1
                safe_write(f'  Updated: {service_data["name"]}')
            else:
                # Create new service
                Service.objects.create(**service_data)
                created_count += 1
                safe_write(f'  Created: {service_data["name"]}')

        # Summary
        total_services = Service.objects.count()
        safe_write('\nSeeding completed!')
        safe_write(f'  Total services: {total_services}')
        safe_write(f'  Created: {created_count}')
        safe_write(f'  Updated: {updated_count}')

        # Show breakdown by category
        safe_write('\nServices by category:')
        for category_value, category_name in Service.CATEGORY_CHOICES:
            count = Service.objects.filter(category=category_value, is_active=True).count()
            if count > 0:
                safe_write(f'  {category_name}: {count} services')
