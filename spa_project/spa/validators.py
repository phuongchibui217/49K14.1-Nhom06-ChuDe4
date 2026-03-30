"""
BACKWARD COMPATIBILITY WRAPPER

File này giữ lại để tương thích ngược. Tất cả validators đã được chuyển
sang core/validators.py. File này chỉ import lại từ core để code cũ vẫn chạy.

DEPRECATED: Vui lòng import trực tiếp từ core.validators
"""

# Import tất cả từ core.validators
from core.validators import *
