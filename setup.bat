@echo off
echo ========================================
echo    Link Bot - Setup Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python installed nai! 
    echo Download korte jao: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

:: Install dependencies
echo.
echo [1/3] Libraries install korchi...
pip install -r D:\link_bot\requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Installation failed!
    pause
    exit /b 1
)
echo [OK] Libraries installed

:: Install Playwright browser
echo.
echo [2/3] Browser download korchi (ektu time lagbe)...
playwright install chromium
if errorlevel 1 (
    echo [ERROR] Browser install failed!
    pause
    exit /b 1
)
echo [OK] Browser ready

:: Create downloads folder
echo.
echo [3/3] Folders create korchi...
if not exist "D:\link_bot\downloads" mkdir "D:\link_bot\downloads"
echo [OK] Downloads folder ready

echo.
echo ========================================
echo    Setup complete!
echo ========================================
echo.
echo Ekhon config.py-te BOT_TOKEN set koro.
echo Tarpor run_bot.bat double-click kore bot chalao.
echo.
pause
