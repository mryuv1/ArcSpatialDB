@echo off
title ArcSpatialDB Environment Switcher
color 0A

echo ========================================
echo    ArcSpatialDB Environment Switcher
echo ========================================
echo.

:menu
echo Choose your environment:
echo.
echo [1] Local Development (localhost:5000)
echo [2] Staging Environment
echo [3] Production Environment
echo [4] Show Current Configuration
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto local
if "%choice%"=="2" goto staging
if "%choice%"=="3" goto production
if "%choice%"=="4" goto show
if "%choice%"=="5" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:local
echo.
echo Switching to LOCAL environment...
python switch_environment.py local
echo.
pause
goto menu

:staging
echo.
set /p domain="Enter your staging domain (e.g., mysite.com): "
if "%domain%"=="" (
    echo Domain is required for staging environment.
    pause
    goto menu
)
echo.
echo Switching to STAGING environment with domain: %domain%
python switch_environment.py staging %domain%
echo.
pause
goto menu

:production
echo.
set /p domain="Enter your production domain (e.g., arcspatialdb.com): "
if "%domain%"=="" (
    echo Domain is required for production environment.
    pause
    goto menu
)
echo.
echo Switching to PRODUCTION environment with domain: %domain%
python switch_environment.py production %domain%
echo.
pause
goto menu

:show
echo.
echo Current Configuration:
python switch_environment.py show
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
exit 