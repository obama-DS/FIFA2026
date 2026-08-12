@echo off
REM =============================================================================
REM run_tests.bat
REM =============================================================================
REM Phase 10: Execute prediction pipeline tests
REM
REM Runs comprehensive tests covering:
REM - Model loading and validation
REM - Feature preparation
REM - Prediction generation
REM - Full pipeline execution
REM - Edge cases and error handling
REM =============================================================================

echo ======================================================================
echo PHASE 10: PREDICTION PIPELINE TESTS
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

REM Run tests
echo Running test suite...
echo.
python src\models\test_predictions.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo ALL TESTS PASSED
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo SOME TESTS FAILED
    echo ======================================================================
    echo.
    echo Please review the test output above
)

pause
exit /b %ERRORLEVEL%
