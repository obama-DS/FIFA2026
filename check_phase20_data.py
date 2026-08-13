"""Quick check of Phase 20 data requirements."""
import pandas as pd
import os

print("=" * 70)
print("PHASE 20 DATA VALIDATION")
print("=" * 70)
print()

errors = []
warnings = []

# Check fixtures file
print("[1] Checking fixtures_2026_27.csv...")
try:
    fixtures = pd.read_csv("data/master/fixtures_2026_27.csv")
    print(f"    ✓ Loaded {len(fixtures)} rows")
    
    required_cols = ['fixture_id', 'season', 'home_team_name', 'away_team_name', 'kickoff', 'round_number']
    missing_cols = [col for col in required_cols if col not in fixtures.columns]
    
    if missing_cols:
        errors.append(f"Fixtures CSV missing columns: {missing_cols}")
        print(f"    ✗ Missing columns: {missing_cols}")
    else:
        print(f"    ✓ All required columns present")
    
    # Check round_number field
    if 'round_number' in fixtures.columns:
        unique_gws = sorted(fixtures['round_number'].dropna().unique())
        print(f"    ✓ round_number field exists: {len(unique_gws)} gameweeks ({min(unique_gws)}-{max(unique_gws)})")
    else:
        errors.append("round_number field missing from fixtures")
    
    # Check season filter
    if 'season' in fixtures.columns:
        seasons = fixtures['season'].unique()
        has_2026_27 = '2026/27' in seasons
        print(f"    Seasons: {list(seasons)}")
        if not has_2026_27:
            warnings.append("No 2026/27 season fixtures found")
            print(f"    ⚠ No 2026/27 fixtures")
        else:
            gw1_fixtures = fixtures[fixtures['season'] == '2026/27']
            print(f"    ✓ Found {len(gw1_fixtures)} fixtures for 2026/27")
    
except Exception as e:
    errors.append(f"Cannot load fixtures: {e}")
    print(f"    ✗ Error: {e}")

print()

# Check features file
print("[2] Checking match_features.csv...")
try:
    features = pd.read_csv("data/features/match_features.csv", low_memory=False)
    print(f"    ✓ Loaded {len(features)} rows")
    
    required_cols = ['season', 'home_team_name', 'away_team_name', 'is_fixture']
    missing_cols = [col for col in required_cols if col not in features.columns]
    
    if missing_cols:
        errors.append(f"Features CSV missing columns: {missing_cols}")
        print(f"    ✗ Missing columns: {missing_cols}")
    else:
        print(f"    ✓ All required columns present")
    
    # Check for fixture rows
    if 'is_fixture' in features.columns:
        fixture_rows = features[features['is_fixture'] == True]
        print(f"    ✓ Found {len(fixture_rows)} fixture feature rows")
        
        if len(fixture_rows) == 0:
            warnings.append("No fixture rows in features (predictions will fail)")
    
except Exception as e:
    errors.append(f"Cannot load features: {e}")
    print(f"    ✗ Error: {e}")

print()

# Check models
print("[3] Checking models directory...")
try:
    if os.path.exists("models/best_model_home.pkl"):
        print("    ✓ best_model_home.pkl exists")
    else:
        errors.append("best_model_home.pkl missing")
        print("    ✗ best_model_home.pkl missing")
    
    if os.path.exists("models/best_model_away.pkl"):
        print("    ✓ best_model_away.pkl exists")
    else:
        errors.append("best_model_away.pkl missing")
        print("    ✗ best_model_away.pkl missing")
    
    if os.path.exists("models/best_model.json"):
        print("    ✓ best_model.json exists")
    else:
        errors.append("best_model.json missing")
        print("    ✗ best_model.json missing")
        
except Exception as e:
    errors.append(f"Cannot check models: {e}")
    print(f"    ✗ Error: {e}")

print()

# Check Phase 20 files
print("[4] Checking Phase 20 files...")
phase20_files = [
    "src/gameweek/__init__.py",
    "src/gameweek/gameweek_engine.py",
    "test_gameweek_engine.py",
    "run_gameweek_test.bat"
]

for file in phase20_files:
    if os.path.exists(file):
        print(f"    ✓ {file}")
    else:
        errors.append(f"Missing file: {file}")
        print(f"    ✗ {file} MISSING")

print()

# Summary
print("=" * 70)
if errors:
    print("❌ ERRORS FOUND:")
    for err in errors:
        print(f"  - {err}")
    print()

if warnings:
    print("⚠ WARNINGS:")
    for warn in warnings:
        print(f"  - {warn}")
    print()

if not errors and not warnings:
    print("✅ ALL CHECKS PASSED - Phase 20 is ready")
elif not errors:
    print("✅ NO CRITICAL ERRORS - Phase 20 should work (with warnings)")
else:
    print("❌ CRITICAL ERRORS FOUND - Phase 20 needs fixes")

print("=" * 70)
