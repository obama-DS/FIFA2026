# =============================================================================
# train_compare_models.py
# =============================================================================
# Phase 9: Model Selection and Comparison
# 
# Trains multiple models for match outcome prediction:
# 1. Linear Regression (baseline)
# 2. Random Forest Regressor
# 3. Gradient Boosting Regressor
# 4. XGBoost Regressor (if available)
#
# Target: Goals prediction (home_goals, away_goals) for regression metrics
# Alternative: Classification accuracy for result (H/D/A)
#
# Evaluation: MAE, RMSE, R² on validation set
# Output: Model comparison table + best model
# =============================================================================

import os
import sys
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Try to import XGBoost
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("WARNING: XGBoost not available, will skip")

warnings.filterwarnings('ignore')

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

print("=" * 70)
print("PHASE 9: MODEL SELECTION AND COMPARISON")
print("=" * 70)
print()

# ---------------------------------------------------------------------------
# 1. Load Data (reuse Phase 8 preprocessing)
# ---------------------------------------------------------------------------

print("[1] Loading data...")
match_df = pd.read_csv(
    os.path.join(FEATURES_DIR, "match_features.csv"),
    encoding="utf-8-sig",
    low_memory=False
)
match_df["match_date"] = pd.to_datetime(match_df["match_date"].astype(str).str.strip(), format="mixed")
print(f"  Total rows: {len(match_df)}")
print()

# ---------------------------------------------------------------------------
# 2. Define Targets and Features
# ---------------------------------------------------------------------------

print("[2] Defining regression targets...")

# PRIMARY TARGET: Average goals (continuous) for regression
# We'll predict (home_goals + away_goals) / 2 as a single target
# Alternative: Predict home_goals and away_goals separately

TARGET_HOME = "home_goals"
TARGET_AWAY = "away_goals"

# For simplicity, we'll predict home_goals and away_goals separately
# then evaluate each model on both targets

KEY_COLS = [
    "match_id", "row_id", "season", "match_date", "is_fixture",
    "home_team_id", "away_team_id", "home_team_name", "away_team_name"
]

TARGET_COLS = ["result", "home_goals", "away_goals"]

FEATURE_COLS = [c for c in match_df.columns if c not in KEY_COLS + TARGET_COLS]

# Drop duplicate columns
DUPLICATE_COLS = ["sca_per_90_calc", "gca_per_90_calc"]
FEATURE_COLS = [c for c in FEATURE_COLS if c not in DUPLICATE_COLS]

print(f"  Target (home): {TARGET_HOME}")
print(f"  Target (away): {TARGET_AWAY}")
print(f"  Features: {len(FEATURE_COLS)}")
print()

# ---------------------------------------------------------------------------
# 3. Temporal Split (same as Phase 8)
# ---------------------------------------------------------------------------

print("[3] Creating temporal train/validation split...")

train_seasons = ["2018/19", "2019/20", "2020/21", "2021/22", 
                 "2022/23", "2023/24", "2024/25"]
val_seasons = ["2025/26"]

match_df_hist = match_df[~match_df["is_fixture"]].copy()
match_df_hist = match_df_hist[
    match_df_hist[TARGET_HOME].notna() & 
    match_df_hist[TARGET_AWAY].notna()
].copy()

train_df = match_df_hist[match_df_hist["season"].isin(train_seasons)]
val_df = match_df_hist[match_df_hist["season"].isin(val_seasons)]

print(f"  Train: {len(train_df)} matches")
print(f"  Val:   {len(val_df)} matches")
print()

X_train = train_df[FEATURE_COLS].copy()
y_train_home = train_df[TARGET_HOME].copy()
y_train_away = train_df[TARGET_AWAY].copy()

X_val = val_df[FEATURE_COLS].copy()
y_val_home = val_df[TARGET_HOME].copy()
y_val_away = val_df[TARGET_AWAY].copy()

# ---------------------------------------------------------------------------
# 4. Define Models
# ---------------------------------------------------------------------------

print("[4] Defining models...")

# Preprocessing (shared)
preprocessor = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

# Model configurations
models_config = {
    "Linear_Regression": LinearRegression(),
    "Ridge": Ridge(alpha=10.0, random_state=42),
    "Random_Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1
    ),
    "Gradient_Boosting": GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42
    ),
}

if XGBOOST_AVAILABLE:
    models_config["XGBoost"] = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )

print(f"  Models to train: {len(models_config)}")
for name in models_config.keys():
    print(f"    - {name}")
print()

# ---------------------------------------------------------------------------
# 5. Train and Evaluate All Models
# ---------------------------------------------------------------------------

print("[5] Training and evaluating models...")
print()

results = []

