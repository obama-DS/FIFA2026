@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
"C:\Program Files\Python314\python.exe" validate_features.py > validation_report.txt 2>&1
type validation_report.txt
