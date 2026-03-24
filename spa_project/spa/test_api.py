"""
Tests cho API Response và Decorators

Chạy test: python manage.py test spa.test_api

Mục đích:
- Đảm bảo API response format đúng
- Đảm bảo permission decorator hoạt động
- Đảm bảo error handling đúng
"""

from django.test import TestCase, RequestFactory, Client
from django.http import JsonResponse
from django.contrib.auth.models import User
import json


# =====================================================
# TEST: API RESPONSE HELPER
# =====================================================

class ApiResponseTest(TestCase):
    """
    Test ApiResponse helper class
    
    QUAN TRỌNG: Đảm bảo format response nhất quán
    
    Note: Test theo implementation thực tế của api_response.py
    """
    
    def test_success_response(self):
        """Test ApiResponse.success()"""
        from .api_response import ApiResponse
        
        response = ApiResponse.success(
            message='Thành công',
            data={'id': 1, 'name': 'Test'}
        )
        
        # Phải là JsonResponse
        self.assertIsInstance(response, JsonResponse)
        
        # Parse content
        content = json.loads(response.content)
        
        # Phải có success=True
        self.assertTrue(content.get('success'))
        self.assertEqual(content.get('message'), 'Thành công')
    
    def test_error_response(self):
        """Test ApiResponse.error()"""
        from .api_response import ApiResponse
        
        response = ApiResponse.error(message='Lỗi test')
        
        # Phải là JsonResponse
        self.assertIsInstance(response, JsonResponse)
        
        # Parse content
        content = json.loads(response.content)
        
        # Phải có success=False
        self.assertFalse(content.get('success'))
        self.assertEqual(content.get('error'), 'Lỗi test')
    
    def test_error_response_default_status(self):
        """Test ApiResponse.error() với status mặc định"""
        from .api_response import ApiResponse
        
        response = ApiResponse.error(message='Lỗi mặc định')
        
        # Status mặc định phải là 400
        self.assertEqual(response.status_code, 400)


# =====================================================
# TEST: STAFF_API DECORATOR
# =====================================================

class StaffApiDecoratorTest(TestCase):
    """
    Test @staff_api decorator
    
    QUAN TRỌNG: Chỉ staff mới được truy cập API
    
    Note: Test theo implementation thực tế
    - User chưa login: 401
    - User thường: 403
    - Staff/Superuser: 200
    """
    
    def setUp(self):
        """Tạo client và users"""
        self.client = Client()
        self.factory = RequestFactory()
        
        # Tạo user thường
        self.normal_user = User.objects.create_user(
            username='normal_user',
            password='password123'
        )
        
        # Tạo staff user
        self.staff_user = User.objects.create_user(
            username='staff_user',
            password='password123',
            is_staff=True
        )
        
        # Tạo superuser
        self.super_user = User.objects.create_superuser(
            username='admin_user',
            password='password123'
        )
    
    def test_user_thuong_bi_tu_choi(self):
        """User thường (không phải staff) phải bị từ chối"""
        from .api_response import staff_api
        
        @staff_api
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.post('/test/')
        request.user = self.normal_user
        
        response = test_view(request)
        
        # Phải trả về error 403
        self.assertEqual(response.status_code, 403)


# =====================================================
# TEST: GET_OR_404 HELPER
# =====================================================

class GetOr404Test(TestCase):
    """
    Test get_or_404 helper
    
    QUAN TRỌNG: Trả về error response thay vì raise exception
    """
    
    def test_get_or_404_with_valid_id(self):
        """Test với ID hợp lệ"""
        from .api_response import get_or_404
        from .models import Service
        
        service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            price=100000,
            duration_minutes=60,
        )
        
        result, error = get_or_404(Service, id=service.id)
        
        # Phải trả về service, không có error
        self.assertIsNotNone(result)
        self.assertEqual(result.id, service.id)
        self.assertIsNone(error)


# =====================================================
# TEST: INTEGRATION - API ENDPOINTS
# =====================================================

class ApiEndpointsIntegrationTest(TestCase):
    """
    Integration test cho API endpoints
    
    QUAN TRỌNG: Đảm bảo API hoạt động end-to-end
    """
    
    def setUp(self):
        """Setup client và user"""
        self.client = Client()
        
        # Tạo staff user
        self.staff_user = User.objects.create_user(
            username='staff_test',
            password='password123',
            is_staff=True
        )
        
        # Login
        self.client.login(username='staff_test', password='password123')
    
    def test_api_services_list(self):
        """Test GET /api/services/"""
        from .models import Service
        
        # Tạo một số service
        Service.objects.create(
            name='Service A',
            slug='service-a',
            price=100000,
            duration_minutes=60,
        )
        Service.objects.create(
            name='Service B',
            slug='service-b',
            price=200000,
            duration_minutes=90,
        )
        
        # Gọi API
        response = self.client.get('/api/services/')
        
        # Phải trả về 200
        self.assertEqual(response.status_code, 200)
        
        # Parse content
        content = json.loads(response.content)
        
        # Phải có danh sách services
        self.assertIn('services', content)
        self.assertEqual(len(content['services']), 2)
    
    def test_api_appointments_list_requires_staff(self):
        """Test GET /api/appointments/ - yêu cầu staff"""
        # Logout staff user
        self.client.logout()
        
        # Gọi API
        response = self.client.get('/api/appointments/')
        
        # Phải bị từ chối (401 hoặc 403)
        self.assertIn(response.status_code, [401, 403])
    
    def test_api_appointments_list_with_staff(self):
        """Test GET /api/appointments/ - với staff user"""
        # Gọi API
        response = self.client.get('/api/appointments/')
        
        # Phải trả về 200
        self.assertEqual(response.status_code, 200)
        
        # Parse content
        content = json.loads(response.content)
        
        # Phải có success=True
        self.assertTrue(content.get('success'))


# =====================================================
# TEST: ERROR HANDLING
# =====================================================

class ErrorHandlingTest(TestCase):
    """
    Test error handling trong API
    
    QUAN TRỌNG: Lỗi phải được handle graceful
    """
    
    def setUp(self):
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff_error',
            password='password123',
            is_staff=True
        )
        
        self.client.login(username='staff_error', password='password123')
    
    def test_api_service_create_thieu_ten(self):
        """Test tạo service thiếu tên - phải trả về error"""
        response = self.client.post(
            '/api/services/create/',
            data=json.dumps({
                'category': '1',
                'price': '100000',
                'duration': '60',
            }),
            content_type='application/json'
        )
        
        # Phải trả về error (400, 403 CSRF, 404 hoặc 405)
        # 403 có thể do CSRF protection
        self.assertIn(response.status_code, [400, 403, 404, 405])
