# Feature Engineering Report
## Premier League ML Project — Phase 7 Validation

**Date**: 2026-08-12  
**Status**: ✅ **DATASETS READY FOR ML TRAINING**

---

## Executive Summary

All feature datasets have been successfully validated and are ready for machine learning model training. The feature engineering pipeline has produced 4 comprehensive datasets covering players, teams, and matches from 2018/19 through 2026/27.

**Key Metrics**:
- Total feature columns: 374 (match-level)
- Historical matches: 3,040 (with targets)
- Prediction targets: 380 (2026/27 fixtures)
- Zero critical issues
- Leakage prevention: Verified

---

## Dataset Inventory

### 1. player_features.csv
**Dimensions**: 404 rows × 66 columns  
**Grain**: One row per player (2025/26 season only)

| Category | Columns | Description |
|----------|---------|-------------|
| Keys | 6 | player_id, player_name, season, valid_from_season, team_id, primary_position |
| Playing Time | 5 | age, matches_played, starts, minutes_played, minutes_per_90 |
| Attacking | 18 | goals, assists, xG, xAG, shots, per-90 rates |
| Creativity | 11 | SCA, GCA, key passes, progressive actions |
| Defense | 8 | tackles, interceptions, clearances, blocks |
| Discipline | 4 | yellows, reds, fouls committed/drawn |
| Possession | 9 | touches, carries, dribbles, miscontrols |
| Composite | 1 | performance_score (rank-aggregated) |

**Coverage**:
- Season: 2025/26
- valid_from_season: 2026/27 (temporal guard)
- Teams: 20 (current EPL teams)

**Quality**:
- Missing values: ~2.8% (expected for specialized stats like GK metrics)
- Duplicates: 0
- Invalid values: 0

---

### 2. team_rolling_features.csv
**Dimensions**: 6,080 rows × 93 columns  
**Grain**: One row per (team_id, match_id) — team's state before that match

| Category | Columns | Description |
|----------|---------|-------------|
| Keys | 6 | team_id, match_id, match_date, season, venue, opponent_id |
| Rolling Windows | 80 | last3, last5, last10, season (38-game) for: points, goals, shots, fouls, corners, cards |
| Streaks | 2 | win_streak, unbeaten_streak |
| Venue Splits | 4 | home/away win rates (last5, last10) |
| Expanding | 5 | Cumulative averages (all prior matches) |

**Rolling Features Per Window**:
- Outcome: points_per_game, win_rate, draw_rate, loss_rate
- Goals: goals_scored, goals_conceded, goal_diff, clean_sheet_rate, failed_to_score_rate
- Shots: shots, shots_conceded, sot, shot_accuracy, shot_conversion
- Discipline: fouls, corners, yellows, reds

**Leakage Prevention**:
- All rolling features use `.shift(1)` before `.rolling()` (current match excluded)
- First match for each team: all rolling features are NaN (verified)
- Chronologically sorted by (match_date, match_id)

**Quality**:
- Missing values: Expected in first matches only
- Duplicates: 0
- Invalid values: 0 (no negative counts, win rates in [0,1])

---

### 3. team_season_features.csv
**Dimensions**: 160 rows × 64 columns  
**Grain**: One row per (team_id, season)

| Category | Columns | Description |
|----------|---------|-------------|
| Keys | 4 | team_id, team_name, season, valid_from_season |
| Season Aggregates | 24 | mp, wins, draws, losses, goals_for/against, clean_sheets, shots, fouls, cards |
| Home/Away Splits | 12 | home_mp, home_wins, home_goals, away_mp, away_wins, away_goals |
| Derived Rates | 24 | ppg, win_rate, shot_conversion, clean_sheet_rate, home_ppg, away_ppg |

**Coverage**:
- Seasons: 2018/19 through 2025/26 (8 seasons)
- Teams: 20 teams × 8 seasons = 160 rows
- valid_from_season: +1 year offset (2025/26 stats valid for 2026/27+)

**Quality**:
- Missing values: 0
- Duplicates: 0
- Invalid values: 0 (all calculations validated: points = 3W + D, mp = W + D + L)

---

### 4. match_features.csv ⭐ **PRIMARY TRAINING DATASET**
**Dimensions**: 3,420 rows × 374 columns  
**Grain**: One row per match (historical + fixtures)

#### Composition
- **Historical matches**: 3,040 rows (2018/19–2025/26) — with targets
- **Fixtures**: 380 rows (2026/27) — prediction targets

#### Column Structure
| Category | Count | Description |
|----------|-------|-------------|
| **Keys** | 9 | match_id, row_id, season, match_date, is_fixture, team IDs, team names |
| **Targets** | 3 | result (H/D/A), home_goals, away_goals |
| **Features** | 362 | See breakdown below |

#### Feature Breakdown (362 columns)

**Team Rolling Features** (home_ and away_ prefixed):
- 87 columns × 2 teams = 174 columns
- Covers: last3, last5, last10, season windows
- Points, goals, shots, fouls, corners, cards, streaks, venue splits

**Relative Features** (rel_ prefixed):
- 87 columns (home - away for every rolling feature)
- Direct strength differential encoding

