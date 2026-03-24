"""
Appointment Services - Business logic cho Appointment model

File này chứa các hàm xử lý nghiệp vụ liên quan đến Appointment:
- Parse và validate dữ liệu từ request
- Tạo/Cập nhật lịch hẹn
- Helper functions cho serialization

Tách ra khỏi views.py để:
- Code gọn hơn, dễ đọc
- Dùng lại được ở nhiều nơi (DRY)
- Dễ test riêng biệt
"""

from datetime import datetime
from django.utils import timezone
from .models import Appointment, CustomerProfile, Service, Room
from .services import validate_appointment_create


# =====================================================
# PARSING SERVICES
# =====================================================

def parse_appointment_data(request_body, content_type=None):
    """
    Parse dữ liệu lịch hẹn từ request
    
    Hỗ trợ cả JSON và multipart/form-data
    
    Args:
        request_body: str hoặc request.POST - Dữ liệu từ request
        content_type: str - Content type header
        
    Returns:
        dict: Dữ liệu đã parse
    """
    import json
    
    data = {}
    
    # Check if multipart/form-data
    if content_type and 'multipart/form-data' in content_type:
        # Parse từ POST data
        data = {
            'customer_name': request_body.get('customerName', '').strip(),
            'phone': request_body.get('phone', '').strip(),
            'service_id': request_body.get('serviceId') or request_body.get('service'),
            'room_id': request_body.get('roomId') or request_body.get('room'),
            'date_str': request_body.get('date', ''),
            'time_str': request_body.get('time') or request_body.get('start', ''),
            'duration': request_body.get('duration') or request_body.get('durationMin', 60),
            'guests': request_body.get('guests', 1),
            'notes': request_body.get('note', ''),
            'status': request_body.get('apptStatus', 'not_arrived'),
            'pay_status': request_body.get('payStatus', 'unpaid'),
        }
    else:
        # Parse từ JSON
        try:
            json_data = json.loads(request_body)
            data = {
                'customer_name': json_data.get('customerName', '').strip(),
                'phone': json_data.get('phone', '').strip(),
                'service_id': json_data.get('serviceId') or json_data.get('service'),
                'room_id': json_data.get('roomId') or json_data.get('room'),
                'date_str': json_data.get('date', ''),
                'time_str': json_data.get('time') or json_data.get('start', ''),
                'duration': json_data.get('duration') or json_data.get('durationMin', 60),
                'guests': json_data.get('guests', 1),
                'notes': json_data.get('note', ''),
                'status': json_data.get('apptStatus', 'not_arrived'),
                'pay_status': json_data.get('payStatus', 'unpaid'),
            }
        except json.JSONDecodeError:
            pass
    
    return data


def validate_appointment_data(data, exclude_code=None):
    """
    Validate dữ liệu lịch hẹn
    
    Args:
        data: dict - Dữ liệu đã parse
        exclude_code: str - Mã lịch hẹn cần loại trừ (khi update)
        
    Returns:
        dict: {'valid': bool, 'errors': list, 'cleaned_data': dict}
    """
    errors = []
    cleaned_data = {}
    
    # Validate customer name
    customer_name = data.get('customer_name', '').strip()
    if not customer_name:
        errors.append('Vui lòng nhập tên khách hàng')
    else:
        cleaned_data['customer_name'] = customer_name
    
    # Validate phone
    phone = data.get('phone', '').strip()
    phone = ''.join(filter(str.isdigit, phone))  # Chỉ giữ số
    if not phone:
        errors.append('Vui lòng nhập số điện thoại')
    elif len(phone) < 10:
        errors.append('Số điện thoại không hợp lệ')
    else:
        cleaned_data['phone'] = phone
    
    # Validate service
    service_id = data.get('service_id')
    if not service_id:
        errors.append('Vui lòng chọn dịch vụ')
    else:
        try:
            service = Service.objects.get(id=service_id)
            cleaned_data['service'] = service
        except Service.DoesNotExist:
            errors.append('Dịch vụ không tồn tại')
    
    # Validate date
    date_str = data.get('date_str', '')
    if not date_str:
        errors.append('Vui lòng chọn ngày hẹn')
    else:
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            cleaned_data['appointment_date'] = appointment_date
        except ValueError:
            errors.append('Định dạng ngày không hợp lệ')
    
    # Validate time
    time_str = data.get('time_str', '')
    if not time_str:
        errors.append('Vui lòng chọn giờ hẹn')
    else:
        try:
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
            cleaned_data['appointment_time'] = appointment_time
        except ValueError:
            errors.append('Định dạng giờ không hợp lệ')
    
    # Validate duration
    duration = data.get('duration', 60)
    try:
        duration = int(duration)
        cleaned_data['duration_minutes'] = duration
    except (ValueError, TypeError):
        cleaned_data['duration_minutes'] = cleaned_data['service'].duration_minutes if 'service' in cleaned_data else 60
    
    # Validate room (optional)
    room_id = data.get('room_id')
    if room_id:
        try:
            room = Room.objects.get(code=room_id)
            cleaned_data['room'] = room
        except Room.DoesNotExist:
            cleaned_data['room'] = None
    else:
        cleaned_data['room'] = None
    
    # Validate guests
    guests = data.get('guests', 1)
    try:
        guests = int(guests)
        if guests < 1:
            guests = 1
        cleaned_data['guests'] = guests
    except (ValueError, TypeError):
        cleaned_data['guests'] = 1
    
    # Notes
    cleaned_data['notes'] = data.get('notes', '')
    
    # Status
    cleaned_data['status'] = data.get('status', 'not_arrived')
    cleaned_data['payment_status'] = data.get('pay_status', 'unpaid')
    
    # Nếu có lỗi cơ bản, return luôn
    if errors:
        return {'valid': False, 'errors': errors, 'cleaned_data': cleaned_data}
    
    # Validate nâng cao: ngày giờ và phòng trống
    if 'appointment_date' in cleaned_data and 'appointment_time' in cleaned_data:
        validation_result = validate_appointment_create(
            appointment_date=cleaned_data['appointment_date'],
            appointment_time=cleaned_data['appointment_time'],
            duration_minutes=cleaned_data['duration_minutes'],
            room_code=room_id if room_id else None,
            exclude_appointment_code=exclude_code
        )
        
        if not validation_result['valid']:
            errors.extend(validation_result['errors'])
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'cleaned_data': cleaned_data
    }


