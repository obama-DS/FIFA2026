# =============================================================================
# test_predictions.py
# =============================================================================
# Phase 10: Prediction Pipeline Tests
#
# Tests:
# - Successful model loading
# - Successful prediction generation
# - Invalid input handling
# - Missing data handling
# - Edge cases
# =============================================================================

import os
import sys
import tempfile
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.model_loader import ModelLoader, ModelLoadError
from models.predict import MatchPredictor, PredictionError

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
FEATURES_DIR = os.path.join(PROJECT_ROOT, "data", "features")


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, name: str, message: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "PASS", "message": message})
        print(f"  ✓ {name}")
        if message:
            print(f"    {message}")
    
    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "FAIL", "message": error})
        print(f"  ✗ {name}")
        print(f"    Error: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {(self.passed / total * 100):.1f}%")
        print()
        
        if self.failed > 0:
            print("Failed tests:")
            for test in self.tests:
                if test["status"] == "FAIL":
                    print(f"  - {test['name']}: {test['message']}")
            print()
        
        return self.failed == 0


def test_model_loader(results: TestResults):
    """Test model loading functionality"""
    print("\n[1] Testing Model Loader")
    print("-" * 70)
    
    # Test 1: Load models successfully
    try:
        loader = ModelLoader(MODELS_DIR)
        home_model, away_model, metadata = loader.load_models()
        
        if home_model is None or away_model is None:
            results.add_fail("Load models", "Models are None after loading")
        else:
            results.add_pass("Load models", f"Loaded {metadata.get('best_model_name', 'Unknown')}")
    except Exception as e:
        results.add_fail("Load models", str(e))
    
    # Test 2: Validate models
    try:
        loader = ModelLoader(MODELS_DIR)
        loader.load_models()
        is_valid = loader.validate_model()
        
        if is_valid:
            results.add_pass("Validate models", "Models have predict() methods")
        else:
            results.add_fail("Validate models", "Validation failed")
    except Exception as e:
        results.add_fail("Validate models", str(e))
    
    # Test 3: Get model info
    try:
        loader = ModelLoader(MODELS_DIR)
        loader.load_models()
        info = loader.get_model_info()
        
        required_keys = ["status", "model_name", "val_mae_avg"]
        missing = [k for k in required_keys if k not in info]
        
        if missing:
            results.add_fail("Get model info", f"Missing keys: {missing}")
        else:
            results.add_pass("Get model info", f"MAE: {info.get('val_mae_avg')}")
    except Exception as e:
        results.add_fail("Get model info", str(e))
    
    # Test 4: Handle missing models directory
    try:
        fake_dir = os.path.join(tempfile.gettempdir(), "fake_models_dir_12345")
        loader = ModelLoader(fake_dir)
        
        try:
            loader.load_models()
            results.add_fail("Handle missing models", "Should raise ModelLoadError")
        except ModelLoadError as e:
            results.add_pass("Handle missing models", "Correctly raised ModelLoadError")
    except Exception as e:
        results.add_fail("Handle missing models", f"Unexpected error: {e}")


def test_feature_loading(results: TestResults):
    """Test feature loading functionality"""
    print("\n[2] Testing Feature Loading")
    print("-" * 70)
    
    # Test 1: Load match features
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        fixtures_df = predictor.load_match_features()
        
        if len(fixtures_df) == 0:
            results.add_fail("Load match features", "No fixtures found")
        else:
            results.add_pass("Load match features", f"Loaded {len(fixtures_df)} fixtures")
    except Exception as e:
        results.add_fail("Load match features", str(e))
    
    # Test 2: Load with season filter
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        fixtures_df = predictor.load_match_features(season="2026/27")
        
        if len(fixtures_df) == 0:
            results.add_fail("Load with season filter", "No fixtures found for 2026/27")
        else:
            # Check all rows are for the correct season
            if (fixtures_df["season"] == "2026/27").all():
                results.add_pass("Load with season filter", f"Loaded {len(fixtures_df)} fixtures for 2026/27")
            else:
                results.add_fail("Load with season filter", "Some fixtures are not for 2026/27")
    except Exception as e:
        results.add_fail("Load with season filter", str(e))
    
    # Test 3: Prepare features
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        fixtures_df = predictor.load_match_features()
        metadata_df, features_df = predictor.prepare_features(fixtures_df)
        
        # Check that features don't contain metadata
        metadata_cols = ["match_id", "home_team_name", "away_team_name"]
        has_metadata = any(col in features_df.columns for col in metadata_cols)
        
        if has_metadata:
            results.add_fail("Prepare features", "Features contain metadata columns")
        else:
            results.add_pass("Prepare features", f"Extracted {len(features_df.columns)} clean features")
    except Exception as e:
        results.add_fail("Prepare features", str(e))
    
    # Test 4: Handle invalid season
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        
        try:
            fixtures_df = predictor.load_match_features(season="9999/00")
            results.add_fail("Handle invalid season", "Should raise PredictionError")
        except PredictionError as e:
            results.add_pass("Handle invalid season", "Correctly raised PredictionError")
    except Exception as e:
        results.add_fail("Handle invalid season", f"Unexpected error: {e}")


