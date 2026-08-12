@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
"C:\Program Files\Python314\python.exe" "src\features\leakage_checks.py" > leakage_audit.txt 2>&1
type leakage_audit.txt
