# =============================================================================
# player_features.py
# =============================================================================
# Builds data/features/player_features.csv
#
# Source tables (read-only):
#   data/master/players_master.csv       -- identity (player_id, team_id, position)
#   data/master/player_season_stats.csv  -- season-level FBref stats (2025/26)
#
# Leakage rule:
#   Player stats are end-of-season aggregates. They are safe to use as features
#   only when predicting matches in a LATER season. The output therefore carries
#   a `valid_from_season` column: consumer scripts must filter so that the match
#   season is strictly after `valid_from_season`.
#
#   Example: 2025/26 player stats are valid features for 2026/27 predictions,
#            NOT for any match within 2025/26 itself.
#
# Output columns (one row per player_id x season):
#   Keys      : player_id, season, valid_from_season, team_id, player_name,
#               primary_position
#   Playing   : minutes_played, matches_played, starts, minutes_per_90
#   Attacking : goals, assists, goals_assists, non_pen_goals,
#               xg, xag, npxg, npxg_xag,
#               shots, shots_on_target, sot_pct, goals_per_shot, goals_per_sot,
#               xg_per_90, xag_per_90, npxg_per_90, g_a_per_90
#   Creativity: sca, gca, sca_per_90, gca_per_90,
#               key_passes, passes_into_box, prog_passes, prog_carries, prog_receptions
#   Defense   : tackles, tackles_won, interceptions, clearances,
#               blocks, tackle_win_rate, pressures_applied
#   Discipline: yellows, reds, fouls_committed, fouls_drawn
#   Possession: touches, carries, carry_dist, progressive_carry_dist,
#               dribbles_attempted, dribble_success_rate, miscontrols, dispossessed
#   Composite : performance_score (rank-aggregated, leakage-safe)
# =============================================================================

import sys
import os
import numpy as np
import pandas as pd

# Allow running directly from src/features/ or from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from common import read_master, save_features, safe_div

# ---------------------------------------------------------------------------
# Column mapping: FBref raw name -> clean feature name
# Only columns that exist in the file are used (graceful missing-column handling)
# ---------------------------------------------------------------------------
RENAME = {
    "Age":          "age",
    "MP":           "matches_played",
    "Starts":       "starts",
    "Min":          "minutes_played",
    "90s":          "minutes_per_90",
    # Attacking
    "Gls":          "goals",
    "Ast":          "assists",
    "G+A":          "goals_assists",
    "G-PK":         "non_pen_goals",
    "xG":           "xg",
    "xAG":          "xag",
    "npxG":         "npxg",
    "npxG+xAG":     "npxg_xag",
    "PrgC":         "prog_carries",
    "PrgP":         "prog_passes",
    "PrgR":         "prog_receptions",
    # Shooting
    "Sh":           "shots",
    "SoT":          "shots_on_target",
    "SoT%":         "sot_pct",
    "G/Sh":         "goals_per_shot",
    "G/SoT":        "goals_per_sot",
    "Dist":         "avg_shot_distance",
    # Passing / creativity
    "KP":           "key_passes",
    "PPA":          "passes_into_box",
    "SCA":          "sca",
    "SCA90":        "sca_per_90",
    "GCA":          "gca",
    "GCA90":        "gca_per_90",
    # Defense
    "Tkl":          "tackles",
    "TklW":         "tackles_won",
    "Int":          "interceptions",
    "Clr":          "clearances",
    "Err":          "errors_leading_to_shot",
    # Possession
    "Touches":      "touches",
    "Carries":      "carries",
    "TotDist_stats_possession":  "carry_dist",
    "PrgDist_stats_possession":  "progressive_carry_dist",
    "Att_stats_possession":      "dribbles_attempted",
    "Succ":         "dribbles_completed",
    "Succ%":        "dribble_success_rate",
    "Mis":          "miscontrols",
    "Dis":          "dispossessed",
    # Discipline
    "CrdY":         "yellows",
    "CrdR":         "reds",
    "Fls":          "fouls_committed",
    "Fld_stats_misc": "fouls_drawn",
    # Blocks (defense)
    "Blocks_stats_defense": "blocks",
}

# These per-90 features are derived explicitly (avoid FBref rounding)
PER90_DERIVE = {
    "goals_per_90":      "goals",
    "assists_per_90":    "assists",
    "xg_per_90":         "xg",
    "xag_per_90":        "xag",
    "npxg_per_90":       "npxg",
    "g_a_per_90":        "goals_assists",
    "shots_per_90":      "shots",
    "sot_per_90":        "shots_on_target",
    "tackles_per_90":    "tackles",
    "interceptions_per_90": "interceptions",
    "sca_per_90_calc":   "sca",
    "gca_per_90_calc":   "gca",
}

