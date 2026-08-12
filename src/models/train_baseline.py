# =============================================================================
# train_baseline.py
# =============================================================================
# Professional ML training pipeline for Premier League match prediction.
# 
# Target: Match result classification (Home Win / Draw / Away Win)
# Model: Random Forest (baseline)
# Features: 362 match-level features from match_features.csv
# Split: Temporal (2018-2024 train, 2025/26 val)
# Output: Trained pipeline + metrics + feature importance
# =============================================================================

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, log_loss, roc_auc_score
)

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Load and Prepare Data
# ---------------------------------------------------------------------------

print("=" * 70)
print("PHASE 8: ML TRAINING PIPELINE")
print("=" * 70)
print()

print("[1] Loading match_features.csv...")
match_df = pd.read_csv(
    os.path.join(FEATURES_DIR, "match_features.csv"),
    encoding="utf-8-sig",
    low_memory=False
)
match_df["match_date"] = pd.to_datetime(match_df["match_date"])
print(f"  Total rows: {len(match_df)}")
print(f"  Columns: {len(match_df.columns)}")
print()

# ---------------------------------------------------------------------------
# 2. Define Target and Features
# ---------------------------------------------------------------------------

print("[2] Defining target and features...")

# Target: result (H/D/A)
TARGET_COL = "result"
print(f"  Target: {TARGET_COL}")

# Key columns (not features)
KEY_COLS = [
    "match_id", "row_id", "season", "match_date", "is_fixture",
    "home_team_id", "away_team_id", "home_team_name", "away_team_name"
]

# Target columns
TARGET_COLS = ["result", "home_goals", "away_goals"]

# Feature columns
FEATURE_COLS = [c for c in match_df.columns if c not in KEY_COLS + TARGET_COLS]

# Drop duplicate columns (sca_per_90_calc, gca_per_90_calc)
DUPLICATE_COLS = ["sca_per_90_calc", "gca_per_90_calc"]
FEATURE_COLS = [c for c in FEATURE_COLS if c not in DUPLICATE_COLS]

print(f"  Feature columns: {len(FEATURE_COLS)}")
print(f"  Dropped duplicates: {DUPLICATE_COLS}")
print()

# ---------------------------------------------------------------------------
# 3. Temporal Train/Val Split
# ---------------------------------------------------------------------------

print("[3] Creating temporal train/validation split...")

# Training: 2018/19 through 2024/25 (7 seasons)
train_seasons = ["2018/19", "2019/20", "2020/21", "2021/22", 
                 "2022/23", "2023/24", "2024/25"]

# Validation: 2025/26 (1 season)
val_seasons = ["2025/26"]

# Filter: only historical matches with non-null targets
match_df_hist = match_df[~match_df["is_fixture"]].copy()
match_df_hist = match_df_hist[match_df_hist[TARGET_COL].notna()].copy()

train_df = match_df_hist[match_df_hist["season"].isin(train_seasons)]
val_df = match_df_hist[match_df_hist["season"].isin(val_seasons)]

print(f"  Train: {len(train_df)} matches ({', '.join(train_seasons)})")
print(f"  Val:   {len(val_df)} matches ({', '.join(val_seasons)})")
print()

# Check class distribution
print("  Target distribution (train):")
train_dist = train_df[TARGET_COL].value_counts(normalize=True).sort_index()
for cls, pct in train_dist.items():
    count = train_df[TARGET_COL].value_counts()[cls]
    print(f"    {cls}: {count:4d} ({pct:.1%})")
print()

# Separate X and y
X_train = train_df[FEATURE_COLS].copy()
y_train = train_df[TARGET_COL].copy()
X_val = val_df[FEATURE_COLS].copy()
y_val = val_df[TARGET_COL].copy()

# Verify no leakage: val matches are all after train matches
train_max_date = train_df["match_date"].max()
val_min_date = val_df["match_date"].min()
print(f"  Leakage check:")
print(f"    Train max date: {train_max_date.date()}")
print(f"    Val min date:   {val_min_date.date()}")
print(f"    Temporal gap:   {'✓ PASS' if val_min_date > train_max_date else '✗ FAIL'}")
print()

# ---------------------------------------------------------------------------
# 4. Build Preprocessing + Model Pipeline
# ---------------------------------------------------------------------------

print("[4] Building sklearn Pipeline...")

# Preprocessing: Impute missing + Scale
preprocessor = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

# Model: Random Forest (baseline)
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=10,
    min_samples_leaf=5,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
    verbose=0
)

# Full pipeline
pipeline = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", model)
])

