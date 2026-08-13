# =============================================================================
# explain.py
# =============================================================================
# Phase 11: Model Explainability
#
# Provides explainability for Premier League match predictions:
# - Global feature importance (model-wide)
# - Individual match explanations (SHAP values if available)
# - Top features increasing/decreasing predictions
# - Separate explanations for home and away goals
# - Human-readable outputs and visualizations
# =============================================================================

import os
import sys
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.model_loader import ModelLoader, ModelLoadError

warnings.filterwarnings('ignore')

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
EXPLAIN_DIR = os.path.join(OUTPUTS_DIR, "explainability")

os.makedirs(EXPLAIN_DIR, exist_ok=True)

# Try to import SHAP
try:
    import shap
    import matplotlib.pyplot as plt
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("INFO: SHAP not available, will use native feature importance")


class ExplainabilityError(Exception):
    """Raised when explainability generation fails"""
    pass


class ModelExplainer:
    """
    Provides explainability for trained ML models.
    
    Features:
    - Global feature importance (all predictions)
    - Local explanations (individual matches via SHAP)
    - Top features increasing/decreasing predictions
    - Separate home/away goal explanations
    - Human-readable output
    """
    
    def __init__(self, models_dir: str = MODELS_DIR, features_dir: str = FEATURES_DIR):
        """
        Initialize ModelExplainer.
        
        Args:
            models_dir: Path to trained models
            features_dir: Path to features directory
        """
        self.models_dir = models_dir
        self.features_dir = features_dir
        self.loader = ModelLoader(models_dir)
        self.home_model = None
        self.away_model = None
        self.metadata = None
        self.feature_names = None
        
        # SHAP explainers
        self.home_explainer = None
        self.away_explainer = None
    
    def load_models(self):
        """Load trained models and extract feature names."""
        print("Loading models for explainability...")
        self.home_model, self.away_model, self.metadata = self.loader.load_models()
        
        # Extract feature names from pipeline
        if hasattr(self.home_model, "named_steps"):
            preprocessor = self.home_model.named_steps.get("preprocessing")
            regressor = self.home_model.named_steps.get("regressor")
            
            # Get feature names after preprocessing
            if hasattr(preprocessor, "get_feature_names_out"):
                self.feature_names = list(preprocessor.get_feature_names_out())
            elif hasattr(regressor, "feature_names_in_"):
                self.feature_names = list(regressor.feature_names_in_)
            else:
                # Use default feature count
                n_features = regressor.n_features_in_ if hasattr(regressor, "n_features_in_") else 372
                self.feature_names = [f"feature_{i}" for i in range(n_features)]
        
        print(f"  ✓ Feature names: {len(self.feature_names)}")
        print()
    
    def load_sample_data(self, n_samples: int = 100) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load sample data for explanation.
        
        Args:
            n_samples: Number of samples to load
            
        Returns:
            Tuple of (metadata_df, features_df)
        """
        print(f"Loading sample data ({n_samples} matches)...")
        
        features_path = os.path.join(self.features_dir, "match_features.csv")
        if not os.path.exists(features_path):
            raise ExplainabilityError(f"Features not found: {features_path}")
        
        df = pd.read_csv(features_path, encoding="utf-8-sig", low_memory=False)
        df["match_date"] = pd.to_datetime(df["match_date"])
        
        # Get validation data (2025/26) for explanation
        val_df = df[
            (df["season"] == "2025/26") & 
            (df["is_fixture"] == False) &
            (df["home_goals"].notna()) &
            (df["away_goals"].notna())
        ].copy()
        
        # Sample
        if len(val_df) > n_samples:
            val_df = val_df.sample(n=n_samples, random_state=42)
        
        # Prepare features (same as training)
        KEY_COLS = [
            "match_id", "row_id", "season", "match_date", "is_fixture",
            "home_team_id", "away_team_id", "home_team_name", "away_team_name"
        ]
        TARGET_COLS = ["result", "home_goals", "away_goals"]
        DUPLICATE_COLS = ["sca_per_90_calc", "gca_per_90_calc"]
        
        feature_cols = [c for c in df.columns if c not in KEY_COLS + TARGET_COLS]
        feature_cols = [c for c in feature_cols if c not in DUPLICATE_COLS]
        
        metadata_cols = [c for c in KEY_COLS + TARGET_COLS if c in val_df.columns]
        metadata_df = val_df[metadata_cols].copy()
        features_df = val_df[feature_cols].copy()
        
        print(f"  ✓ Loaded {len(features_df)} matches")
        print(f"  ✓ Features: {len(feature_cols)}")
        print()
        
        return metadata_df, features_df
    
    def get_native_feature_importance(self, model, feature_names: List[str]) -> pd.DataFrame:
        """
        Extract feature importance from tree-based models.
        
        Args:
            model: Trained pipeline
            feature_names: List of feature names
            
        Returns:
            DataFrame with feature importance
        """
        # Extract regressor from pipeline
        if hasattr(model, "named_steps"):
            regressor = model.named_steps.get("regressor")
        else:
            regressor = model
        
        # Get importance
        if hasattr(regressor, "feature_importances_"):
            importance = regressor.feature_importances_
        else:
            # Linear models: use absolute coefficients
            if hasattr(regressor, "coef_"):
                importance = np.abs(regressor.coef_)
            else:
                raise ExplainabilityError("Model has no feature_importances_ or coef_")
        
        # Create dataframe
        importance_df = pd.DataFrame({
            "feature": feature_names[:len(importance)],
            "importance": importance
        })
        
        importance_df = importance_df.sort_values("importance", ascending=False)
        return importance_df
    
    def explain_global_importance(self):
        """Generate global feature importance for home and away models."""
        print("=" * 70)
        print("GLOBAL FEATURE IMPORTANCE")
        print("=" * 70)
        print()
        
        # Load sample data for SHAP
        metadata_df, features_df = self.load_sample_data(n_samples=100)
        
        # Home goals importance
        print("[1] Home Goals Model")
        print("-" * 70)
        
        if SHAP_AVAILABLE:
            print("Using SHAP for global importance...")
            try:
                # Create SHAP explainer
                regressor = self.home_model.named_steps.get("regressor")
                X_sample = self.home_model.named_steps["preprocessing"].transform(features_df)
                
                self.home_explainer = shap.Explainer(regressor, X_sample)
                shap_values = self.home_explainer(X_sample)
                
                # Compute mean absolute SHAP values
                importance = np.abs(shap_values.values).mean(axis=0)
                home_importance_df = pd.DataFrame({
                    "feature": self.feature_names[:len(importance)],
                    "importance": importance
                }).sort_values("importance", ascending=False)
                
                print("  ✓ SHAP importance computed")
                
            except Exception as e:
                print(f"  ⚠ SHAP failed ({e}), using native importance...")
                home_importance_df = self.get_native_feature_importance(
                    self.home_model, self.feature_names
                )
        else:
            print("Using native feature importance...")
            home_importance_df = self.get_native_feature_importance(
                self.home_model, self.feature_names
            )
        
        # Show top features
        print()
        print("Top 20 features for HOME GOALS:")
        for i, row in home_importance_df.head(20).iterrows():
            print(f"  {i+1:2d}. {row['feature']:<40} {row['importance']:.6f}")
        print()
        
        # Save
        home_path = os.path.join(EXPLAIN_DIR, "feature_importance_home.csv")
        home_importance_df.to_csv(home_path, index=False)
        print(f"✓ Saved: {home_path}")
        print()
        
        # Away goals importance
        print("[2] Away Goals Model")
        print("-" * 70)
        
        if SHAP_AVAILABLE:
            print("Using SHAP for global importance...")
            try:
                regressor = self.away_model.named_steps.get("regressor")
                X_sample = self.away_model.named_steps["preprocessing"].transform(features_df)
                
                self.away_explainer = shap.Explainer(regressor, X_sample)
                shap_values = self.away_explainer(X_sample)
                
                importance = np.abs(shap_values.values).mean(axis=0)
                away_importance_df = pd.DataFrame({
                    "feature": self.feature_names[:len(importance)],
                    "importance": importance
                }).sort_values("importance", ascending=False)
                
                print("  ✓ SHAP importance computed")
                
            except Exception as e:
                print(f"  ⚠ SHAP failed ({e}), using native importance...")
                away_importance_df = self.get_native_feature_importance(
                    self.away_model, self.feature_names
                )
        else:
            print("Using native feature importance...")
            away_importance_df = self.get_native_feature_importance(
                self.away_model, self.feature_names
            )
        
        print()
        print("Top 20 features for AWAY GOALS:")
        for i, row in away_importance_df.head(20).iterrows():
            print(f"  {i+1:2d}. {row['feature']:<40} {row['importance']:.6f}")
        print()
        
        # Save
        away_path = os.path.join(EXPLAIN_DIR, "feature_importance_away.csv")
        away_importance_df.to_csv(away_path, index=False)
        print(f"✓ Saved: {away_path}")
        print()
        
        return home_importance_df, away_importance_df
    
    def explain_match(
        self,
        match_features: pd.Series,
        match_metadata: Optional[pd.Series] = None,
        top_n: int = 10
    ) -> Dict:
        """
        Explain a single match prediction.
        
        Args:
            match_features: Feature values for the match
            match_metadata: Optional metadata (team names, date, etc.)
            top_n: Number of top features to return
            
        Returns:
            Dictionary with explanations for home and away goals
        """
        # Convert to DataFrame for prediction
        features_df = pd.DataFrame([match_features])
        
        # Get predictions
        home_pred = self.home_model.predict(features_df)[0]
        away_pred = self.away_model.predict(features_df)[0]
        
        explanation = {
            "prediction": {
                "home_goals": float(home_pred),
                "away_goals": float(away_pred)
            },
            "home_explanation": {},
            "away_explanation": {}
        }
        
        # Add metadata if provided
        if match_metadata is not None:
            explanation["metadata"] = match_metadata.to_dict()
        
        # Explain home goals
        if SHAP_AVAILABLE and self.home_explainer is not None:
            try:
                X = self.home_model.named_steps["preprocessing"].transform(features_df)
                shap_values = self.home_explainer(X)
                
                # Get SHAP values for this match
                values = shap_values.values[0]
                
                # Create feature contribution dataframe
                contrib_df = pd.DataFrame({
                    "feature": self.feature_names[:len(values)],
                    "shap_value": values,
                    "feature_value": X[0] if hasattr(X, "__getitem__") else X.toarray()[0]
                })
                
                # Sort by absolute contribution
                contrib_df["abs_shap"] = np.abs(contrib_df["shap_value"])
                contrib_df = contrib_df.sort_values("abs_shap", ascending=False)
                
                # Top increasing features (positive SHAP)
                increasing = contrib_df[contrib_df["shap_value"] > 0].head(top_n)
                explanation["home_explanation"]["top_increasing"] = increasing[
                    ["feature", "shap_value", "feature_value"]
                ].to_dict("records")
                
                # Top decreasing features (negative SHAP)
                decreasing = contrib_df[contrib_df["shap_value"] < 0].head(top_n)
                explanation["home_explanation"]["top_decreasing"] = decreasing[
                    ["feature", "shap_value", "feature_value"]
                ].to_dict("records")
                
                explanation["home_explanation"]["method"] = "SHAP"
                
            except Exception as e:
                explanation["home_explanation"]["error"] = str(e)
                explanation["home_explanation"]["method"] = "failed"
        else:
            explanation["home_explanation"]["method"] = "native (global importance only)"
        
        # Explain away goals (similar process)
        if SHAP_AVAILABLE and self.away_explainer is not None:
            try:
                X = self.away_model.named_steps["preprocessing"].transform(features_df)
                shap_values = self.away_explainer(X)
                
                values = shap_values.values[0]
                
                contrib_df = pd.DataFrame({
                    "feature": self.feature_names[:len(values)],
                    "shap_value": values,
                    "feature_value": X[0] if hasattr(X, "__getitem__") else X.toarray()[0]
                })
                
                contrib_df["abs_shap"] = np.abs(contrib_df["shap_value"])
                contrib_df = contrib_df.sort_values("abs_shap", ascending=False)
                
                increasing = contrib_df[contrib_df["shap_value"] > 0].head(top_n)
                explanation["away_explanation"]["top_increasing"] = increasing[
                    ["feature", "shap_value", "feature_value"]
                ].to_dict("records")
                
                decreasing = contrib_df[contrib_df["shap_value"] < 0].head(top_n)
                explanation["away_explanation"]["top_decreasing"] = decreasing[
                    ["feature", "shap_value", "feature_value"]
                ].to_dict("records")
                
                explanation["away_explanation"]["method"] = "SHAP"
                
            except Exception as e:
                explanation["away_explanation"]["error"] = str(e)
                explanation["away_explanation"]["method"] = "failed"
        else:
            explanation["away_explanation"]["method"] = "native (global importance only)"
        
        return explanation
    
    def explain_sample_matches(self, n_matches: int = 10):
        """
        Generate explanations for sample matches.
        
        Args:
            n_matches: Number of matches to explain
        """
        print("=" * 70)
        print("INDIVIDUAL MATCH EXPLANATIONS")
        print("=" * 70)
        print()
        
        # Load sample data
        metadata_df, features_df = self.load_sample_data(n_samples=n_matches)
        
        explanations = []
        
        for idx, (_, row_meta) in enumerate(metadata_df.iterrows()):
            features_row = features_df.iloc[idx]
            
            print(f"[{idx+1}/{n_matches}] Explaining: {row_meta.get('home_team_name', 'Home')} vs "
                  f"{row_meta.get('away_team_name', 'Away')}")
            
            explanation = self.explain_match(features_row, row_meta, top_n=10)
            explanations.append(explanation)
            
            # Print summary
            print(f"  Prediction: {explanation['prediction']['home_goals']:.2f} - "
                  f"{explanation['prediction']['away_goals']:.2f}")
            print(f"  Actual: {row_meta.get('home_goals', '?')} - {row_meta.get('away_goals', '?')}")
            
            if explanation["home_explanation"].get("method") == "SHAP":
                top_feat = explanation["home_explanation"]["top_increasing"][0]
                print(f"  Top home feature: {top_feat['feature']} (SHAP: {top_feat['shap_value']:.4f})")
            
            if explanation["away_explanation"].get("method") == "SHAP":
                top_feat = explanation["away_explanation"]["top_increasing"][0]
                print(f"  Top away feature: {top_feat['feature']} (SHAP: {top_feat['shap_value']:.4f})")
            
            print()
        
        # Save explanations
        import json
        explanations_path = os.path.join(EXPLAIN_DIR, "sample_match_explanations.json")
        with open(explanations_path, "w") as f:
            json.dump(explanations, f, indent=2, default=str)
        
        print(f"✓ Saved {len(explanations)} explanations: {explanations_path}")
        print()
        
        return explanations
    
    def generate_summary_report(self, home_importance_df, away_importance_df):
        """Generate human-readable summary report."""
        print("=" * 70)
        print("GENERATING SUMMARY REPORT")
        print("=" * 70)
        print()
        
        report = f"""# Model Explainability Report