for model_name, model in models_config.items():
    print(f"  Training {model_name}...")
    
    # Build pipeline
    pipeline = Pipeline([
        ("preprocessing", preprocessor),
        ("regressor", model)
    ])
    
    # Train on home goals
    pipeline.fit(X_train, y_train_home)
    
    # Predict
    y_train_pred_home = pipeline.predict(X_train)
    y_val_pred_home = pipeline.predict(X_val)
    
    # Train on away goals (refit)
    pipeline.fit(X_train, y_train_away)
    y_train_pred_away = pipeline.predict(X_train)
    y_val_pred_away = pipeline.predict(X_val)
    
    # Compute metrics for home goals
    train_mae_home = mean_absolute_error(y_train_home, y_train_pred_home)
    train_rmse_home = np.sqrt(mean_squared_error(y_train_home, y_train_pred_home))
    train_r2_home = r2_score(y_train_home, y_train_pred_home)
    
    val_mae_home = mean_absolute_error(y_val_home, y_val_pred_home)
    val_rmse_home = np.sqrt(mean_squared_error(y_val_home, y_val_pred_home))
    val_r2_home = r2_score(y_val_home, y_val_pred_home)
    
    # Compute metrics for away goals
    train_mae_away = mean_absolute_error(y_train_away, y_train_pred_away)
    train_rmse_away = np.sqrt(mean_squared_error(y_train_away, y_train_pred_away))
    train_r2_away = r2_score(y_train_away, y_train_pred_away)
    
    val_mae_away = mean_absolute_error(y_val_away, y_val_pred_away)
    val_rmse_away = np.sqrt(mean_squared_error(y_val_away, y_val_pred_away))
    val_r2_away = r2_score(y_val_away, y_val_pred_away)
    
    # Average metrics
    val_mae_avg = (val_mae_home + val_mae_away) / 2
    val_rmse_avg = (val_rmse_home + val_rmse_away) / 2
    val_r2_avg = (val_r2_home + val_r2_away) / 2
    
    # Check overfitting
    overfit_mae = train_mae_home - val_mae_home
    overfit_r2 = train_r2_home - val_r2_home
    
    print(f"    Val MAE (home): {val_mae_home:.4f}")
    print(f"    Val RMSE (home): {val_rmse_home:.4f}")
    print(f"    Val R² (home): {val_r2_home:.4f}")
    print(f"    Val MAE (away): {val_mae_away:.4f}")
    print(f"    Val R² (away): {val_r2_away:.4f}")
    print(f"    Overfit check (MAE): {overfit_mae:.4f} (negative = good)")
    print()
    
    results.append({
        "model": model_name,
        "train_mae_home": train_mae_home,
        "train_rmse_home": train_rmse_home,
        "train_r2_home": train_r2_home,
        "val_mae_home": val_mae_home,
        "val_rmse_home": val_rmse_home,
        "val_r2_home": val_r2_home,
        "train_mae_away": train_mae_away,
        "train_rmse_away": train_rmse_away,
        "train_r2_away": train_r2_away,
        "val_mae_away": val_mae_away,
        "val_rmse_away": val_rmse_away,
        "val_r2_away": val_r2_away,
        "val_mae_avg": val_mae_avg,
        "val_rmse_avg": val_rmse_avg,
        "val_r2_avg": val_r2_avg,
        "overfit_mae": overfit_mae,
        "overfit_r2": overfit_r2
    })

# ---------------------------------------------------------------------------
# 6. Model Comparison
# ---------------------------------------------------------------------------

print("=" * 70)
print("[6] MODEL COMPARISON")
print("=" * 70)
print()

results_df = pd.DataFrame(results)
results_df = results_df.sort_values("val_mae_avg")

print("Validation Performance (sorted by average MAE):")
print()
print(f"{'Model':<20} {'MAE (avg)':<12} {'RMSE (avg)':<12} {'R² (avg)':<10} {'Overfit':<10}")
print("-" * 70)
for _, row in results_df.iterrows():
    print(f"{row['model']:<20} {row['val_mae_avg']:<12.4f} {row['val_rmse_avg']:<12.4f} {row['val_r2_avg']:<10.4f} {row['overfit_mae']:<10.4f}")
print()

# Select best model
best_model_name = results_df.iloc[0]["model"]
best_mae = results_df.iloc[0]["val_mae_avg"]
best_r2 = results_df.iloc[0]["val_r2_avg"]

print(f"BEST MODEL: {best_model_name}")
print(f"  Validation MAE (avg): {best_mae:.4f}")
print(f"  Validation R² (avg):  {best_r2:.4f}")
print()

# ---------------------------------------------------------------------------
# 7. Retrain Best Model and Save
# ---------------------------------------------------------------------------

print("[7] Retraining best model on full training set...")

best_model_obj = models_config[best_model_name]
best_pipeline = Pipeline([
    ("preprocessing", preprocessor),
    ("regressor", best_model_obj)
])

# Train on home goals
best_pipeline.fit(X_train, y_train_home)
best_model_path = os.path.join(MODELS_DIR, "best_model_home.pkl")
joblib.dump(best_pipeline, best_model_path)
print(f"  ✓ Saved best model (home): {best_model_path}")

