#!/usr/bin/env python3
"""
Test Phase 12 versioning system integration.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.versioning import ModelRegistry, ModelVersion

def test_versioning_integration():
    """Test versioning system completeness."""
    print("=" * 60)
    print("TESTING PHASE 12: MODEL VERSIONING INTEGRATION")
    print("=" * 60)
    print()
    
    # Test 1: Registry loads
    print("[1] Testing registry loading...")
    registry = ModelRegistry()
    versions = registry.list_versions()
    print(f"  ✓ Found {len(versions)} versions")
    
    # Test 2: Active version exists
    print("[2] Testing active version...")
    active = registry.get_active_version()
    if active:
        print(f"  ✓ Active version: {active.version}")
        print(f"  ✓ Model type: {active.model_type}")
        print(f"  ✓ MAE: {active.metrics['val_mae_avg']:.4f}")
    else:
        print("  ✗ No active version found")
        return False
    
    # Test 3: Files exist
    print("[3] Testing model files...")
    model_files = active.model_files
    for name, path in model_files.items():
        full_path = os.path.join("models", os.path.basename(path))
        if os.path.exists(full_path):
            print(f"  ✓ {name}: {path}")
        else:
            print(f"  ✗ Missing: {path}")
            return False
    
    # Test 4: Version comparison
    print("[4] Testing version operations...")
    try:
        best_version = registry.get_best_version("val_mae_avg", lower_is_better=True)
        print(f"  ✓ Best version by MAE: {best_version.version}")
    except Exception as e:
        print(f"  ✗ Version comparison failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ PHASE 12 VERSIONING: ALL TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_versioning_integration()
    sys.exit(0 if success else 1)