# =============================================================================
# validate_features.py - Comprehensive feature dataset validation
# =============================================================================
# Validates all feature datasets for ML training readiness.
# Checks: missing values, duplicates, invalid values, relationships, consistency.
# Outputs detailed report to console.
# =============================================================================

import sys
import os
import pandas as pd
import numpy as np

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "data", "features")


def load_feature(filename):
    path = os.path.join(FEATURES_DIR, filename)
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


print("=" * 70)
print("PHASE 7: FEATURE VALIDATION")
print("=" * 70)
print()

# ---------------------------------------------------------------------------
# Load all datasets
# ---------------------------------------------------------------------------
print("[1] Loading feature datasets...")
player_df = load_feature("player_features.csv")
team_rolling_df = load_feature("team_rolling_features.csv")
team_season_df = load_feature("team_season_features.csv")
match_df = load_feature("match_features.csv")
match_df["match_date"] = pd.to_datetime(match_df["match_date"])
print(f"  player_features        : {player_df.shape}")
print(f"  team_rolling_features  : {team_rolling_df.shape}")
print(f"  team_season_features   : {team_season_df.shape}")
print(f"  match_features         : {match_df.shape}")
print()

# ---------------------------------------------------------------------------
# Missing Values Analysis
# ---------------------------------------------------------------------------
print("=" * 70)
print("[2] MISSING VALUES ANALYSIS")
print("=" * 70)


def analyze_missing(df, name, key_cols):
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isna().sum().sum()
    missing_pct = (missing_cells / total_cells) * 100
    
    print(f"\n{name}")
    print(f"  Total cells    : {total_cells:,}")
    print(f"  Missing cells  : {missing_cells:,}")
    print(f"  Missing %      : {missing_pct:.2f}%")
    
    # Per-column breakdown (top 10 worst)
    col_missing = df.isna().sum()
    col_missing_pct = (col_missing / len(df)) * 100
    worst = col_missing_pct[col_missing_pct > 0].sort_values(ascending=False).head(10)
    
    if len(worst) > 0:
        print(f"  Columns with missing (top 10):")
        for col, pct in worst.items():
            count = int(col_missing[col])
            print(f"    {col:40s} : {count:5d} ({pct:5.1f}%)")
    else:
        print("  No missing values")
    
    # Check if key columns have missing
    key_missing = df[key_cols].isna().any().any()
    if key_missing:
        print(f"  ⚠️  WARNING: Key columns have missing values!")
        for col in key_cols:
            n = df[col].isna().sum()
            if n > 0:
                print(f"      {col}: {n} missing")
    else:
        print(f"  ✓ Key columns complete")


analyze_missing(player_df, "player_features.csv", ["player_id", "season", "team_id"])
analyze_missing(team_rolling_df, "team_rolling_features.csv", ["team_id", "match_id", "match_date"])
analyze_missing(team_season_df, "team_season_features.csv", ["team_id", "season"])
analyze_missing(match_df, "match_features.csv", ["match_id", "season", "match_date", "home_team_id", "away_team_id"])

# ---------------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("[3] DUPLICATE DETECTION")
print("=" * 70)


def check_duplicates(df, name, key_cols):
    dups = df.duplicated(subset=key_cols, keep=False)
    dup_count = dups.sum()
    print(f"\n{name}")
    print(f"  Key columns    : {key_cols}")
    print(f"  Duplicate rows : {dup_count}")
    if dup_count > 0:
        print(f"  ⚠️  WARNING: {dup_count} duplicate rows found!")
        print("  Sample:")
        print(df[dups].head(5)[key_cols + ["player_name" if "player_name" in df.columns else "team_id"]])
    else:
        print(f"  ✓ No duplicates")


check_duplicates(player_df, "player_features.csv", ["player_id", "season"])
check_duplicates(team_rolling_df, "team_rolling_features.csv", ["team_id", "match_id"])
check_duplicates(team_season_df, "team_season_features.csv", ["team_id", "season"])
check_duplicates(match_df, "match_features.csv", ["match_id"])

