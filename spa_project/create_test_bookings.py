"""
TẠO TEST DATA CHO BOOKING FILTER
Chạy file này để tạo test data cho bộ lọc
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa_project.settings')
django.setup()

from appointments.models import Appointment
from spa_services.models import Service
from accounts.models import CustomerProfile
from datetime import date, time

def create_test_bookings():
    """Tạo test bookings với các status khác nhau"""

    try:
        # Lấy service và customer đầu tiên
        service = Service.objects.first()
        if not service:
            print("❌ Không tìm thấy service! Hãy tạo service trước.")
            return

        customer = CustomerProfile.objects.first()
        if not customer:
            print("❌ Không tìm thấy customer! Hãy tạo customer trước.")
            return

        print(f"✅ Dùng service: {service.name}")
        print(f"✅ Dùng customer: {customer.full_name}")

        # Xóa test bookings cũ (nếu có)
        deleted = Appointment.objects.filter(
            customer__full_name__contains="TEST BOOKING"
        ).delete()
        if deleted[0] > 0:
            print(f"🗑️ Đã xóa {deleted[0]} test bookings cũ")

        # Tạo bookings với các status khác nhau
        test_data = [
            {
                'appointment_code': 'TEST001',
                'status': 'pending',
                'time': time(9, 0),
                'notes': 'TEST BOOKING - Pending'
            },
            {
                'appointment_code': 'TEST002',
                'status': 'pending',
                'time': time(10, 0),
                'notes': 'TEST BOOKING - Pending 2'
            },
            {
                'appointment_code': 'TEST003',
                'status': 'pending',
                'time': time(11, 0),
                'notes': 'TEST BOOKING - Pending 3'
            },
            {
                'appointment_code': 'TEST004',
                'status': 'cancelled',
                'time': time(14, 0),
                'notes': 'TEST BOOKING - Cancelled'
            },
            {
                'appointment_code': 'TEST005',
                'status': 'not_arrived',
                'time': time(15, 0),
                'notes': 'TEST BOOKING - Not Arrived'
            },
            {
                'appointment_code': 'TEST006',
                'status': 'arrived',
                'time': time(16, 0),
                'notes': 'TEST BOOKING - Arrived'
            },
            {
                'appointment_code': 'TEST007',
                'status': 'completed',
                'time': time(17, 0),
                'notes': 'TEST BOOKING - Completed'
            },
        ]

        created_count = 0
        for data in test_data:
            try:
                # Kiểm tra xem booking đã tồn tại chưa
                if Appointment.objects.filter(appointment_code=data['appointment_code']).exists():
                    print(f"⏭️ Skipping {data['appointment_code']} (already exists)")
                    continue

                appointment = Appointment.objects.create(
                    appointment_code=data['appointment_code'],
                    customer=customer,
                    service=service,
                    room=None,  # Để trống, sẽ gán sau
                    appointment_date=date.today(),
                    appointment_time=data['time'],
                    duration_minutes=service.duration_minutes,
                    guests=1,
                    status=data['status'],
                    payment_status='unpaid',
                    source='web',
                    notes=data['notes'],
                    created_by=None  # Admin bookings
                )
                print(f"✅ Created {data['appointment_code']}: {data['status']}")
                created_count += 1
            except Exception as e:
                print(f"❌ Error creating {data['appointment_code']}: {e}")

        print(f"\n🎉 Đã tạo {created_count} test bookings!")

        # Hiển thị thống kê
        print("\n📊 THỐNG KÊ APPOINTMENTS:")
        for status in ['pending', 'not_arrived', 'arrived', 'completed', 'cancelled']:
            count = Appointment.objects.filter(status=status).count()
            print(f"  {status}: {count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 50)
    print("TẠO TEST DATA CHO BOOKING FILTER")
    print("=" * 50)
    create_test_bookings()
    print("\n✅ Done! Vào trang admin để test filter:")
    print("   http://127.0.0.1:8000/manage/appointments/")
    print("   → Click tab 'Yêu cầu đặt lịch'")
    print("   → Chọn filter và test!")
