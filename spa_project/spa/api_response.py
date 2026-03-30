"""
BACKWARD COMPATIBILITY WRAPPER

File này giữ lại để tương thích ngược. Tất cả API response helpers đã được chuyển
sang core/api_response.py. File này chỉ import lại từ core để code cũ vẫn chạy.

DEPRECATED: Vui lòng import trực tiếp từ core.api_response
"""

# Import tất cả từ core.api_response
from core.api_response import *
