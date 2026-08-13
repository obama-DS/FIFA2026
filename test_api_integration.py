#!/usr/bin/env python3
"""
Quick integration test for FastAPI with actual model files.
Tests if the API can load models and respond correctly.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_model_loading():
    """Test if models can be loaded for the API."""
    print("Testing model loading for FastAPI...")
    
    try:
        from src.models.model_loader import load_best_models
        from src.models.versioning import ModelRegistry
        
        # Test model loading
        models_dir = os.path.join(project_root, "models")
        home_model, away_model, metadata = load_best_models(models_dir)
        
        print(f"✅ Models loaded successfully")
        print(f"   Model type: {metadata.get('best_model_name', 'Unknown')}")
        print(f"   MAE: {metadata.get('val_mae_avg', 'Unknown')}")
        
        # Test registry loading
        registry = ModelRegistry()
        active_version = registry.get_active_version()
        
        if active_version:
            print(f"✅ Registry loaded successfully")
            print(f"   Active version: {active_version.version}")
            print(f"   Model type: {active_version.model_type}")
        else:
            print("⚠️  No active version in registry")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

def test_prediction_pipeline():
    """Test the prediction pipeline components."""
    print("\nTesting prediction pipeline...")
    
    try:
        import pandas as pd
        import numpy as np
        from src.models.model_loader import load_best_models
        
        # Load models
        models_dir = os.path.join(project_root, "models")
        home_model, away_model, metadata = load_best_models(models_dir)
        
        # Create sample features (simplified)
        sample_features = {f"feature_{i}": np.random.random() for i in range(20)}
        features_df = pd.DataFrame([sample_features])
        
        # Test predictions
        home_pred = home_model.predict(features_df)[0]
        away_pred = away_model.predict(features_df)[0]
        
        home_pred = np.clip(home_pred, 0, 10)
        away_pred = np.clip(away_pred, 0, 10)
        
        print(f"✅ Prediction pipeline works")
        print(f"   Sample prediction: {home_pred:.2f} - {away_pred:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction pipeline failed: {e}")
        return False

def test_fastapi_imports():
    """Test if FastAPI dependencies can be imported."""
    print("\nTesting FastAPI imports...")
    
    try:
        import fastapi
        import uvicorn
        import pydantic
        
        print("✅ FastAPI dependencies available")
        print(f"   FastAPI version: {fastapi.__version__}")
        print(f"   Pydantic version: {pydantic.__version__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ FastAPI dependencies missing: {e}")
        print("   Install with: pip install fastapi uvicorn pydantic")
        return False

def main():
    """Run integration tests."""
    print("🔧 FASTAPI INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("Model Loading", test_model_loading),
        ("Prediction Pipeline", test_prediction_pipeline),
        ("FastAPI Imports", test_fastapi_imports)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<35} {status}")
    
    print("=" * 50)
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("   FastAPI backend is ready to run")
        print("\n💡 To start the API:")
        print("   run_api.bat")
        print("   # or")
        print("   python src\\api\\main.py")
    else:
        print("⚠️  Some integration tests failed")
        print("   Fix the issues above before starting the API")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)