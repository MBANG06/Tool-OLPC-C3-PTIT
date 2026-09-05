@echo off
chcp 65001 >nul
title Khởi động Google Chrome Debugging (Port 9222) - MADE BY BANG DZ UwU
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
    pause
    exit /b 1
)

echo [+] Đã tìm thấy Chrome tại:
echo     "%CHROME_PATH%"
echo.

:: Kiểm tra cổng 9222 đã hoạt động chưa
netstat -ano | findstr /R /C:":9222 " >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [THÔNG BÁO] Cổng 9222 đã đang mở và sẵn sàng kết nối!
    echo Bạn có thể chạy ngay run_solver.bat.
    echo.
    pause
    exit /b 0
)

:: Kiểm tra xem Chrome có đang chạy bình thường không
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo [LƯU Ý QUAN TRỌNG]
    echo Google Chrome đang chạy nhưng chưa bật chế độ Debugging Port.
    echo Để bật được Port 9222, bạn cần đóng toàn bộ cửa sổ Chrome hiện tại.
    echo.
    set /p "CHOICE=Bạn có muốn tự động đóng tất cả Chrome và mở lại ngay không? (Y/N): "
    if /I "%CHOICE%"=="Y" (
        echo Đang đóng Chrome...
        taskkill /F /IM chrome.exe >nul 2>&1
        timeout /t 2 /nobreak >nul
    ) else (
        echo Vui lòng lưu các tab quan trọng, đóng Chrome rồi chạy lại file này.
        pause
        exit /b 0
    )
)

echo [+] Đang khởi động Google Chrome với Remote Debugging Port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --remote-allow-origins=* "https://edtoeic.engdis.com/EdToeic1#/home"

timeout /t 3 /nobreak >nul
echo.
echo =====================================================================
echo [+] Chrome đã khởi động thành công!
echo 1. Hãy đăng nhập tài khoản TOEIC trên trình duyệt vừa mở (nếu cần).
echo 2. Sau khi vào đến trang chính, chạy file 'run_solver.bat' để giải bài.
echo.
echo                    ★ MADE BY BANG DZ UwU ★
echo =====================================================================
echo.
pause
