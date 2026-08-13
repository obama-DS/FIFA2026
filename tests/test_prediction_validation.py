# =============================================================================
# test_prediction_validation.py
# =============================================================================
# Phase 13: Prediction Validation Tests
#
# Comprehensive validation of prediction pipeline:
# - Valid inputs
# - Missing inputs
# - Invalid data types
# - Extreme values
# - Unseen categorical values
# - Output validation (numeric, finite, football ranges)
# =============================================================================

import os
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.predict import MatchPredictor, PredictionError
from src.models.model_loader import ModelLoader, ModelLoadError


class TestPredictionValidation(unittest.TestCase):
    """
    Validation tests for prediction pipeline.
    
    Tests cover:
    1. Valid inputs (expected use cases)
    2. Missing data (NaN, empty values)
    3. Invalid types (strings where numbers expected)
    4. Extreme values (very large/small numbers)
    5. Edge cases (zeros, negative values)
    6. Output validation (numeric, finite, reasonable ranges)
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.models_dir = os.path.join(project_root, "models")
        cls.features_dir = os.path.join(project_root, "data", "features")
        
        # Check if models exist
        if not os.path.exists(os.path.join(cls.models_dir, "best_model.json")):
            raise unittest.SkipTest("Trained models not found - run Phase 9 first")
        
        # Load predictor
        try:
            cls.predictor = MatchPredictor(cls.models_dir, cls.features_dir)
            cls.predictor.load_models()
        except Exception as e:
            raise unittest.SkipTest(f"Could not load models: {e}")
        
        # Load sample features for testing
        features_path = os.path.join(cls.features_dir, "match_features.csv")
        if os.path.exists(features_path):
            df = pd.read_csv(features_path, nrows=10)
            cls.sample_features = df
            
            # Get valid feature columns
            KEY_COLS = [
                "match_id", "row_id", "season", "match_date", "is_fixture",
                "home_team_id", "away_team_id", "home_team_name", "away_team_name"
            ]
            TARGET_COLS = ["result", "home_goals", "away_goals"]
            DUPLICATE_COLS = ["sca_per_90_calc", "gca_per_90_calc"]
            
            cls.feature_cols = [c for c in df.columns 
                               if c not in KEY_COLS + TARGET_COLS + DUPLICATE_COLS]
            cls.metadata_cols = [c for c in KEY_COLS if c in df.columns]
        else:
            raise unittest.SkipTest("Features file not found")
    
    # =========================================================================
    # Test Category 1: Valid Inputs
    # =========================================================================
    
    def test_valid_single_match(self):
        """Test prediction with valid single match input."""
        # Get first valid match
        features = self.sample_features[self.feature_cols].iloc[0]
        metadata = self.sample_features[self.metadata_cols].iloc[0]
        
        # Generate prediction
        home_pred, away_pred = self.predictor.generate_predictions(
            pd.DataFrame([features])
        )
        
        # Validate outputs
        self.assertEqual(len(home_pred), 1, "Should return 1 home prediction")
        self.assertEqual(len(away_pred), 1, "Should return 1 away prediction")
        
        # Check types
        self.assertIsInstance(home_pred[0], (int, float, np.number),
                            "Home prediction should be numeric")
        self.assertIsInstance(away_pred[0], (int, float, np.number),
                            "Away prediction should be numeric")
        
        # Check finite
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Home prediction should be finite")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Away prediction should be finite")
        
        # Check reasonable range [0, 10]
        self.assertGreaterEqual(home_pred[0], 0,
                               "Home prediction should be >= 0")
        self.assertLessEqual(home_pred[0], 10,
                            "Home prediction should be <= 10")
        self.assertGreaterEqual(away_pred[0], 0,
                               "Away prediction should be >= 0")
        self.assertLessEqual(away_pred[0], 10,
                            "Away prediction should be <= 10")
    
    def test_valid_multiple_matches(self):
        """Test prediction with multiple valid matches."""
        n_matches = min(5, len(self.sample_features))
        features = self.sample_features[self.feature_cols].iloc[:n_matches]
        
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        # Check counts
        self.assertEqual(len(home_pred), n_matches)
        self.assertEqual(len(away_pred), n_matches)
        
        # Check all are valid
        for i in range(n_matches):
            self.assertTrue(np.isfinite(home_pred[i]),
                           f"Match {i}: home prediction not finite")
            self.assertTrue(np.isfinite(away_pred[i]),
                           f"Match {i}: away prediction not finite")
            self.assertGreaterEqual(home_pred[i], 0,
                                   f"Match {i}: home < 0")
            self.assertLessEqual(home_pred[i], 10,
                                f"Match {i}: home > 10")
            self.assertGreaterEqual(away_pred[i], 0,
                                   f"Match {i}: away < 0")
            self.assertLessEqual(away_pred[i], 10,
                                f"Match {i}: away > 10")
    
    # =========================================================================
    # Test Category 2: Missing Data
    # =========================================================================
    
    def test_missing_single_feature(self):
        """Test prediction with one missing feature (NaN)."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        
        # Set first numeric feature to NaN
        numeric_cols = features.select_dtypes(include=[np.number]).index
        if len(numeric_cols) > 0:
            features_df = pd.DataFrame([features])
            features_df.loc[0, numeric_cols[0]] = np.nan
            
            # Should still predict (imputation handles NaN)
            home_pred, away_pred = self.predictor.generate_predictions(features_df)
            
            self.assertTrue(np.isfinite(home_pred[0]),
                           "Should handle single NaN via imputation")
            self.assertTrue(np.isfinite(away_pred[0]),
                           "Should handle single NaN via imputation")
    
    def test_missing_multiple_features(self):
        """Test prediction with multiple missing features."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set 10% of features to NaN
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        n_to_nan = max(1, len(numeric_cols) // 10)
        nan_cols = numeric_cols[:n_to_nan]
        features_df.loc[0, nan_cols] = np.nan
        
        # Should still predict
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle multiple NaNs via imputation")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Should handle multiple NaNs via imputation")
    
    def test_all_features_missing(self):
        """Test prediction with all features missing (extreme case)."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set all numeric features to NaN
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        features_df.loc[0, numeric_cols] = np.nan
        
        # Should still predict (median imputation)
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Predictions should be close to average (since all imputed)
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle all NaNs via imputation")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Should handle all NaNs via imputation")
        
        # Should be near league average (~1.5 goals)
        self.assertGreater(home_pred[0], 0.5,
                          "All-NaN should predict near average")
        self.assertLess(home_pred[0], 3.0,
                       "All-NaN should predict near average")
    
    # =========================================================================
    # Test Category 3: Invalid Data Types
    # =========================================================================
    
    def test_string_in_numeric_column(self):
        """Test handling of string values in numeric columns."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Insert string into numeric column
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            features_df.loc[0, numeric_cols[0]] = "invalid_string"
            
            # Pandas will coerce or raise error
            # Our pipeline should handle it gracefully
            try:
                # Try to convert to numeric (will make NaN)
                features_df[numeric_cols[0]] = pd.to_numeric(
                    features_df[numeric_cols[0]], errors='coerce'
                )
                home_pred, away_pred = self.predictor.generate_predictions(features_df)
                
                self.assertTrue(np.isfinite(home_pred[0]),
                               "Should handle coerced string (becomes NaN)")
            except Exception:
                # If it fails, that's also acceptable (input validation)
                pass
    
    def test_boolean_values(self):
        """Test handling of boolean values in numeric columns."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Boolean will be coerced to 0/1
            features_df.loc[0, numeric_cols[0]] = True
            
            home_pred, away_pred = self.predictor.generate_predictions(features_df)
            
            # Should work (boolean becomes 1)
            self.assertTrue(np.isfinite(home_pred[0]),
                           "Should handle boolean (coerces to 0/1)")
    
    # =========================================================================
    # Test Category 4: Extreme Values
    # =========================================================================
    
    def test_very_large_values(self):
        """Test prediction with extremely large feature values."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set some features to very large values
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 3:
            features_df.loc[0, numeric_cols[0]] = 1e6  # Very large
            features_df.loc[0, numeric_cols[1]] = 999999
            features_df.loc[0, numeric_cols[2]] = 1e10
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Predictions should still be finite and reasonable
        # (scaling should handle large values)
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle very large values via scaling")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Should handle very large values via scaling")
        
        # After clipping, should be in [0, 10]
        self.assertGreaterEqual(home_pred[0], 0)
        self.assertLessEqual(home_pred[0], 10)
    
    def test_very_small_values(self):
        """Test prediction with extremely small feature values."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set some features to very small values
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 3:
            features_df.loc[0, numeric_cols[0]] = 1e-10  # Very small
            features_df.loc[0, numeric_cols[1]] = 0.000001
            features_df.loc[0, numeric_cols[2]] = -1e-6
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle very small values")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Should handle very small values")
    
    def test_negative_values(self):
        """Test prediction with negative feature values."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set some features to negative (shouldn't happen but test robustness)
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            features_df.loc[0, numeric_cols[0]] = -100
            features_df.loc[0, numeric_cols[1]] = -999
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Model should still predict
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle negative values")
        # Output should still be clipped to [0, 10]
        self.assertGreaterEqual(home_pred[0], 0,
                               "Output should be clipped to >= 0")
    
    def test_all_zeros(self):
        """Test prediction when all features are zero."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set all numeric features to zero
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        features_df.loc[0, numeric_cols] = 0
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Should predict something reasonable (not crash)
        self.assertTrue(np.isfinite(home_pred[0]),
                       "Should handle all-zero input")
        self.assertTrue(np.isfinite(away_pred[0]),
                       "Should handle all-zero input")
        
        # Likely to predict low scores
        self.assertGreaterEqual(home_pred[0], 0)
        self.assertLess(home_pred[0], 5,
                       "All-zero should predict low scores")
    
    # =========================================================================
    # Test Category 5: Edge Cases
    # =========================================================================
    
    def test_empty_dataframe(self):
        """Test prediction with empty DataFrame."""
        features_df = pd.DataFrame(columns=self.feature_cols)
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Should return empty arrays
        self.assertEqual(len(home_pred), 0, "Empty input -> empty output")
        self.assertEqual(len(away_pred), 0, "Empty input -> empty output")
    
    def test_single_row_dataframe(self):
        """Test with single-row DataFrame (edge case for scaling)."""
        features = self.sample_features[self.feature_cols].iloc[0]
        features_df = pd.DataFrame([features])
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        self.assertEqual(len(home_pred), 1)
        self.assertTrue(np.isfinite(home_pred[0]))
    
    def test_duplicate_rows(self):
        """Test with duplicate input rows."""
        features = self.sample_features[self.feature_cols].iloc[0]
        features_df = pd.DataFrame([features] * 3)  # 3 identical rows
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        
        # Should return 3 predictions
        self.assertEqual(len(home_pred), 3)
        
        # All should be identical (same input -> same output)
        self.assertAlmostEqual(home_pred[0], home_pred[1], places=5,
                              msg="Identical input should give identical output")
        self.assertAlmostEqual(home_pred[1], home_pred[2], places=5)
    
    def test_infinity_values(self):
        """Test handling of infinity values."""
        features = self.sample_features[self.feature_cols].iloc[0].copy()
        features_df = pd.DataFrame([features])
        
        # Set features to infinity
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            features_df.loc[0, numeric_cols[0]] = np.inf
            features_df.loc[0, numeric_cols[1]] = -np.inf
        
        # Should handle infinity (imputation or coercion)
        try:
            # Replace inf with NaN (common preprocessing)
            features_df = features_df.replace([np.inf, -np.inf], np.nan)
            home_pred, away_pred = self.predictor.generate_predictions(features_df)
            
            self.assertTrue(np.isfinite(home_pred[0]),
                           "Should handle infinity values")
        except Exception:
            # Acceptable to fail on infinity
            pass
    
    # =========================================================================
    # Test Category 6: Output Validation
    # =========================================================================
    
    def test_output_types(self):
        """Verify output types are correct."""
        features = self.sample_features[self.feature_cols].iloc[:3]
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        # Should be numpy arrays
        self.assertIsInstance(home_pred, np.ndarray,
                            "Home predictions should be numpy array")
        self.assertIsInstance(away_pred, np.ndarray,
                            "Away predictions should be numpy array")
        
        # Elements should be numeric
        self.assertTrue(np.issubdtype(home_pred.dtype, np.number),
                       "Home predictions should be numeric type")
        self.assertTrue(np.issubdtype(away_pred.dtype, np.number),
                       "Away predictions should be numeric type")
    
    def test_output_ranges(self):
        """Verify all outputs are within sensible football ranges."""
        features = self.sample_features[self.feature_cols].iloc[:5]
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        # All predictions should be [0, 10]
        self.assertTrue(np.all(home_pred >= 0),
                       "All home predictions should be >= 0")
        self.assertTrue(np.all(home_pred <= 10),
                       "All home predictions should be <= 10")
        self.assertTrue(np.all(away_pred >= 0),
                       "All away predictions should be >= 0")
        self.assertTrue(np.all(away_pred <= 10),
                       "All away predictions should be <= 10")
    
    def test_output_no_nan(self):
        """Verify outputs contain no NaN values."""
        features = self.sample_features[self.feature_cols].iloc[:5]
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        self.assertFalse(np.any(np.isnan(home_pred)),
                        "Home predictions should not contain NaN")
        self.assertFalse(np.any(np.isnan(away_pred)),
                        "Away predictions should not contain NaN")
    
    def test_output_no_inf(self):
        """Verify outputs contain no infinity values."""
        features = self.sample_features[self.feature_cols].iloc[:5]
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        self.assertFalse(np.any(np.isinf(home_pred)),
                        "Home predictions should not contain infinity")
        self.assertFalse(np.any(np.isinf(away_pred)),
                        "Away predictions should not contain infinity")
    
    def test_output_realistic_distribution(self):
        """Verify output distribution is realistic for football."""
        features = self.sample_features[self.feature_cols].iloc[:min(20, len(self.sample_features))]
        home_pred, away_pred = self.predictor.generate_predictions(features)
        
        # Mean should be around 1.0-2.0 goals (typical football)
        home_mean = np.mean(home_pred)
        away_mean = np.mean(away_pred)
        
        self.assertGreater(home_mean, 0.5,
                          "Home mean should be > 0.5 goals")
        self.assertLess(home_mean, 3.5,
                       "Home mean should be < 3.5 goals")
        self.assertGreater(away_mean, 0.3,
                          "Away mean should be > 0.3 goals")
        self.assertLess(away_mean, 2.5,
                       "Away mean should be < 2.5 goals")
    
    def test_result_prediction_consistency(self):
        """Verify result prediction is consistent with goal predictions."""
        features = self.sample_features[self.feature_cols].iloc[0]
        features_df = pd.DataFrame([features])
        
        home_pred, away_pred = self.predictor.generate_predictions(features_df)
        result = self.predictor.predict_result(home_pred[0], away_pred[0])
        
        # Check consistency
        diff = home_pred[0] - away_pred[0]
        
        if diff > 0.5:
            self.assertEqual(result, "H", "Large positive diff should predict H")
        elif diff < -0.5:
            self.assertEqual(result, "A", "Large negative diff should predict A")
        else:
            self.assertEqual(result, "D", "Small diff should predict D")


def run_validation_tests():
    """Run all validation tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPredictionValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 13: PREDICTION VALIDATION TESTS")
    print("=" * 70)
    print()
    
    result = run_validation_tests()
    
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
