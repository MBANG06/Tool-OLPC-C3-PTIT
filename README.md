# 👑 MADE BY BANG DZ UwU 👑
## 🚀 ETS TOEIC OLPC - Auto Solver Portable (Toàn Trình 100%)

> **Tác giả:** BANG DZ UwU  
> **Dự án:** Bộ công cụ tự động hóa toàn trình khóa học **ETS TOEIC Online Practice Component (OLPC)**

---

### 🔥 Tính Năng Nổi Bật:
1. **Hoàn thành 100% tất cả các bài học (Lessons)**: Tự động gửi tiến độ qua API `SetProgressPerTask` với cơ chế chống giới hạn tần suất (Rate Limit retry).
2. **Giải đúng 100% toàn bộ bài kiểm tra bài học (Step 3: Test)**: Xử lý chính xác tất cả các dạng bài (`type 25` trắc nghiệm, `type 23` kéo thả, `type 51` hội thoại điền nhiều chỗ trống chuẩn Format A) và lưu điểm 100% vĩnh viễn trên máy chủ qua `SaveUserTest`.
3. **Trích xuất 100% đáp án chuẩn 30/30 câu của Unit Test**: Quét trực tiếp metadata đề thi của ETS, bóc tách chính xác vị trí đáp án đúng cho từng câu.
4. **Tự động làm và nộp bài Unit Test**: Đạt điểm tối đa **100/100**, bỏ qua audio/video, xử lý các màn hình hướng dẫn và nộp bài an toàn.
5. **Tự động đồng bộ giao diện và cơ sở dữ liệu**: Cập nhật tiến độ ngay trên trang chủ và lưu ảnh chụp màn hình xác thực điểm số.
6. **Bản quyền chính chủ**: Tích hợp biểu ngữ ASCII Art và chữ ký bản quyền `MADE BY BANG DZ UwU` trong terminal và tệp khởi động.

---

## 💻 Yêu Cầu Hệ Thống

1. **Hệ điều hành**: Windows 10/11
2. **Trình duyệt**: Google Chrome
3. **Python**: Phiên bản 3.9 trở lên (đã tích chọn `Add Python to PATH` khi cài đặt)

---

## ⚡ Hướng Dẫn Sử Dụng Nhanh (Dành cho người nhận script)

### Bước 1: Khởi động Chrome chế độ Debug
- Chạy file: **`start_chrome_debug.bat`** (Nhấp đúp chuột).
- Nếu Chrome đang mở bình thường, file sẽ hỏi và tự động khởi động lại Chrome với cổng kết nối an toàn `9222`.
- Trên cửa sổ Chrome vừa mở, **đăng nhập vào tài khoản TOEIC** của bạn nếu chưa đăng nhập.
- Điều hướng đến khóa học bạn muốn học (Module 1, Module 2 hoặc Module 3).

### Bước 2: Chạy bộ giải tự động
- Chạy file: **`run_solver.bat`** (Nhấp đúp chuột).
- Menu điều khiển trực quan:
  - Chọn `1` - `8`: Để giải một Unit cụ thể (Ví dụ: bấm `1` rồi Enter để giải Unit 1).
  - Chọn `A`: Để **tự động giải tuần tự toàn bộ cả 8 Unit** từ đầu đến cuối!
  - Chọn `L`: Để kiểm tra thông tin Module và tiến độ hiện tại.

---

## 🛠️ Sử Dụng Nâng Cao (Qua Command Line)

```powershell
# Xem hướng dẫn các tham số
python toeic_solver.py --help

# Giải Unit 1 của Module đang mở trong trình duyệt
python toeic_solver.py --unit 1

# Giải tự động toàn bộ 8 Unit của Module
python toeic_solver.py --all

# Ép chạy cho một Module cụ thể (1, 2, hoặc 3)
python toeic_solver.py --module 3 --unit 2

# Chỉ hoàn thành bài học (bỏ qua Unit Test)
python toeic_solver.py --unit 1 --skip-test

# Chỉ giải Unit Test (bỏ qua hoàn thành bài học)
python toeic_solver.py --unit 1 --only-test
```

---

## 📁 Thư Mục Kết Quả (`output/`)

Tất cả các tài nguyên tạo ra sẽ được lưu tự động trong thư mục `output/`:
- `unit{X}_answers_key.json`: Bộ 30 đáp án chi tiết trích xuất từ đề thi ETS.
- `unit{X}_100_final_verified.png`: Ảnh chụp màn hình điểm số 100/100 chính thức của Unit Test.
- `home_unit{X}_completed.png`: Ảnh chụp màn hình trang chủ đã hoàn thành 100%.

---

**Made with ❤️ by BANG DZ UwU**
