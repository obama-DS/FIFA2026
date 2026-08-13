@echo off
REM =============================================================================
REM run_api.bat
REM =============================================================================
REM Phase 14: FastAPI Server Runner
REM
REM Starts the FastAPI development server
REM =============================================================================

echo ======================================================================
echo PHASE 14: FASTAPI SERVER
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check if Python exists
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your PATH
    exit /b 1
)

REM Check if models exist
if not exist "models\best_model.json" (
    echo ERROR: Trained models not found
    echo Please run Phase 9 training first
    exit /b 1
)

REM Install required packages if needed
echo Checking dependencies...
python -c "import fastapi, uvicorn" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing FastAPI and Uvicorn...
    pip install fastapi uvicorn python-multipart
)

REM Start the API server
echo.
echo ======================================================================
echo Starting FastAPI server...
echo ======================================================================
echo.
echo API will be available at:
echo - Swagger UI: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo - API Base: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python src\api\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo SERVER STARTUP FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
    echo Check the output above for details
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo SERVER STOPPED
echo ======================================================================
pause