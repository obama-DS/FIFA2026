# Shared utilities for the feature engineering layer.
# No raw data is modified here; all functions are pure transformations.

import os
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER_DIR   = os.path.join(PROJECT_ROOT, "data", "master")
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_master(filename: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(MASTER_DIR, filename), encoding="utf-8-sig")


def save_features(df: pd.DataFrame, filename: str) -> str:
    os.makedirs(FEATURES_DIR, exist_ok=True)
    path = os.path.join(FEATURES_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  Saved {path}  ({len(df)} rows x {len(df.columns)} cols)")
    return path


# ---------------------------------------------------------------------------
# Arithmetic helpers
# ---------------------------------------------------------------------------

def safe_div(numerator, denominator, fill=0.0):
    """Element-wise division that returns `fill` wherever denominator is 0."""
    num = np.asarray(numerator, dtype=float)
    den = np.asarray(denominator, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(den == 0, fill, num / den)
    return result


# ---------------------------------------------------------------------------
# Rolling / expanding window helpers (strictly look-back, no leakage)
# ---------------------------------------------------------------------------

def expanding_mean(series: pd.Series) -> pd.Series:
    """
    Expanding mean up to but NOT including the current row.
    Returns NaN for the first row (no prior data).
    """
    return series.shift(1).expanding().mean()


def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    """
    Rolling mean over the previous `window` rows (shift by 1 to exclude current).
    Returns NaN where fewer than `window` prior rows exist.
    """
    return series.shift(1).rolling(window=window, min_periods=window).mean()


def rolling_mean_min1(series: pd.Series, window: int) -> pd.Series:
    """
    Same as rolling_mean but requires only 1 prior observation (fills early rows).
    Useful for short-window recent-form where cold-start NaNs are undesirable.
    """
    return series.shift(1).rolling(window=window, min_periods=1).mean()


def rolling_sum(series: pd.Series, window: int) -> pd.Series:
    """Rolling sum of previous `window` rows (shift by 1)."""
    return series.shift(1).rolling(window=window, min_periods=window).sum()


def rolling_sum_min1(series: pd.Series, window: int) -> pd.Series:
    return series.shift(1).rolling(window=window, min_periods=1).sum()


def rolling_std(series: pd.Series, window: int) -> pd.Series:
    """Rolling std-dev of previous `window` rows (shift by 1)."""
    return series.shift(1).rolling(window=window, min_periods=window).std()


# ---------------------------------------------------------------------------
# Form / streak helpers
# ---------------------------------------------------------------------------

def points_from_result(result_series: pd.Series, team_role: str) -> pd.Series:
    """
    Convert FTR column ('H','D','A') to points earned by a given team role
    ('home' or 'away').
    """
    if team_role == "home":
        return result_series.map({"H": 3, "D": 1, "A": 0}).fillna(0).astype(float)
    else:
        return result_series.map({"H": 0, "D": 1, "A": 3}).fillna(0).astype(float)


def win_indicator(result_series: pd.Series, team_role: str) -> pd.Series:
    win_val = "H" if team_role == "home" else "A"
    return result_series.eq(win_val).astype(float)


def draw_indicator(result_series: pd.Series) -> pd.Series:
    return result_series.eq("D").astype(float)


def loss_indicator(result_series: pd.Series, team_role: str) -> pd.Series:
    loss_val = "A" if team_role == "home" else "H"
    return result_series.eq(loss_val).astype(float)


def current_win_streak(result_series: pd.Series, team_role: str) -> pd.Series:
    """
    For each row, count consecutive wins immediately preceding it.
    Strictly uses only prior rows.
    """
    win_val = "H" if team_role == "home" else "A"
    wins = result_series.eq(win_val).astype(int).shift(1).fillna(0)
    streak = []
    count = 0
    for w in wins:
        streak.append(count)
        count = count + 1 if w else 0
    return pd.Series(streak, index=result_series.index)


def current_unbeaten_streak(result_series: pd.Series, team_role: str) -> pd.Series:
    """Consecutive matches without a loss (W or D), using only prior rows."""
    loss_val = "A" if team_role == "home" else "H"
    not_loss = (~result_series.eq(loss_val)).astype(int).shift(1).fillna(0)
    streak = []
    count = 0
    for nl in not_loss:
        streak.append(count)
        count = count + 1 if nl else 0
    return pd.Series(streak, index=result_series.index)