def test_prediction_generation(results: TestResults):
    """Test prediction generation"""
    print("\n[3] Testing Prediction Generation")
    print("-" * 70)
    
    # Test 1: Generate predictions
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictor.load_models()
        fixtures_df = predictor.load_match_features(season="2026/27")
        metadata_df, features_df = predictor.prepare_features(fixtures_df)
        
        home_preds, away_preds = predictor.generate_predictions(features_df)
        
        # Check predictions are valid
        if len(home_preds) != len(features_df):
            results.add_fail("Generate predictions", "Prediction count mismatch")
        elif np.any(np.isnan(home_preds)) or np.any(np.isnan(away_preds)):
            results.add_fail("Generate predictions", "Predictions contain NaN")
        elif np.any(home_preds < 0) or np.any(away_preds < 0):
            results.add_fail("Generate predictions", "Predictions contain negative values")
        elif np.any(home_preds > 10) or np.any(away_preds > 10):
            results.add_fail("Generate predictions", "Predictions exceed maximum (10 goals)")
        else:
            avg_home = home_preds.mean()
            avg_away = away_preds.mean()
            results.add_pass("Generate predictions", 
                           f"Avg: {avg_home:.2f} home, {avg_away:.2f} away goals")
    except Exception as e:
        results.add_fail("Generate predictions", str(e))
    
    # Test 2: Predict without loading models
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        fixtures_df = predictor.load_match_features(season="2026/27")
        metadata_df, features_df = predictor.prepare_features(fixtures_df)
        
        try:
            home_preds, away_preds = predictor.generate_predictions(features_df)
            results.add_fail("Predict without models", "Should raise PredictionError")
        except PredictionError as e:
            results.add_pass("Predict without models", "Correctly raised PredictionError")
    except Exception as e:
        results.add_fail("Predict without models", f"Unexpected error: {e}")
    
    # Test 3: Result prediction logic
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        
        # Test home win
        result = predictor.predict_result(2.5, 1.2)
        if result != "H":
            results.add_fail("Result prediction - home win", f"Expected 'H', got '{result}'")
        else:
            results.add_pass("Result prediction - home win", "Correctly predicted 'H'")
        
        # Test away win
        result = predictor.predict_result(0.8, 2.3)
        if result != "A":
            results.add_fail("Result prediction - away win", f"Expected 'A', got '{result}'")
        else:
            results.add_pass("Result prediction - away win", "Correctly predicted 'A'")
        
        # Test draw
        result = predictor.predict_result(1.5, 1.4)
        if result != "D":
            results.add_fail("Result prediction - draw", f"Expected 'D', got '{result}'")
        else:
            results.add_pass("Result prediction - draw", "Correctly predicted 'D'")
        
    except Exception as e:
        results.add_fail("Result prediction logic", str(e))


def test_full_pipeline(results: TestResults):
    """Test complete prediction pipeline"""
    print("\n[4] Testing Full Pipeline")
    print("-" * 70)
    
    # Test 1: Run full pipeline
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictions_df = predictor.predict(season="2026/27", save=False)
        
        # Validate output structure
        required_cols = [
            "match_id", "home_team_name", "away_team_name",
            "predicted_home_goals", "predicted_away_goals",
            "predicted_result", "model_name"
        ]
        missing = [col for col in required_cols if col not in predictions_df.columns]
        
        if missing:
            results.add_fail("Run full pipeline", f"Missing columns: {missing}")
        elif len(predictions_df) == 0:
            results.add_fail("Run full pipeline", "No predictions generated")
        else:
            results.add_pass("Run full pipeline", 
                           f"Generated {len(predictions_df)} predictions with all required columns")
    except Exception as e:
        results.add_fail("Run full pipeline", str(e))
    
    # Test 2: Predictions dataframe structure
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        fixtures_df = predictor.load_match_features(season="2026/27")
        predictor.load_models()
        metadata_df, features_df = predictor.prepare_features(fixtures_df)
        home_preds, away_preds = predictor.generate_predictions(features_df)
        
        predictions_df = predictor.create_predictions_dataframe(metadata_df, home_preds, away_preds)
        
        # Check for expected columns
        expected = ["predicted_home_goals", "predicted_away_goals", "predicted_result", 
                   "confidence", "model_name", "prediction_timestamp"]
        missing = [col for col in expected if col not in predictions_df.columns]
        
        if missing:
            results.add_fail("Predictions dataframe", f"Missing columns: {missing}")
        else:
            results.add_pass("Predictions dataframe", "All expected columns present")
    except Exception as e:
        results.add_fail("Predictions dataframe", str(e))
    
    # Test 3: Save predictions
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictions_df = predictor.predict(season="2026/27", save=False)
        
        # Save to temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"test_predictions_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        
        predictor.save_predictions(predictions_df, temp_path)
        
        # Verify file exists and can be read
        if not os.path.exists(temp_path):
            results.add_fail("Save predictions", "Output file not created")
        else:
            # Try to read it back
            loaded_df = pd.read_csv(temp_path)
            if len(loaded_df) != len(predictions_df):
                results.add_fail("Save predictions", "Row count mismatch after save/load")
            else:
                results.add_pass("Save predictions", f"Saved and verified {len(loaded_df)} predictions")
            
            # Clean up
            os.remove(temp_path)
    except Exception as e:
        results.add_fail("Save predictions", str(e))


