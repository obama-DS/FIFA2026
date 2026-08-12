# Shared utilities and reusable merge helpers for the integration layer.
# Read-only with respect to the raw datasets.

import os

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DATA_DIR = PROJECT_ROOT
MASTER_DIR = os.path.join(PROJECT_ROOT, "data", "master")

RAW_PLAYERS = "players_data_light-2025_2026.csv"
RAW_FIXTURES = "epl-2026-GMTStandardTime.csv"

EPL_COMP = "eng Premier League"

# Raw file -> season.
MATCH_FILES = {
    "E0 (8).csv": "2018/19",
    "E0 (6).csv": "2019/20",
    "E0 (5).csv": "2020/21",
    "E0 (4).csv": "2021/22",
    "E0 (3).csv": "2022/23",
    "E0 (2).csv": "2023/24",
    "E0 (1).csv": "2024/25",
    "E0.csv": "2025/26",
}

# Alias -> canonical team name. Canonical names follow the Football-Data.co.uk
# (E0) style because the match data is the backbone of the project.
NAME_OVERRIDES = {
    "Man Utd": "Man United",
    "Manchester Utd": "Man United",
    "Manchester United": "Man United",
    "Manchester City": "Man City",
    "Newcastle Utd": "Newcastle",
    "Newcastle United": "Newcastle",
    "Nott'ham Forest": "Nott'm Forest",
    "Nottingham Forest": "Nott'm Forest",
    "Leeds United": "Leeds",
    "Spurs": "Tottenham",
    "Tottenham Hotspur": "Tottenham",
    "West Bromwich Albion": "West Brom",
    "Brighton & Hove Albion": "Brighton",
    "Wolverhampton Wanderers": "Wolves",
    "Huddersfield Town": "Huddersfield",
    "Leicester City": "Leicester",
    "Luton Town": "Luton",
    "Norwich City": "Norwich",
    "West Ham United": "West Ham",
    "Cardiff City": "Cardiff",
    "Coventry City": "Coventry",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "AFC Bournemouth": "Bournemouth",
}

FULL_NAMES = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton & Hove Albion",
    "Burnley": "Burnley",
    "Cardiff": "Cardiff City",
    "Chelsea": "Chelsea",
    "Coventry": "Coventry City",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Ipswich": "Ipswich Town",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Liverpool": "Liverpool",
    "Luton": "Luton Town",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Norwich": "Norwich City",
    "Nott'm Forest": "Nottingham Forest",
    "Sheffield United": "Sheffield United",
    "Southampton": "Southampton",
    "Sunderland": "Sunderland",
    "Tottenham": "Tottenham Hotspur",
    "Watford": "Watford",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
}


def ensure_dirs():
    os.makedirs(MASTER_DIR, exist_ok=True)


def canonical(name):
    key = str(name).strip()
    return NAME_OVERRIDES.get(key, key)


def full_name(name):
    key = str(name).strip()
    return FULL_NAMES.get(key, key)


def load_raw(filename):
    path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"raw dataset not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def read_master(filename):
    return pd.read_csv(os.path.join(MASTER_DIR, filename), encoding="utf-8-sig")


def export(df, filename):
    ensure_dirs()
    path = os.path.join(MASTER_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  Wrote {path} ({len(df)} rows x {len(df.columns)} cols)")
    return path


def check_unique(df, keys, label):
    dups = df[df.duplicated(subset=keys, keep=False)]
    if dups.empty:
        print(f"  OK: {label}: unique on {keys}")
        return True
    print(f"  WARNING: {label}: {len(dups)} duplicate row(s) on {keys}")
    return False


def map_names(series, lookup, label):
    mapped = series.map(lookup)
    missing = mapped.isna().sum()
    if missing:
        print(f"  WARNING: {label}: {missing} value(s) did not match the lookup")
        print("   unmatched:", list(series[mapped.isna()].unique())[:20])
    else:
        print(f"  OK: {label}: all {len(series)} values matched the lookup")
    return mapped


def merge_checked(left, right, on, how="left", label=""):
    result = left.merge(right, on=on, how=how, suffixes=("_L", "_R"), indicator=True)
    counts = result["_merge"].value_counts()
    matched = int(counts.get("both", 0))
    left_only = int(counts.get("left_only", 0))
    right_only = int(counts.get("right_only", 0))
    print(f"  merge [{label}]: matched={matched}, left-only={left_only}, right-only={right_only}")
    if how != "left" and right_only:
        print(f"  WARNING: {label}: {right_only} right-side row(s) had no match")
    return result.drop(columns=["_merge"])
