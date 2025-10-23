@echo off
echo Starting Digital Products Store...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if setup was run
if not exist store.db (
    echo Database not found. Running setup...
    python setup.py
    echo.
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

REM Start the application
echo Starting the application...
echo.
echo Access the store at: http://localhost:5000
echo Admin panel at: http://localhost:5000/admin
echo Default admin: admin/admin123
echo.
echo Press Ctrl+C to stop the server
echo =====================================
python app.py

pause