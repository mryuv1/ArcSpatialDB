@echo off
title ArcSpatialDB - Complete Application Starter
color 0B
echo.
echo  ========================================
echo   ArcSpatialDB - Complete Application
echo  ========================================
echo.
echo  Starting both Backend and Frontend...
echo.
echo  Backend API will be available at: http://localhost:5000
echo  Frontend Web App will be available at: http://localhost:8000
echo.
echo  ========================================
echo.

:: Start backend in a new window
echo Starting Backend API Server...
start "ArcSpatialDB Backend" cmd /k "cd /d %~dp0backend && python app.py"

:: Wait a moment for backend to start
timeout /t 3 /nobreak > nul

:: Start frontend in a new window
echo Starting Frontend Web Server...
start "ArcSpatialDB Frontend" cmd /k "cd /d %~dp0frontend && python -m http.server 8000"

:: Wait a moment for frontend to start
timeout /t 3 /nobreak > nul

:: Open the application in default browser
echo Opening application in browser...
start http://localhost:8000

echo.
echo  ========================================
echo   ArcSpatialDB is now running!
echo.
echo   Frontend: http://localhost:8000
echo   Backend API: http://localhost:5000
echo.
echo   Close the backend and frontend windows to stop.
echo  ========================================
echo.
pause
