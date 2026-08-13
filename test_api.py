#!/usr/bin/env python3
"""
Test script for FastAPI endpoints.
Tests /health, /model-info, and /predict endpoints.
"""

import sys
import os
import json
import requests
import time
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Test a single API endpoint."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
        
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection failed - is the API server running?"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_health_endpoint():
    """Test GET /health endpoint."""
    print("=" * 60)
    print("TESTING /health ENDPOINT")
    print("=" * 60)
    
    result = test_endpoint("GET", "/health")
    
    if not result["success"]:
        print(f"❌ Health check failed: {result['error']}")
        return False
    
    if result["status_code"] != 200:
        print(f"❌ Expected status 200, got {result['status_code']}")
        return False
    
    response = result["response"]
    required_fields = ["status", "timestamp", "version"]
    
    for field in required_fields:
        if field not in response:
            print(f"❌ Missing field: {field}")
            return False
    
    print("✅ Health check passed")
    print(f"   Status: {response['status']}")
    print(f"   Version: {response['version']}")
    print(f"   Timestamp: {response['timestamp']}")
    
    return True


def test_model_info_endpoint():
    """Test GET /model-info endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /model-info ENDPOINT")
    print("=" * 60)
    
    result = test_endpoint("GET", "/model-info")
    
    if not result["success"]:
        print(f"❌ Model info failed: {result['error']}")
        return False
    
    if result["status_code"] != 200:
        print(f"❌ Expected status 200, got {result['status_code']}")
        return False
    
    response = result["response"]
    required_fields = ["model_version", "model_type", "training_date", "metrics", "feature_count"]
    
    for field in required_fields:
        if field not in response:
            print(f"❌ Missing field: {field}")
            return False
    
    print("✅ Model info passed")
    print(f"   Version: {response['model_version']}")
    print(f"   Type: {response['model_type']}")
    print(f"   Training Date: {response['training_date']}")
    print(f"   Feature Count: {response['feature_count']}")
    
    if "metrics" in response and response["metrics"]:
        print(f"   MAE: {response['metrics'].get('val_mae_avg', 'N/A')}")
        print(f"   R²: {response['metrics'].get('val_r2_avg', 'N/A')}")
    
    return True


def test_predict_endpoint():
    """Test POST /predict endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /predict ENDPOINT")
    print("=" * 60)
    
    # Sample match data
    sample_match = {
        "home_team_name": "Arsenal",
        "away_team_name": "Chelsea",
        "home_goals_last3": 2.0,
        "home_conceded_last3": 1.0,
        "away_goals_last3": 1.5,
        "away_conceded_last3": 1.5,
        "home_goals_last5": 2.2,
        "home_conceded_last5": 1.2,
        "away_goals_last5": 1.8,
        "away_conceded_last5": 1.4,
        "home_goals_last10": 2.1,
        "home_conceded_last10": 1.3,
        "away_goals_last10": 1.7,
        "away_conceded_last10": 1.5,
        "home_season_goals": 35.0,
        "home_season_conceded": 20.0,
        "away_season_goals": 28.0,
        "away_season_conceded": 22.0,
        "h2h_home_wins": 5,
        "h2h_away_wins": 3,
        "h2h_draws": 2
    }
    
    result = test_endpoint("POST", "/predict", sample_match)
    
    if not result["success"]:
        print(f"❌ Prediction failed: {result['error']}")
        return False
    
    if result["status_code"] != 200:
        print(f"❌ Expected status 200, got {result['status_code']}")
        print(f"   Response: {result['response']}")
        return False
    
    response = result["response"]
    required_fields = ["home_team", "away_team", "predicted_home_goals", "predicted_away_goals", "predicted_result", "confidence"]
    
    for field in required_fields:
        if field not in response:
            print(f"❌ Missing field: {field}")
            return False
    
    # Validate prediction values
    home_goals = response["predicted_home_goals"]
    away_goals = response["predicted_away_goals"]
    result_pred = response["predicted_result"]
    
    if not (0 <= home_goals <= 10):
        print(f"❌ Invalid home goals prediction: {home_goals}")
        return False
    
    if not (0 <= away_goals <= 10):
        print(f"❌ Invalid away goals prediction: {away_goals}")
        return False
    
    if result_pred not in ["H", "D", "A"]:
        print(f"❌ Invalid result prediction: {result_pred}")
        return False
    
    print("✅ Prediction passed")
    print(f"   Match: {response['home_team']} vs {response['away_team']}")
    print(f"   Prediction: {home_goals} - {away_goals}")
    print(f"   Result: {result_pred}")
    
    if "confidence" in response:
        confidence = response["confidence"]
        print(f"   Confidence: H={confidence.get('home_win', 0):.2f}, D={confidence.get('draw', 0):.2f}, A={confidence.get('away_win', 0):.2f}")
    
    return True


