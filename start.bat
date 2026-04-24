@echo off
REM Kangaroo Math Brain Backend Startup Script (Windows)
REM Usage: start.bat

setlocal

REM Project directory
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo === Kangaroo Math Brain Backend ===
echo Project: %PROJECT_DIR%

REM Check if .venv exists
if not exist ".venv" (
    echo ERROR: .venv directory not found
    echo.
    echo Please create virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

REM Check if port 8000 is in use
echo Checking port 8000...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo Port 8000 is in use, stopping existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Start service
echo Starting uvicorn server...
echo Service URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

REM Start in background with start command
start "KangarooMathBackend" /min cmd /c ".venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >> logs\server.log 2>&1"

REM Wait for service to start
timeout /t 3 /nobreak >nul

REM Check if service started successfully
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Service started successfully!
    powershell -Command "(Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing).Content"
    echo.
    echo Stop service: stop.bat
    echo View logs: type logs\server.log
) else (
    echo [ERROR] Service failed to start, check logs: logs\server.log
    exit /b 1
)

endlocal