def test_edge_cases(results: TestResults):
    """Test edge cases and error handling"""
    print("\n[5] Testing Edge Cases")
    print("-" * 70)
    
    # Test 1: Empty feature dataframe
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictor.load_models()
        
        # Create empty dataframe with correct columns
        fixtures_df = predictor.load_match_features(season="2026/27")
        _, features_df = predictor.prepare_features(fixtures_df)
        empty_df = features_df.iloc[:0].copy()
        
        home_preds, away_preds = predictor.generate_predictions(empty_df)
        
        if len(home_preds) == 0 and len(away_preds) == 0:
            results.add_pass("Empty input", "Correctly handled empty dataframe")
        else:
            results.add_fail("Empty input", f"Expected empty output, got {len(home_preds)} predictions")
    except Exception as e:
        results.add_fail("Empty input", str(e))
    
    # Test 2: Prediction value ranges
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictor.load_models()
        fixtures_df = predictor.load_match_features(season="2026/27")
        metadata_df, features_df = predictor.prepare_features(fixtures_df)
        
        home_preds, away_preds = predictor.generate_predictions(features_df)
        
        # Check reasonable ranges
        if home_preds.min() < 0:
            results.add_fail("Prediction ranges", "Home predictions contain negative values")
        elif home_preds.max() > 10:
            results.add_fail("Prediction ranges", "Home predictions exceed 10 goals")
        elif away_preds.min() < 0:
            results.add_fail("Prediction ranges", "Away predictions contain negative values")
        elif away_preds.max() > 10:
            results.add_fail("Prediction ranges", "Away predictions exceed 10 goals")
        else:
            results.add_pass("Prediction ranges", 
                           f"All predictions within [0, 10]: home [{home_preds.min():.2f}, {home_preds.max():.2f}], "
                           f"away [{away_preds.min():.2f}, {away_preds.max():.2f}]")
    except Exception as e:
        results.add_fail("Prediction ranges", str(e))
    
    # Test 3: Result distribution sanity check
    try:
        predictor = MatchPredictor(MODELS_DIR, FEATURES_DIR)
        predictions_df = predictor.predict(season="2026/27", save=False)
        
        result_counts = predictions_df["predicted_result"].value_counts()
        
        # Check all result types present
        if not all(r in result_counts.index for r in ["H", "D", "A"]):
            results.add_fail("Result distribution", "Not all result types (H/D/A) present")
        else:
            home_pct = result_counts.get("H", 0) / len(predictions_df) * 100
            draw_pct = result_counts.get("D", 0) / len(predictions_df) * 100
            away_pct = result_counts.get("A", 0) / len(predictions_df) * 100
            
            # Sanity check: home advantage typically 40-50%, draws 20-30%, away 20-30%
            if home_pct < 20 or home_pct > 70:
                results.add_fail("Result distribution", 
                               f"Home win % ({home_pct:.1f}%) outside realistic range [20%, 70%]")
            else:
                results.add_pass("Result distribution", 
                               f"H: {home_pct:.1f}%, D: {draw_pct:.1f}%, A: {away_pct:.1f}%")
    except Exception as e:
        results.add_fail("Result distribution", str(e))


def run_all_tests():
    """Run all test suites"""
    print("=" * 70)
    print("PHASE 10: PREDICTION PIPELINE TESTS")
    print("=" * 70)
    
    results = TestResults()
    
    try:
        test_model_loader(results)
        test_feature_loading(results)
        test_prediction_generation(results)
        test_full_pipeline(results)
        test_edge_cases(results)
        
    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    success = results.summary()
    
    if success:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