print(f"  Imputation: median")
print(f"  Scaling: StandardScaler")
print(f"  Model: RandomForestClassifier")
print(f"    n_estimators: 200")
print(f"    max_depth: 15")
print(f"    class_weight: balanced")
print()

# ---------------------------------------------------------------------------
# 5. Train Model
# ---------------------------------------------------------------------------

print("[5] Training model...")
print(f"  Training on {len(X_train)} samples...")

pipeline.fit(X_train, y_train)

print(f"  ✓ Training complete")
print()

# ---------------------------------------------------------------------------
# 6. Evaluate on Train and Val
# ---------------------------------------------------------------------------

print("[6] Evaluating model...")

def evaluate(X, y, name):
    """Compute comprehensive classification metrics"""
    y_pred = pipeline.predict(X)
    y_pred_proba = pipeline.predict_proba(X)
    
    acc = accuracy_score(y, y_pred)
    
    # Multi-class averaging
    prec = precision_score(y, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y, y_pred, average="weighted", zero_division=0)
    
    # Log loss and ROC-AUC (for probabilistic evaluation)
    ll = log_loss(y, y_pred_proba)
    
    # ROC-AUC: one-vs-rest for multi-class
    from sklearn.preprocessing import label_binarize
    classes = sorted(y.unique())
    y_bin = label_binarize(y, classes=classes)
    
    if len(classes) == 3:
        auc = roc_auc_score(y_bin, y_pred_proba, average="weighted", multi_class="ovr")
    else:
        auc = np.nan
    
    # Confusion matrix
    cm = confusion_matrix(y, y_pred, labels=["H", "D", "A"])
    
    # Per-class metrics
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)
    
    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "log_loss": ll,
        "roc_auc": auc,
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }

train_metrics = evaluate(X_train, y_train, "train")
val_metrics = evaluate(X_val, y_val, "val")

print(f"\n  TRAIN METRICS:")
print(f"    Accuracy:  {train_metrics['accuracy']:.4f}")
print(f"    Precision: {train_metrics['precision']:.4f}")
print(f"    Recall:    {train_metrics['recall']:.4f}")
print(f"    F1 Score:  {train_metrics['f1']:.4f}")
print(f"    Log Loss:  {train_metrics['log_loss']:.4f}")
print(f"    ROC-AUC:   {train_metrics['roc_auc']:.4f}")

print(f"\n  VALIDATION METRICS:")
print(f"    Accuracy:  {val_metrics['accuracy']:.4f}")
print(f"    Precision: {val_metrics['precision']:.4f}")
print(f"    Recall:    {val_metrics['recall']:.4f}")
print(f"    F1 Score:  {val_metrics['f1']:.4f}")
print(f"    Log Loss:  {val_metrics['log_loss']:.4f}")
print(f"    ROC-AUC:   {val_metrics['roc_auc']:.4f}")

print(f"\n  Confusion Matrix (Validation):")
print(f"           Predicted")
print(f"             H    D    A")
print(f"  Actual H {val_metrics['confusion_matrix'][0][0]:4d} {val_metrics['confusion_matrix'][0][1]:4d} {val_metrics['confusion_matrix'][0][2]:4d}")
print(f"         D {val_metrics['confusion_matrix'][1][0]:4d} {val_metrics['confusion_matrix'][1][1]:4d} {val_metrics['confusion_matrix'][1][2]:4d}")
print(f"         A {val_metrics['confusion_matrix'][2][0]:4d} {val_metrics['confusion_matrix'][2][1]:4d} {val_metrics['confusion_matrix'][2][2]:4d}")

print()

# ---------------------------------------------------------------------------
# 7. Feature Importance
# ---------------------------------------------------------------------------

print("[7] Computing feature importance...")

# Get feature importances from the trained RandomForest
rf_model = pipeline.named_steps["classifier"]
importances = rf_model.feature_importances_

# Create DataFrame
feature_importance = pd.DataFrame({
    "feature": FEATURE_COLS,
    "importance": importances
}).sort_values("importance", ascending=False)

top_20 = feature_importance.head(20)
print(f"\n  Top 20 Most Important Features:")
for i, (_, row) in enumerate(top_20.iterrows(), 1):
    print(f"    {i:2d}. {row['feature']:45s} : {row['importance']:.6f}")
print()

# ---------------------------------------------------------------------------
# 8. Save Outputs
# ---------------------------------------------------------------------------

print("[8] Saving outputs...")

# Save trained pipeline
model_filename = os.path.join(MODELS_DIR, "baseline_rf_pipeline.pkl")
joblib.dump(pipeline, model_filename)
print(f"  ✓ Saved pipeline: {model_filename}")

