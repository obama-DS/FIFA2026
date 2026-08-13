#!/usr/bin/env python3
"""
Test Docker containerized API endpoints.
Verifies all endpoints work correctly inside the container.
"""

import sys
import time
import requests

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10


def wait_for_api(max_attempts=30, delay=2):
    """Wait for API to be ready."""
    print("Waiting for API to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
            if response.status_code == 200:
                print(f"✅ API ready after {attempt + 1} attempts")
                return True
        except requests.exceptions.ConnectionError:
            print(f"  Attempt {attempt + 1}/{max_attempts}...", end="\r")
            time.sleep(delay)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(delay)
    
    print(f"❌ API not ready after {max_attempts} attempts")
    return False


def test_health_endpoint():
    """Test /health endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /health ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_model_info_endpoint():
    """Test /model-info endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /model-info ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/model-info", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Model info retrieved")
            print(f"   Model Type: {data.get('model_type')}")
            print(f"   Version: {data.get('model_version')}")
            print(f"   MAE: {data.get('metrics', {}).get('val_mae_avg')}")
            print(f"   Features: {data.get('feature_count')}")
            
            # Verify models loaded correctly
            if data.get('feature_count', 0) > 0:
                print("✅ Model files loaded correctly in container")
                return True
            else:
                print("❌ Model may not have loaded correctly")
                return False
        else:
            print(f"❌ Model info failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False


def test_predict_endpoint():
    """Test /predict endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /predict ENDPOINT")
    print("=" * 60)
    
    sample_match = {
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
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=sample_match,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Prediction successful")
            print(f"   Match: {data.get('home_team')} vs {data.get('away_team')}")
            print(f"   Prediction: {data.get('predicted_home_goals')} - {data.get('predicted_away_goals')}")
            print(f"   Result: {data.get('predicted_result')}")
            
            # Verify prediction is valid
            home_goals = data.get('predicted_home_goals', -1)
            away_goals = data.get('predicted_away_goals', -1)
            result = data.get('predicted_result', '')
            
            if 0 <= home_goals <= 10 and 0 <= away_goals <= 10 and result in ['H', 'D', 'A']:
                print("✅ Prediction values are valid")
                return True
            else:
                print("❌ Prediction values are invalid")
                return False
        else:
            print(f"❌ Prediction failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False


def test_docs_endpoints():
    """Test documentation endpoints."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENTATION ENDPOINTS")
    print("=" * 60)
    
    endpoints = {
        "/docs": "Swagger UI",
        "/redoc": "ReDoc",
        "/openapi.json": "OpenAPI Schema"
    }
    
    results = {}
    
    for endpoint, name in endpoints.items():
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=TIMEOUT)
            if response.status_code == 200:
                print(f"✅ {name} accessible at {endpoint}")
                results[endpoint] = True
            else:
                print(f"❌ {name} failed with status {response.status_code}")
                results[endpoint] = False
        except Exception as e:
            print(f"❌ {name} error: {e}")
            results[endpoint] = False
    
    return all(results.values())


def main():
    """Run all Docker container tests."""
    print("🐋 DOCKER CONTAINER API TESTING")
    print("=" * 70)
    print("Testing API endpoints inside Docker container")
    print("=" * 70)
    
    # Wait for API to be ready
    if not wait_for_api():
        print("\n❌ API not responding. Check if container is running:")
        print("   docker ps")
        print("   docker logs ml-api")
        return False
    
    # Run tests
    test_results = [
        ("Health Endpoint", test_health_endpoint()),
        ("Model Info Endpoint", test_model_info_endpoint()),
        ("Predict Endpoint", test_predict_endpoint()),
        ("Documentation Endpoints", test_docs_endpoints())
    ]
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DOCKER CONTAINER TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("🎉 ALL CONTAINER TESTS PASSED")
        print("\nDocker container is working correctly!")
        print("\n✨ API Endpoints:")
        print(f"   Health:     {API_BASE_URL}/health")
        print(f"   Model Info: {API_BASE_URL}/model-info")
        print(f"   Predict:    {API_BASE_URL}/predict")
        print(f"   Swagger UI: {API_BASE_URL}/docs")
        print(f"   ReDoc:      {API_BASE_URL}/redoc")
    else:
        print(f"⚠️  {total - passed} container tests failed")
        print("\nTroubleshooting:")
        print("   1. Check container logs: docker logs ml-api")
        print("   2. Check container status: docker ps")
        print("   3. Check if models exist: docker exec ml-api ls -l models/")
        print("   4. Rebuild image: docker-build.bat")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)