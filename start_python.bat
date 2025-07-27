@echo off
title ArcSpatialDB - Complete System Startup
color 0F
echo.
echo  ============================================================
echo   ArcSpatialDB - Complete System Startup
echo  ============================================================
echo.
echo  This will start both the backend API and frontend servers
echo.
echo  1. Backend API Server: http://localhost:5000
echo  2. Frontend Web App:   http://localhost:8000
echo.
echo  ============================================================
echo.

echo  Step 1: Starting Backend API Server...
start "ArcSpatialDB Backend" cmd /k "cd /d "%~dp0backend" && START_BACKEND.bat"

echo  Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak > nul

echo  Step 2: Starting Frontend Web Server...
start "ArcSpatialDB Frontend" cmd /k "cd /d "%~dp0frontend" && start_frontend.bat"

echo  Waiting 3 seconds for frontend to initialize...
timeout /t 3 /nobreak > nul

echo.
echo  ============================================================
echo   🎉 ArcSpatialDB System Started Successfully!
echo  ============================================================
echo.
echo   📡 Backend API:    http://localhost:5000
echo   🎨 Frontend App:   http://localhost:8000
echo.
echo   💡 Open http://localhost:8000 in your browser to use the app
echo.
echo   ⚠️  Keep both server windows open while using the system
echo   ❌ Close this window or press any key to finish setup
echo  ============================================================
echo.

pause
