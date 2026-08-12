import sys
sys.path.insert(0, "src/features")

outfile = open("C:\\Users\\Administrator\\Desktop\\FIFA2026\\audit_results.txt", "w")
sys.stdout = outfile
sys.stderr = outfile

try:
    import leakage_checks
    # Run the main audit (it calls print statements)
    exec(open("src/features/leakage_checks.py").read())
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    outfile.close()
