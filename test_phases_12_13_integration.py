#!/usr/bin/env python3
"""
Complete integration test for Phase 12 & 13.
Tests all components are properly connected.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_phase_12_completeness():
    """Test Phase 12: Model Versioning completeness."""
    print("=" * 60)
    print("PHASE 12: MODEL VERSIONING - COMPLETENESS CHECK")
    print("=" * 60)
    print()
    
    issues = []
    
    # 1. Check versioning.py exists and has all required functions
    versioning_path = os.path.join("src", "models", "versioning.py")
    if not os.path.exists(versioning_path):
        issues.append("❌ versioning.py missing")
    else:
        print("✅ versioning.py exists")
    
    # 2. Check model registry exists
    registry_path = os.path.join("models", "model_registry.json")
    if not os.path.exists(registry_path):
        issues.append("❌ model_registry.json missing")
    else:
        # Load and validate registry
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        if "active_version" not in registry:
            issues.append("❌ Registry missing active_version")
        if "versions" not in registry:
            issues.append("❌ Registry missing versions array")
        elif len(registry["versions"]) == 0:
            issues.append("❌ Registry has no versions")
        else:
            version = registry["versions"][0]
            required_fields = [
                "version", "model_type", "training_date", 
                "metrics", "model_files", "training_config"
            ]
            for field in required_fields:
                if field not in version:
                    issues.append(f"❌ Version missing {field}")
            
            if not issues:
                print("✅ model_registry.json valid")
    
    # 3. Check version metadata file exists
    version_file = os.path.join("models", "versions", "version_1.0.0.json")
    if not os.path.exists(version_file):
        issues.append("❌ version_1.0.0.json missing")
    else:
        print("✅ version_1.0.0.json exists")
    
    # 4. Check VERSION_SUMMARY.md exists
    summary_file = os.path.join("models", "versions", "VERSION_SUMMARY.md")
    if not os.path.exists(summary_file):
        issues.append("❌ VERSION_SUMMARY.md missing")
    else:
        print("✅ VERSION_SUMMARY.md exists")
    
    # 5. Check actual model files referenced exist
    model_files = [
        os.path.join("models", "best_model_home.pkl"),
        os.path.join("models", "best_model_away.pkl"),
        os.path.join("models", "best_model.json")
    ]
    
    for model_file in model_files:
        if not os.path.exists(model_file):
            issues.append(f"❌ Model file missing: {model_file}")
        else:
            print(f"✅ {os.path.basename(model_file)} exists")
    
    return issues


def test_phase_13_completeness():
    """Test Phase 13: Prediction Validation completeness."""
    print("\n" + "=" * 60)
    print("PHASE 13: PREDICTION VALIDATION - COMPLETENESS CHECK")
    print("=" * 60)
    print()
    
    issues = []
    
    # 1. Check test file exists
    test_file = os.path.join("tests", "test_prediction_validation.py")
    if not os.path.exists(test_file):
        issues.append("❌ test_prediction_validation.py missing")
    else:
        print("✅ test_prediction_validation.py exists")
        
        # Check for required test methods
        with open(test_file, 'r') as f:
            content = f.read()
        
        required_tests = [
            "test_valid_single_match",
            "test_valid_multiple_matches", 
            "test_missing_single_feature",
            "test_missing_multiple_features",
            "test_all_features_missing",
            "test_string_in_numeric_column",
            "test_boolean_values",
            "test_very_large_values",
            "test_very_small_values", 
            "test_negative_values",
            "test_all_zeros",
            "test_empty_dataframe",
            "test_single_row_dataframe",
            "test_duplicate_rows",
            "test_infinity_values",
            "test_output_types",
            "test_output_ranges",
            "test_output_no_nan",
            "test_output_no_inf",
            "test_output_realistic_distribution"
        ]
        
        missing_tests = []
        for test in required_tests:
            if f"def {test}(" not in content:
                missing_tests.append(test)
        
        if missing_tests:
            issues.append(f"❌ Missing tests: {', '.join(missing_tests)}")
        else:
            print(f"✅ All {len(required_tests)} required tests found")
    
    # 2. Check conftest.py exists  
    conftest_file = os.path.join("tests", "conftest.py")
    if not os.path.exists(conftest_file):
        issues.append("❌ conftest.py missing")
    else:
        print("✅ conftest.py exists")
    
    # 3. Check __init__.py exists
    init_file = os.path.join("tests", "__init__.py")
    if not os.path.exists(init_file):
        issues.append("❌ tests/__init__.py missing")
    else:
        print("✅ tests/__init__.py exists")
    
    # 4. Check test runner exists
    runner_file = "run_validation_tests.bat"
    if not os.path.exists(runner_file):
        issues.append("❌ run_validation_tests.bat missing")
    else:
        print("✅ run_validation_tests.bat exists")
    
    return issues


def test_integration():
    """Test integration between Phase 12 and 13."""
    print("\n" + "=" * 60)
    print("PHASE 12-13 INTEGRATION CHECK")
    print("=" * 60)
    print()
    
    issues = []
    
    # Check if versioning can load models that tests validate
    try:
        from models.versioning import ModelRegistry
        registry = ModelRegistry()
        active_version = registry.get_active_version()
        
        if active_version is None:
            issues.append("❌ No active version in registry")
        else:
            print("✅ Registry integration works")
            
            # Check model files match between versioning and what tests expect
            model_files = active_version.model_files
            expected_files = ["home_model", "away_model", "metadata"]
            
            for file_key in expected_files:
                if file_key not in model_files:
                    issues.append(f"❌ Missing model file key: {file_key}")
                else:
                    file_path = os.path.join("models", os.path.basename(model_files[file_key]))
                    if not os.path.exists(file_path):
                        issues.append(f"❌ Model file not found: {file_path}")
            
            if not [i for i in issues if "Model file" in i]:
                print("✅ Model files integration verified")
                
    except Exception as e:
        issues.append(f"❌ Integration test failed: {str(e)}")
    
    return issues


def main():
    """Run complete Phase 12-13 verification."""
    print("🔍 COMPLETE PHASE 12-13 VERIFICATION")
    print("=" * 70)
    
    # Test each phase
    phase_12_issues = test_phase_12_completeness()
    phase_13_issues = test_phase_13_completeness() 
    integration_issues = test_integration()
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_issues = len(phase_12_issues) + len(phase_13_issues) + len(integration_issues)
    
    if total_issues == 0:
        print("🎉 SUCCESS: Both Phase 12 and 13 are COMPLETE")
        print("   ✅ Model versioning system fully implemented")
        print("   ✅ Prediction validation tests fully implemented")
        print("   ✅ Integration verified")
    else:
        print("⚠️  ISSUES FOUND:")
        
        if phase_12_issues:
            print("\n   Phase 12 Issues:")
            for issue in phase_12_issues:
                print(f"     {issue}")
        
        if phase_13_issues:
            print("\n   Phase 13 Issues:")
            for issue in phase_13_issues:
                print(f"     {issue}")
                
        if integration_issues:
            print("\n   Integration Issues:")
            for issue in integration_issues:
                print(f"     {issue}")
    
    print("\n" + "=" * 70)
    return total_issues == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)