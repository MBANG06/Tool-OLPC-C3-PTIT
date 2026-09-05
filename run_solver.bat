@echo off
chcp 65001 >nul
title ETS TOEIC OLPC - Auto Solver Portable - MADE BY BANG DZ UwU
echo =====================================================================
echo                    ★ ★ ★ MADE BY BANG DZ UwU ★ ★ ★
echo         ETS TOEIC OLPC - BỘ TỰ ĐỘNG HÓA HOÀN THÀNH TOÀN TRÌNH
echo =====================================================================
echo.

:: Kiểm tra Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo Vui lòng cài đặt Python (phiên bản 3.9 trở lên) và tích chọn "Add Python to PATH".
    echo Tải tại: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Kiểm tra thư viện websockets
python -c "import websockets" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [+] Đang tự động cài đặt thư viện phụ trợ (websockets)...
    pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% neq 0 (
        echo [LỖI] Không thể cài đặt websockets. Vui lòng kiểm tra kết nối mạng.
        pause
        exit /b 1
    )
)

:MENU
cls
echo =====================================================================
echo                    ★ ★ ★ MADE BY BANG DZ UwU ★ ★ ★
echo         ETS TOEIC OLPC - BỘ TỰ ĐỘNG HÓA HOÀN THÀNH TOÀN TRÌNH
echo =====================================================================
echo.
echo   [1] Giải Unit 1
echo   [2] Giải Unit 2
echo   [3] Giải Unit 3
echo   [4] Giải Unit 4
echo   [5] Giải Unit 5
echo   [6] Giải Unit 6
echo   [7] Giải Unit 7
echo   [8] Giải Unit 8
echo.
echo   [A] Giải TOÀN BỘ cả 8 Units (Tự động từ Unit 1 đến 8)
echo   [L] Liệt kê thông tin Module và Unit hiện tại
echo   [Q] Thoát
echo.
echo =====================================================================
set /p "OPT=Chọn một tùy chọn (1-8, A, L, Q): "

if /I "%OPT%"=="Q" exit /b 0
if /I "%OPT%"=="A" (
    echo.
    echo [+] Bắt đầu giải tự động toàn bộ 8 Units của Module hiện tại...
    python "%~dp0toeic_solver.py" --all
    echo.
    pause
    goto MENU
)
if /I "%OPT%"=="L" (
    echo.
    python "%~dp0toeic_solver.py" --list
    echo.
    pause
    goto MENU
)
if "%OPT%" geq "1" if "%OPT%" leq "8" (
    echo.
    echo [+] Bắt đầu giải Unit %OPT%...
    python "%~dp0toeic_solver.py" --unit %OPT%
    echo.
    pause
    goto MENU
)

echo Lựa chọn không hợp lệ! Vui lòng chọn lại.
timeout /t 2 /nobreak >nul
goto MENU
