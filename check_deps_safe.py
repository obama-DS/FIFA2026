outfile = open("C:\\Users\\Administrator\\Desktop\\FIFA2026\\deps_check.txt", "w")
import sys
sys.stdout = outfile
sys.stderr = outfile

try:
    exec(open("check_deps.py").read())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    outfile.close()
