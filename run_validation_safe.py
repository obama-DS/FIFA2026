import sys

outfile = open("C:\\Users\\Administrator\\Desktop\\FIFA2026\\validation_output.txt", "w", encoding="utf-8")
sys.stdout = outfile
sys.stderr = outfile

try:
    exec(open("validate_features.py").read())
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    outfile.close()
