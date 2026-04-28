# Cập nhật Layout Form "Tạo lịch hẹn"

## Thay đổi chính

### Trước đây:
- Mỗi khách chỉ có 1 dòng chính (tên, SĐT, dịch vụ, gói)
- Nhấn dấu 3 chấm → bung ra: Email, Trạng thái, Thanh toán, Ghi chú khách, Ghi chú nội bộ
- **Vấn đề**: Trạng thái và Thanh toán là field thao tác thường xuyên nhưng bị ẩn

### Sau khi sửa:
Mỗi khách giờ có **3 phần rõ ràng**:

#### 1. Dòng chính (luôn hiện):
- Số thứ tự
- Phòng · Giờ
- Tên khách + checkbox "= người đặt"
- SĐT
- Dịch vụ
- Gói
- Nút 3 chấm (expand)
- Nút xóa

#### 2. Dòng phụ (luôn hiện ngay dưới dòng chính):
- **Trạng thái** (Chờ xác nhận / Chưa đến / Đã đến / Hoàn thành / Đã hủy)
- **Thanh toán** (Chưa thanh toán / Một phần / Đã thanh toán)
- Khi chọn "Đã thanh toán" → hiện thêm: Phương thức, Số tiền thu

#### 3. Phần mở rộng (toggle bằng dấu 3 chấm):
- Email
- Ghi chú khách
- Ghi chú nội bộ
- Nút "Từ người đặt"

## Lợi ích

✅ **Trạng thái** và **Thanh toán** luôn thấy ngay → thao tác nhanh hơn  
✅ Form gọn hơn, logic hơn  
✅ Dấu 3 chấm chỉ dành cho thông tin phụ (email + ghi chú)  
✅ Dễ quét mắt, dễ nhập liệu  
✅ Không bị cảm giác quá nhiều field khi mở rộng  

## Files đã sửa

1. **static/js/admin-appointments.js**
   - Hàm `_buildGuestItem()`: Tách layout thành 3 phần
   - Hàm `toggleGuestCard()`: Giảm max-height từ 300px → 80px (vì phần mở rộng giờ nhỏ hơn)
   - Version: v20260422-004

2. **staticfiles/js/admin-appointments.js**
   - Đồng bộ từ static/

3. **templates/manage/pages/admin_appointments.html**
   - Cập nhật version query string: ?v=20260422-004

## Kiểm tra

Sau khi deploy, test các tình huống:
- Tạo lịch hẹn mới → kiểm tra Trạng thái + Thanh toán hiện ngay
- Nhấn dấu 3 chấm → chỉ hiện Email + 2 ghi chú
- Chọn "Đã thanh toán" → hiện Phương thức + Số tiền thu
- Responsive trên mobile
