# 📘 HƯỚNG DẪN SỬ DỤNG CHI TIẾT - ETS TOEIC OLPC AUTO SOLVER
### ★ ★ ★ MADE BY BANG DZ UwU ★ ★ ★

Chào mừng bạn đến với bộ công cụ tự động hóa giải bài tập và bài thi **ETS TOEIC Online Practice Component (OLPC)**!  
Bộ công cụ này giúp bạn đạt **100% tiến độ bài học (Lessons)** và **100/100 điểm tuyệt đối mọi bài kiểm tra (Unit Test, Midterm, Final Test)** chỉ với vài cú nhấp chuột.

---

## 📋 MỤC LỤC
1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Hướng dẫn cài đặt nhanh trong 1 phút](#2-hướng-dẫn-cài-đặt-nhanh-trong-1-phút)
3. [Quy trình sử dụng (Chỉ 2 bước)](#3-quy-trình-sử-dụng-chỉ-2-bước)
4. [Các tính năng trong Menu điều khiển](#4-các-tính-năng-trong-menu-điều-khiển)
5. [Giải bài thi Midterm và Final Test (Assessment Center)](#5-giải-bài-thi-midterm-và-final-test)
6. [Các lỗi thường gặp và cách khắc phục](#6-các-lỗi-thường-gặp-và-cách-khắc-phục)

---

## 1. Yêu cầu hệ thống

- **Hệ điều hành**: Windows 10 hoặc Windows 11.
- **Trình duyệt**: Google Chrome (bản mới nhất).
- **Python**: Phiên bản 3.9 trở lên ([Tải tại đây](https://www.python.org/downloads/)).
  > ⚠️ **CỰC KỲ QUAN TRỌNG KHI CÀI PYTHON**: Lúc vừa mở file cài đặt Python lên, bạn **BẮT BUỘC** phải tích chọn ô **`Add python.exe to PATH`** ở góc dưới cùng màn hình trước khi nhấn Install!

---

## 2. Hướng dẫn cài đặt nhanh trong 1 phút

1. Tải bộ công cụ về máy và giải nén (ví dụ ra màn hình Desktop hoặc thư mục bạn muốn).
2. Thư mục sau khi giải nén gồm có:
   - 📄 `start_chrome_debug.bat` : File mở Chrome ở chế độ kết nối tự động.
   - 📄 `run_solver.bat` : File khởi chạy Menu giải bài tập.
   - 📄 `toeic_solver.py` : Trái tim của bộ giải tự động (All-in-one).
   - 📁 `data/` : Chứa sẵn toàn bộ đáp án chuẩn 100% từ đề thi ETS.
   - 📁 `output/` : Thư mục lưu ảnh chụp màn hình điểm số và kết quả.

---

## 3. Quy trình sử dụng (Chỉ 2 bước)

### 🔹 Bước 1: Mở Chrome kết nối tự động
- Nhấp đúp chuột vào file **`start_chrome_debug.bat`**.
- File sẽ kiểm tra và mở trình duyệt Google Chrome với cổng kết nối an toàn `9222`.
- Trên cửa sổ Chrome vừa mở:
  1. Đăng nhập tài khoản TOEIC của bạn (nếu chưa đăng nhập).
  2. Vào trang chủ khóa học của bạn (Module 1, 2 hoặc 3).

### 🔹 Bước 2: Bật bộ giải tự động
- Nhấp đúp chuột vào file **`run_solver.bat`**.
- Lần đầu tiên chạy, chương trình sẽ tự động cài thư viện `websockets` (nếu chưa có).
- Bảng menu trực quan sẽ hiện ra, bạn chỉ cần gõ phím tương ứng và nhấn `Enter`:
  - Nhập **`1`** đến **`8`**: Để hoàn thành trọn gói Unit tương ứng (Bài học 100% + Unit Test 100/100).
  - Nhập **`A`**: **TỰ ĐỘNG GIẢI TOÀN BỘ CẢ 8 UNITS** liên tục từ Unit 1 đến Unit 8!
  - Nhập **`S`**: Xem bảng điểm và tiến độ tất cả các Module.

---

## 4. Các tính năng trong Menu điều khiển

| Phím chọn | Ý nghĩa chức năng | Chi tiết hoạt động |
| :---: | :--- | :--- |
| **`1` - `8`** | Giải trọn gói 1 Unit | Vừa hoàn thành 100% bài học (Lessons/Step Tests) vừa làm Unit Test đạt 100/100 |
| **`A`** | Chạy toàn bộ 8 Units | Tự động chạy tuần tự từ Unit 1 đến Unit 8, nghỉ giải lao giữa mỗi Unit |
| **`T`** | Chỉ thi Unit Test | Bỏ qua bài học, vào thẳng bài kiểm tra 30 câu và nộp bài với điểm 100/100 |
| **`L`** | Chỉ làm bài học | Hoàn thành 100% tất cả các task bài học và Step Test, không làm Unit Test |
| **`M`** | Thi Assessment Center | Mở danh sách giải các bài Mid-term và Final Test |
| **`S`** | Xem Bảng điều khiển (Dashboard) | Quét và hiển thị bảng điểm, phần trăm hoàn thành của Module 1, 2, 3 |
| **`Q`** | Thoát chương trình | Đóng bộ công cụ an toàn |

---

## 5. Giải bài thi Midterm và Final Test

Khi trường hoặc giảng viên yêu cầu làm bài thi giữa kỳ (Mid-term) hoặc cuối kỳ (Final Test):
1. Chạy **`run_solver.bat`** -> Chọn phím **`M`**.
2. Chọn số tương ứng với bài thi bạn cần làm:
   - `[1]` Module 2: Intermediate Mid-term test (100 câu)
   - `[2]` Module 2: Intermediate Final Test (200 câu)
   - `[3]` Module 3: Advanced Mid-term test (100 câu)
   - `[4]` Module 3: Advanced Final Test I (200 câu)
   - `[5]` Module 3: Advanced Final Test II (200 câu)
3. Bộ công cụ sẽ tự động mở bài thi, tự điền chính xác 100% đáp án từ dữ liệu đề chuẩn của ETS, và nộp bài.

---

## 6. Các lỗi thường gặp và cách khắc phục

### ❓ Lỗi: "Không tìm thấy Chrome. Hãy chạy start_chrome_debug.bat trước."
👉 **Khắc phục:** 
- Bạn chưa mở Chrome bằng file `start_chrome_debug.bat`.
- Hãy tắt hết các cửa sổ Chrome đang mở trên máy tính, sau đó nhấp đúp lại vào `start_chrome_debug.bat`.

### ❓ Lỗi: "Python was not found" hoặc "'python' is not recognized"
👉 **Khắc phục:**
- Máy tính của bạn chưa có Python hoặc khi cài đặt quên tích chọn `Add python.exe to PATH`.
- Hãy gỡ Python ra và cài lại, nhớ tích chọn ô `Add python.exe to PATH` ở bước đầu tiên.

### ❓ Có thể tự chỉnh sửa hoặc thêm đáp án không?
👉 **Trả lời:**
- Toàn bộ đáp án được lưu dưới dạng file JSON chuẩn trong thư mục `data/`.
- File `data/all_module_answers.json` chứa đáp án 30/30 câu của tất cả các Unit trong Module 2 và Module 3.

---

## 👑 TÁC GIẢ & BẢN QUYỀN

- Bộ công cụ được phát triển và tối ưu bởi **BANG DZ UwU**.
- Dành tặng cho cộng đồng học viên TOEIC.
- Chúc các bạn đạt điểm số tối đa và hoàn thành khóa học nhanh chóng! 🎉