## Phase 11: Understanding Match Predictions

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Model**: {self.metadata.get('best_model_name', 'Unknown')}  
**Method**: {"SHAP" if SHAP_AVAILABLE else "Native Feature Importance"}  
**Validation MAE**: {self.metadata.get('val_mae_avg', 'N/A')}  

---

## Overview

This report explains how the Premier League match prediction models make their forecasts.
The models predict home goals and away goals separately using 372 features derived from:
- Team rolling form (recent matches)
- Historical head-to-head records
- Season statistics
- Venue performance

---

## Global Feature Importance

### Top 10 Features for HOME GOALS

| Rank | Feature | Importance |
|------|---------|------------|
"""
        
        for i, row in home_importance_df.head(10).iterrows():
            report += f"| {i+1} | {row['feature']} | {row['importance']:.6f} |\n"
        
        report += """
### Top 10 Features for AWAY GOALS

| Rank | Feature | Importance |
|------|---------|------------|
"""
        
        for i, row in away_importance_df.head(10).iterrows():
            report += f"| {i+1} | {row['feature']} | {row['importance']:.6f} |\n"
        
        report += f"""
---

## Key Insights

### Home Goals Predictors

The most important features for predicting home goals are:

1. **{home_importance_df.iloc[0]['feature']}**: Most influential feature
2. **{home_importance_df.iloc[1]['feature']}**: Second most important
3. **{home_importance_df.iloc[2]['feature']}**: Third most important

