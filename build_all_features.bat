@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
echo ============================================================
echo Building player features...
echo ============================================================
"C:\Program Files\Python314\python.exe" "src\features\player_features.py"
if %errorlevel% neq 0 (
    echo ERROR: player_features.py failed
    exit /b 1
)

echo.
echo ============================================================
echo Building team features...
echo ============================================================
"C:\Program Files\Python314\python.exe" "src\features\team_features.py"
if %errorlevel% neq 0 (
    echo ERROR: team_features.py failed
    exit /b 1
)

echo.
echo ============================================================
echo Building match features...
echo ============================================================
"C:\Program Files\Python314\python.exe" "src\features\match_features.py"
if %errorlevel% neq 0 (
    echo ERROR: match_features.py failed
    exit /b 1
)

echo.
echo ============================================================
echo ALL FEATURES BUILT SUCCESSFULLY
echo ============================================================
