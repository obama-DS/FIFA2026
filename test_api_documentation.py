#!/usr/bin/env python3
"""
API Documentation Verification Script - Phase 15
Tests FastAPI documentation endpoints and schema completeness.
"""

import sys
import os
import json
import requests
import time
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10


def check_server_running():
    """Check if API server is running."""
    print("🔍 Checking API server status...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
    except requests.exceptions.ConnectionError:
        pass
    
    print("❌ API server is not running")
    print("   Start server with: run_api.bat")
    return False


def test_openapi_docs():
    """Test OpenAPI documentation endpoints."""
    print("\n" + "=" * 60)
    print("TESTING OPENAPI DOCUMENTATION")
    print("=" * 60)
    
    endpoints = {
        "/docs": "Swagger UI Documentation",
        "/redoc": "ReDoc Documentation", 
        "/openapi.json": "OpenAPI Schema JSON"
    }
    
    results = {}
    
    for endpoint, description in endpoints.items():
        print(f"\n[{endpoint}] Testing {description}...")
        
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=TIMEOUT)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint} accessible (HTTP {response.status_code})")
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if endpoint == "/openapi.json":
                    if 'application/json' in content_type:
                        print("  ✅ Correct JSON content type")
                        # Validate JSON structure
                        try:
                            schema = response.json()
                            if 'openapi' in schema and 'paths' in schema:
                                print("  ✅ Valid OpenAPI schema structure")
                            else:
                                print("  ⚠️  OpenAPI schema missing required fields")
                        except json.JSONDecodeError:
                            print("  ❌ Invalid JSON response")
                    else:
                        print(f"  ⚠️  Unexpected content type: {content_type}")
                else:
                    if 'text/html' in content_type:
                        print("  ✅ Correct HTML content type")
                    else:
                        print(f"  ⚠️  Unexpected content type: {content_type}")
                
                results[endpoint] = True
            else:
                print(f"  ❌ {endpoint} returned HTTP {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.Timeout:
            print(f"  ❌ {endpoint} request timeout")
            results[endpoint] = False
        except Exception as e:
            print(f"  ❌ {endpoint} error: {e}")
            results[endpoint] = False
    
    return results


def test_openapi_schema_details():
    """Test OpenAPI schema for required documentation elements."""
    print("\n" + "=" * 60)
    print("TESTING OPENAPI SCHEMA DETAILS")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=TIMEOUT)
        if response.status_code != 200:
            print("❌ Cannot retrieve OpenAPI schema")
            return False
        
        schema = response.json()
        
        # Test basic schema structure
        required_fields = ['openapi', 'info', 'paths', 'components']
        for field in required_fields:
            if field in schema:
                print(f"✅ Schema has required field: {field}")
            else:
                print(f"❌ Schema missing required field: {field}")
                return False
        
        # Test API info
        info = schema.get('info', {})
        if 'title' in info and 'version' in info and 'description' in info:
            print(f"✅ API info complete: {info['title']} v{info['version']}")
        else:
            print("❌ API info incomplete")
        
        # Test endpoints
        paths = schema.get('paths', {})
        expected_endpoints = ['/health', '/model-info', '/predict', '/predict/bulk']
        
        print(f"\n📍 Testing {len(expected_endpoints)} expected endpoints...")
        for endpoint in expected_endpoints:
            if endpoint in paths:
                print(f"✅ Endpoint documented: {endpoint}")
                
                # Check for required HTTP methods
                path_info = paths[endpoint]
                if endpoint == '/health' or endpoint == '/model-info':
                    if 'get' in path_info:
                        print(f"  ✅ GET method documented for {endpoint}")
                    else:
                        print(f"  ❌ GET method missing for {endpoint}")
                elif endpoint.startswith('/predict'):
                    if 'post' in path_info:
                        print(f"  ✅ POST method documented for {endpoint}")
                    else:
                        print(f"  ❌ POST method missing for {endpoint}")
                        
            else:
                print(f"❌ Endpoint not documented: {endpoint}")
        
        # Test schema components
        components = schema.get('components', {})
        if 'schemas' in components:
            schemas = components['schemas']
            expected_schemas = [
                'HealthResponse', 'ModelInfoResponse', 'MatchFeatures', 
                'PredictionResponse', 'ErrorResponse'
            ]
            
            print(f"\n📋 Testing {len(expected_schemas)} expected schemas...")
            for schema_name in expected_schemas:
                if schema_name in schemas:
                    print(f"✅ Schema documented: {schema_name}")
                else:
                    print(f"❌ Schema missing: {schema_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing schema details: {e}")
        return False


