@echo off
REM =============================================================================
REM run_explainability.bat
REM =============================================================================
REM Phase 11: Execute model explainability analysis
REM
REM Generates:
REM - Global feature importance (home/away)
REM - Individual match explanations
REM - SHAP values (if available)
REM - Summary report
REM =============================================================================

echo ======================================================================
echo PHASE 11: MODEL EXPLAINABILITY
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
if not exist "models\best_model_home.pkl" (
    echo ERROR: Models not found
    echo Please run Phase 9 training first: run_training.bat
    exit /b 1
)

REM Run explainability
echo Running explainability analysis...
echo.
python src\models\explain.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo EXPLAINABILITY ANALYSIS COMPLETE
    echo ======================================================================
    echo.
    echo Check outputs/explainability/ for results
) else (
    echo.
    echo ======================================================================
    echo EXPLAINABILITY ANALYSIS FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
)

pause
exit /b %ERRORLEVEL%
