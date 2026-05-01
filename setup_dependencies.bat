@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: INEC Voter Registration System - Universal Setup
:: ===================================================

set "GREEN= [92m"
set "RED= [91m"
set "CYAN= [96m"
set "YELLOW= [93m"
set "RESET= [0m"

echo %CYAN%
echo  ===================================================
echo    UNIVERSAL DEPENDENCY INSTALLER
echo  ===================================================
echo %RESET%
echo.

:: 1. System Dependency Check (Winget)
echo [%CYAN%1/5%RESET%] Checking System Dependencies...
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Winget detected. Checking for Tesseract OCR...
    where tesseract >nul 2>&1
    if %errorlevel% neq 0 (
        echo [*] Installing Tesseract OCR (Required for ID verification)...
        winget install --id=UB-Mannheim.TesseractOCR -e --accept-package-agreements --accept-source-agreements
    ) else (
        echo [+] Tesseract OCR already installed.
    )
) else (
    echo %YELLOW%[!] Winget not found. Skipping automatic system binary installation.%RESET%
    echo Please manually install Tesseract OCR from: 
    echo https://github.com/UB-Mannheim/tesseract/wiki
)

:: 2. Python Environment
echo [%CYAN%2/5%RESET%] Setting up Python Virtual Environment...
set PYTHON_EXE=
where python >nul 2>&1
if %errorlevel% equ 0 (set PYTHON_EXE=python) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (set PYTHON_EXE=py)
)

if "%PYTHON_EXE%"=="" (
    echo %RED%[ERROR] Python not found. Please install Python 3.10+ and add to PATH.%RESET%
    pause
    exit /b 1
)

:: Check bitness
echo [%CYAN%*%RESET%] Verifying Python Architecture...
%PYTHON_EXE% -c "import platform; print(platform.architecture()[0])" | findstr "64bit" >nul
if %errorlevel% neq 0 (
    echo %RED%[ERROR] 32-bit Python detected!%RESET%
    echo TensorFlow and other AI libraries require 64-bit Python.
    echo Please uninstall 32-bit Python and install the 64-bit version from python.org.
    pause
    exit /b 1
)
echo [+] 64-bit Python verified.

if not exist venv (
    echo [*] Creating virtual environment...
    %PYTHON_EXE% -m venv venv
)

echo [%CYAN%3/5%RESET%] Installing Heavy AI Dependencies (this will take time)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

:: 3. Pre-download AI Models
echo [%CYAN%4/5%RESET%] Pre-loading AI Models (Ensures offline compatibility later)...
echo [*] This step downloads ~500MB of AI models for Age Estimation and OCR.
set /p download="Download models now? (y/n) [Default: y]: "
if "%download%"=="" set download=y
if /i "%download%"=="y" (
    echo [*] Downloading Age Estimation model...
    python -c "import os; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'; from deepface import DeepFace; print('   - Initializing DeepFace models...'); DeepFace.build_model('Age')"
    echo [*] Downloading EasyOCR models...
    python -c "import easyocr; print('   - Initializing EasyOCR models...'); reader = easyocr.Reader(['en'])"
)

:: 4. Database Initialization
echo [%CYAN%5/5%RESET%] Initializing Database and Default Users...
pushd backend
python manage.py makemigrations
python manage.py migrate
python manage.py seed_nigeria

:: Setup Admin/Staff
set DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='staff').delete(); user = User.objects.create_user('staff', 'staff@example.com', 'admin'); user.is_staff=True; user.save(); print('   - Staff user created.')" 2>nul
set DJANGO_SUPERUSER_PASSWORD=
popd

echo.
echo %GREEN%===================================================%RESET%
echo   %GREEN%SETUP COMPLETE!%RESET%
echo.
echo   You can now run 'run.bat' to start the system.
echo   - Admin: admin / admin
echo   - Staff: staff / admin
echo %GREEN%===================================================%RESET%
echo.
pause
