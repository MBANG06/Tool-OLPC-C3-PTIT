@echo off
chcp 65001 >nul
title ETS TOEIC OLPC - Auto Solver Pro - MADE BY BANG DZ UwU

echo =====================================================================
echo                    ★ ★ ★ MADE BY BANG DZ UwU ★ ★ ★
echo         ETS TOEIC OLPC - BỘ TỰ ĐỘNG HÓA HOÀN THÀNH TOÀN TRÌNH
echo =====================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo.
    echo Vui lòng cài đặt Python (phiên bản 3.9 trở lên) và nhớ TÍCH CHỌN:
    echo   [x] "Add python.exe to PATH" khi cài đặt!
    echo.
    echo Link tải chính thức: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 2. Kiểm tra và tự động cài đặt thư viện websockets
python -c "import websockets" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [+] Đang tự động cài đặt thư viện kết nối Chrome [websockets]...
    python -m pip install --user websockets
    if %ERRORLEVEL% neq 0 (
        python -m ensurepip --default-pip >nul 2>&1
        python -m pip install --user websockets --trusted-host pypi.org --trusted-host files.pythonhosted.org
    )
    python -c "import websockets" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo.
        echo =====================================================================
        echo [LỖI] Không thể tự động cài đặt thư viện websockets!
        echo.
        echo Hướng dẫn cài đặt thủ công:
        echo   1. Mở PowerShell hoặc Command Prompt (cmd)
        echo   2. Nhập lệnh: python -m pip install websockets
        echo   3. Sau khi cài xong, mở lại file này!
        echo =====================================================================
        echo.
        pause
        exit /b 1
    )
    echo [+] Cài đặt websockets thành công!
    echo.
)

:: 3. Khởi chạy bộ giải tự động (chuyển tiếp toàn bộ tham số nếu có)
python "%~dp0toeic_solver.py" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [THÔNG BÁO] Chương trình kết thúc với mã lỗi %ERRORLEVEL%.
    pause
)
