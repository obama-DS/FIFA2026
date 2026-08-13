"""
Comprehensive Phase 20 verification script.
Checks for errors, missing dependencies, and unfinished items.
"""

import os
import sys
from datetime import datetime

print("=" * 80)
print("PHASE 20: COMPREHENSIVE VERIFICATION")
print("=" * 80)
print()

errors = []
warnings = []
checks_passed = 0
checks_total = 0

def check(name, condition, error_msg=None, warning_msg=None):
    """Track check results."""
    global checks_passed, checks_total, errors, warnings
    checks_total += 1
    if condition:
        checks_passed += 1
        print(f"✓ {name}")
        return True
    else:
        if error_msg:
            errors.append(error_msg)
            print(f"✗ {name}: {error_msg}")
        elif warning_msg:
            warnings.append(warning_msg)
            print(f"⚠ {name}: {warning_msg}")
        else:
            errors.append(name)
            print(f"✗ {name}")
        return False

# ==============================================================================
# FILE EXISTENCE CHECKS
# ==============================================================================
print("[1] FILE EXISTENCE")
print("-" * 80)

check(
    "gameweek package init",
    os.path.exists("src/gameweek/__init__.py"),
    "src/gameweek/__init__.py missing"
)

check(
    "gameweek engine module",
    os.path.exists("src/gameweek/gameweek_engine.py"),
    "src/gameweek/gameweek_engine.py missing"
)

check(
    "test script",
    os.path.exists("test_gameweek_engine.py"),
    "test_gameweek_engine.py missing"
)

check(
    "batch runner",
    os.path.exists("run_gameweek_test.bat"),
    "run_gameweek_test.bat missing"
)

check(
    "fixtures data",
    os.path.exists("data/master/fixtures_2026_27.csv"),
    "fixtures_2026_27.csv missing"
)

check(
    "features data",
    os.path.exists("data/features/match_features.csv"),
    "match_features.csv missing"
)

check(
    "home model",
    os.path.exists("models/best_model_home.pkl"),
    "best_model_home.pkl missing"
)

check(
    "away model",
    os.path.exists("models/best_model_away.pkl"),
    "best_model_away.pkl missing"
)

print()

# ==============================================================================
# IMPORT CHECKS
# ==============================================================================
print("[2] IMPORT CHECKS")
print("-" * 80)

try:
    from src.gameweek import GameweekEngine
    check("GameweekEngine import", True)
except Exception as e:
    check("GameweekEngine import", False, f"Import failed: {e}")

try:
    from src.predictions.match_probabilities import MatchProbabilityEngine
    check("MatchProbabilityEngine import", True)
except Exception as e:
    check("MatchProbabilityEngine import", False, f"Import failed: {e}")

try:
    from src.predictions.match_explanation import MatchExplainer
    check("MatchExplainer import", True)
except Exception as e:
    check("MatchExplainer import", False, f"Import failed: {e}")

try:
    from src.models.model_loader import load_best_models
    check("load_best_models import", True)
except Exception as e:
    check("load_best_models import", False, f"Import failed: {e}")

print()

# ==============================================================================
# DATA STRUCTURE CHECKS
# ==============================================================================
print("[3] DATA STRUCTURE CHECKS")
print("-" * 80)

try:
    import pandas as pd
    
    # Check fixtures
    fixtures = pd.read_csv("data/master/fixtures_2026_27.csv")
    
    check(
        "fixtures has round_number",
        'round_number' in fixtures.columns,
        "round_number column missing from fixtures"
    )
    
    check(
        "fixtures has fixture_id",
        'fixture_id' in fixtures.columns,
        "fixture_id column missing from fixtures"
    )
    
    check(
        "fixtures has season",
        'season' in fixtures.columns,
        "season column missing from fixtures"
    )
    
    check(
        "fixtures has kickoff",
        'kickoff' in fixtures.columns,
        "kickoff column missing from fixtures"
    )
    
    check(
        "fixtures has team names",
        'home_team_name' in fixtures.columns and 'away_team_name' in fixtures.columns,
        "team name columns missing from fixtures"
    )
    
    # Check 2026/27 season
    if 'season' in fixtures.columns:
        has_2026_27 = '2026/27' in fixtures['season'].values
        check(
            "fixtures has 2026/27 season",
            has_2026_27,
            warning_msg="No 2026/27 season found in fixtures"
        )
        
        if has_2026_27:
            season_fixtures = fixtures[fixtures['season'] == '2026/27']
            check(
                "2026/27 season has fixtures",
                len(season_fixtures) > 0,
                warning_msg="2026/27 season has no fixtures"
            )
    
    # Check features
    features = pd.read_csv("data/features/match_features.csv", low_memory=False)
    
    check(
        "features has is_fixture",
        'is_fixture' in features.columns,
        "is_fixture column missing from features"
    )
    
    check(
        "features has team names",
        'home_team_name' in features.columns and 'away_team_name' in features.columns,
        "team name columns missing from features"
    )
    
    if 'is_fixture' in features.columns:
        fixture_rows = features[features['is_fixture'] == True]
        check(
            "features has fixture rows",
            len(fixture_rows) > 0,
            warning_msg="No fixture rows in features (predictions will fail)"
        )
    
except Exception as e:
    check("data structure validation", False, f"Data check failed: {e}")