# Train on away goals
best_pipeline.fit(X_train, y_train_away)
best_model_path_away = os.path.join(MODELS_DIR, "best_model_away.pkl")
joblib.dump(best_pipeline, best_model_path_away)
print(f"  ✓ Saved best model (away): {best_model_path_away}")

# Also save a combined model reference
best_model_info = {
    "best_model_name": best_model_name,
    "home_model_path": "best_model_home.pkl",
    "away_model_path": "best_model_away.pkl",
    "val_mae_avg": float(best_mae),
    "val_r2_avg": float(best_r2),
    "timestamp": datetime.now().isoformat()
}

best_model_json = os.path.join(MODELS_DIR, "best_model.json")
with open(best_model_json, "w") as f:
    json.dump(best_model_info, f, indent=2)
print(f"  ✓ Saved best model info: {best_model_json}")
print()

# ---------------------------------------------------------------------------
# 8. Save Outputs
# ---------------------------------------------------------------------------

print("[8] Saving outputs...")

# Save comparison CSV
comparison_csv = os.path.join(OUTPUTS_DIR, "model_comparison.csv")
results_df.to_csv(comparison_csv, index=False)
print(f"  ✓ Saved: {comparison_csv}")

# Save detailed report
report_md = f"""# Model Selection Report
## Phase 9: Model Comparison

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Target**: Goal prediction (home_goals, away_goals)  
**Evaluation Metrics**: MAE, RMSE, R²

---

## Models Trained

{len(models_config)} models were trained and evaluated:

"""

for name in models_config.keys():
    report_md += f"- {name}\n"

report_md += f"""
---

## Validation Performance

| Model | MAE (avg) | RMSE (avg) | R² (avg) | Overfit (MAE) |
|-------|-----------|------------|----------|---------------|
"""

for _, row in results_df.iterrows():
    report_md += f"| {row['model']} | {row['val_mae_avg']:.4f} | {row['val_rmse_avg']:.4f} | {row['val_r2_avg']:.4f} | {row['overfit_mae']:.4f} |\n"

report_md += f"""
---

## Best Model

**Winner**: {best_model_name}

**Performance**:
- Validation MAE (average): {best_mae:.4f}
- Validation RMSE (average): {results_df.iloc[0]["val_rmse_avg"]:.4f}
- Validation R² (average): {best_r2:.4f}

**Home Goals Prediction**:
- MAE: {results_df[results_df['model'] == best_model_name]['val_mae_home'].values[0]:.4f}
- RMSE: {results_df[results_df['model'] == best_model_name]['val_rmse_home'].values[0]:.4f}
- R²: {results_df[results_df['model'] == best_model_name]['val_r2_home'].values[0]:.4f}

**Away Goals Prediction**:
- MAE: {results_df[results_df['model'] == best_model_name]['val_mae_away'].values[0]:.4f}
- RMSE: {results_df[results_df['model'] == best_model_name]['val_rmse_away'].values[0]:.4f}
- R²: {results_df[results_df['model'] == best_model_name]['val_r2_away'].values[0]:.4f}

---

## Overfitting Analysis

Overfitting is measured as (train_metric - val_metric):
- Negative MAE diff = good (val better than expected)
- Positive R² diff = overfitting

| Model | MAE Overfit | R² Overfit | Assessment |
|-------|-------------|------------|------------|
"""

for _, row in results_df.iterrows():
    assessment = "Good" if abs(row['overfit_mae']) < 0.2 else "Moderate" if abs(row['overfit_mae']) < 0.4 else "High"
    report_md += f"| {row['model']} | {row['overfit_mae']:.4f} | {row['overfit_r2']:.4f} | {assessment} |\n"

report_md += f"""
---

## Conclusion

The {best_model_name} model was selected based on validation performance. It achieves an average MAE of {best_mae:.4f} goals per match, meaning predictions are typically within {best_mae:.2f} goals of the actual score.

**Saved Models**:
- `models/best_model_home.pkl` (home goals predictor)
- `models/best_model_away.pkl` (away goals predictor)
- `models/best_model.json` (metadata)

**Next Steps**:
- Use best model for 2026/27 predictions
- Consider ensemble methods
- Add player features for improvement

---

"""

report_path = os.path.join(OUTPUTS_DIR, "model_selection_report.md")
with open(report_path, "w") as f:
    f.write(report_md)
print(f"  ✓ Saved: {report_path}")
print()

# ---------------------------------------------------------------------------
# 9. Summary
# ---------------------------------------------------------------------------

print("=" * 70)
print("PHASE 9 COMPLETE")
print("=" * 70)
print()
print(f"Best Model: {best_model_name}")
print(f"Validation MAE: {best_mae:.4f} goals")
print(f"Validation R²: {best_r2:.4f}")
print()
print("Outputs:")
print(f"  - models/best_model_home.pkl")
print(f"  - models/best_model_away.pkl")
print(f"  - models/best_model.json")
print(f"  - outputs/model_comparison.csv")
print(f"  - outputs/model_selection_report.md")
print()
