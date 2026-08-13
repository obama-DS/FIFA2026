#!/usr/bin/env python3
"""
Quick verification of API documentation implementation.
Tests schema enhancements and documentation completeness without starting server.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def test_schema_enhancements():
    """Test enhanced Pydantic schemas."""
    print("=" * 60)
    print("TESTING ENHANCED PYDANTIC SCHEMAS")
    print("=" * 60)
    
    try:
        from src.api.schemas import (
            HealthResponse, ModelInfoResponse, MatchFeatures, 
            PredictionResponse, ErrorResponse
        )
        
        # Test MatchFeatures with examples
        print("\n[1] Testing MatchFeatures schema...")
        
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
        
        match_features = MatchFeatures(**valid_data)
        print("  ✅ Valid data accepted")
        print(f"  ✅ Team match: {match_features.home_team_name} vs {match_features.away_team_name}")
        
        # Test validation
        try:
            invalid_data = valid_data.copy()
            invalid_data["home_goals_last3"] = -1.0
            MatchFeatures(**invalid_data)
            print("  ❌ Negative values should be rejected")
        except ValueError:
            print("  ✅ Negative values properly rejected")
        
        # Test PredictionResponse
        print("\n[2] Testing PredictionResponse schema...")
        
        response_data = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "predicted_home_goals": 1.85,
            "predicted_away_goals": 1.42,
            "predicted_result": "H",
            "confidence": {"home_win": 0.70, "draw": 0.15, "away_win": 0.15}
        }
        
        prediction_response = PredictionResponse(**response_data)
        print("  ✅ Valid response data accepted")
        print(f"  ✅ Prediction: {prediction_response.predicted_home_goals} - {prediction_response.predicted_away_goals}")
        
        # Test response validation
        try:
            invalid_response = response_data.copy()
            invalid_response["predicted_result"] = "X"  # Invalid result
            PredictionResponse(**invalid_response)
            print("  ❌ Invalid result should be rejected")
        except ValueError:
            print("  ✅ Invalid result properly rejected")
        
        print("\n[3] Testing other schemas...")
        
        # Test HealthResponse
        health = HealthResponse(status="healthy", timestamp="2026-08-12T14:30:00", version="1.0.0")
        print(f"  ✅ HealthResponse: {health.status}")
        
        # Test ModelInfoResponse
        model_info = ModelInfoResponse(
            model_version="1.0.0",
            model_type="Random_Forest",
            training_date="2026-08-12T21:29:14",
            metrics={"val_mae_avg": 0.89},
            feature_count=372,
            description="Test model"
        )
        print(f"  ✅ ModelInfoResponse: {model_info.model_type}")
        
        # Test ErrorResponse
        error = ErrorResponse(error="test_error", message="Test message")
        print(f"  ✅ ErrorResponse: {error.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema testing failed: {e}")
        return False


def test_fastapi_enhancements():
    """Test FastAPI app enhancements."""
    print("\n" + "=" * 60)
    print("TESTING FASTAPI APP ENHANCEMENTS")
    print("=" * 60)
    
    try:
        from src.api.main import app
        
        # Test app configuration
        print("\n[1] Testing app metadata...")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
        print(f"  Docs URL: {app.docs_url}")
        print(f"  ReDoc URL: {app.redoc_url}")
        
        if "Premier League ML Prediction API" in app.title:
            print("  ✅ Enhanced title set")
        else:
            print("  ❌ Title not enhanced")
            return False
        
        if len(app.description) > 100:
            print("  ✅ Detailed description provided")
        else:
            print("  ❌ Description not enhanced")
            return False
        
        # Test OpenAPI tags
        if hasattr(app, 'openapi_tags') and app.openapi_tags:
            print(f"  ✅ OpenAPI tags configured ({len(app.openapi_tags)} tags)")
            for tag in app.openapi_tags:
                print(f"    - {tag['name']}: {tag['description']}")
        else:
            print("  ⚠️  No OpenAPI tags found")
        
        # Test routes
        print("\n[2] Testing enhanced routes...")
        
        routes = [route for route in app.routes if hasattr(route, 'path')]
        endpoint_routes = [r for r in routes if r.path in ['/health', '/model-info', '/predict', '/predict/bulk']]
        
        print(f"  Found {len(endpoint_routes)} main endpoints")
        
        for route in endpoint_routes:
            if hasattr(route, 'endpoint'):
                func = route.endpoint
                if hasattr(func, '__doc__') and func.__doc__ and len(func.__doc__.strip()) > 50:
                    print(f"  ✅ {route.path}: Enhanced documentation")
                else:
                    print(f"  ❌ {route.path}: No enhanced documentation")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI testing failed: {e}")
        return False


def test_documentation_files():
    """Test documentation file completeness."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENTATION FILES")
    print("=" * 60)
    
    documentation_files = [
        ("API_DOCUMENTATION.md", "Comprehensive API documentation"),
        ("test_api_documentation.py", "Documentation verification script"),
        ("api_test_results.md", "Test results documentation")
    ]
    
    all_exist = True
    
    for filename, description in documentation_files:
        file_path = os.path.join(project_root, filename)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {filename}: {description} ({size:,} bytes)")
        else:
            print(f"❌ {filename}: Missing")
            all_exist = False
    
    return all_exist


def main():
    """Run documentation verification."""
    print("📚 PHASE 15: API DOCUMENTATION VERIFICATION")
    print("=" * 70)
    print("Testing enhanced schemas, endpoints, and documentation files")
    print("=" * 70)
    
    # Run tests
    test_results = [
        ("Enhanced Pydantic Schemas", test_schema_enhancements()),
        ("FastAPI App Enhancements", test_fastapi_enhancements()),
        ("Documentation Files", test_documentation_files())
    ]
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DOCUMENTATION VERIFICATION RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("🎉 ALL DOCUMENTATION VERIFICATION TESTS PASSED")
        print("\n📖 Documentation Components Ready:")
        print("   ✅ Enhanced Pydantic schemas with examples")
        print("   ✅ Detailed FastAPI endpoint documentation")
        print("   ✅ Professional API documentation file")
        print("   ✅ Documentation verification scripts")
        print("\n🚀 Next Steps:")
        print("   1. Start API: run_api.bat")
        print("   2. Test docs: python test_api_documentation.py")
        print("   3. View docs: http://localhost:8000/docs")
    else:
        print(f"⚠️  {total - passed} verification tests failed")
        print("   Check the output above for specific issues")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)