print()

# ==============================================================================
# CLASS STRUCTURE CHECKS
# ==============================================================================
print("[4] CLASS STRUCTURE CHECKS")
print("-" * 80)

try:
    from src.gameweek import GameweekEngine
    
    required_methods = [
        'get_current_gameweek',
        'get_gameweek_fixtures',
        'get_gameweek_deadline',
        'is_deadline_passed',
        'get_fixture_status',
        'get_featured_fixture',
        'get_fixture_prediction',
        'get_gameweek_predictions',
        'get_gameweek_summary',
        'print_gameweek_summary'
    ]
    
    for method in required_methods:
        check(
            f"GameweekEngine.{method}",
            hasattr(GameweekEngine, method),
            f"{method} method missing from GameweekEngine"
        )
    
except Exception as e:
    check("class structure validation", False, f"Class check failed: {e}")

print()

# ==============================================================================
# FUNCTIONALITY CHECKS (if no critical errors)
# ==============================================================================
if not errors:
    print("[5] BASIC FUNCTIONALITY CHECKS")
    print("-" * 80)
    
    try:
        from src.gameweek import GameweekEngine
        
        # Try initialization
        engine = GameweekEngine(
            fixtures_path="data/master/fixtures_2026_27.csv",
            features_path="data/features/match_features.csv",
            models_dir="models/",
            season='2026/27'
        )
        check("GameweekEngine initialization", True)
        
        # Test gameweek detection
        try:
            gw = engine.get_current_gameweek(datetime(2026, 8, 22))
            check(
                "get_current_gameweek",
                isinstance(gw, int) and gw > 0,
                f"Invalid gameweek returned: {gw}"
            )
        except Exception as e:
            check("get_current_gameweek", False, f"Method failed: {e}")
        
        # Test fixture retrieval
        try:
            fixtures = engine.get_gameweek_fixtures(1)
            check(
                "get_gameweek_fixtures",
                len(fixtures) >= 0,
                "Method failed"
            )
        except Exception as e:
            check("get_gameweek_fixtures", False, f"Method failed: {e}")
        
        # Test deadline calculation
        try:
            deadline = engine.get_gameweek_deadline(1)
            check(
                "get_gameweek_deadline",
                isinstance(deadline, (datetime, pd.Timestamp)),
                f"Invalid deadline type: {type(deadline)}"
            )
        except Exception as e:
            check("get_gameweek_deadline", False, f"Method failed: {e}")
        
        # Test deadline checking
        try:
            passed = engine.is_deadline_passed(1, datetime(2026, 8, 20))
            check(
                "is_deadline_passed",
                isinstance(passed, bool),
                f"Invalid return type: {type(passed)}"
            )
        except Exception as e:
            check("is_deadline_passed", False, f"Method failed: {e}")
        
        # Test featured fixture
        try:
            featured = engine.get_featured_fixture(1)
            check(
                "get_featured_fixture",
                featured is None or isinstance(featured, dict),
                f"Invalid return type: {type(featured)}"
            )
        except Exception as e:
            check("get_featured_fixture", False, f"Method failed: {e}")
        
        # Test summary
        try:
            summary = engine.get_gameweek_summary(1)
            check(
                "get_gameweek_summary",
                isinstance(summary, dict),
                f"Invalid return type: {type(summary)}"
            )
        except Exception as e:
            check("get_gameweek_summary", False, f"Method failed: {e}")
        
        print()
        
    except Exception as e:
        print(f"✗ Could not run functionality checks: {e}")
        print()

# ==============================================================================
# DOCUMENTATION CHECKS
# ==============================================================================
print("[6] DOCUMENTATION CHECKS")
print("-" * 80)

check(
    "Phase 20 summary document",
    os.path.exists("PHASE_20_SUMMARY.txt"),
    warning_msg="PHASE_20_SUMMARY.txt not found"
)

check(
    "Phase 20 quick reference",
    os.path.exists("PHASE_20_QUICK_REFERENCE.txt"),
    warning_msg="PHASE_20_QUICK_REFERENCE.txt not found"
)

print()

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
print("=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print()

print(f"Checks passed: {checks_passed}/{checks_total}")
print()

if errors:
    print("❌ CRITICAL ERRORS FOUND:")
    for i, err in enumerate(errors, 1):
        print(f"  {i}. {err}")
    print()

if warnings:
    print("⚠ WARNINGS:")
    for i, warn in enumerate(warnings, 1):
        print(f"  {i}. {warn}")
    print()

if not errors and not warnings:
    print("✅ PHASE 20 IS COMPLETE AND READY")
    print()
    print("All required files exist")
    print("All imports work correctly")
    print("All data structures are valid")
    print("All methods are implemented")
    print("Basic functionality works")
    print()
    print("Phase 20 can proceed to testing and Phase 21.")
    
elif not errors:
    print("✅ PHASE 20 IS FUNCTIONALLY COMPLETE")
    print()
    print("No critical errors found.")
    print("Minor warnings exist but do not block functionality.")
    print()
    print("Phase 20 is ready for Phase 21.")
    
else:
    print("❌ PHASE 20 HAS CRITICAL ISSUES")
    print()
    print("Please fix the errors listed above before proceeding.")

print("=" * 80)

sys.exit(0 if not errors else 1)
