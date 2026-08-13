#!/usr/bin/env python3
"""
Simple API test - tests the API components without running the server.
Verifies model loading, feature preparation, and prediction logic.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project root to path  
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def test_model_loading():
    """Test if the API can load models correctly."""
    print("=" * 60)
    print("TESTING MODEL LOADING")
    print("=" * 60)
    
    try:
        from src.models.model_loader import load_best_models
        from src.models.versioning import ModelRegistry
        
        # Load models
        models_dir = os.path.join(project_root, "models")
        home_model, away_model, metadata = load_best_models(models_dir)
        
        print("✅ Models loaded successfully")
        print(f"   Model type: {metadata.get('best_model_name', 'Unknown')}")
        print(f"   MAE: {metadata.get('val_mae_avg', 'Unknown')}")
        
        # Test registry
        registry = ModelRegistry()
        active_version = registry.get_active_version()
        
        if active_version:
            print("✅ Model registry loaded successfully")
            print(f"   Version: {active_version.version}")
            print(f"   Type: {active_version.model_type}")
        
        return True, (home_model, away_model, metadata, registry)
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False, None


def test_feature_preparation():
    """Test feature preparation for API prediction."""
    print("\n" + "=" * 60)
    print("TESTING FEATURE PREPARATION")
    print("=" * 60)
    
    try:
        # Load actual feature columns
        features_path = os.path.join(project_root, "data", "features", "match_features.csv")
        
        if os.path.exists(features_path):
            sample_df = pd.read_csv(features_path, nrows=1)
            feature_columns = [col for col in sample_df.columns if col not in [
                "match_id", "row_id", "season", "match_date", "is_fixture",
                "home_team_id", "away_team_id", "home_team_name", "away_team_name",
                "result", "home_goals", "away_goals"
            ]]
            print(f"✅ Loaded {len(feature_columns)} feature columns from dataset")
        else:
            print("⚠️  Features file not found, using fallback columns")
            feature_columns = [
                "home_gf_last3", "home_ga_last3", "away_gf_last3", "away_ga_last3"
            ]
        
        # Test feature mapping
        field_mapping = {
            "home_goals_last3": "home_gf_last3",
            "home_conceded_last3": "home_ga_last3", 
            "away_goals_last3": "away_gf_last3",
            "away_conceded_last3": "away_ga_last3",
        }
        
        # Create sample input
        sample_input = {
            "home_goals_last3": 5.0,
            "home_conceded_last3": 2.0,
            "away_goals_last3": 4.0,
            "away_conceded_last3": 3.0,
        }
        
        # Map to features
        features_dict = {}
        for schema_field, feature_col in field_mapping.items():
            if schema_field in sample_input:
                features_dict[feature_col] = sample_input[schema_field]
        
        # Fill missing features with default values
        for col in feature_columns:
            if col not in features_dict:
                features_dict[col] = 0.0
        
        # Create DataFrame
        features_df = pd.DataFrame([features_dict])
        features_df = features_df[feature_columns]
        
        print(f"✅ Feature preparation successful")
        print(f"   Input features: {len(sample_input)}")
        print(f"   Output features: {len(features_df.columns)}")
        print(f"   Sample values: {list(features_df.iloc[0][:5])}")
        
        return True, (features_df, feature_columns)
        
    except Exception as e:
        print(f"❌ Feature preparation failed: {e}")
        return False, None


def test_prediction_pipeline(models_data, feature_data):
    """Test the complete prediction pipeline."""
    print("\n" + "=" * 60)
    print("TESTING PREDICTION PIPELINE")
    print("=" * 60)
    
    try:
        home_model, away_model, metadata, registry = models_data
        features_df, feature_columns = feature_data
        
        # Make predictions
        home_pred = home_model.predict(features_df)[0]
        away_pred = away_model.predict(features_df)[0]
        
        # Clip predictions
        home_pred = np.clip(home_pred, 0, 10)
        away_pred = np.clip(away_pred, 0, 10)
        
        # Determine result
        goal_diff = home_pred - away_pred
        
        if goal_diff > 0.5:
            result = "H"  # Home win
        elif goal_diff < -0.5:
            result = "A"  # Away win
        else:
            result = "D"  # Draw
        
        print("✅ Prediction pipeline successful")
        print(f"   Predicted home goals: {home_pred:.2f}")
        print(f"   Predicted away goals: {away_pred:.2f}")
        print(f"   Predicted result: {result}")
        
        # Validate predictions
        if 0 <= home_pred <= 10 and 0 <= away_pred <= 10:
            print("✅ Predictions are in valid range [0,10]")
        else:
            print("❌ Predictions out of valid range")
            return False
        
        if result in ["H", "D", "A"]:
            print("✅ Result prediction is valid")
        else:
            print("❌ Invalid result prediction")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction pipeline failed: {e}")
        return False


def test_pydantic_schemas():
    """Test Pydantic schema validation."""
    print("\n" + "=" * 60)
    print("TESTING PYDANTIC SCHEMAS")
    print("=" * 60)
    
    try:
        from src.api.schemas import MatchFeatures, PredictionResponse
        
        # Test valid input
        valid_data = {
            "home_team_name": "Arsenal",
            "away_team_name": "Chelsea",
            "home_goals_last3": 5.0,
            "home_conceded_last3": 2.0,
            "away_goals_last3": 4.0,
            "away_conceded_last3": 3.0,
            "home_goals_last5": 8.0,
            "home_conceded_last5": 4.0,
            "away_goals_last5": 7.0,
            "away_conceded_last5": 5.0,
            "home_goals_last10": 15.0,
            "home_conceded_last10": 8.0,
            "away_goals_last10": 13.0,
            "away_conceded_last10": 10.0,
            "home_season_goals": 45.0,
            "home_season_conceded": 25.0,
            "away_season_goals": 38.0,
            "away_season_conceded": 30.0,
            "h2h_home_wins": 5,
            "h2h_away_wins": 3,
            "h2h_draws": 2
        }
        
        # Test schema validation
        match_features = MatchFeatures(**valid_data)
        print("✅ MatchFeatures validation successful")
        
        # Test response schema
        response_data = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "predicted_home_goals": 1.85,
            "predicted_away_goals": 1.42,
            "predicted_result": "H",
            "confidence": {"home_win": 0.7, "draw": 0.15, "away_win": 0.15}
        }
        
        prediction_response = PredictionResponse(**response_data)
        print("✅ PredictionResponse validation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


def main():
    """Run all API component tests."""
    print("🧪 FASTAPI COMPONENT TESTING")
    print("=" * 70)
    print("Testing individual API components without starting the server")
    print("=" * 70)
    
    # Run tests
    tests_results = []
    
    # Test 1: Model loading
    success, models_data = test_model_loading()
    tests_results.append(("Model Loading", success))
    
    if not success:
        print("\n❌ Cannot continue without models")
        return False
    
    # Test 2: Feature preparation
    success, feature_data = test_feature_preparation()
    tests_results.append(("Feature Preparation", success))
    
    if not success:
        print("\n❌ Cannot continue without feature preparation")
        return False
    
    # Test 3: Prediction pipeline
    success = test_prediction_pipeline(models_data, feature_data)
    tests_results.append(("Prediction Pipeline", success))
    
    # Test 4: Schema validation
    success = test_pydantic_schemas()
    tests_results.append(("Schema Validation", success))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPONENT TEST RESULTS")
    print("=" * 70)
    
    passed = sum(result for _, result in tests_results)
    total = len(tests_results)
    
    for test_name, result in tests_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("🎉 ALL COMPONENT TESTS PASSED")
        print("\nAPI components are working correctly!")
        print("\n💡 Next steps:")
        print("1. Start the API server: run_api.bat")
        print("2. Test endpoints: python test_api.py")
        print("3. View docs: http://localhost:8000/docs")
    else:
        print(f"⚠️  {total - passed} component tests failed")
        print("Fix the issues above before running the full API")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)