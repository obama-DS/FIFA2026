@echo off
REM =============================================================================
REM docker-stop.bat
REM =============================================================================
REM Stop and remove Docker container
REM =============================================================================

echo ======================================================================
echo STOPPING DOCKER CONTAINER
echo ======================================================================
echo.

cd /d "%~dp0"

REM Stop container
echo Stopping container: ml-api
docker stop ml-api

REM Remove container
echo Removing container: ml-api
docker rm ml-api

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo CONTAINER STOPPED AND REMOVED
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo ERROR STOPPING CONTAINER
    echo ======================================================================
    echo.
    echo Container may not exist or may already be stopped
)

pause