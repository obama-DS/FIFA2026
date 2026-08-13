#!/usr/bin/env python3
"""Quick validation of Match Probability Engine."""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("QUICK PROBABILITY ENGINE TEST")
print("=" * 60)

try:
    # Import
    print("\n[1] Testing import...")
    from src.predictions.match_probabilities import MatchProbabilityEngine
    print("✓ Import successful")
    
    # Create engine
    print("\n[2] Creating engine...")
    engine = MatchProbabilityEngine(max_goals=10)
    print("✓ Engine created")
    
    # Test calculation
    print("\n[3] Testing calculation...")
    result = engine.calculate_match_probabilities(1.8, 1.3)
    print(f"✓ Calculated probabilities")
    print(f"  Home: {result['home_win_prob']:.1%}")
    print(f"  Draw: {result['draw_prob']:.1%}")
    print(f"  Away: {result['away_win_prob']:.1%}")
    
    # Test validation
    print("\n[4] Testing validation...")
    validations = engine.validate_probabilities(result)
    if all(validations.values()):
        print("✓ All validations passed")
    else:
        print(f"✗ Validations failed: {validations}")
        sys.exit(1)
    
    # Test probability sum
    print("\n[5] Testing probability sum...")
    prob_sum = result['home_win_prob'] + result['draw_prob'] + result['away_win_prob']
    if 0.99 < prob_sum < 1.01:
        print(f"✓ Probabilities sum correctly: {prob_sum:.6f}")
    else:
        print(f"✗ Probabilities don't sum to 1: {prob_sum}")
        sys.exit(1)
    
    # Test scorelines
    print("\n[6] Testing scoreline calculation...")
    scorelines = result['most_likely_scorelines']
    print(f"✓ Generated {len(scorelines)} scorelines")
    print(f"  Most likely: {scorelines[0]['scoreline']} ({scorelines[0]['probability']:.1%})")
    
    # Test error handling
    print("\n[7] Testing error handling...")
    try:
        engine.calculate_match_probabilities(-1.0, 1.0)
        print("✗ Should have raised ValueError")
        sys.exit(1)
    except ValueError:
        print("✓ Correctly rejects negative values")
    
    print("\n" + "=" * 60)
    print("✅ ALL QUICK TESTS PASSED")
    print("=" * 60)
    print("\nMatch Probability Engine is working!")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
