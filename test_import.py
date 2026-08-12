import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "features"))

try:
    print("Testing player_features import...")
    import player_features
    print("SUCCESS: player_features imported")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

try:
    print("\nTesting team_features import...")
    import team_features
    print("SUCCESS: team_features imported")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

try:
    print("\nTesting match_features import...")
    import match_features
    print("SUCCESS: match_features imported")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
