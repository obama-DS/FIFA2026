# =============================================================================
# match_features.py
# =============================================================================
# Builds data/features/match_features.csv
#
# One row per match (3 040 historical + 380 fixtures = 3 420 rows).
# Every feature is strictly pre-match (no leakage).
#
# Assembly layers:
#   1. Base         -- match identity + target (result / goals)
#   2. Team rolling -- home/away team rolling features (from team_rolling_features.csv)
#                      For 2026/27 fixtures, the last known rolling state is forward-filled
#                      (i.e. the team's state after their last 2025/26 match).
#   3. Relative     -- home minus away for every shared rolling feature
#   4. H2H          -- head-to-head record between the two teams in prior matches
#   5. Season prior -- prior-season team stats (from team_season_features.csv)
#                      joined on the season immediately before the match season
#
# Leakage guarantees:
#   - Rolling features are computed with shift(1) in team_features.py; the row
#     attached to a match reflects the team's state BEFORE that match.
#   - H2H uses only matches with match_date < current match_date.
#   - Prior-season features use valid_from_season == current season (i.e. stats
#     from the previous season).
#   - Target columns (result, home_goals, away_goals) are included for
#     historical matches only; fixtures rows have NaN targets.
#
# Output columns (one row per match_id / fixture_id):
#   Keys       : match_id, season, match_date, home_team_id, away_team_id,
#                home_team_name, away_team_name, is_fixture
#   Target     : result, home_goals, away_goals            (NaN for fixtures)
#   Home rolling (prefixed home_)
#   Away rolling (prefixed away_)
#   Relative   (prefixed rel_)  = home_X - away_X
#   H2H        : h2h_matches, h2h_home_win_rate, h2h_draw_rate,
#                h2h_away_win_rate, h2h_avg_home_goals, h2h_avg_away_goals,
#                h2h_last3_home_wins, h2h_last3_draws, h2h_last3_away_wins
#   Prior season home team (prefixed ps_home_)
#   Prior season away team (prefixed ps_away_)
# =============================================================================

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from common import read_master, save_features, safe_div

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "features")


def _read_feature(filename: str) -> pd.DataFrame:
    path = os.path.join(FEATURES_DIR, filename)
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


# ---------------------------------------------------------------------------
# Helper: season ordering
# ---------------------------------------------------------------------------

SEASON_ORDER = {
    "2018/19": 0, "2019/20": 1, "2020/21": 2, "2021/22": 3,
    "2022/23": 4, "2023/24": 5, "2024/25": 6, "2025/26": 7, "2026/27": 8,
}

def _prev_season(season: str) -> str | None:
    start = int(season[:4])
    if start == 2018:
        return None
    return f"{start-1}/{str(start)[2:]}"


# ---------------------------------------------------------------------------
# Layer 1: build base table (historical matches + 2026/27 fixtures)
# ---------------------------------------------------------------------------

def build_base(matches: pd.DataFrame, fixtures: pd.DataFrame) -> pd.DataFrame:
    matches = matches.copy()
    fixtures = fixtures.copy()

    matches["match_date"] = pd.to_datetime(matches["match_date"])
    matches["is_fixture"] = False
    matches["row_id"]     = matches["match_id"].astype(str)

    fixtures["match_date"] = pd.to_datetime(fixtures["kickoff"])
    fixtures["is_fixture"] = True
    fixtures["match_id"]   = -fixtures["fixture_id"]          # negative IDs for fixtures
    fixtures["row_id"]     = ("f" + fixtures["fixture_id"].astype(str))
    fixtures["result"]     = np.nan
    fixtures["home_goals"] = np.nan
    fixtures["away_goals"] = np.nan

    shared = [
        "match_id", "season", "match_date", "is_fixture", "row_id",
        "home_team_id", "away_team_id", "home_team_name", "away_team_name",
        "result", "home_goals", "away_goals",
    ]

    hist_cols   = ["match_id","season","match_date","is_fixture","row_id",
                   "home_team_id","away_team_id","home_team_name","away_team_name",
                   "result","home_goals","away_goals"]
    fix_rename  = {"home_goals": "home_goals", "away_goals": "away_goals"}

    hist = matches[hist_cols].copy()
    fix  = fixtures[["match_id","season","match_date","is_fixture","row_id",
                     "home_team_id","away_team_id","home_team_name","away_team_name",
                     "result","home_goals","away_goals"]].copy()

    base = pd.concat([hist, fix], ignore_index=True)
    base = base.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    return base


# ---------------------------------------------------------------------------
# Layer 2: attach rolling features for home and away teams
# ---------------------------------------------------------------------------

