@echo off
cd /d "C:\Users\Administrator\Desktop\FIFA2026"
"C:\Program Files\Python314\python.exe" test_import.py > test_output.txt 2>&1
type test_output.txt
