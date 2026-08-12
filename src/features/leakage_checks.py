# =============================================================================
# leakage_checks.py
# =============================================================================
# Reusable validation functions to detect common leakage patterns in feature
# datasets. Each check returns (passed: bool, message: str, details: dict).
#
# Leakage categories:
#   1. Future-data leakage  : features contain information from after the
#                             prediction point (match_date or season boundary)
#   2. Target leakage       : features directly encode the target variable
#   3. Time-ordering errors : features are not sorted chronologically or use
#                             data from later matches in the same time period
#   4. Duplicate information: same data appears in multiple feature columns
# =============================================================================

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. Future-data leakage checks
# ---------------------------------------------------------------------------

def check_rolling_first_match_nan(
    df: pd.DataFrame,
    group_col: str,
    sort_cols: list,
    rolling_cols: list,
) -> tuple[bool, str, dict]:
    """
    Verifies that the first row for each group has NaN for rolling features
    (because no prior data exists). If not NaN, the rolling window may be
    seeing current or future data.
    
    Args:
        df: feature dataframe
        group_col: column defining groups (e.g. 'team_id')
        sort_cols: columns to sort by (e.g. ['match_date', 'match_id'])
        rolling_cols: list of rolling feature column names to check
    
    Returns:
        (passed, message, details)
    """
    df_sorted = df.sort_values(sort_cols)
    first_rows = df_sorted.groupby(group_col).first()
    
    issues = []
    for col in rolling_cols:
        if col not in df.columns:
            continue
        non_nan = first_rows[col].notna().sum()
        total = len(first_rows)
        if non_nan > 0:
            issues.append({
                "column": col,
                "non_nan_first_rows": int(non_nan),
                "total_groups": int(total),
                "pct": round(non_nan / total * 100, 1),
            })
    
    if issues:
        return (
            False,
            f"FAIL: {len(issues)} rolling columns have non-NaN values in first rows (potential leakage)",
            {"issues": issues}
        )
    return (
        True,
        f"PASS: All {len(rolling_cols)} rolling columns are NaN for first rows",
        {}
    )


def check_valid_from_season(
    df: pd.DataFrame,
    season_col: str,
    valid_from_col: str,
) -> tuple[bool, str, dict]:
    """
    Verifies that valid_from_season is always AFTER the season the stats
    were collected in. This prevents using current-season stats as features
    for current-season predictions.
    
    Args:
        df: feature dataframe with season and valid_from_season columns
        season_col: name of the season column (e.g. 'season')
        valid_from_col: name of the valid_from column (e.g. 'valid_from_season')
    
    Returns:
        (passed, message, details)
    """
    if valid_from_col not in df.columns:
        return (True, f"SKIP: {valid_from_col} column not present", {})
    
    def _season_to_int(s):
        return int(str(s)[:4])
    
    df_check = df[[season_col, valid_from_col]].dropna()
    df_check["season_int"] = df_check[season_col].map(_season_to_int)
    df_check["valid_int"] = df_check[valid_from_col].map(_season_to_int)
    df_check["diff"] = df_check["valid_int"] - df_check["season_int"]
    
    bad = df_check[df_check["diff"] <= 0]
    if len(bad) > 0:
        return (
            False,
            f"FAIL: {len(bad)} rows have valid_from <= season (leakage)",
            {"bad_rows": int(len(bad)), "examples": bad.head(5).to_dict("records")}
        )
    
    return (
        True,
        f"PASS: All {len(df_check)} rows have valid_from > season (correct +1 year offset)",
        {}
    )


