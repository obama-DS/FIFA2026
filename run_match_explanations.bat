@echo off
REM =============================================================================
REM run_match_explanations.bat
REM =============================================================================
REM Phase 19: Generate Explainable Match Predictions
REM =============================================================================

echo ======================================================================
echo PHASE 19: EXPLAINABLE MATCH PREDICTIONS
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo Generating match explanations...
echo.

python src\predictions\match_explanation.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo SUCCESS
    echo ======================================================================
    echo.
    echo Explanations generated successfully!
    echo Check: outputs\explanations\
) else (
    echo.
    echo ======================================================================
    echo FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
)

pause
