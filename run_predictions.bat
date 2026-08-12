@echo off
REM =============================================================================
REM run_predictions.bat
REM =============================================================================
REM Phase 10: Execute prediction pipeline
REM
REM Usage:
REM   run_predictions.bat          - Predict all fixtures
REM   run_predictions.bat 2026/27  - Predict only 2026/27 season
REM =============================================================================

echo ======================================================================
echo PHASE 10: MATCH PREDICTION PIPELINE
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

REM Run predictions
if "%~1"=="" (
    echo Running predictions for all fixtures...
    echo.
    python src\models\predict.py
) else (
    echo Running predictions for season: %~1
    echo.
    python src\models\predict.py "%~1"
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo PREDICTION PIPELINE COMPLETE
    echo ======================================================================
    echo.
    echo Check outputs/predictions.csv for results
) else (
    echo.
    echo ======================================================================
    echo PREDICTION PIPELINE FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
)

pause
exit /b %ERRORLEVEL%