def test_predict_validation():
    """Test prediction endpoint input validation."""
    print("\n" + "=" * 60)
    print("TESTING /predict INPUT VALIDATION")
    print("=" * 60)
    
    # Test missing required fields
    invalid_match = {
        "home_team_name": "Arsenal",
        # Missing away_team_name and other required fields
    }
    
    result = test_endpoint("POST", "/predict", invalid_match)
    
    if result["success"] and result["status_code"] == 422:
        print("✅ Input validation working (returned 422 for invalid input)")
        return True
    elif result["success"] and result["status_code"] != 200:
        print(f"✅ Input validation working (returned {result['status_code']})")
        return True
    else:
        print("❌ Input validation may not be working properly")
        return False


def test_bulk_prediction():
    """Test POST /predict/bulk endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /predict/bulk ENDPOINT")  
    print("=" * 60)
    
    # Sample bulk data
    bulk_data = {
        "matches": [
            {
                "home_team_name": "Arsenal",
                "away_team_name": "Chelsea",
                "home_goals_last3": 2.0,
                "home_conceded_last3": 1.0,
                "away_goals_last3": 1.5,
                "away_conceded_last3": 1.5,
                "home_goals_last5": 2.2,
                "home_conceded_last5": 1.2,
                "away_goals_last5": 1.8,
                "away_conceded_last5": 1.4,
                "home_goals_last10": 2.1,
                "home_conceded_last10": 1.3,
                "away_goals_last10": 1.7,
                "away_conceded_last10": 1.5,
                "home_season_goals": 35.0,
                "home_season_conceded": 20.0,
                "away_season_goals": 28.0,
                "away_season_conceded": 22.0,
                "h2h_home_wins": 5,
                "h2h_away_wins": 3,
                "h2h_draws": 2
            },
            {
                "home_team_name": "Manchester United",
                "away_team_name": "Liverpool",
                "home_goals_last3": 1.8,
                "home_conceded_last3": 1.2,
                "away_goals_last3": 2.5,
                "away_conceded_last3": 0.8,
                "home_goals_last5": 1.9,
                "home_conceded_last5": 1.1,
                "away_goals_last5": 2.3,
                "away_conceded_last5": 0.9,
                "home_goals_last10": 2.0,
                "home_conceded_last10": 1.2,
                "away_goals_last10": 2.4,
                "away_conceded_last10": 1.0,
                "home_season_goals": 32.0,
                "home_season_conceded": 25.0,
                "away_season_goals": 40.0,
                "away_season_conceded": 15.0,
                "h2h_home_wins": 3,
                "h2h_away_wins": 4,
                "h2h_draws": 3
            }
        ]
    }
    
    result = test_endpoint("POST", "/predict/bulk", bulk_data)
    
    if not result["success"]:
        print(f"❌ Bulk prediction failed: {result['error']}")
        return False
    
    if result["status_code"] != 200:
        print(f"❌ Expected status 200, got {result['status_code']}")
        return False
    
    response = result["response"]
    
    if "predictions" not in response or "summary" not in response:
        print("❌ Missing predictions or summary in bulk response")
        return False
    
    predictions = response["predictions"]
    summary = response["summary"]
    
    if len(predictions) != 2:
        print(f"❌ Expected 2 predictions, got {len(predictions)}")
        return False
    
    print("✅ Bulk prediction passed")
    print(f"   Predictions: {len(predictions)}")
    print(f"   Total matches: {summary.get('total_matches', 0)}")
    print(f"   Avg home goals: {summary.get('avg_home_goals', 0)}")
    print(f"   Avg away goals: {summary.get('avg_away_goals', 0)}")
    
    return True


def check_server_running():
    """Check if the API server is running."""
    print("Checking if API server is running...")
    
    result = test_endpoint("GET", "/health")
    
    if result["success"]:
        print("✅ API server is running")
        return True
    else:
        print("❌ API server is not running")
        print("   Please start the server with: python src/api/main.py")
        return False


def main():
    """Run all API tests."""
    print("🧪 FASTAPI ENDPOINT TESTING")
    print("=" * 70)
    
    # Check if server is running
    if not check_server_running():
        print("\n⚠️  Start the API server first:")
        print("   cd c:\\Users\\Administrator\\Desktop\\FIFA2026")
        print("   python src\\api\\main.py")
        return False
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run all tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Model Info", test_model_info_endpoint),
        ("Single Prediction", test_predict_endpoint),
        ("Input Validation", test_predict_validation),
        ("Bulk Prediction", test_bulk_prediction)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - FastAPI backend is working correctly!")
    else:
        print("⚠️  Some tests failed - check the output above for details")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)