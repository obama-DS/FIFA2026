import sys

outfile = open("C:\\Users\\Administrator\\Desktop\\FIFA2026\\training_output.txt", "w", encoding="utf-8")
sys.stdout = outfile
sys.stderr = outfile

try:
    exec(open("src/models/train_baseline.py").read())
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    outfile.close()
