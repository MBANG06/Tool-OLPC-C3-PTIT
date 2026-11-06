# 👑 ETS TOEIC OLPC - Auto Solver Pro (Portable) 👑
### ★ ★ ★ MADE BY BANG DZ UwU ★ ★ ★

Bộ công cụ tự động hóa toàn diện và hoàn hảo nhất dành cho nền tảng học trực tuyến **ETS TOEIC Online Practice Component (OLPC)** (edtoeic.engdis.com & ets.toeicolpc.com).

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Status](https://img.shields.io/badge/Status-100%25%20Working-brightgreen.svg)
![Author](https://img.shields.io/badge/Author-BANG%20DZ%20UwU-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

---

```
========================================================================================
  __  __    _    ____  _____   ______   __   ____    _    _   _  ____   ____  _____ 
 |  \/  |  / \  |  _ \| ____| | __ ) \ / /  | __ )  / \  | \ | |/ ___| |  _ \|__  / 
 | |\/| | / _ \ | | | |  _|   |  _ \\ V /   |  _ \ / _ \ |  \| | |  _  | | | | / /  
 | |  | |/ ___ \| |_| | |___  | |_) || |    | |_) / ___ \| |\  | |_| | | |_| |/ /_  
 |_|  |_/_/   \_\____/|_____| |____/ |_|    |____/_/   \_\_| \_|\____| |____//____| 
                                                                                     
                    ★ ★ ★  M A D E   B Y   B A N G   D Z   U w U  ★ ★ ★
========================================================================================
```

---

## 🔥 Tính Năng Đột Phá

1. **Hoàn thành 100% bài học (Lessons & Tasks)**:
   - Tự động vượt qua tất cả các bài học và bài tập tương tác trong Unit qua API `SetProgressPerTask`.
   - Cơ chế Rate Limit Retry thông minh, không bị nghẽn mạng hay chặn request.

2. **Giải đúng 100% toàn bộ Step Tests**:
   - Xử lý chính xác tất cả các dạng bài: `type 25` (trắc nghiệm), `type 23` (kéo thả từ), `type 51` (hội thoại điền nhiều chỗ trống chuẩn Format A).
   - Lưu điểm 100% vĩnh viễn trên máy chủ qua `SaveUserTest`.

3. **100/100 điểm tuyệt đối mọi bài kiểm tra Unit Test (30/30 câu)**:
   - Tích hợp sẵn bộ dữ liệu đáp án chuẩn 100% (`data/all_module_answers.json`) cho tất cả các Unit trong Module 2 và Module 3.
   - Cơ chế tự động quét trực tiếp metadata và explanation từ máy chủ ETS nếu thiếu đề mới.
   - Vượt qua màn hình SysCheck, tắt Audio/Video tự động, bấm Start / Next / Submit an toàn tuyệt đối.

4. **Giải bài thi Midterm & Final Test (Assessment Center)**:
   - Hỗ trợ đầy đủ: Module 2 Mid-term (100 câu), Module 2 Final (200 câu), Module 3 Mid-term (100 câu), Module 3 Final I & II (200 câu).
   - Tự động điền đáp án chuẩn xác từng câu và gửi nộp bài.

5. **Bảng điều khiển (Dashboard) trực quan**:
   - Quét và hiển thị thời gian thực tiến độ học, điểm số từng Unit của toàn bộ các Module.

6. **Chạy 1 Click (Portable)**:
   - Không cần cấu hình phức tạp, chỉ cần click chuột chạy các file `.bat`.

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh

### Bước 1: Khởi động Chrome
- Nhấp đúp chuột vào file **`start_chrome_debug.bat`**.
- Đăng nhập tài khoản TOEIC trên cửa sổ Chrome vừa mở.

### Bước 2: Chạy bộ giải tự động
- Nhấp đúp chuột vào file **`run_solver.bat`**.
- Chọn tính năng trong Menu:
  - Nhập **`1`** - **`8`** : Giải hoàn chỉnh Unit tương ứng.
  - Nhập **`A`** : **Tự động giải toàn bộ 8 Units** của Module hiện tại.
  - Nhập **`T`** : Chỉ thi Unit Test (100/100 tuyệt đối).
  - Nhập **`L`** : Chỉ làm bài học (100% Lessons).
  - Nhập **`M`** : Giải Midterm / Final Tests (Assessment Center).
  - Nhập **`S`** : Xem Bảng điểm & tiến độ toàn bộ Module.

> 📖 Xem hướng dẫn chi tiết từng bước bằng tiếng Việt tại file: [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)

---

## 💻 Dành Cho Lập Trình Viên & CLI Nâng Cao

Bạn có thể chạy trực tiếp bằng dòng lệnh:

```bash
# Xem trợ giúp các tham số
python toeic_solver.py --help

# Xem Dashboard tiến độ và bảng điểm
python toeic_solver.py --status

# Giải Unit 1 của Module hiện tại
python toeic_solver.py --unit 1

# Giải tự động toàn bộ 8 Units của Module hiện tại
python toeic_solver.py --all

# Chỉ định rõ Module cần giải (1, 2, hoặc 3)
python toeic_solver.py --module 3 --all

# Chỉ thi Unit Test (bỏ qua bài học)
python toeic_solver.py --unit 2 --only-test

# Chỉ làm bài học (bỏ qua Unit Test)
python toeic_solver.py --unit 2 --skip-test

# Giải bài thi Assessment Center (1: M2 Mid, 2: M2 Final, 3: M3 Mid, 4: M3 Final 1, 5: M3 Final 2)
python toeic_solver.py --assessment 3
```

---

## 📁 Cấu Trúc Thư Mục Dự Án

```
toeic_auto_solver/
│── start_chrome_debug.bat       # Script mở Google Chrome kết nối Debug 9222
│── run_solver.bat               # Script khởi chạy bộ giải tự động
│── toeic_solver.py              # Bộ giải All-in-one hoàn chỉnh
│── requirements.txt             # Danh sách thư viện phụ trợ (websockets)
│── README.md                    # Tài liệu kỹ thuật
│── HUONG_DAN_SU_DUNG.md         # Hướng dẫn sử dụng cho người mới bắt đầu
│
├── data/                        # Kho dữ liệu đáp án chuẩn 100%
│   ├── all_module_answers.json  # 30/30 câu chuẩn cho toàn bộ Unit Tests M2 & M3
│   └── assessment_answers/      # Đáp án chuẩn cho Midterm & Final Tests
│       ├── module2_midterm_989011001.json
│       ├── module2_final_143541.json
│       ├── module3_midterm_989010001.json
│       ├── module3_final_1_1539000.json
│       └── module3_final_2_1540000.json
│
└── output/                      # Thư mục chứa ảnh chụp màn hình chứng nhận kết quả
```

---

## 🛡️ Tác Giả & Bản Quyền

- Tác giả: **BANG DZ UwU**
- Phát hành miễn phí cho cộng đồng học viên TOEIC.
- Chúc các bạn học tập tốt và đạt kết quả cao nhất!
