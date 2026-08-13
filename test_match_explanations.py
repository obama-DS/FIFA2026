#!/usr/bin/env python3
"""
Test Match Explanation System (Phase 19).

Tests explanation generation for multiple fixtures.
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_explanation import MatchExplainer


def test_explanation_system():
    """Test the complete explanation system."""
    print("=" * 70)
    print("MATCH EXPLANATION SYSTEM TEST")
    print("=" * 70)
    print()
    
    # Paths
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations_test")
    
    try:
        # Initialize
        print("[1] Initializing Match Explainer...")
        explainer = MatchExplainer(models_dir, features_path, output_dir)
        print("✓ Initialization successful\n")
        
        # Test with 5 fixtures
        print("[2] Generating explanations for 5 fixtures...")
        explanations = explainer.explain_fixtures(season='2026/27', n_fixtures=5, save=True)
        print(f"✓ Generated {len(explanations)} explanations\n")
        
        # Validate structure
        print("[3] Validating explanation structure...")
        all_valid = True
        
        for i, exp in enumerate(explanations, 1):
            required_keys = ['prediction', 'home_explanation', 'away_explanation', 'summary', 'metadata']
            missing = [k for k in required_keys if k not in exp]
            
            if missing:
                print(f"  ✗ Explanation {i} missing keys: {missing}")
                all_valid = False
            else:
                # Check prediction
                pred = exp['prediction']
                if not (0 <= pred['home_goals'] <= 10 and 0 <= pred['away_goals'] <= 10):
                    print(f"  ✗ Explanation {i}: Invalid prediction values")
                    all_valid = False
                
                # Check summary
                summary = exp['summary']
                if 'short_explanation' not in summary:
                    print(f"  ✗ Explanation {i}: Missing short_explanation")
                    all_valid = False
                
                # Check factors
                home_exp = exp['home_explanation']
                method = home_exp.get('method', 'none')
                
                if method == 'SHAP':
                    if 'supporting_factors' not in home_exp:
                        print(f"  ✗ Explanation {i}: Missing supporting_factors")
                        all_valid = False
        
        if all_valid:
            print("✓ All explanations have valid structure\n")
        else:
            print("✗ Some explanations have invalid structure\n")
            return False
        
        # Print samples
        print("[4] Sample Explanations:")
        print("-" * 70)
        
        for i in range(min(3, len(explanations))):
            exp = explanations[i]
            meta = exp['metadata']
            pred = exp['prediction']
            summary = exp['summary']
            
            print(f"\n[{i+1}] {meta['home_team']} vs {meta['away_team']}")
            print(f"    Prediction: {pred['home_goals']:.2f} - {pred['away_goals']:.2f}")
            print(f"    {summary['short_explanation']}")
            
            # Show top factor
            home_exp = exp['home_explanation']
            if home_exp.get('method') == 'SHAP' and home_exp.get('supporting_factors'):
                top = home_exp['supporting_factors'][0]
                print(f"    Top factor: {top['readable_name']} ({top['contribution']:+.3f})")
        
        print()
        print("-" * 70)
        print()
        
        # Test detailed print
        print("[5] Detailed Explanation Example:")
        print()
        explainer.print_explanation(explanations[0])
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Match Explanation System is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_explanation_system()
    sys.exit(0 if success else 1)
