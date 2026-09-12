@echo off
echo ========================================
echo    Link Bot - Starting...
echo ========================================
cd /d D:\link_bot
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Bot crash hoyeche! Error dekho upore.
    pause
)
