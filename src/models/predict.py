# =============================================================================
# predict.py
# =============================================================================
# Phase 10: Production Prediction Pipeline
#
# Responsible for:
# - Loading match features for fixtures
# - Applying trained models to generate predictions
# - Handling missing/invalid inputs safely
# - Saving prediction results with metadata
# - Providing clear prediction outputs
# =============================================================================

import os
import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.model_loader import ModelLoader, ModelLoadError

warnings.filterwarnings('ignore')

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(OUTPUTS_DIR, exist_ok=True)


class PredictionError(Exception):
    """Raised when prediction generation fails"""
    pass


class MatchPredictor:
    """
    Production prediction pipeline for Premier League matches.
    
    Handles:
    - Loading match features
    - Validating input data
    - Generating predictions using trained models
    - Saving predictions with metadata
    - Error handling and logging
    """
    
    def __init__(self, models_dir: str = MODELS_DIR, features_dir: str = FEATURES_DIR):
        """
        Initialize MatchPredictor.
        
        Args:
            models_dir: Path to trained models directory
            features_dir: Path to features directory
        """
        self.models_dir = models_dir
        self.features_dir = features_dir
        self.loader = ModelLoader(models_dir)
        self.home_model = None
        self.away_model = None
        self.metadata = None
        self.feature_cols = None
        
    def load_models(self):
        """Load trained models."""
        print("Initializing prediction pipeline...")
        self.home_model, self.away_model, self.metadata = self.loader.load_models()
        
        if not self.loader.validate_model():
            raise PredictionError("Loaded models failed validation")
    
    def load_match_features(self, season: Optional[str] = None) -> pd.DataFrame:
        """
        Load match features for prediction.
        
        Args:
            season: Optional season filter (e.g., "2026/27"). If None, loads all fixtures.
            
        Returns:
            DataFrame with match features
            
        Raises:
            PredictionError: If features cannot be loaded
        """
        print(f"Loading match features...")
        
        features_path = os.path.join(self.features_dir, "match_features.csv")
        if not os.path.exists(features_path):
            raise PredictionError(
                f"Match features not found: {features_path}\n"
                "Please run Phase 5 feature engineering first."
            )
        
        try:
            df = pd.read_csv(features_path, encoding="utf-8-sig", low_memory=False)
            df["match_date"] = pd.to_datetime(df["match_date"])
        except Exception as e:
            raise PredictionError(f"Failed to load match features: {e}")
        
        # Filter for fixtures only (is_fixture = True)
        fixtures_df = df[df["is_fixture"] == True].copy()
        
        if len(fixtures_df) == 0:
            raise PredictionError("No fixtures found in match_features.csv")
        
        # Optionally filter by season
        if season:
            fixtures_df = fixtures_df[fixtures_df["season"] == season].copy()
            if len(fixtures_df) == 0:
                raise PredictionError(f"No fixtures found for season {season}")
        
        print(f"  ✓ Loaded {len(fixtures_df)} fixtures")
        if season:
            print(f"  ✓ Season: {season}")
        else:
            seasons = fixtures_df["season"].unique()
            print(f"  ✓ Seasons: {', '.join(sorted(seasons))}")
        print()
        
        return fixtures_df
    
    def prepare_features(self, fixtures_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare features for prediction by extracting feature columns.
        
        Args:
            fixtures_df: DataFrame with fixture data
            
        Returns:
            Tuple of (metadata_df, features_df)
            
        Raises:
            PredictionError: If feature preparation fails
        """
        print("Preparing features for prediction...")
        
        # Define columns (same as training)
        KEY_COLS = [
            "match_id", "row_id", "season", "match_date", "is_fixture",
            "home_team_id", "away_team_id", "home_team_name", "away_team_name"
        ]
        
        TARGET_COLS = ["result", "home_goals", "away_goals"]
        
        # Feature columns are everything except keys and targets
        all_cols = fixtures_df.columns.tolist()
        feature_cols = [c for c in all_cols if c not in KEY_COLS + TARGET_COLS]
        
        # Drop duplicate columns (same as training)
        DUPLICATE_COLS = ["sca_per_90_calc", "gca_per_90_calc"]
        feature_cols = [c for c in feature_cols if c not in DUPLICATE_COLS]
        
        self.feature_cols = feature_cols
        
        # Extract metadata and features
        metadata_cols = [c for c in KEY_COLS if c in fixtures_df.columns]
        metadata_df = fixtures_df[metadata_cols].copy()
        
        # Extract features
        try:
            features_df = fixtures_df[feature_cols].copy()
        except KeyError as e:
            missing = [c for c in feature_cols if c not in fixtures_df.columns]
            raise PredictionError(f"Missing required features: {missing[:5]}... ({len(missing)} total)")
        
        # Check for missing data
        missing_pct = features_df.isnull().mean().mean() * 100
        print(f"  ✓ Extracted {len(feature_cols)} features")
        print(f"  ✓ Missing data: {missing_pct:.2f}%")
        
        if missing_pct > 50:
            print(f"  ⚠ WARNING: High missing data percentage ({missing_pct:.1f}%)")
        
        print()
        
        return metadata_df, features_df
    
    def generate_predictions(self, features_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate predictions using trained models.
        
        Args:
            features_df: DataFrame with features (no metadata columns)
            
        Returns:
            Tuple of (home_goals_predictions, away_goals_predictions)
            
        Raises:
            PredictionError: If prediction generation fails
        """
        print("Generating predictions...")
        
        if self.home_model is None or self.away_model is None:
            raise PredictionError("Models not loaded. Call load_models() first.")
        
        try:
            # Predict home goals
            home_preds = self.home_model.predict(features_df)
            
            # Predict away goals
            away_preds = self.away_model.predict(features_df)
            
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
        
        # Clip predictions to reasonable range [0, 10]
        home_preds = np.clip(home_preds, 0, 10)
        away_preds = np.clip(away_preds, 0, 10)
        
        print(f"  ✓ Generated {len(home_preds)} predictions")
        print(f"  ✓ Home goals range: [{home_preds.min():.2f}, {home_preds.max():.2f}]")
        print(f"  ✓ Away goals range: [{away_preds.min():.2f}, {away_preds.max():.2f}]")
        print()
        
        return home_preds, away_preds
    
    def predict_result(self, home_goals: float, away_goals: float, margin: float = 0.5) -> str:
        """
        Predict match result from goal predictions.
        
        Args:
            home_goals: Predicted home goals
            away_goals: Predicted away goals
            margin: Minimum goal difference to call a win (default 0.5)
            
        Returns:
            Result string: "H" (home win), "D" (draw), "A" (away win)
        """
        diff = home_goals - away_goals
        
        if diff > margin:
            return "H"
        elif diff < -margin:
            return "A"
        else:
            return "D"
    
    def create_predictions_dataframe(
        self,
        metadata_df: pd.DataFrame,
        home_preds: np.ndarray,
        away_preds: np.ndarray
    ) -> pd.DataFrame:
        """
        Create predictions DataFrame with metadata and predictions.
        
        Args:
            metadata_df: DataFrame with match metadata
            home_preds: Home goals predictions
            away_preds: Away goals predictions
            
        Returns:
            DataFrame with predictions
        """
        print("Creating predictions output...")
        
        # Create output dataframe
        output_df = metadata_df.copy()
        
        # Add predictions
        output_df["predicted_home_goals"] = home_preds
        output_df["predicted_away_goals"] = away_preds
        output_df["predicted_total_goals"] = home_preds + away_preds
        
        # Predict results
        output_df["predicted_result"] = [
            self.predict_result(h, a) for h, a in zip(home_preds, away_preds)
        ]
        
        # Add confidence metrics
        output_df["goal_diff"] = home_preds - away_preds
        output_df["confidence"] = np.abs(home_preds - away_preds)  # Higher diff = more confident
        
        # Round for readability
        output_df["predicted_home_goals"] = output_df["predicted_home_goals"].round(2)
        output_df["predicted_away_goals"] = output_df["predicted_away_goals"].round(2)
        output_df["predicted_total_goals"] = output_df["predicted_total_goals"].round(2)
        output_df["goal_diff"] = output_df["goal_diff"].round(2)
        output_df["confidence"] = output_df["confidence"].round(2)
        
        # Add metadata
        output_df["model_name"] = self.metadata.get("best_model_name", "Unknown")
        output_df["model_mae"] = self.metadata.get("val_mae_avg", None)
        output_df["prediction_timestamp"] = datetime.now().isoformat()
        
        print(f"  ✓ Created predictions for {len(output_df)} matches")
        print()
        
        return output_df
    
    def save_predictions(self, predictions_df: pd.DataFrame, output_path: Optional[str] = None):
        """
        Save predictions to CSV file.
        
        Args:
            predictions_df: DataFrame with predictions
            output_path: Optional custom output path. If None, uses default.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(OUTPUTS_DIR, f"predictions_{timestamp}.csv")
        
        predictions_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✓ Saved predictions: {output_path}")
        
        # Also save as predictions.csv (overwrite)
        latest_path = os.path.join(OUTPUTS_DIR, "predictions.csv")
        predictions_df.to_csv(latest_path, index=False, encoding="utf-8-sig")
        print(f"✓ Saved latest predictions: {latest_path}")
        print()
        
        return output_path
    
    def predict(self, season: Optional[str] = None, save: bool = True) -> pd.DataFrame:
        """
        Complete prediction pipeline.
        
        Args:
            season: Optional season filter (e.g., "2026/27")
            save: Whether to save predictions to file
            
        Returns:
            DataFrame with predictions
        """
        # Load models
        self.load_models()
        
        # Load fixtures
        fixtures_df = self.load_match_features(season)
        
        # Prepare features
        metadata_df, features_df = self.prepare_features(fixtures_df)
        
        # Generate predictions
        home_preds, away_preds = self.generate_predictions(features_df)
        
        # Create output dataframe
        predictions_df = self.create_predictions_dataframe(metadata_df, home_preds, away_preds)
        
        # Save predictions
        if save:
            self.save_predictions(predictions_df)
        
        return predictions_df
    
    def summarize_predictions(self, predictions_df: pd.DataFrame):
        """
        Print summary statistics of predictions.
        
        Args:
            predictions_df: DataFrame with predictions
        """
        print("=" * 70)
        print("PREDICTION SUMMARY")
        print("=" * 70)
        print()
        
        print(f"Total matches: {len(predictions_df)}")
        print()
        
        print("Predicted results:")
        result_counts = predictions_df["predicted_result"].value_counts()
        for result in ["H", "D", "A"]:
            count = result_counts.get(result, 0)
            pct = (count / len(predictions_df)) * 100
            result_name = {"H": "Home wins", "D": "Draws", "A": "Away wins"}[result]
            print(f"  {result_name}: {count} ({pct:.1f}%)")
        print()
        
        print("Goal predictions:")
        print(f"  Avg home goals: {predictions_df['predicted_home_goals'].mean():.2f}")
        print(f"  Avg away goals: {predictions_df['predicted_away_goals'].mean():.2f}")
        print(f"  Avg total goals: {predictions_df['predicted_total_goals'].mean():.2f}")
        print()
        
        print("Highest scoring matches (predicted):")
        top_scoring = predictions_df.nlargest(5, "predicted_total_goals")[
            ["home_team_name", "away_team_name", "predicted_home_goals", 
             "predicted_away_goals", "predicted_total_goals"]
        ]
        for _, row in top_scoring.iterrows():
            print(f"  {row['home_team_name']} {row['predicted_home_goals']:.1f} - "
                  f"{row['predicted_away_goals']:.1f} {row['away_team_name']} "
                  f"(Total: {row['predicted_total_goals']:.1f})")
        print()
        
        print("Model info:")
        print(f"  Model: {predictions_df['model_name'].iloc[0]}")
        print(f"  Validation MAE: {predictions_df['model_mae'].iloc[0]:.4f} goals")
        print()


def predict_fixtures(season: Optional[str] = None, save: bool = True) -> pd.DataFrame:
    """
    Convenience function to generate predictions.
    
    Args:
        season: Optional season filter (e.g., "2026/27")
        save: Whether to save predictions to file
        
    Returns:
        DataFrame with predictions
    """
    predictor = MatchPredictor()
    predictions_df = predictor.predict(season=season, save=save)
    predictor.summarize_predictions(predictions_df)
    return predictions_df


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 10: MATCH PREDICTION PIPELINE")
    print("=" * 70)
    print()
    
    # Check for season argument
    season_filter = None
    if len(sys.argv) > 1:
        season_filter = sys.argv[1]
        print(f"Season filter: {season_filter}")
        print()
    
    try:
        # Run predictions
        predictions_df = predict_fixtures(season=season_filter, save=True)
        
        print("=" * 70)
        print("PREDICTION PIPELINE COMPLETE")
        print("=" * 70)
        print()
        print("✓ Predictions saved to outputs/predictions.csv")
        print()
        
    except (ModelLoadError, PredictionError) as e:
        print(f"✗ Prediction failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