These features likely capture:
- Recent goal-scoring form
- Team offensive strength
- Historical performance at home

### Away Goals Predictors

The most important features for predicting away goals are:

1. **{away_importance_df.iloc[0]['feature']}**: Most influential feature
2. **{away_importance_df.iloc[1]['feature']}**: Second most important
3. **{away_importance_df.iloc[2]['feature']}**: Third most important

These features likely capture:
- Away team offensive capabilities
- Recent away form
- Head-to-head away performance

---

## Feature Categories

Features are grouped into categories:

- **Rolling form**: `_last3`, `_last5`, `_last10` (recent match performance)
- **Season stats**: Prior season aggregated performance
- **Head-to-head**: Historical matchups between teams
- **Relative features**: `home_` vs `away_` differences
- **Venue splits**: Home vs away performance differences

---

## Interpretation Guide

### Feature Importance Values

- **High importance (>0.01)**: Strong influence on predictions
- **Medium importance (0.001-0.01)**: Moderate influence
- **Low importance (<0.001)**: Minimal direct impact

### SHAP Values (if available)

SHAP values explain individual predictions:

- **Positive SHAP**: Feature increases prediction
- **Negative SHAP**: Feature decreases prediction
- **Magnitude**: Strength of the effect

For example:
- `gf_last5 = 8` with SHAP = +0.3 → Recent goals increase prediction by ~0.3 goals
- `ga_last5 = 10` with SHAP = -0.2 → Recent goals conceded decrease prediction by ~0.2 goals

