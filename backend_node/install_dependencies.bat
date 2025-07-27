@echo off
echo Installing ArcSpatialDB Node.js Backend Dependencies...
cd /d "%~dp0"

echo.
echo Checking if Node.js is installed...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js is installed.
echo.

echo Installing npm packages...
call npm install

if %errorlevel% equ 0 (
    echo.
    echo ✓ Dependencies installed successfully!
    echo.
    echo You can now start the server with:
    echo   npm start           (production mode)
    echo   npm run dev         (development mode)
    echo   start_backend_node.bat
    echo.
) else (
    echo.
    echo ✗ Error installing dependencies.
    echo Please check the error messages above.
    echo.
)

pause
