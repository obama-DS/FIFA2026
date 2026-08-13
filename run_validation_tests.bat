@echo off
REM =============================================================================
REM run_validation_tests.bat
REM =============================================================================
REM Phase 13: Execute prediction validation tests
REM
REM Runs comprehensive validation tests:
REM - Valid inputs
REM - Missing data
REM - Invalid types
REM - Extreme values
REM - Edge cases
REM - Output validation
REM =============================================================================

echo ======================================================================
echo PHASE 13: PREDICTION VALIDATION TESTS
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

REM Run validation tests
echo Running validation tests...
echo.
python tests\test_prediction_validation.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo ALL VALIDATION TESTS PASSED
    echo ======================================================================
    echo.
    echo Prediction pipeline validated successfully
) else (
    echo.
    echo ======================================================================
    echo SOME VALIDATION TESTS FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
    echo Review test output above for details
)

pause
exit /b %ERRORLEVEL%
