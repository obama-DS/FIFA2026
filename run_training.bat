@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
echo ============================================================
echo Phase 8: ML Training Pipeline
echo ============================================================
"C:\Program Files\Python314\python.exe" "src\models\train_baseline.py"
if %errorlevel% neq 0 (
    echo ERROR: Training failed
    exit /b 1
)
echo.
echo ============================================================
echo Training complete
echo ============================================================
