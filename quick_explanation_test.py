#!/usr/bin/env python3
"""Quick test of Match Explanation System."""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("QUICK EXPLANATION SYSTEM TEST")
print("=" * 60)

try:
    # Test import
    print("\n[1] Testing import...")
    from src.predictions.match_explanation import MatchExplainer
    print("✓ Import successful")
    
    # Test initialization
    print("\n[2] Testing initialization...")
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations_test")
    
    explainer = MatchExplainer(models_dir, features_path, output_dir)
    print("✓ Initialization successful")
    
    # Test explanation generation
    print("\n[3] Generating test explanation...")
    explanations = explainer.explain_fixtures(season='2026/27', n_fixtures=1, save=False)
    
    if len(explanations) > 0:
        print("✓ Generated explanation")
        
        # Check structure
        exp = explanations[0]
        required = ['prediction', 'home_explanation', 'away_explanation', 'summary']
        missing = [k for k in required if k not in exp]
        
        if missing:
            print(f"✗ Missing keys: {missing}")
            sys.exit(1)
        
        print("✓ Valid structure")
        
        # Show summary
        print("\n[4] Sample explanation:")
        print(f"  Prediction: {exp['prediction']['home_goals']:.2f} - {exp['prediction']['away_goals']:.2f}")
        print(f"  {exp['summary']['short_explanation']}")
        
        print("\n" + "=" * 60)
        print("✅ QUICK TEST PASSED")
        print("=" * 60)
        print("\nMatch Explanation System is working!")
        
    else:
        print("✗ No explanations generated")
        sys.exit(1)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
