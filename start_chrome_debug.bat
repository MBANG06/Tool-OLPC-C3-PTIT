@echo off
chcp 65001 >nul
title Khởi động Google Chrome Debugging (Port 9222) - MADE BY BANG DZ UwU
cls
echo =====================================================================
echo               ★ ★ ★  MADE BY BANG DZ UwU  ★ ★ ★
echo    KHỞI ĐỘNG GOOGLE CHROME VỚI CHẾ ĐỘ REMOTE DEBUGGING (PORT 9222)
echo =====================================================================
echo.

:: Tìm đường dẫn Chrome.exe
set "CHROME_PATH="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME_PATH%"=="" (
    echo [ERROR] Không tìm thấy Google Chrome trên máy tính của bạn!
    echo Vui lòng cài đặt Google Chrome hoặc khởi động thủ công với tham số:
    echo   --remote-debugging-port=9222 --remote-allow-origins=*
    echo.
    pause
    exit /b 1
)

echo [+] Đã tìm thấy Chrome tại:
echo     "%CHROME_PATH%"
echo.

:: Kiểm tra cổng 9222 đã hoạt động chưa
netstat -ano | findstr /R /C:":9222 " >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [THÔNG BÁO] Cổng 9222 ĐÃ ĐANG MỞ và sẵn sàng kết nối!
    echo Bạn có thể chạy ngay 'run_solver.bat' để bắt đầu giải bài.
    echo.
    pause
    exit /b 0
)

:: Kiểm tra xem Chrome có đang chạy bình thường không
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo ---------------------------------------------------------------------
    echo [CHÚ Ý] Google Chrome đang mở nhưng chưa bật cổng kết nối Debugging (9222).
    echo Để công cụ có thể kết nối và điều khiển tự động, vui lòng chọn:
    echo.
    echo   [1] Tự động đóng Chrome và mở lại (KHUYÊN DÙNG - giữ nguyên đăng nhập của bạn)
    echo   [2] Mở Chrome cửa sổ phụ riêng biệt (KHÔNG tắt các tab làm việc của bạn)
    echo   [3] Hủy bỏ và thoát
    echo ---------------------------------------------------------------------
    echo.
    set /p "USER_MODE=Nhập lựa chọn của bạn (1, 2, hoặc 3): "

    if "%USER_MODE%"=="2" (
        echo.
        echo [+] Đang khởi động Chrome cửa sổ độc lập (Profile riêng)...
        start "" "%CHROME_PATH%" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%~dp0chrome_debug_profile" "https://edtoeic.engdis.com/login.aspx?dist=1&distDomain=https://ets.toeicolpc.com/#/login"
        goto FINISH
    )
    if "%USER_MODE%"=="3" (
        exit /b 0
    )
    
    echo.
    echo [+] Đang đóng các tiến trình Chrome cũ...
    taskkill /F /IM chrome.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [+] Đang khởi động Google Chrome với Remote Debugging Port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --remote-allow-origins=* "https://edtoeic.engdis.com/login.aspx?dist=1&distDomain=https://ets.toeicolpc.com/#/login"

:FINISH
timeout /t 3 /nobreak >nul
echo.
echo =====================================================================
echo [+] Chrome đã khởi động thành công với cổng Debug 9222!
echo.
echo CÁC BƯỚC TIẾP THEO:
echo 1. Hãy đăng nhập tài khoản TOEIC trên cửa sổ Chrome vừa mở (nếu cần).
echo 2. Chọn Module bạn muốn học (Module 1, 2, hoặc 3).
echo 3. Mở file 'run_solver.bat' để bắt đầu giải bài!
echo.
echo                    ★ MADE BY BANG DZ UwU ★
echo =====================================================================
echo.
pause
