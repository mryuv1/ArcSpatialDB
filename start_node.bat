@echo off
setlocal EnableDelayedExpansion
title ArcSpatialDB - Node.js + Frontend Launcher
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║            ArcSpatialDB Full Stack               ║
echo  ║              Node.js + Frontend                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM Check if Node.js is installed
echo [Step 1/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ❌ ERROR: Node.js is not installed!
    echo    Please install Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo    ✅ Node.js !NODE_VERSION! detected

REM Check if Python is installed
echo.
echo [Step 2/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ❌ ERROR: Python is not installed!
    echo    Please install Python from: https://python.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo    ✅ !PYTHON_VERSION! detected

REM Check if npm dependencies are installed
echo.
echo [Step 3/5] Checking Node.js dependencies...
if not exist "backend_node\node_modules" (
    echo    ⚠️  Node.js dependencies not found. Installing...
    cd backend_node
    call npm install
    if !errorlevel! neq 0 (
        echo    ❌ Failed to install dependencies!
        pause
        exit /b 1
    )
    cd ..
    echo    ✅ Dependencies installed successfully
) else (
    echo    ✅ Node.js dependencies found
)

REM Start Node.js Backend
echo.
echo [Step 4/5] Starting Node.js Backend Server...
echo    🚀 Starting backend on http://localhost:5001
cd backend_node
start "ArcSpatialDB Node.js Backend" /min cmd /c "title ArcSpatialDB Backend ^& echo Backend Server Starting... ^& echo. ^& echo ================================== ^& echo   ArcSpatialDB Node.js Backend ^& echo   Port: 5001 ^& echo   API: http://localhost:5001/api ^& echo ================================== ^& echo. ^& node app.js ^& pause"
cd ..

REM Wait for backend to start
echo    ⏳ Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

REM Test backend connection
echo    🔍 Testing backend connection...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5001/api/health' -UseBasicParsing -TimeoutSec 3; if ($response.StatusCode -eq 200) { Write-Host '    ✅ Backend is responding' -ForegroundColor Green } } catch { Write-Host '    ⚠️  Backend may still be starting...' -ForegroundColor Yellow }"

REM Start Frontend
echo.
echo [Step 5/5] Starting Frontend Web Server...
echo    🌐 Starting frontend on http://localhost:8000
cd frontend
start "ArcSpatialDB Frontend" /min cmd /c "title ArcSpatialDB Frontend ^& echo Frontend Server Starting... ^& echo. ^& echo ================================== ^& echo   ArcSpatialDB Frontend ^& echo   Port: 8000 ^& echo   URL: http://localhost:8000 ^& echo ================================== ^& echo. ^& python -m http.server 8000"
cd ..

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                🎉 LAUNCH COMPLETE! 🎉            ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  📊 Services Status:
echo    • Node.js Backend:  ✅ http://localhost:5001
echo    • Frontend Server:  ✅ http://localhost:8000
echo.
echo  🔗 Quick Links:
echo    • Application:      http://localhost:8000
echo    • API Health:       http://localhost:5001/api/health
echo    • Projects API:     http://localhost:5001/api/projects
echo    • Areas API:        http://localhost:5001/api/areas
echo.
echo  💡 Both services are running in minimized windows.
echo     Check your taskbar for "ArcSpatialDB Backend" and "ArcSpatialDB Frontend"
echo.

REM Ask user if they want to open the application
choice /c YN /m "Open the application in your browser now? (Y/N)"
if !errorlevel! equ 1 (
    echo.
    echo  🌐 Opening ArcSpatialDB in your default browser...
    start http://localhost:8000
    timeout /t 2 /nobreak >nul
)

echo.
echo  ℹ️  To stop the services:
echo     1. Close the backend and frontend terminal windows, OR
echo     2. Press Ctrl+C in their respective windows
echo.
echo  📝 Log files and output can be seen in the service windows.
echo.

pause