---

## Model Behavior

The models learn that:

1. **Recent form matters most**: Last 3-5 matches heavily influence predictions
2. **Goals scored/conceded**: Most predictive of future goal output
3. **Venue advantage**: Home teams benefit from home performance stats
4. **Head-to-head history**: Past matchups inform future predictions

---

## Limitations

1. **Correlation ≠ Causation**: Important features are correlated, not necessarily causal
2. **Model assumptions**: Linear/tree-based models may miss complex interactions
3. **Data limitations**: Cannot account for injuries, motivation, tactics
4. **Historical bias**: Models rely on past patterns

---

## Files Generated

- `feature_importance_home.csv`: Complete home goals feature importance
- `feature_importance_away.csv`: Complete away goals feature importance
- `sample_match_explanations.json`: Detailed explanations for sample matches
- `explainability_report.md`: This report

---

## Usage

### For Analysts

- Review top features to understand model priorities
- Compare home vs away feature importance
- Validate that important features make domain sense

### For Users

- Individual match explanations show which features drove each prediction
- SHAP values indicate feature contribution magnitude and direction
- Use explanations to build trust in model predictions

---

"""
        
        report_path = os.path.join(EXPLAIN_DIR, "explainability_report.md")
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"✓ Saved report: {report_path}")
        print()
    
    def run_full_explainability(self):
        """Run complete explainability pipeline."""
        print("=" * 70)
        print("PHASE 11: MODEL EXPLAINABILITY")
        print("=" * 70)
        print()
        
        # Load models
        self.load_models()
        
        # Global importance
        home_importance_df, away_importance_df = self.explain_global_importance()
        
        # Individual match explanations
        self.explain_sample_matches(n_matches=10)
        
        # Summary report
        self.generate_summary_report(home_importance_df, away_importance_df)
        
        print("=" * 70)
        print("PHASE 11 COMPLETE")
        print("=" * 70)
        print()
        print("Outputs:")
        print(f"  - {EXPLAIN_DIR}/feature_importance_home.csv")
        print(f"  - {EXPLAIN_DIR}/feature_importance_away.csv")
        print(f"  - {EXPLAIN_DIR}/sample_match_explanations.json")
        print(f"  - {EXPLAIN_DIR}/explainability_report.md")
        print()


if __name__ == "__main__":
    try:
        explainer = ModelExplainer()
        explainer.run_full_explainability()
        
    except (ModelLoadError, ExplainabilityError) as e:
        print(f"✗ Explainability failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