# =====================================================
# CRUD SERVICES
# =====================================================

def get_or_create_customer(phone, customer_name):
    """
    Lấy hoặc tạo khách hàng
    
    Args:
        phone: str - Số điện thoại
        customer_name: str - Tên khách hàng
        
    Returns:
        CustomerProfile: Khách hàng
    """
    customer, created = CustomerProfile.objects.get_or_create(
        phone=phone,
        defaults={'full_name': customer_name}
    )
    
    # Cập nhật tên nếu khác
    if not created and customer.full_name != customer_name:
        customer.full_name = customer_name
        customer.save()
    
    return customer


def create_appointment(data, created_by=None):
    """
    Tạo lịch hẹn mới
    
    Args:
        data: dict - Dữ liệu đã validate
        created_by: User - Người tạo
        
    Returns:
        tuple: (appointment: Appointment|None, error: str|None)
    """
    # Validate data
    validation = validate_appointment_data(data)
    if not validation['valid']:
        return (None, validation['errors'][0])
    
    cleaned = validation['cleaned_data']
    
    # Get hoặc tạo customer
    customer = get_or_create_customer(
        phone=cleaned['phone'],
        customer_name=cleaned['customer_name']
    )
    
    try:
        appointment = Appointment.objects.create(
            customer=customer,
            service=cleaned['service'],
            room=cleaned.get('room'),
            appointment_date=cleaned['appointment_date'],
            appointment_time=cleaned['appointment_time'],
            duration_minutes=cleaned['duration_minutes'],
            guests=cleaned['guests'],
            notes=cleaned['notes'],
            status=cleaned['status'],
            payment_status=cleaned['payment_status'],
            source='admin',
            created_by=created_by,
        )
        
        return (appointment, None)
        
    except Exception as e:
        return (None, f'Lỗi khi tạo lịch hẹn: {str(e)}')


def update_appointment(appointment, data):
    """
    Cập nhật lịch hẹn
    
    Args:
        appointment: Appointment - Lịch hẹn cần cập nhật
        data: dict - Dữ liệu mới
        
    Returns:
        tuple: (appointment: Appointment|None, error: str|None)
    """
    # Validate data (exclude current appointment)
    validation = validate_appointment_data(data, exclude_code=appointment.appointment_code)
    if not validation['valid']:
        return (None, validation['errors'][0])
    
    cleaned = validation['cleaned_data']
    
    try:
        # Update customer info
        if 'customer_name' in cleaned:
            appointment.customer.full_name = cleaned['customer_name']
        if 'phone' in cleaned:
            appointment.customer.phone = cleaned['phone']
        appointment.customer.save()
        
        # Update appointment fields
        if 'service' in cleaned:
            appointment.service = cleaned['service']
        if 'room' in cleaned:
            appointment.room = cleaned['room']
        if 'appointment_date' in cleaned:
            appointment.appointment_date = cleaned['appointment_date']
        if 'appointment_time' in cleaned:
            appointment.appointment_time = cleaned['appointment_time']
        if 'duration_minutes' in cleaned:
            appointment.duration_minutes = cleaned['duration_minutes']
        if 'guests' in cleaned:
            appointment.guests = cleaned['guests']
        if 'notes' in cleaned:
            appointment.notes = cleaned['notes']
        if 'status' in cleaned:
            appointment.status = cleaned['status']
        if 'payment_status' in cleaned:
            appointment.payment_status = cleaned['payment_status']
        
        appointment.save()
        
        return (appointment, None)
        
    except Exception as e:
        return (None, f'Lỗi khi cập nhật lịch hẹn: {str(e)}')


# =====================================================
# SERIALIZATION SERVICES
# =====================================================

def serialize_appointment(appointment):
    """
    Serialize lịch hẹn thành dict (cho API response)
    
    Args:
        appointment: Appointment - Lịch hẹn cần serialize
        
    Returns:
        dict: Dữ liệu lịch hẹn
    """
    return {
        'id': appointment.appointment_code,
        'customerName': appointment.customer.full_name,
        'phone': appointment.customer.phone,
        'email': getattr(appointment.customer.user, 'email', '') if appointment.customer.user else '',
        'service': appointment.service.name,
        'serviceId': appointment.service.id,
        'roomId': appointment.room.code if appointment.room else '',
        'roomName': appointment.room.name if appointment.room else '',
        'guests': appointment.guests,
        'date': appointment.appointment_date.strftime('%Y-%m-%d'),
        'start': appointment.appointment_time.strftime('%H:%M'),
        'end': appointment.get_end_time_display(),
        'durationMin': appointment.duration_minutes or appointment.service.duration_minutes,
        'note': appointment.notes or '',
        'apptStatus': appointment.status,
        'payStatus': appointment.payment_status,
        'source': appointment.source,
    }


def serialize_appointments(appointments):
    """
    Serialize danh sách lịch hẹn
    
    Args:
        appointments: QuerySet - Danh sách lịch hẹn
        
    Returns:
        list: Danh sách dữ liệu lịch hẹn
    """
    return [serialize_appointment(appt) for appt in appointments]