# Columns that form the composite performance score
PERF_COMPONENTS = [
    "goals", "assists", "xg", "xag",
    "prog_carries", "prog_passes", "prog_receptions",
    "sca", "gca",
    "tackles", "tackles_won", "interceptions", "clearances",
    "carries", "dribbles_completed",
]


def _rename_present(df: pd.DataFrame) -> pd.DataFrame:
    """Rename only columns that exist in the dataframe."""
    present = {k: v for k, v in RENAME.items() if k in df.columns}
    return df.rename(columns=present)


def _add_per90(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-90 columns derived from the clean feature names."""
    m90 = df.get("minutes_per_90", pd.Series(np.nan, index=df.index))
    for feat_name, src_col in PER90_DERIVE.items():
        if src_col in df.columns:
            df[feat_name] = safe_div(df[src_col], m90)
        else:
            df[feat_name] = np.nan
    return df


def _composite_score(df: pd.DataFrame) -> pd.Series:
    """
    Rank-aggregated performance score (0–1) using available components.
    Leakage-safe because it is built entirely from the same season's
    end-of-season stats; see `valid_from_season` for correct usage.
    """
    cols = [c for c in PERF_COMPONENTS if c in df.columns]
    if not cols:
        return pd.Series(0.5, index=df.index)
    ranked = df[cols].rank(pct=True, na_option="keep")
    return ranked.mean(axis=1)


def _next_season(season: str) -> str:
    """'2025/26' -> '2026/27'"""
    start = int(season[:4])
    return f"{start + 1}/{str(start + 2)[2:]}"


def build():
    print("=" * 65)
    print("BUILDING PLAYER FEATURES")
    print("=" * 65)

    players = read_master("players_master.csv")
    pstats  = read_master("player_season_stats.csv")

    # Merge identity onto stats
    df = pstats.merge(
        players[["player_id", "player_name", "primary_position"]],
        on="player_id", how="left"
    )

    # Rename FBref columns to clean names
    df = _rename_present(df)

    # Add derived per-90 features
    df = _add_per90(df)

    # Composite performance score
    df["performance_score"] = _composite_score(df)

    # valid_from_season: this season's stats are features for the NEXT season only
    df["valid_from_season"] = df["season"].map(_next_season)

    # Clamp percentages to [0, 100]
    for col in ["sot_pct", "dribble_success_rate"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 100)

    # Define final column order — only include what actually exists
    key_cols = ["player_id", "player_name", "season", "valid_from_season",
                "team_id", "primary_position"]
    playing_cols = ["age", "matches_played", "starts", "minutes_played", "minutes_per_90"]
    attacking_cols = [
        "goals", "assists", "goals_assists", "non_pen_goals",
        "xg", "xag", "npxg", "npxg_xag",
        "shots", "shots_on_target", "sot_pct", "avg_shot_distance",
        "goals_per_shot", "goals_per_sot",
        "goals_per_90", "assists_per_90", "xg_per_90", "xag_per_90",
        "npxg_per_90", "g_a_per_90", "shots_per_90", "sot_per_90",
    ]
    creativity_cols = [
        "sca", "gca", "sca_per_90", "gca_per_90",
        "sca_per_90_calc", "gca_per_90_calc",
        "key_passes", "passes_into_box",
        "prog_passes", "prog_carries", "prog_receptions",
    ]
    defense_cols = [
        "tackles", "tackles_won", "interceptions", "clearances",
        "blocks", "errors_leading_to_shot",
        "tackles_per_90", "interceptions_per_90",
    ]
    discipline_cols = ["yellows", "reds", "fouls_committed", "fouls_drawn"]
    possession_cols = [
        "touches", "carries", "carry_dist", "progressive_carry_dist",
        "dribbles_attempted", "dribbles_completed", "dribble_success_rate",
        "miscontrols", "dispossessed",
    ]
    composite_cols = ["performance_score"]

    all_desired = (key_cols + playing_cols + attacking_cols + creativity_cols
                   + defense_cols + discipline_cols + possession_cols + composite_cols)
    output_cols = [c for c in all_desired if c in df.columns]

    out = df[output_cols].copy()
    out = out.sort_values(["season", "team_id", "player_id"]).reset_index(drop=True)

    save_features(out, "player_features.csv")

    # Summary
    seasons = sorted(out["season"].unique())
    print(f"  Seasons covered : {seasons}")
    print(f"  Players         : {out['player_id'].nunique()}")
    print(f"  Features        : {len(output_cols) - len(key_cols)} (excl. keys)")
    print(f"  valid_from      : {sorted(out['valid_from_season'].unique())}")
    null_pct = out[output_cols].isnull().mean().mean() * 100
    print(f"  Overall null %  : {null_pct:.1f}%")

    return out


if __name__ == "__main__":
    build()