def attach_rolling(base: pd.DataFrame, rolling: pd.DataFrame) -> pd.DataFrame:
    """
    For each match in base, attach the rolling-feature row for the home team
    and the away team. Rolling rows are identified by (team_id, match_id).

    For 2026/27 fixtures (is_fixture=True), there is no rolling row because
    those matches haven't been played yet. We forward-fill using the team's
    most recent (last 2025/26) rolling state.
    """
    rolling = rolling.copy()
    rolling["match_date"] = pd.to_datetime(rolling["match_date"])

    # Columns that are features (exclude keys)
    key_cols = {"team_id", "match_id", "match_date", "season", "venue", "opponent_id"}
    feat_cols = [c for c in rolling.columns if c not in key_cols]

    # --- Historical: direct join on (team_id, match_id) ---
    roll_indexed = rolling.set_index(["team_id", "match_id"])

    def _get_team_feats(team_id_series, match_id_series, prefix):
        idx = list(zip(team_id_series, match_id_series))
        rows = []
        for tid, mid in idx:
            key = (tid, mid)
            if key in roll_indexed.index:
                row = roll_indexed.loc[key, feat_cols]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
            else:
                row = pd.Series(np.nan, index=feat_cols)
            rows.append(row)
        result = pd.DataFrame(rows, columns=feat_cols)
        result.columns = [f"{prefix}{c}" for c in feat_cols]
        return result.reset_index(drop=True)

    # --- For fixtures: find each team's last rolling state ---
    # "Last state" = the rolling row with the highest match_date (most recent match played)
    last_state = (
        rolling.sort_values("match_date")
               .groupby("team_id")[feat_cols]
               .last()
    )

    def _get_fixture_feats(team_id_series, prefix):
        rows = []
        for tid in team_id_series:
            if tid in last_state.index:
                row = last_state.loc[tid]
            else:
                row = pd.Series(np.nan, index=feat_cols)
            rows.append(row)
        result = pd.DataFrame(rows, columns=feat_cols)
        result.columns = [f"{prefix}{c}" for c in feat_cols]
        return result.reset_index(drop=True)

    hist_mask = ~base["is_fixture"]
    fix_mask  = base["is_fixture"]

    print(f"  Historical rows: {hist_mask.sum()}  |  Fixture rows: {fix_mask.sum()}")

    # Home features
    home_hist = _get_team_feats(
        base.loc[hist_mask, "home_team_id"].values,
        base.loc[hist_mask, "match_id"].values,
        "home_"
    )
    home_fix = _get_fixture_feats(
        base.loc[fix_mask, "home_team_id"].values,
        "home_"
    )

    # Away features
    away_hist = _get_team_feats(
        base.loc[hist_mask, "away_team_id"].values,
        base.loc[hist_mask, "match_id"].values,
        "away_"
    )
    away_fix = _get_fixture_feats(
        base.loc[fix_mask, "away_team_id"].values,
        "away_"
    )

    # Re-assemble in original row order
    home_all = pd.concat([
        home_hist.assign(_orig_idx=base[hist_mask].index.tolist()),
        home_fix.assign(_orig_idx=base[fix_mask].index.tolist()),
    ]).sort_values("_orig_idx").drop(columns="_orig_idx").reset_index(drop=True)

    away_all = pd.concat([
        away_hist.assign(_orig_idx=base[hist_mask].index.tolist()),
        away_fix.assign(_orig_idx=base[fix_mask].index.tolist()),
    ]).sort_values("_orig_idx").drop(columns="_orig_idx").reset_index(drop=True)

    base = base.reset_index(drop=True)
    result = pd.concat([base, home_all, away_all], axis=1)
    return result, feat_cols


# ---------------------------------------------------------------------------
# Layer 3: relative (home - away) features
# ---------------------------------------------------------------------------

def add_relative_features(df: pd.DataFrame, feat_cols: list) -> pd.DataFrame:
    """
    For every feature that exists for both home and away, add a relative
    column: rel_X = home_X - away_X. This makes the model's job easier by
    directly encoding the strength differential.
    """
    added = 0
    for col in feat_cols:
        hcol = f"home_{col}"
        acol = f"away_{col}"
        if hcol in df.columns and acol in df.columns:
            df[f"rel_{col}"] = df[hcol] - df[acol]
            added += 1
    print(f"  Relative features added: {added}")
    return df


# ---------------------------------------------------------------------------
# Layer 4: head-to-head features
# ---------------------------------------------------------------------------

