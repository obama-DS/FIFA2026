@echo off
REM =============================================================================
REM run_match_probabilities_test.bat
REM =============================================================================
REM Phase 18: Test Match Probability Engine
REM =============================================================================

echo ======================================================================
echo MATCH PROBABILITY ENGINE - TEST
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check if Python exists
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Run standalone test first
echo [1] Testing Match Probability Engine standalone...
echo.
python src\predictions\match_probabilities.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo STANDALONE TEST FAILED
    echo ======================================================================
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo.

REM Run comprehensive test with real fixtures
echo [2] Testing with 2026/27 fixtures...
echo.
python test_match_probabilities.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo ALL TESTS PASSED
    echo ======================================================================
    echo.
    echo Match Probability Engine is ready for:
    echo   - Season Oracle integration
    echo   - Beat the AI API
) else (
    echo.
    echo ======================================================================
    echo TESTS FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
)

pause
