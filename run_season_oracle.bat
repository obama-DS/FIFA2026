@echo off
REM =============================================================================
REM run_season_oracle.bat
REM =============================================================================
REM Phase 17: Run Season Oracle simulation for 2026/27 season
REM =============================================================================

echo ======================================================================
echo SEASON ORACLE ENGINE - 2026/27 PREMIER LEAGUE
echo ======================================================================
echo.

cd /d "%~dp0"

REM Check if Python exists
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Check if models exist
if not exist "models\best_model_home.pkl" (
    echo ERROR: Trained models not found
    echo Please ensure Phase 9 training is complete
    exit /b 1
)

REM Run simulation
echo Running Season Oracle simulation...
echo This will generate 10,000 season simulations
echo.
python src\simulation\season_simulator.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo SIMULATION COMPLETE
    echo ======================================================================
    echo.
    echo Results saved to: outputs\season_simulations\
    echo.
    echo Key files:
    echo   - ai_fixture_predictions.csv
    echo   - team_probabilities.csv
    echo   - most_likely_final_table.csv
) else (
    echo.
    echo ======================================================================
    echo SIMULATION FAILED
    echo ======================================================================
    echo.
    echo Error code: %ERRORLEVEL%
)

pause