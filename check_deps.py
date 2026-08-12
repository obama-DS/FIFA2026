import sys

try:
    import sklearn
    print(f"sklearn version: {sklearn.__version__}")
except ImportError:
    print("sklearn NOT installed")
    sys.exit(1)

try:
    import pandas
    print(f"pandas version: {pandas.__version__}")
except ImportError:
    print("pandas NOT installed")
    sys.exit(1)

try:
    import numpy
    print(f"numpy version: {numpy.__version__}")
except ImportError:
    print("numpy NOT installed")
    sys.exit(1)

try:
    import joblib
    print(f"joblib version: {joblib.__version__}")
except ImportError:
    print("joblib NOT installed")
    sys.exit(1)

print("\nAll dependencies OK")
