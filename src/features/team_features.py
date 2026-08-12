# =============================================================================
# team_features.py
# =============================================================================
# Builds two output files:
#
#   data/features/team_rolling_features.csv
#       One row per (team_id, match_id). Contains rolling pre-match features
#       for that team computed from all their previous matches. These are the
#       primary team features for match prediction and have ZERO leakage: every
#       statistic is computed exclusively from matches before match_date.
#
#   data/features/team_season_features.csv
#       One row per (team_id, season). Full-season aggregated features derived
#       from team_season_stats.csv. Safe as prior-season features only; the
#       output carries a `valid_from_season` column for consumer enforcement.
#
# Rolling windows computed:
#   last3  (w=3)  -- very recent form
#   last5  (w=5)  -- short-term form
#   last10 (w=10) -- medium-term form
#   season (w=38) -- full-season rolling (uses min_periods=1, no NaN)
#
# For each window, the following are computed:
#   Outcome : points_per_game, win_rate, draw_rate, loss_rate
#   Goals   : goals_scored_pg, goals_conceded_pg, goal_diff_pg,
#             clean_sheet_rate, failed_to_score_rate
#   Shots   : shots_pg, shots_conceded_pg, sot_pg, sot_conceded_pg,
#             shot_accuracy, shot_conversion
#   Misc    : corners_pg, fouls_pg, yellows_pg, reds_pg
#
# Additionally (window-independent):
#   Streaks      : win_streak, unbeaten_streak (from all prior matches)
#   Venue splits : home/away win_rate over last5, last10
#   Expanding    : cumulative ppg, goals_pg, xcs_rate (all prior matches)
#
# =============================================================================

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from common import (
    read_master, save_features, safe_div,
    rolling_mean_min1, rolling_sum_min1, expanding_mean,
    points_from_result, win_indicator, draw_indicator, loss_indicator,
    current_win_streak, current_unbeaten_streak,
)

WINDOWS = [3, 5, 10, 38]


# ---------------------------------------------------------------------------
# Step 1: flatten matches into a per-team, chronological "team-match" table
# ---------------------------------------------------------------------------