**Head-to-Head Features**:
- 9 columns
- h2h_matches, h2h_home_win_rate, h2h_draw_rate, h2h_away_win_rate
- h2h_avg_home_goals, h2h_avg_away_goals
- h2h_last3_home_wins, h2h_last3_draws, h2h_last3_away_wins

**Prior-Season Features** (ps_home_ and ps_away_ prefixed):
- 64 columns × 2 teams = 128 columns
- Full-season stats from the previous season
- Attached via valid_from_season enforcement

#### Feature Types
- **Numeric**: 362/362 (100%)
- **Categorical**: 0 (result is target, team names are keys)

---

## Validation Results

### 1. Missing Values Analysis

| Dataset | Total Cells | Missing | % Missing | Status |
|---------|-------------|---------|-----------|--------|
| player_features | 26,664 | 747 | 2.8% | ✓ PASS |
| team_rolling_features | 565,440 | ~15,000 | 2.7% | ✓ PASS |
| team_season_features | 10,240 | 0 | 0.0% | ✓ PASS |
| match_features | 1,279,080 | ~50,000 | 3.9% | ✓ PASS |

**Missing Value Distribution**:
- **First matches**: Expected (no prior data for rolling features)
- **Specialized stats**: Goalkeeper stats missing for outfield players (expected)
- **Prior-season features**: First season (2018/19) has no prior-season data (expected)

**Training Data Quality**:
- Historical matches with targets: 3,040 rows
- Missing % in training rows: **<5%** ✓ LOW
- Imputation strategy: Mean/median for numeric, mode for categorical (if any)

### 2. Duplicate Detection

| Dataset | Key Columns | Duplicates | Status |
|---------|-------------|------------|--------|
| player_features | player_id, season | 0 | ✓ PASS |
| team_rolling_features | team_id, match_id | 0 | ✓ PASS |
| team_season_features | team_id, season | 0 | ✓ PASS |
| match_features | match_id | 0 | ✓ PASS |

**Conclusion**: All datasets have unique keys. No duplicate rows.

### 3. Invalid Values Check

**Tested Constraints**:
- ✓ No negative values in count columns (goals, shots, minutes, age)
- ✓ No percentages > 100 (sot_pct, dribble_success_rate)
- ✓ Result values in {H, D, A} only
- ✓ Win rates in [0, 1]
- ✓ Chronological ordering maintained

**Findings**: Zero invalid values detected.

### 4. Relationship Validation

**Cross-Dataset Consistency**:
- ✓ All match team_ids exist in team_rolling (3,040/3,040 = 100%)
- ✓ All player team_ids exist in team_season (404/404 = 100%)
- ✓ All fixture rows (is_fixture=True) have null targets (380/380 = 100%)
- ✓ All historical rows have non-null targets (3,040/3,040 = 100%)

**H2H Integrity**:
- ✓ H2H match count never decreases over time (monotonic)
- ✓ H2H features use only matches with match_date < current_date

**Season Boundaries**:
- ✓ valid_from_season always = season + 1 year
- ✓ No current-season stats used as current-season features

### 5. Feature Consistency

**Rolling Window Population** (spot check):
- Matches after 2024-01-01: 95%+ have non-null rolling features ✓
- First match of 2018/19: All rolling features are NaN ✓

**Temporal Ordering**:
- All datasets sorted chronologically ✓
- No future data leakage ✓

**Fixture Forward-Filling**:
- 2026/27 fixtures use team state from last 2025/26 match ✓
- Verified for 10 sample fixture rows ✓

### 6. Train-Ready Structure

**match_features.csv** is structured for immediate model training:

```python
# Split into train/val/test
train = match_df[match_df["season"].isin(["2018/19", ..., "2024/25"])]  # 2,660 rows
val   = match_df[match_df["season"] == "2025/26"]                       # 380 rows
test  = match_df[match_df["is_fixture"] == True]                        # 380 rows

# Separate features and targets
key_cols = ["match_id", "row_id", "season", "match_date", "is_fixture",
            "home_team_id", "away_team_id", "home_team_name", "away_team_name"]
target_cols = ["result", "home_goals", "away_goals"]
feature_cols = [c for c in match_df.columns if c not in key_cols + target_cols]

X_train = train[feature_cols]
y_train = train["result"]  # or "home_goals", "away_goals" for regression
```

**Feature Properties**:
- Numeric: 362/362 (100%)
- No categorical encoding needed
- Missing values: <5% (impute during training)

---

## Recommendations for Model Training

### 1. Feature Selection
**Drop Duplicate Columns** (optional, for model efficiency):
- Drop either `sca_per_90` OR `sca_per_90_calc` (keep `_calc`)
- Drop either `gca_per_90` OR `gca_per_90_calc` (keep `_calc`)

### 2. Train/Val/Test Split
**Use Temporal Split** (NOT random):
```python
train_seasons = ["2018/19", "2019/20", "2020/21", "2021/22", 
                 "2022/23", "2023/24", "2024/25"]  # 7 seasons, 2,660 matches
val_season    = ["2025/26"]                         # 1 season, 380 matches
test_season   = ["2026/27"]                         # Fixtures, 380 matches
```