def check_h2h_uses_only_prior_matches(
    df: pd.DataFrame,
    date_col: str,
    h2h_match_col: str,
) -> tuple[bool, str, dict]:
    """
    Verifies that h2h_matches count is monotonically increasing or stable
    (never decreases) as we move forward in time. A decrease would indicate
    that a later match is using fewer prior H2H encounters than an earlier
    match, which is logically impossible and suggests time-ordering errors.
    
    Args:
        df: match features dataframe
        date_col: match_date column
        h2h_match_col: column with H2H match count (e.g. 'h2h_matches')
    
    Returns:
        (passed, message, details)
    """
    if h2h_match_col not in df.columns:
        return (True, f"SKIP: {h2h_match_col} not present", {})
    
    df_sorted = df.sort_values(date_col).copy()
    df_sorted["h2h_prev"] = df_sorted[h2h_match_col].shift(1)
    df_sorted["h2h_delta"] = df_sorted[h2h_match_col] - df_sorted["h2h_prev"]
    
    # Allow same or increase; flag decreases (excluding first row)
    bad = df_sorted[df_sorted["h2h_delta"] < 0]
    if len(bad) > 0:
        return (
            False,
            f"FAIL: {len(bad)} matches have FEWER h2h_matches than the previous match (time-ordering error)",
            {"bad_count": int(len(bad))}
        )
    
    return (
        True,
        f"PASS: h2h_matches count never decreases over time",
        {}
    )


# ---------------------------------------------------------------------------
# 2. Target leakage checks
# ---------------------------------------------------------------------------

def check_target_not_in_features(
    df: pd.DataFrame,
    target_cols: list,
    feature_cols: list,
) -> tuple[bool, str, dict]:
    """
    Verifies that no target column appears in the feature column list.
    Simple name-based check.
    
    Args:
        df: feature dataframe
        target_cols: list of target column names (e.g. ['result', 'home_goals', 'away_goals'])
        feature_cols: list of feature column names
    
    Returns:
        (passed, message, details)
    """
    overlap = set(target_cols) & set(feature_cols)
    if overlap:
        return (
            False,
            f"FAIL: Target columns found in features: {sorted(overlap)}",
            {"overlap": sorted(overlap)}
        )
    return (
        True,
        f"PASS: No target columns found in feature list",
        {}
    )


def check_fixtures_have_null_targets(
    df: pd.DataFrame,
    is_fixture_col: str,
    target_cols: list,
) -> tuple[bool, str, dict]:
    """
    Verifies that all rows where is_fixture=True have NaN for target columns.
    If fixture rows have non-null targets, the dataset was contaminated.
    
    Args:
        df: match features dataframe
        is_fixture_col: boolean column indicating fixture rows
        target_cols: list of target column names
    
    Returns:
        (passed, message, details)
    """
    if is_fixture_col not in df.columns:
        return (True, "SKIP: is_fixture column not present", {})
    
    fixtures = df[df[is_fixture_col] == True]
    if len(fixtures) == 0:
        return (True, "SKIP: No fixture rows found", {})
    
    issues = []
    for col in target_cols:
        if col not in df.columns:
            continue
        non_null = fixtures[col].notna().sum()
        if non_null > 0:
            issues.append({"column": col, "non_null_count": int(non_null)})
    
    if issues:
        return (
            False,
            f"FAIL: {len(issues)} target columns have non-null values in fixture rows",
            {"issues": issues}
        )
    
    return (
        True,
        f"PASS: All target columns are null for {len(fixtures)} fixture rows",
        {}
    )


# ---------------------------------------------------------------------------
# 3. Time-ordering checks
# ---------------------------------------------------------------------------

def check_chronological_order(
    df: pd.DataFrame,
    date_col: str,
    id_col: str = None,
) -> tuple[bool, str, dict]:
    """
    Verifies that the dataframe is sorted chronologically (ascending date).
    If id_col is provided, also checks secondary sort.
    
    Args:
        df: feature dataframe
        date_col: date column name
        id_col: optional ID column for tie-breaking
    
    Returns:
        (passed, message, details)
    """
    if date_col not in df.columns:
        return (True, f"SKIP: {date_col} not present", {})
    
    df_check = df[[date_col] + ([id_col] if id_col else [])].copy()
    df_check["_row"] = range(len(df_check))
    
    sort_cols = [date_col] + ([id_col] if id_col else [])
    df_sorted = df_check.sort_values(sort_cols).reset_index(drop=True)
    
    mismatches = (df_check["_row"] != df_sorted["_row"]).sum()
    if mismatches > 0:
        return (
            False,
            f"FAIL: DataFrame is not sorted by {sort_cols} ({mismatches} row-order mismatches)",
            {"mismatches": int(mismatches)}
        )
    
    return (
        True,
        f"PASS: DataFrame is sorted chronologically by {sort_cols}",
        {}
    )


