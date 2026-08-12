@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
echo ============================================================
echo Phase 9: Model Selection and Comparison
echo ============================================================
"C:\Program Files\Python314\python.exe" "src\models\train_compare_models.py"
if %errorlevel% neq 0 (
    echo ERROR: Model selection failed
    exit /b 1
)
echo.
echo ============================================================
echo Model selection complete
echo ============================================================
