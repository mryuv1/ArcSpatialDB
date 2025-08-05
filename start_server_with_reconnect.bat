@echo off
echo ========================================
echo ArcSpatialDB Server with Auto-Reconnect
echo ========================================
echo.

:start_server
echo [%date% %time%] Starting ArcSpatialDB server...
echo.

python server_with_reconnect.py

echo.
echo [%date% %time%] Server stopped or crashed.
echo [%date% %time%] Waiting 10 seconds before restarting...
timeout /t 10 /nobreak > nul

echo [%date% %time%] Restarting server...
echo.
goto start_server 