@echo off
cd /d "%~dp0"
echo Running training...
python -u src\models\train_compare_models.py 2>&1
echo Exit code: %ERRORLEVEL%
pause
