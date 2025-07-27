@echo off
title ArcSpatialDB - Frontend Web Server
color 0B
echo.
echo  ========================================
echo   ArcSpatialDB Frontend Web Server
echo  ========================================
echo.
echo  Starting frontend web server...
echo  Frontend will be available at: http://localhost:8000
echo.
echo  Make sure the backend is running on port 5000!
echo  Press Ctrl+C to stop the server
echo  ========================================
echo.

cd /d "%~dp0"
python -m http.server 8000

echo.
echo  ========================================
echo   Server stopped. Press any key to exit.
echo  ========================================
pause > nul
