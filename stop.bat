@echo off
REM Kangaroo Math Brain Backend Stop Script (Windows)
REM Usage: stop.bat

echo === Stopping Kangaroo Math Brain Backend ===

REM Check if port 8000 is in use
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        echo Stopping process PID: %%a
        taskkill /F /PID %%a >nul 2>&1
        if %errorlevel% equ 0 (
            echo [OK] Service stopped
        ) else (
            echo [ERROR] Cannot stop process %%a
        )
    )
) else (
    echo Port 8000 is not in use
)

REM Check for python processes
tasklist | findstr "python.exe" >nul
if %errorlevel% equ 0 (
    echo.
    echo Tip: If service is not fully stopped, manually close "KangarooMathBackend" window
)

echo.