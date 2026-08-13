#!/usr/bin/env python3
"""
Complete validation runner for Phase 12-13.
Runs all checks and tests in proper sequence.
"""

import sys
import os
import subprocess

def run_phase_12_validation():
    """Run Phase 12 versioning validation."""
    print("=" * 60)
    print("🔧 PHASE 12: MODEL VERSIONING VALIDATION")
    print("=" * 60)
    
    # Run versioning integration test
    try:
        result = subprocess.run([
            sys.executable, "test_versioning.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Versioning system integration: PASSED")
        else:
            print("❌ Versioning system integration: FAILED")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Versioning validation error: {e}")
        return False
    
    return True

def run_phase_13_validation():
    """Run Phase 13 prediction validation."""
    print("\n" + "=" * 60)  
    print("🧪 PHASE 13: PREDICTION VALIDATION TESTS")
    print("=" * 60)
    
    # Check if we can import the test module
    try:
        sys.path.insert(0, 'tests')
        from test_prediction_validation import run_validation_tests
        
        print("Running 20 prediction validation tests...")
        result = run_validation_tests()
        
        if result.wasSuccessful():
            print("✅ All prediction validation tests: PASSED")
            return True
        else:
            print("❌ Some prediction validation tests: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        return False

def run_complete_integration():
    """Run complete integration verification."""
    print("\n" + "=" * 60)
    print("🔗 COMPLETE INTEGRATION VERIFICATION") 
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "test_phases_12_13_integration.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Complete integration: PASSED")
            return True
        else:
            print("❌ Integration issues found")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def main():
    """Run complete Phase 12-13 validation."""
    print("🚀 COMPLETE PHASE 12-13 VALIDATION")
    print("=" * 70)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    results = []
    
    # Run all validations
    results.append(("Phase 12 Versioning", run_phase_12_validation()))
    results.append(("Phase 13 Testing", run_phase_13_validation()))  
    results.append(("Integration", run_complete_integration()))
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("🎉 SUCCESS: Phase 12 & 13 COMPLETELY FINISHED")
        print("   • Model versioning system: 100% complete")
        print("   • Prediction validation tests: 100% complete")
        print("   • All integration verified")
    else:
        print("⚠️  Some components need attention")
    
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)