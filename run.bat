@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: INEC Voter Registration System - Professional Edition
:: ===================================================

:: ANSI Color Codes (via PowerShell)
set "ESC="
set "GREEN=[92m"
set "RED=[91m"
set "CYAN=[96m"
set "YELLOW=[93m"
set "RESET=[0m"

:MENU
cls
echo %CYAN%
echo   _____ _   _ ______ _____  __      ______ _______ ______ _____  
echo  |_   _\| \ \ |  ____/ ____\ \ \    / / __ \__   __|  ____|  __ \ 
echo    | | |  \  | | |__ | |     \ \  / / |  | | | |  | |__  | |__) |
echo    | | | . ` | |  __|| |      \ \/ /|  |  | | | |  |  __| |  _  / 
echo   _| |_| |\  | | |___| |____   \  / |  |__| | | |  | |____| | \ \ 
echo  |_____|_| \_| \______\_____|   \/   \____/  |_|  |______|_|  \_\
echo.
echo   VOTER REGISTRATION SYSTEM - UNIVERSAL STARTUP
echo %RESET%
echo ---------------------------------------------------
echo  1. [DEFAULT] Start System
echo  2. First Time Setup / Update Dependencies
echo  3. Reset Environment (Clean venv and Database)
echo  4. Seed Sample Data (States/LGAs)
echo  5. Setup Default Users (Admin/Staff)
echo  6. Run System Diagnostics
echo  7. Exit
echo ---------------------------------------------------
set /p choice="Select an option [1-7] (Default is 1): "

if "%choice%"=="" set choice=1
if "%choice%"=="1" goto START_SYSTEM
if "%choice%"=="2" goto SETUP
if "%choice%"=="3" goto RESET
if "%choice%"=="4" goto SEED
if "%choice%"=="5" goto SETUP_USERS
if "%choice%"=="6" goto DIAGNOSE
if "%choice%"=="7" exit /b 0
goto MENU

:START_SYSTEM
echo.
echo [%CYAN%*%RESET%] Initializing system...

:: 1. Detect Python
call :DETECT_PYTHON
if %errorlevel% neq 0 exit /b 1

:: 2. Check Port 8000
echo [%CYAN%*%RESET%] Checking port 8000...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo %YELLOW%[WARNING] Port 8000 is already in use.%RESET%
    echo Please close any other running Django servers or applications on port 8000.
    pause
    goto MENU
)

:: 3. Setup Environment File
if not exist .env (
    if exist .env.example (
        echo [%CYAN%*%RESET%] Creating .env file from example...
        copy .env.example .env >nul
    )
)

:: 4. Virtual Environment
if not exist venv (
    echo %YELLOW%[!] Virtual environment not found.%RESET%
    goto SETUP
)

:: 5. Activate
echo [%CYAN%*%RESET%] Activating environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo %RED%[ERROR] Virtual environment activation script not found.%RESET%
    goto SETUP
)

:: 6. Verify Environment
python scripts\check_env.py >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[!] Environment verification failed. Dependencies might be missing.%RESET%
    echo Running diagnostics...
    python scripts\diagnose.py
    pause
    goto MENU
)

:: 6. Database Check
pushd backend
if not exist db.sqlite3 (
    echo %YELLOW%[!] Database not found. Initializing database...%RESET%
    python manage.py makemigrations
    python manage.py migrate
)
popd

:: 7. Launch
echo.
echo %GREEN%===================================================%RESET%
echo   %GREEN%SYSTEM READY!%RESET%
echo.
echo   - Web Access: %CYAN%http://127.0.0.1:8000/%RESET%
echo   - Admin Panel: %CYAN%http://127.0.0.1:8000/admin/%RESET%
echo   - Credentials: %YELLOW%admin / admin%RESET% or %YELLOW%staff / admin%RESET%
echo %GREEN%===================================================%RESET%
echo.

start "" http://127.0.0.1:8000/

echo [%CYAN%*%RESET%] Starting Django server...
pushd backend
..\venv\Scripts\python.exe manage.py runserver
popd
pause
goto MENU

:DIAGNOSE
echo.
echo [%CYAN%*%RESET%] Running System Diagnostics...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe scripts\diagnose.py
) else (
    echo %YELLOW%[!] No virtual environment found. Running diagnostics with global Python...%RESET%
    call :DETECT_PYTHON
    !PYTHON_EXE! scripts\diagnose.py
)
echo.
echo [INFO] You can send 'diag_report.json' to support if issues persist.
pause
goto MENU

:SETUP
echo.
echo [%CYAN%*%RESET%] Redirecting to Universal Setup Script...
if exist setup_dependencies.bat (
    call setup_dependencies.bat
) else (
    echo %RED%[ERROR] setup_dependencies.bat not found.%RESET%
    pause
)
goto MENU

:RESET
echo.
echo %RED%[CAUTION] This will delete the virtual environment and the database!%RESET%
set /p confirm="Are you sure? (y/n): "
if /i "%confirm%" neq "y" goto MENU

echo [%CYAN%*%RESET%] Cleaning up...
if exist venv (
    echo - Removing venv...
    rd /s /q venv
)
if exist backend\db.sqlite3 (
    echo - Removing database...
    del backend\db.sqlite3
)
echo %GREEN%[SUCCESS] Environment reset.%RESET%
pause
goto MENU

:SEED
echo.
echo [%CYAN%*%RESET%] Seeding Nigeria sample data...
call venv\Scripts\activate.bat
pushd backend
python manage.py seed_nigeria
popd
echo %GREEN%[SUCCESS] Seeding complete.%RESET%
pause
goto MENU

:SETUP_USERS
echo.
echo [%CYAN%*%RESET%] Setting up default users (admin/admin and staff/admin)...
call venv\Scripts\activate.bat
pushd backend

:: Setup Admin
echo - Configuring Admin...
set DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul
if !errorlevel! equ 0 (
    echo   [+] Superuser 'admin' created.
) else (
    echo   [!] Superuser 'admin' already exists.
)

:: Setup Staff
echo - Configuring Staff...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='staff').delete(); user = User.objects.create_user('staff', 'staff@example.com', 'admin'); user.is_staff=True; user.save(); print('   [+] Staff user created.')" 2>nul
if !errorlevel! neq 0 (
    echo   [!] Could not create staff user (might already exist).
)

set DJANGO_SUPERUSER_PASSWORD=
popd
echo %GREEN%[SUCCESS] Users ready.%RESET%
pause
goto MENU

:: --- Helpers ---

:DETECT_PYTHON
set PYTHON_EXE=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_EXE=py
    )
)

if "%PYTHON_EXE%"=="" (
    echo %RED%[ERROR] Python not found.%RESET%
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
exit /b 0

