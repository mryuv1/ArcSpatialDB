@echo off
title ArcSpatialDB - Backend API Server
color 0A
echo.
echo  ========================================
echo   ArcSpatialDB Backend API Server
echo  ========================================
echo.
echo  Starting Flask backend server...
echo  Server will be available at: http://localhost:5000
echo  API endpoints at: http://localhost:5000/api/
echo.
echo  Press Ctrl+C to stop the server
echo  ========================================
echo.

cd /d "%~dp0"
python app.py

echo.
echo  ========================================
echo   Server stopped. Press any key to exit.
echo  ========================================
pause > nul