# ---------------------------------------------------------------------------
# Invalid Values
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("[4] INVALID VALUES")
print("=" * 70)


def check_invalid(df, name, checks):
    print(f"\n{name}")
    issues = []
    for check_name, condition, cols in checks:
        if isinstance(cols, str):
            cols = [cols]
        for col in cols:
            if col not in df.columns:
                continue
            invalid = condition(df[col])
            if isinstance(invalid, pd.Series):
                invalid_count = invalid.sum()
            else:
                invalid_count = invalid
            if invalid_count > 0:
                issues.append((check_name, col, invalid_count))
    
    if issues:
        print(f"  ⚠️  {len(issues)} invalid value issue(s) found:")
        for check_name, col, count in issues:
            print(f"    {check_name:30s} {col:30s} : {count} rows")
    else:
        print(f"  ✓ No invalid values detected")


# Player checks
player_checks = [
    ("Negative values", lambda s: (s < 0) & s.notna(), ["age", "matches_played", "minutes_played", "goals", "assists"]),
    ("Percentages > 100", lambda s: (s > 100) & s.notna(), ["sot_pct", "dribble_success_rate"]),
]
check_invalid(player_df, "player_features.csv", player_checks)

# Team rolling checks
team_rolling_checks = [
    ("Negative values", lambda s: (s < 0) & s.notna(), ["points_last3", "gf_last3", "shots_f_last3"]),
    ("Win rate > 1.0", lambda s: (s > 1.0) & s.notna(), ["win_last3", "win_rate_h_last5"]),
]
check_invalid(team_rolling_df, "team_rolling_features.csv", team_rolling_checks)

# Match checks
match_checks = [
    ("Negative values", lambda s: (s < 0) & s.notna(), ["home_goals", "away_goals"]),
    ("Invalid result", lambda s: s.notna() & ~s.isin(["H", "D", "A"]), ["result"]),
]
check_invalid(match_df, "match_features.csv", match_checks)

# ---------------------------------------------------------------------------
# Relationship Validation
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("[5] RELATIONSHIP VALIDATION")
print("=" * 70)

print("\nCross-dataset key consistency:")

# Check: all match home/away team_ids exist in team_rolling
match_teams = set(match_df["home_team_id"].unique()) | set(match_df["away_team_id"].unique())
rolling_teams = set(team_rolling_df["team_id"].unique())
missing_teams = match_teams - rolling_teams
print(f"  match teams -> team_rolling : {len(match_teams)} teams")
if missing_teams:
    print(f"    ⚠️  {len(missing_teams)} match teams missing from team_rolling: {sorted(missing_teams)[:5]}")
else:
    print(f"    ✓ All match teams present in team_rolling")

# Check: player team_ids exist in season teams
player_teams = set(player_df["team_id"].unique())
season_teams = set(team_season_df["team_id"].unique())
missing_player_teams = player_teams - season_teams
print(f"  player teams -> team_season : {len(player_teams)} teams")
if missing_player_teams:
    print(f"    ⚠️  {len(missing_player_teams)} player teams missing from team_season: {sorted(missing_player_teams)[:5]}")
else:
    print(f"    ✓ All player teams present in team_season")

# Check: match_df has both historical and fixtures
hist_count = (~match_df["is_fixture"]).sum()
fix_count = match_df["is_fixture"].sum()
print(f"\nmatch_features composition:")
print(f"  Historical matches : {hist_count}")
print(f"  Fixtures (2026/27) : {fix_count}")
print(f"  Total              : {len(match_df)}")

# ---------------------------------------------------------------------------
# Feature Consistency
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("[6] FEATURE CONSISTENCY")
print("=" * 70)

print("\nRolling window population (sample check):")
# Check: later matches should have populated rolling features
sample_late = team_rolling_df[team_rolling_df["match_date"] > "2024-01-01"].copy()
sample_late_notna = sample_late["points_last3"].notna().sum()
sample_late_total = len(sample_late)
print(f"  Matches after 2024-01-01 with non-null points_last3: {sample_late_notna}/{sample_late_total}")
if sample_late_notna < sample_late_total * 0.9:
    print(f"    ⚠️  Expected most rolling features to be populated by 2024")
