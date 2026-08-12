import sys
import os

sys.path.insert(0, "src/features")

try:
    import leakage_checks
    print("Import successful")
    import pandas as pd
    
    # Quick test
    df = pd.DataFrame({"season": ["2024/25"], "valid_from_season": ["2025/26"]})
    passed, msg, details = leakage_checks.check_valid_from_season(df, "season", "valid_from_season")
    print(f"Test check: passed={passed}, msg={msg}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