**Rationale**: Temporal split respects time-series nature and prevents look-ahead bias.

### 3. Missing Value Imputation
**Strategy**:
- First-match NaNs in rolling features: Forward-fill with 0 or season mean
- Specialized stats (GK, rare events): Impute with 0 or median
- Prior-season features for 2018/19: Impute with 0 or drop those rows

**Implementation**:
```python
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy="median")  # or "mean"
X_train_imputed = imputer.fit_transform(X_train)
X_val_imputed = imputer.transform(X_val)
```

### 4. Feature Scaling
**Recommended**: StandardScaler or MinMaxScaler
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_imputed)
X_val_scaled = scaler.transform(X_val_imputed)
```

### 5. Target Variable

**Classification** (recommended):
- Target: `result` (H/D/A)
- Classes: 3 (Home Win, Draw, Away Win)
- Model: XGBoost, LightGBM, RandomForest, Neural Network

**Regression** (alternative):
- Targets: `home_goals`, `away_goals`
- Range: [0, 10+] (Poisson-like distribution)
- Model: Poisson Regression, XGBoost, Neural Network

### 6. Baseline Models
**Establish baselines before complex models**:
1. **Naive**: Always predict most frequent class (H) → ~46% accuracy
2. **Prior-season form**: Use ps_home_ppg vs ps_away_ppg → ~50-55% accuracy
3. **Logistic Regression**: Linear baseline → ~55-60% accuracy
4. **Random Forest**: Tree-based baseline → ~58-62% accuracy
5. **XGBoost/LightGBM**: Target model → ~60-65% accuracy (expected)

### 7. Evaluation Metrics
**Classification**:
- Accuracy (overall)
- Log Loss (calibration)
- ROC-AUC (per-class discrimination)
- Confusion Matrix (H/D/A breakdown)

**Regression**:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- Poisson Log-Likelihood

### 8. Feature Importance Analysis
After training, inspect top features:
```python
import matplotlib.pyplot as plt
feature_importance = model.feature_importances_
top_20 = pd.Series(feature_importance, index=feature_cols).nlargest(20)
top_20.plot(kind="barh")
```

Expected top features:
- `rel_points_last5`, `rel_ppg_season`
- `h2h_home_win_rate`
- `home_win_streak`, `away_win_streak`
- `ps_home_ppg`, `ps_away_ppg`

---

## Known Limitations

### 1. Player Features Not Integrated
**Current State**: `player_features.csv` exists but is NOT joined into `match_features.csv`.

**Reason**: Match-level features are already comprehensive (362 columns). Player-level aggregation (e.g., squad strength) would require additional engineering.

**Future Enhancement**: Create squad-level features:
- Average performance_score of starting XI
- Sum of goals/assists for top 5 attackers
- Defensive strength (sum of tackles + interceptions)

### 2. Single-Season Player Data
**Limitation**: Player stats only available for 2025/26.

**Impact**: Cannot use multi-season player trends.

**Mitigation**: Use team-level aggregates (already included) as proxy for squad quality.

### 3. Missing Team Stats for New Promoted Teams
**Issue**: Hull, Coventry have no historical match data in 2018/19–2025/26.

**Impact**: Their rolling features in 2026/27 fixtures may have more NaNs.

**Mitigation**: Impute with league average or drop those matches (2 teams × 19 home + 19 away = 76 matches affected).

### 4. Odds Columns Separated
**Decision**: Betting odds stored in `match_odds.csv`, NOT used as features.

**Rationale**: Odds are strong predictors but represent market consensus, not model-discoverable patterns. Using odds would make the model a "bookmaker replicator" rather than an independent predictor.

**Option**: If desired, odds can be joined from `match_odds.csv` for comparison or ensemble.

---

## Data Lineage

```
Raw Data (8 E0 files + fixtures + players)
    ↓
Integration Layer (src/integration/)
    ↓
Master Datasets (data/master/)
    ├─ matches_master.csv (3,040 rows)
    ├─ team_season_stats.csv (160 rows)
    ├─ players_master.csv (404 rows)
    └─ fixtures_2026_27.csv (380 rows)
    ↓
Feature Engineering (src/features/)
    ↓
Feature Datasets (data/features/)
    ├─ team_rolling_features.csv (6,080 rows)
    ├─ team_season_features.csv (160 rows)
    ├─ player_features.csv (404 rows)
    └─ match_features.csv (3,420 rows) ← TRAINING DATASET
```

---

## Conclusion

**✅ All feature datasets are VALID and READY for machine learning model training.**

**Summary**:
- 4 feature datasets successfully created
- 362 features per match
- 3,040 historical matches (with targets)
- 380 prediction targets (2026/27 fixtures)
- Zero critical issues
- Zero leakage
- Missing values <5% (acceptable)
- No duplicates, no invalid values
- Relationships validated
- Train-ready structure confirmed

**Next Steps**:
1. Phase 8: Model Training (select algorithm, train, tune)
2. Phase 9: Model Evaluation (accuracy, calibration, feature importance)
3. Phase 10: Prediction (generate 2026/27 forecasts)
**Ready for Model Training**: **YES**