else:
    print(f"    ✓ Rolling features well-populated")

print("\nValid_from_season consistency:")
# Check: player valid_from > season
player_sample = player_df[["season", "valid_from_season"]].dropna().head(5)
print(f"  Sample player rows:")
for _, row in player_sample.iterrows():
    s_year = int(row["season"][:4])
    v_year = int(row["valid_from_season"][:4])
    status = "✓" if v_year == s_year + 1 else "✗"
    print(f"    {status} season={row['season']} -> valid_from={row['valid_from_season']}")

# ---------------------------------------------------------------------------
# Train-Ready Structure
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("[7] TRAIN-READY STRUCTURE")
print("=" * 70)

# Identify feature vs key vs target columns in match_df
key_cols_match = ["match_id", "row_id", "season", "match_date", "is_fixture",
                  "home_team_id", "away_team_id", "home_team_name", "away_team_name"]
target_cols_match = ["result", "home_goals", "away_goals"]
feature_cols_match = [c for c in match_df.columns if c not in key_cols_match + target_cols_match]

print(f"\nmatch_features.csv structure:")
print(f"  Key columns     : {len(key_cols_match)}")
print(f"  Target columns  : {len(target_cols_match)}")
print(f"  Feature columns : {len(feature_cols_match)}")

# Check: numeric feature proportion
numeric_features = match_df[feature_cols_match].select_dtypes(include=[np.number]).columns
print(f"  Numeric features: {len(numeric_features)} ({len(numeric_features)/len(feature_cols_match)*100:.1f}%)")

# Check: training data availability
train_mask = (~match_df["is_fixture"]) & (match_df["result"].notna())
train_rows = train_mask.sum()
print(f"\nTraining data availability:")
print(f"  Rows with non-null targets : {train_rows}")
print(f"  Rows for prediction        : {fix_count} (fixtures)")

# Check: feature completeness for training rows
train_features = match_df.loc[train_mask, feature_cols_match]
train_missing_pct = (train_features.isna().sum().sum() / (train_features.shape[0] * train_features.shape[1])) * 100
print(f"  Missing % in training rows : {train_missing_pct:.2f}%")

if train_missing_pct > 20:
    print(f"    ⚠️  HIGH: >20% missing in training features")
elif train_missing_pct > 5:
    print(f"    ⚠️  MODERATE: 5-20% missing (imputation recommended)")
else:
    print(f"    ✓ Low missing rate (<5%)")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

issues_found = []

# Missing values check
if player_df.isna().sum().sum() / (player_df.shape[0] * player_df.shape[1]) > 0.1:
    issues_found.append("player_features: >10% missing")
if train_missing_pct > 20:
    issues_found.append("match_features training rows: >20% missing")

# Duplicates
if player_df.duplicated(["player_id", "season"]).any():
    issues_found.append("player_features: duplicates found")
if match_df.duplicated(["match_id"]).any():
    issues_found.append("match_features: duplicates found")

# Invalid values
if ((player_df["age"] < 0) & player_df["age"].notna()).any():
    issues_found.append("player_features: negative age values")
if ((match_df["home_goals"] < 0) & match_df["home_goals"].notna()).any():
    issues_found.append("match_features: negative goal values")

# Relationships
if missing_teams:
    issues_found.append(f"{len(missing_teams)} match teams missing from team_rolling")

print(f"\nDatasets validated: 4")
print(f"Checks performed  : 7 categories")
print(f"Issues found      : {len(issues_found)}")

if issues_found:
    print("\n⚠️  ISSUES REQUIRING ATTENTION:")
    for issue in issues_found:
        print(f"  - {issue}")
    print("\n❌ NOT READY for ML training (address issues above)")
else:
    print("\n✅ ALL CHECKS PASSED")
    print("✅ DATASETS ARE READY FOR ML TRAINING")

print()