def add_h2h_features(df: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """
    For each match, compute H2H statistics from all PREVIOUS encounters
    between the same two teams (regardless of who was home/away historically).

    Features:
      h2h_matches         -- total prior meetings
      h2h_home_win_rate   -- rate home team won in those meetings
      h2h_draw_rate
      h2h_away_win_rate
      h2h_avg_home_goals  -- average goals for current home team in prior H2H
      h2h_avg_away_goals
      h2h_last3_home_wins -- wins for current home team in last 3 H2H matches
      h2h_last3_draws
      h2h_last3_away_wins
    """
    matches = matches.copy()
    matches["match_date"] = pd.to_datetime(matches["match_date"])

    # Build a lookup: for each (team_a, team_b) pair, sorted, list of past matches
    # We'll compute on-the-fly per row (3040+380 rows — fast enough)

    h2h_records = []

    # Index matches by sorted team pair for quick lookup
    matches["pair"] = matches.apply(
        lambda r: tuple(sorted([int(r["home_team_id"]), int(r["away_team_id"])])),
        axis=1
    )
    pair_groups = {pair: grp for pair, grp in matches.groupby("pair")}

    df = df.reset_index(drop=True)

    h2h_matches_list       = []
    h2h_home_win_rate_list = []
    h2h_draw_rate_list     = []
    h2h_away_win_rate_list = []
    h2h_avg_hg_list        = []
    h2h_avg_ag_list        = []
    h2h_l3_hw_list         = []
    h2h_l3_d_list          = []
    h2h_l3_aw_list         = []

    for _, row in df.iterrows():
        htid = int(row["home_team_id"])
        atid = int(row["away_team_id"])
        match_date = pd.to_datetime(row["match_date"])
        pair = tuple(sorted([htid, atid]))

        prior = pd.DataFrame()
        if pair in pair_groups:
            grp = pair_groups[pair]
            prior = grp[grp["match_date"] < match_date].copy()

        n = len(prior)
        if n == 0:
            h2h_matches_list.append(0)
            h2h_home_win_rate_list.append(np.nan)
            h2h_draw_rate_list.append(np.nan)
            h2h_away_win_rate_list.append(np.nan)
            h2h_avg_hg_list.append(np.nan)
            h2h_avg_ag_list.append(np.nan)
            h2h_l3_hw_list.append(np.nan)
            h2h_l3_d_list.append(np.nan)
            h2h_l3_aw_list.append(np.nan)
            continue

        # From current home team's perspective
        def _goals_for(r):
            return r["home_goals"] if r["home_team_id"] == htid else r["away_goals"]

        def _goals_against(r):
            return r["away_goals"] if r["home_team_id"] == htid else r["home_goals"]

        def _home_win(r):
            # Did current home team (htid) win?
            if r["home_team_id"] == htid:
                return 1 if r["result"] == "H" else 0
            else:
                return 1 if r["result"] == "A" else 0

        def _draw(r):
            return 1 if r["result"] == "D" else 0

        def _away_win(r):
            # Did current away team (atid) win?
            if r["home_team_id"] == atid:
                return 1 if r["result"] == "H" else 0
            else:
                return 1 if r["result"] == "A" else 0

        prior_sorted = prior.sort_values("match_date")

        hw_all  = prior_sorted.apply(_home_win, axis=1)
        d_all   = prior_sorted.apply(_draw, axis=1)
        aw_all  = prior_sorted.apply(_away_win, axis=1)
        hg_all  = prior_sorted.apply(_goals_for, axis=1)
        ag_all  = prior_sorted.apply(_goals_against, axis=1)

        h2h_matches_list.append(n)
        h2h_home_win_rate_list.append(float(hw_all.mean()))
        h2h_draw_rate_list.append(float(d_all.mean()))
        h2h_away_win_rate_list.append(float(aw_all.mean()))
        h2h_avg_hg_list.append(float(hg_all.mean()))
        h2h_avg_ag_list.append(float(ag_all.mean()))

        last3 = min(3, n)
        h2h_l3_hw_list.append(float(hw_all.iloc[-last3:].sum()))
        h2h_l3_d_list.append(float(d_all.iloc[-last3:].sum()))
        h2h_l3_aw_list.append(float(aw_all.iloc[-last3:].sum()))

    df["h2h_matches"]        = h2h_matches_list
    df["h2h_home_win_rate"]  = h2h_home_win_rate_list
    df["h2h_draw_rate"]      = h2h_draw_rate_list
    df["h2h_away_win_rate"]  = h2h_away_win_rate_list
    df["h2h_avg_home_goals"] = h2h_avg_hg_list
    df["h2h_avg_away_goals"] = h2h_avg_ag_list
    df["h2h_last3_home_wins"]= h2h_l3_hw_list
    df["h2h_last3_draws"]    = h2h_l3_d_list
    df["h2h_last3_away_wins"]= h2h_l3_aw_list

    return df


# ---------------------------------------------------------------------------
# Layer 5: prior-season team stats
# ---------------------------------------------------------------------------

def add_prior_season_features(
    df: pd.DataFrame,
    season_feats: pd.DataFrame,
) -> pd.DataFrame:
    """
    Attach prior-season aggregate features for home and away teams.
    Uses valid_from_season == current match season.
    If no prior season exists (first season in data), NaN is inserted.
    """
    # Build lookup: (team_id, valid_from_season) -> feature row
    ps = season_feats.copy()
    ps_key_cols = {"team_id", "team_name", "season", "valid_from_season"}
    ps_feat_cols = [c for c in ps.columns if c not in ps_key_cols]

    ps_indexed = ps.set_index(["team_id", "valid_from_season"])

    def _lookup(team_id, season, prefix):
        key = (team_id, season)
        if key in ps_indexed.index:
            row = ps_indexed.loc[key, ps_feat_cols]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            return {f"{prefix}{c}": v for c, v in row.items()}
        return {f"{prefix}{c}": np.nan for c in ps_feat_cols}

    ps_home_rows = []
    ps_away_rows = []
    for _, row in df.iterrows():
        ps_home_rows.append(_lookup(int(row["home_team_id"]), row["season"], "ps_home_"))
        ps_away_rows.append(_lookup(int(row["away_team_id"]), row["season"], "ps_away_"))

    ps_home_df = pd.DataFrame(ps_home_rows)
    ps_away_df = pd.DataFrame(ps_away_rows)

    df = df.reset_index(drop=True)
    df = pd.concat([df, ps_home_df, ps_away_df], axis=1)
    print(f"  Prior-season features per team: {len(ps_feat_cols)}")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build():
    print("=" * 65)
    print("BUILDING MATCH FEATURES")
    print("=" * 65)

    # Load master tables
    matches      = read_master("matches_master.csv")
    fixtures     = read_master("fixtures_2026_27.csv")

    # Load feature tables (produced by team_features.py)
    rolling      = _read_feature("team_rolling_features.csv")
    season_feats = _read_feature("team_season_features.csv")

    # --- Layer 1: base ---
    print("\n[1] Building base table...")
    base = build_base(matches, fixtures)
    print(f"  Total rows (hist + fixtures): {len(base)}")

    # --- Layer 2: rolling features ---
    print("\n[2] Attaching team rolling features...")
    df, feat_cols = attach_rolling(base, rolling)

    # --- Layer 3: relative features ---
    print("\n[3] Computing relative (home - away) features...")
    df = add_relative_features(df, feat_cols)

    # --- Layer 4: H2H ---
    print("\n[4] Computing head-to-head features...")
    matches_for_h2h = matches[
        ["match_id", "match_date", "season",
         "home_team_id", "away_team_id",
         "home_goals", "away_goals", "result"]
    ].copy()
    df = add_h2h_features(df, matches_for_h2h)
    print(f"  H2H columns: 9")

    # --- Layer 5: prior-season team stats ---
    print("\n[5] Attaching prior-season team features...")
    df = add_prior_season_features(df, season_feats)

    # --- Final column ordering ---
    key_cols = [
        "match_id", "row_id", "season", "match_date", "is_fixture",
        "home_team_id", "away_team_id", "home_team_name", "away_team_name",
    ]
    target_cols = ["result", "home_goals", "away_goals"]
    other_cols  = [c for c in df.columns if c not in key_cols + target_cols]
    df = df[key_cols + target_cols + other_cols]

    # Sort: historical matches first by date, then fixtures
    df = df.sort_values(["is_fixture", "match_date", "match_id"]).reset_index(drop=True)

    save_features(df, "match_features.csv")

    # Summary
    hist_rows = df[~df["is_fixture"]]
    fix_rows  = df[df["is_fixture"]]
    total_feats = len(df.columns) - len(key_cols) - len(target_cols)
    print(f"\n  Historical match rows : {len(hist_rows)}")
    print(f"  Fixture rows          : {len(fix_rows)}")
    print(f"  Total feature columns : {total_feats}")

    # Leakage spot-check: first match of 2018/19 should have NaN for rolling features
    first = df[df["season"] == "2018/19"].iloc[0]
    check_col = "home_points_last3"
    if check_col in df.columns:
        val = first[check_col]
        print(f"  Leakage check — first 2018/19 match, {check_col}: {val}  (expected NaN)")

    # Target integrity: no target leakage into fixture rows
    fix_result_null = df.loc[df["is_fixture"], "result"].isna().all()
    print(f"  Target null for all fixtures: {fix_result_null}")

    return df


if __name__ == "__main__":
    build()