# ---------------------------------------------------------------------------
# 4. Duplicate information checks
# ---------------------------------------------------------------------------

def check_duplicate_columns(
    df: pd.DataFrame,
    exclude_cols: list = None,
) -> tuple[bool, str, dict]:
    """
    Identifies pairs of columns with identical values (100% correlation).
    Duplicate columns waste model capacity and can cause multicollinearity.
    
    Args:
        df: feature dataframe
        exclude_cols: list of column names to exclude from the check
    
    Returns:
        (passed, message, details)
    """
    exclude = set(exclude_cols) if exclude_cols else set()
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c not in exclude]
    
    if len(numeric_cols) < 2:
        return (True, "SKIP: Fewer than 2 numeric columns", {})
    
    duplicates = []
    checked = set()
    
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i+1:]:
            pair = tuple(sorted([col_a, col_b]))
            if pair in checked:
                continue
            checked.add(pair)
            
            a_vals = df[col_a].dropna()
            b_vals = df[col_b].dropna()
            if len(a_vals) == 0 or len(b_vals) == 0:
                continue
            
            # Check if identical (allowing for floating-point tolerance)
            common_idx = a_vals.index.intersection(b_vals.index)
            if len(common_idx) == 0:
                continue
            
            diff = (a_vals.loc[common_idx] - b_vals.loc[common_idx]).abs()
            if diff.max() < 1e-9:
                duplicates.append({"col_a": col_a, "col_b": col_b})
    
    if duplicates:
        return (
            False,
            f"WARN: {len(duplicates)} pairs of duplicate columns detected",
            {"duplicates": duplicates[:10]}  # limit output
        )
    
    return (
        True,
        f"PASS: No duplicate columns found among {len(numeric_cols)} numeric columns",
        {}
    )


# ---------------------------------------------------------------------------
# Master audit function
# ---------------------------------------------------------------------------

def audit_dataset(
    df: pd.DataFrame,
    name: str,
    checks: list,
) -> dict:
    """
    Run a list of checks on a dataset and return a structured report.
    
    Args:
        df: feature dataframe
        name: human-readable dataset name
        checks: list of (check_function, kwargs) tuples
    
    Returns:
        dict with keys: name, total, passed, failed, results (list of check results)
    """
    results = []
    for check_fn, kwargs in checks:
        passed, message, details = check_fn(df, **kwargs)
        results.append({
            "check": check_fn.__name__,
            "passed": passed,
            "message": message,
            "details": details,
        })
    
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    
    return {
        "dataset": name,
        "total_checks": total,
        "passed": passed_count,
        "failed": failed_count,
        "results": results,
    }


def print_audit_report(report: dict):
    """Pretty-print an audit report."""
    print(f"\n{'=' * 65}")
    print(f"LEAKAGE AUDIT: {report['dataset']}")
    print(f"{'=' * 65}")
    print(f"Checks run: {report['total_checks']}  |  "
          f"Passed: {report['passed']}  |  Failed: {report['failed']}")
    print()
    
    for r in report["results"]:
        status = "✓" if r["passed"] else "✗"
        print(f"  [{status}] {r['check']}")
        print(f"      {r['message']}")
        if r["details"]:
            for k, v in r["details"].items():
                if isinstance(v, list) and len(v) > 3:
                    print(f"        {k}: {v[:3]} ... ({len(v)} total)")
                else:
                    print(f"        {k}: {v}")
    print()


