"""
BACKWARD COMPATIBILITY WRAPPER

File này giữ lại để tương thích ngược. Tất cả decorators đã được chuyển
sang core/decorators.py. File này chỉ import lại từ core để code cũ vẫn chạy.

DEPRECATED: Vui lòng import trực tiếp từ core.decorators
"""

# Import tất cả từ core.decorators
from core.decorators import *