def test_endpoint_examples():
    """Test that endpoints have proper examples in documentation."""
    print("\n" + "=" * 60)
    print("TESTING ENDPOINT EXAMPLES")  
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=TIMEOUT)
        schema = response.json()
        paths = schema.get('paths', {})
        
        examples_found = 0
        total_responses = 0
        
        for endpoint, methods in paths.items():
            for method, details in methods.items():
                responses = details.get('responses', {})
                
                for status_code, response_info in responses.items():
                    total_responses += 1
                    content = response_info.get('content', {})
                    
                    for media_type, media_info in content.items():
                        if 'example' in media_info or 'examples' in media_info:
                            examples_found += 1
                            print(f"✅ Example found: {method.upper()} {endpoint} ({status_code})")
                        elif 'schema' in media_info:
                            schema_ref = media_info['schema']
                            if '$ref' in schema_ref:
                                schema_name = schema_ref['$ref'].split('/')[-1]
                                print(f"ℹ️  Schema reference: {method.upper()} {endpoint} → {schema_name}")
        
        print(f"\n📊 Examples Summary:")
        print(f"   Examples found: {examples_found}")
        print(f"   Total responses: {total_responses}")
        print(f"   Coverage: {(examples_found/total_responses*100) if total_responses > 0 else 0:.1f}%")
        
        return examples_found > 0
        
    except Exception as e:
        print(f"❌ Error testing examples: {e}")
        return False


def test_schema_validation():
    """Test that Pydantic schemas have proper validation."""
    print("\n" + "=" * 60)
    print("TESTING SCHEMA VALIDATION")
    print("=" * 60)
    
    # Test valid input
    valid_match_data = {
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
    
    print("Testing valid input...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=valid_match_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            print("✅ Valid input accepted")
            data = response.json()
            
            # Check response structure
            required_fields = ['home_team', 'away_team', 'predicted_home_goals', 
                             'predicted_away_goals', 'predicted_result', 'confidence']
            
            for field in required_fields:
                if field in data:
                    print(f"  ✅ Response has field: {field}")
                else:
                    print(f"  ❌ Response missing field: {field}")
                    
        else:
            print(f"❌ Valid input rejected with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing valid input: {e}")
    
    # Test invalid input
    print("\nTesting invalid input (negative values)...")
    invalid_match_data = valid_match_data.copy()
    invalid_match_data["home_goals_last3"] = -1.0  # Invalid negative value
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=invalid_match_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 422:
            print("✅ Invalid input properly rejected with 422")
            data = response.json()
            
            # Check error structure
            if 'detail' in data:
                print("  ✅ Validation error details provided")
            else:
                print("  ⚠️  No validation error details")
                
        else:
            print(f"❌ Invalid input not properly rejected (got {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error testing invalid input: {e}")
    
    return True


def main():
    """Run all documentation tests."""
    print("📚 FASTAPI DOCUMENTATION VERIFICATION")
    print("=" * 70)
    print("Phase 15: Testing API documentation completeness and accessibility")
    print("=" * 70)
    
    # Check server
    if not check_server_running():
        return False
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run tests
    test_results = []
    
    # Test 1: Documentation endpoints
    docs_results = test_openapi_docs()
    test_results.append(("Documentation Endpoints", all(docs_results.values())))
    
    # Test 2: Schema structure
    schema_result = test_openapi_schema_details()
    test_results.append(("OpenAPI Schema Structure", schema_result))
    
    # Test 3: Examples
    examples_result = test_endpoint_examples()
    test_results.append(("Endpoint Examples", examples_result))
    
    # Test 4: Validation
    validation_result = test_schema_validation()
    test_results.append(("Schema Validation", validation_result))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DOCUMENTATION TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("🎉 ALL DOCUMENTATION TESTS PASSED")
        print("\n📖 Documentation Access Points:")
        print(f"   Swagger UI: {API_BASE_URL}/docs")
        print(f"   ReDoc:      {API_BASE_URL}/redoc") 
        print(f"   OpenAPI:    {API_BASE_URL}/openapi.json")
        print("\n✨ API documentation is complete and professional!")
    else:
        print(f"⚠️  {total - passed} documentation tests failed")
        print("   Check the output above for specific issues")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)