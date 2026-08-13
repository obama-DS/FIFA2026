@echo off
REM =============================================================================
REM docker-run.bat
REM =============================================================================
REM Run Docker container for Premier League ML Prediction API
REM =============================================================================

echo ======================================================================
echo RUNNING DOCKER CONTAINER
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not found in PATH
    exit /b 1
)

REM Stop and remove existing container if it exists
docker stop ml-api >nul 2>&1
docker rm ml-api >nul 2>&1

REM Run the container
echo Starting container: ml-api
echo.
docker run -d ^
    -p 8000:8000 ^
    --name ml-api ^
    --restart unless-stopped ^
    premier-league-ml-api:latest

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo CONTAINER STARTED SUCCESSFULLY
    echo ======================================================================
    echo.
    echo Container name: ml-api
    echo API available at: http://localhost:8000
    echo.
    echo Endpoints:
    echo   - Health:     http://localhost:8000/health
    echo   - Model Info: http://localhost:8000/model-info
    echo   - Swagger UI: http://localhost:8000/docs
    echo   - ReDoc:      http://localhost:8000/redoc
    echo.
    echo To view logs:
    echo   docker logs ml-api
    echo.
    echo To stop container:
    echo   docker stop ml-api
    echo.
    echo To remove container:
    echo   docker rm ml-api
    echo.
    
    REM Wait for container to be ready
    echo Waiting for API to be ready...
    timeout /t 5 /nobreak >nul
    
    REM Test health endpoint
    echo Testing health endpoint...
    curl -s http://localhost:8000/health
    echo.
) else (
    echo.
    echo ======================================================================
    echo CONTAINER START FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
    echo.
    echo Check if:
    echo   1. Image exists: docker images
    echo   2. Port 8000 is available
    echo   3. Docker daemon is running
)

pause