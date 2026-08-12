# Orchestrates the full feature engineering pipeline.
# Run from the project root:  python run_features.py

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "features"))

print("\n" + "=" * 65)
print("STEP 1 / 3 — Player features")
print("=" * 65)
import player_features
player_df = player_features.build()

print("\n" + "=" * 65)
print("STEP 2 / 3 — Team features")
print("=" * 65)
import team_features
rolling_df, season_df = team_features.build()

print("\n" + "=" * 65)
print("STEP 3 / 3 — Match features")
print("=" * 65)
import match_features
match_df = match_features.build()

print("\n" + "=" * 65)
print("PIPELINE COMPLETE")
print("=" * 65)