def build_team_match_long(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the wide matches table (one row per match) into a long table with
    one row per (team, match), from the perspective of that team.
    Columns are named from the team's perspective: gf/ga, shots_f/a, etc.
    """
    matches = matches.copy()
    matches["match_date"] = pd.to_datetime(matches["match_date"])

    home = pd.DataFrame({
        "team_id":      matches["home_team_id"],
        "match_id":     matches["match_id"],
        "match_date":   matches["match_date"],
        "season":       matches["season"],
        "opponent_id":  matches["away_team_id"],
        "venue":        "home",
        "result":       matches["result"],
        "gf":           matches["home_goals"],
        "ga":           matches["away_goals"],
        "shots_f":      matches["home_shots"],
        "shots_a":      matches["away_shots"],
        "sot_f":        matches["home_shots_on_target"],
        "sot_a":        matches["away_shots_on_target"],
        "fouls_f":      matches["home_fouls"],
        "fouls_a":      matches["away_fouls"],
        "corners_f":    matches["home_corners"],
        "corners_a":    matches["away_corners"],
        "yellows_f":    matches["home_yellows"],
        "yellows_a":    matches["away_yellows"],
        "reds_f":       matches["home_reds"],
        "reds_a":       matches["away_reds"],
    })

    away = pd.DataFrame({
        "team_id":      matches["away_team_id"],
        "match_id":     matches["match_id"],
        "match_date":   matches["match_date"],
        "season":       matches["season"],
        "opponent_id":  matches["home_team_id"],
        "venue":        "away",
        "result":       matches["result"],
        "gf":           matches["away_goals"],
        "ga":           matches["home_goals"],
        "shots_f":      matches["away_shots"],
        "shots_a":      matches["home_shots"],
        "sot_f":        matches["away_shots_on_target"],
        "sot_a":        matches["home_shots_on_target"],
        "fouls_f":      matches["away_fouls"],
        "fouls_a":      matches["home_fouls"],
        "corners_f":    matches["away_corners"],
        "corners_a":    matches["home_corners"],
        "yellows_f":    matches["away_yellows"],
        "yellows_a":    matches["home_yellows"],
        "reds_f":       matches["away_reds"],
        "reds_a":       matches["home_reds"],
    })

    long = pd.concat([home, away], ignore_index=True)

    # Derived per-match columns used as the raw inputs to rolling functions
    long["points"]         = long.apply(
        lambda r: 3 if (r["result"] == "H" and r["venue"] == "home")
                    or (r["result"] == "A" and r["venue"] == "away")
                  else (1 if r["result"] == "D" else 0), axis=1
    ).astype(float)
    long["win"]            = (long["points"] == 3).astype(float)
    long["draw"]           = (long["points"] == 1).astype(float)
    long["loss"]           = (long["points"] == 0).astype(float)
    long["clean_sheet"]    = (long["ga"] == 0).astype(float)
    long["failed_to_score"]= (long["gf"] == 0).astype(float)
    long["goal_diff"]      = (long["gf"] - long["ga"]).astype(float)

    # Sort chronologically within each team
    long = long.sort_values(["team_id", "match_date", "match_id"]).reset_index(drop=True)
    return long


# ---------------------------------------------------------------------------
# Step 2: compute rolling features for a single team's sorted match history
# ---------------------------------------------------------------------------

RAW_COLS = [
    "points", "win", "draw", "loss",
    "gf", "ga", "goal_diff", "clean_sheet", "failed_to_score",
    "shots_f", "shots_a", "sot_f", "sot_a",
    "fouls_f", "corners_f", "yellows_f", "reds_f",
]

def _roll_window(grp: pd.DataFrame, w: int, suffix: str) -> pd.DataFrame:
    """
    For each RAW_COL, compute rolling mean over the previous `w` matches
    (min_periods=1 so early rows are populated). Returns a DataFrame of
    feature columns indexed the same as `grp`.
    min_periods=1 means the first match always has a prior-data window of 0;
    the mean is then NaN for that single first match only when w > 1 and we
    use strict min_periods. We use min1 so that the first match gets a value
    derived from whatever little history exists — this is correct because even
    for the team's very first match there is no prior data, so NaN is
    unavoidable and expected.
    """
    feats = {}
    for col in RAW_COLS:
        if col not in grp.columns:
            continue
        rolled = rolling_mean_min1(grp[col], w)
        feats[f"{col}_{suffix}"] = rolled.values

    # Shot-derived rates (computed after rolling)
    sh_f = feats.get(f"shots_f_{suffix}", np.full(len(grp), np.nan))
    sot_f = feats.get(f"sot_f_{suffix}", np.full(len(grp), np.nan))
    gf    = feats.get(f"gf_{suffix}", np.full(len(grp), np.nan))
    feats[f"shot_accuracy_{suffix}"] = safe_div(sot_f, sh_f)
    feats[f"shot_conversion_{suffix}"] = safe_div(gf, sh_f)

    return pd.DataFrame(feats, index=grp.index)


def compute_rolling_features(long: pd.DataFrame) -> pd.DataFrame:
    """
    Applies rolling windows per team and assembles the full feature table.
    """
    all_frames = []

    for team_id, grp in long.groupby("team_id", sort=False):
        grp = grp.sort_values(["match_date", "match_id"]).copy()

        # -- Multi-window rolling features --
        window_frames = []
        for w in WINDOWS:
            suffix = f"last{w}" if w < 38 else "season"
            wf = _roll_window(grp, w, suffix)
            window_frames.append(wf)

        rolled = pd.concat(window_frames, axis=1)

        # -- Expanding (all-prior) features --
        for col in ["points", "gf", "ga", "clean_sheet", "win"]:
            if col in grp.columns:
                rolled[f"{col}_expand"] = expanding_mean(grp[col]).values

        # -- Streak features --
        grp_reset = grp.reset_index(drop=True)
        win_streak    = []
        unbeat_streak = []
        w_count = 0
        ub_count = 0
        for _, row in grp_reset.iterrows():
            win_streak.append(w_count)
            unbeat_streak.append(ub_count)
            if row["win"] == 1:
                w_count += 1
                ub_count += 1
            elif row["draw"] == 1:
                w_count = 0
                ub_count += 1
            else:
                w_count = 0
                ub_count = 0

        rolled["win_streak"]      = win_streak
        rolled["unbeaten_streak"] = unbeat_streak

        # -- Venue-split form (home/away win rate over last5, last10) --
        for venue_val, v_sfx in [("home", "h"), ("away", "a")]:
            mask = (grp["venue"] == venue_val)
            venue_grp = grp[mask].copy()
            venue_idx = venue_grp.index
            for w in [5, 10]:
                col_name = f"win_rate_{v_sfx}_last{w}"
                if len(venue_grp) >= 1:
                    rolled_v = rolling_mean_min1(venue_grp["win"], w)
                    rolled.loc[venue_idx, col_name] = rolled_v.values
                else:
                    rolled[col_name] = np.nan

        # Add keys back
        rolled.index = grp.index
        rolled["team_id"]    = grp["team_id"].values
        rolled["match_id"]   = grp["match_id"].values
        rolled["match_date"] = grp["match_date"].values
        rolled["season"]     = grp["season"].values
        rolled["venue"]      = grp["venue"].values
        rolled["opponent_id"]= grp["opponent_id"].values

        all_frames.append(rolled)

    result = pd.concat(all_frames, ignore_index=True)

    # Reorder: keys first
    key_cols = ["team_id", "match_id", "match_date", "season", "venue", "opponent_id"]
    feat_cols = [c for c in result.columns if c not in key_cols]
    result = result[key_cols + feat_cols]
    result = result.sort_values(["match_date", "match_id", "team_id"]).reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# Step 3: season-level team features from team_season_stats.csv
# ---------------------------------------------------------------------------

def build_season_features(tstats: pd.DataFrame) -> pd.DataFrame:
    """
    Derives normalised and ratio features from the pre-aggregated
    team_season_stats table. These are valid as *prior-season* features only.
    """
    df = tstats.copy()

    # Additional ratios not in the source
    df["sot_accuracy"]        = safe_div(df["sot_for"],    df["shots_for"])
    df["sot_conceded_rate"]   = safe_div(df["sot_against"],df["shots_against"])
    df["shot_conversion"]     = safe_div(df["goals_for"],  df["shots_for"])
    df["clean_sheet_rate"]    = safe_div(df["clean_sheets"],df["mp"])
    df["failed_to_score_rate"]= safe_div(df["failed_to_score"], df["mp"])
    df["corners_pg"]          = safe_div(df["corners_for"], df["mp"])
    df["fouls_pg"]            = safe_div(df["fouls_for"],   df["mp"])
    df["yellows_pg"]          = safe_div(df["yellows_for"], df["mp"])
    df["reds_pg"]             = safe_div(df["reds_for"],    df["mp"])
    df["shots_pg"]            = safe_div(df["shots_for"],   df["mp"])
    df["shots_conceded_pg"]   = safe_div(df["shots_against"],df["mp"])
    df["sot_pg"]              = safe_div(df["sot_for"],     df["mp"])
    df["sot_conceded_pg"]     = safe_div(df["sot_against"], df["mp"])
    df["home_win_rate"]       = safe_div(df["home_wins"],   df["home_mp"])
    df["away_win_rate"]       = safe_div(df["away_wins"],   df["away_mp"])
    df["home_ppg"]            = safe_div(
        3*df["home_wins"] + df["home_draws"], df["home_mp"])
    df["away_ppg"]            = safe_div(
        3*df["away_wins"] + df["away_draws"], df["away_mp"])
    df["home_goal_diff_pg"]   = safe_div(
        df["home_goals_for"] - df["home_goals_against"], df["home_mp"])
    df["away_goal_diff_pg"]   = safe_div(
        df["away_goals_for"] - df["away_goals_against"], df["away_mp"])

    # valid_from_season: these stats are features only for the NEXT season
    def _next(s):
        start = int(s[:4])
        return f"{start+1}/{str(start+2)[2:]}"

    df["valid_from_season"] = df["season"].map(_next)

    keep = [
        "team_id", "team_name", "season", "valid_from_season",
        "mp", "wins", "draws", "losses", "points",
        "goals_for", "goals_against", "goal_difference",
        "clean_sheets", "failed_to_score",
        "home_mp", "home_wins", "home_draws", "home_losses",
        "home_goals_for", "home_goals_against",
        "away_mp", "away_wins", "away_draws", "away_losses",
        "away_goals_for", "away_goals_against",
        "shots_for", "shots_against", "sot_for", "sot_against",
        "fouls_for", "fouls_against", "corners_for", "corners_against",
        "yellows_for", "yellows_against", "reds_for", "reds_against",
        # derived
        "ppg", "win_rate", "draw_rate", "loss_rate",
        "avg_goals_for", "avg_goals_against", "avg_goal_difference",
        "sot_accuracy", "sot_conceded_rate", "shot_conversion",
        "clean_sheet_rate", "failed_to_score_rate",
        "corners_pg", "fouls_pg", "yellows_pg", "reds_pg",
        "shots_pg", "shots_conceded_pg", "sot_pg", "sot_conceded_pg",
        "home_win_rate", "away_win_rate",
        "home_ppg", "away_ppg",
        "home_goal_diff_pg", "away_goal_diff_pg",
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].sort_values(["season", "team_id"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build():
    print("=" * 65)
    print("BUILDING TEAM FEATURES")
    print("=" * 65)

    matches = read_master("matches_master.csv")
    tstats  = read_master("team_season_stats.csv")

    # --- Rolling features ---
    print("\n[1] Building per-team rolling features from matches_master...")
    long = build_team_match_long(matches)
    print(f"  Team-match rows (long format): {len(long)}")
    rolling = compute_rolling_features(long)
    save_features(rolling, "team_rolling_features.csv")
    feat_cols = [c for c in rolling.columns
                 if c not in ["team_id","match_id","match_date","season","venue","opponent_id"]]
    print(f"  Rolling feature columns       : {len(feat_cols)}")

    # Leakage check: verify no feature sees future data
    # The first match for each team should have NaN for window=3/5/10
    first_match = rolling.groupby("team_id").first().reset_index()
    nan_check = first_match["points_last3"].isna().all()
    print(f"  Leakage check (first match last3 is NaN): {nan_check}")

    # --- Season features ---
    print("\n[2] Building season-level team features from team_season_stats...")
    season_feats = build_season_features(tstats)
    save_features(season_feats, "team_season_features.csv")
    print(f"  Seasons x teams : {len(season_feats)}")
    print(f"  Feature columns : {len(season_feats.columns) - 4} (excl. keys + valid_from)")

    return rolling, season_feats


if __name__ == "__main__":
    build()
