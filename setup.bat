@echo off
echo ============================================
echo   ShopKart - Setup Script (Windows)
echo ============================================
echo.

REM Create virtual environment
echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ first.
    pause
    exit /b 1
)

REM Activate venv
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM Create required folders
echo [4/4] Creating required folders...
if not exist "instance" mkdir instance
if not exist "data" mkdir data
if not exist "app\static\css" mkdir app\static\css
if not exist "app\static\js" mkdir app\static\js

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   To run the app:
echo     venv\Scripts\activate
echo     python run.py
echo.
echo   Then open: http://127.0.0.1:5000
echo   Admin Login: admin@shopkart.com / admin123
echo.
echo   OPTIONAL: Place amazon.csv in the data\ folder
echo   for real product data (from Kaggle).
echo   Without it, 10,000 sample products are generated.
echo.

REM Ask to run now
set /p RUN="Run the app now? (y/n): "
if /i "%RUN%"=="y" (
    python run.py
)

pause