# ---------------------------------------------------------------------------
# Main: audit all feature datasets
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    
    FEATURES_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "features"
    )
    
    def load(filename):
        return pd.read_csv(
            os.path.join(FEATURES_DIR, filename),
            encoding="utf-8-sig",
            low_memory=False
        )
    
    print("\n" + "=" * 65)
    print("PHASE 6: LEAKAGE PREVENTION — COMPREHENSIVE AUDIT")
    print("=" * 65)
    
    # --- Player features ---
    player_df = load("player_features.csv")
    player_checks = [
        (check_valid_from_season, {
            "season_col": "season",
            "valid_from_col": "valid_from_season",
        }),
        (check_chronological_order, {
            "date_col": "season",
            "id_col": "player_id",
        }),
    ]
    player_report = audit_dataset(player_df, "player_features.csv", player_checks)
    print_audit_report(player_report)
    
    # --- Team rolling features ---
    team_rolling_df = load("team_rolling_features.csv")
    rolling_feature_cols = [c for c in team_rolling_df.columns
                           if any(x in c for x in ["last3", "last5", "last10", "season", "expand", "streak"])]
    team_rolling_checks = [
        (check_rolling_first_match_nan, {
            "group_col": "team_id",
            "sort_cols": ["match_date", "match_id"],
            "rolling_cols": [c for c in rolling_feature_cols if "last3" in c][:5],  # sample
        }),
        (check_chronological_order, {
            "date_col": "match_date",
            "id_col": "match_id",
        }),
    ]
    team_rolling_report = audit_dataset(
        team_rolling_df, "team_rolling_features.csv", team_rolling_checks
    )
    print_audit_report(team_rolling_report)
    
    # --- Team season features ---
    team_season_df = load("team_season_features.csv")
    team_season_checks = [
        (check_valid_from_season, {
            "season_col": "season",
            "valid_from_col": "valid_from_season",
        }),
    ]
    team_season_report = audit_dataset(
        team_season_df, "team_season_features.csv", team_season_checks
    )
    print_audit_report(team_season_report)
    
    # --- Match features ---
    match_df = load("match_features.csv")
    match_df["match_date"] = pd.to_datetime(match_df["match_date"])
    
    key_cols = [
        "match_id", "row_id", "season", "match_date", "is_fixture",
        "home_team_id", "away_team_id", "home_team_name", "away_team_name",
    ]
    target_cols = ["result", "home_goals", "away_goals"]
    feature_cols = [c for c in match_df.columns if c not in key_cols + target_cols]
    
    match_checks = [
        (check_target_not_in_features, {
            "target_cols": target_cols,
            "feature_cols": feature_cols,
        }),
        (check_fixtures_have_null_targets, {
            "is_fixture_col": "is_fixture",
            "target_cols": target_cols,
        }),
        (check_h2h_uses_only_prior_matches, {
            "date_col": "match_date",
            "h2h_match_col": "h2h_matches",
        }),
        (check_chronological_order, {
            "date_col": "match_date",
            "id_col": "match_id",
        }),
    ]
    match_report = audit_dataset(match_df, "match_features.csv", match_checks)
    print_audit_report(match_report)
    
    # --- Summary ---
    all_reports = [player_report, team_rolling_report, team_season_report, match_report]
    total_checks = sum(r["total_checks"] for r in all_reports)
    total_passed = sum(r["passed"] for r in all_reports)
    total_failed = sum(r["failed"] for r in all_reports)
    
    print("=" * 65)
    print("AUDIT SUMMARY")
    print("=" * 65)
    print(f"Total checks: {total_checks}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print()
    
    if total_failed == 0:
        print("✓ ALL CHECKS PASSED — No leakage detected")
    else:
        print(f"✗ {total_failed} CHECKS FAILED — Review details above")
    print()