# Save metrics
metrics_data = {
    "model": "RandomForestClassifier",
    "target": TARGET_COL,
    "n_features": len(FEATURE_COLS),
    "train_size": len(X_train),
    "val_size": len(X_val),
    "train_seasons": train_seasons,
    "val_seasons": val_seasons,
    "hyperparameters": {
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_split": 10,
        "min_samples_leaf": 5,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "random_state": 42
    },
    "train_metrics": {
        "accuracy": float(train_metrics["accuracy"]),
        "precision": float(train_metrics["precision"]),
        "recall": float(train_metrics["recall"]),
        "f1": float(train_metrics["f1"]),
        "log_loss": float(train_metrics["log_loss"]),
        "roc_auc": float(train_metrics["roc_auc"]),
    },
    "val_metrics": {
        "accuracy": float(val_metrics["accuracy"]),
        "precision": float(val_metrics["precision"]),
        "recall": float(val_metrics["recall"]),
        "f1": float(val_metrics["f1"]),
        "log_loss": float(val_metrics["log_loss"]),
        "roc_auc": float(val_metrics["roc_auc"]),
        "confusion_matrix": val_metrics["confusion_matrix"],
    },
    "timestamp": datetime.now().isoformat()
}

metrics_filename = os.path.join(OUTPUTS_DIR, "baseline_rf_metrics.json")
with open(metrics_filename, "w") as f:
    json.dump(metrics_data, f, indent=2)
print(f"  ✓ Saved metrics: {metrics_filename}")

# Save feature importance
importance_filename = os.path.join(OUTPUTS_DIR, "baseline_rf_feature_importance.csv")
feature_importance.to_csv(importance_filename, index=False)
print(f"  ✓ Saved feature importance: {importance_filename}")

# Save predictions on validation set (for error analysis)
val_predictions = pd.DataFrame({
    "match_id": val_df["match_id"].values,
    "season": val_df["season"].values,
    "match_date": val_df["match_date"].values,
    "home_team": val_df["home_team_name"].values,
    "away_team": val_df["away_team_name"].values,
    "actual": y_val.values,
    "predicted": pipeline.predict(X_val),
    "prob_H": pipeline.predict_proba(X_val)[:, 0],
    "prob_D": pipeline.predict_proba(X_val)[:, 1],
    "prob_A": pipeline.predict_proba(X_val)[:, 2],
})
val_predictions["correct"] = (val_predictions["actual"] == val_predictions["predicted"])

predictions_filename = os.path.join(OUTPUTS_DIR, "baseline_rf_val_predictions.csv")
val_predictions.to_csv(predictions_filename, index=False)
print(f"  ✓ Saved validation predictions: {predictions_filename}")

print()

# ---------------------------------------------------------------------------
# 9. Summary
# ---------------------------------------------------------------------------

print("=" * 70)
print("TRAINING SUMMARY")
print("=" * 70)
print(f"Model:              RandomForestClassifier (baseline)")
print(f"Target:             {TARGET_COL} (H/D/A)")
print(f"Features:           {len(FEATURE_COLS)}")
print(f"Training samples:   {len(X_train)} (2018/19-2024/25)")
print(f"Validation samples: {len(X_val)} (2025/26)")
print()
print(f"Validation Accuracy:  {val_metrics['accuracy']:.2%}")
print(f"Validation F1 Score:  {val_metrics['f1']:.4f}")
print(f"Validation Log Loss:  {val_metrics['log_loss']:.4f}")
print()

# Compare to baseline (always predict most frequent class)
naive_baseline = train_df[TARGET_COL].value_counts(normalize=True).max()
print(f"Naive Baseline (always predict mode): {naive_baseline:.2%}")
print(f"Model improvement over naive:          {val_metrics['accuracy'] - naive_baseline:+.2%}")
print()

# Football-specific insights
val_pred_dist = pd.Series(pipeline.predict(X_val)).value_counts(normalize=True).sort_index()
print(f"Prediction distribution (validation):")
for cls in ["H", "D", "A"]:
    if cls in val_pred_dist.index:
        print(f"  {cls}: {val_pred_dist[cls]:.1%}")
print()

print("=" * 70)
print("✓ PHASE 8 COMPLETE")
print("=" * 70)
print()
print("Saved files:")
print(f"  models/baseline_rf_pipeline.pkl")
print(f"  outputs/baseline_rf_metrics.json")
print(f"  outputs/baseline_rf_feature_importance.csv")
print(f"  outputs/baseline_rf_val_predictions.csv")
print()
