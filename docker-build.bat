@echo off
REM =============================================================================
REM docker-build.bat
REM =============================================================================
REM Build Docker image for Premier League ML Prediction API
REM =============================================================================

echo ======================================================================
echo BUILDING DOCKER IMAGE
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not found in PATH
    echo Please install Docker Desktop for Windows
    echo Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker daemon is not running
    echo Please start Docker Desktop
    exit /b 1
)

REM Build the image
echo Building Docker image: premier-league-ml-api:latest
echo.
docker build -t premier-league-ml-api:latest .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo BUILD SUCCESSFUL
    echo ======================================================================
    echo.
    echo Image: premier-league-ml-api:latest
    echo.
    echo To run the container:
    echo   docker-run.bat
    echo.
    echo To run manually:
    echo   docker run -d -p 8000:8000 --name ml-api premier-league-ml-api:latest
) else (
    echo.
    echo ======================================================================
    echo BUILD FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
    echo Check the output above for details
)

pause