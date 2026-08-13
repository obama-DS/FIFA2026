#!/usr/bin/env python3
"""
Final verification script for Phase 18.
Performs all critical checks.
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 70)
print("PHASE 18 FINAL VERIFICATION")
print("=" * 70)
print()

all_passed = True

# Test 1: Import check
print("[1] Import Check")
try:
    from src.predictions.match_probabilities import (
        MatchProbabilityEngine,
        calculate_match_probability
    )
    print("    ✓ Imports successful")
except Exception as e:
    print(f"    ✗ Import failed: {e}")
    all_passed = False

print()

# Test 2: Basic functionality
print("[2] Basic Functionality")
try:
    from src.predictions.match_probabilities import MatchProbabilityEngine
    
    engine = MatchProbabilityEngine(max_goals=10)
    result = engine.calculate_match_probabilities(1.8, 1.3)
    
    # Check return structure
    required_keys = [
        'expected_home_goals', 'expected_away_goals',
        'home_win_prob', 'draw_prob', 'away_win_prob',
        'most_likely_result', 'scoreline_distribution',
        'most_likely_scorelines'
    ]
    
    missing = [k for k in required_keys if k not in result]
    if missing:
        print(f"    ✗ Missing keys: {missing}")
        all_passed = False
    else:
        print("    ✓ All required keys present")
    
except Exception as e:
    print(f"    ✗ Basic test failed: {e}")
    all_passed = False

print()

# Test 3: Probability sum
print("[3] Probability Sum Validation")
try:
    result = engine.calculate_match_probabilities(2.0, 1.5)
    prob_sum = (result['home_win_prob'] + 
               result['draw_prob'] + 
               result['away_win_prob'])
    
    if 0.999 < prob_sum < 1.001:
        print(f"    ✓ Probabilities sum correctly: {prob_sum:.6f}")
    else:
        print(f"    ✗ Invalid sum: {prob_sum}")
        all_passed = False
        
except Exception as e:
    print(f"    ✗ Test failed: {e}")
    all_passed = False

print()

# Test 4: Input validation
print("[4] Input Validation")
try:
    # Should reject negative
    try:
        engine.calculate_match_probabilities(-1.0, 1.0)
        print("    ✗ Failed to reject negative value")
        all_passed = False
    except ValueError:
        print("    ✓ Correctly rejects negative values")
    
    # Should reject None
    try:
        engine.calculate_match_probabilities(None, 1.0)
        print("    ✗ Failed to reject None")
        all_passed = False
    except ValueError:
        print("    ✓ Correctly rejects None values")
        
except Exception as e:
    print(f"    ✗ Validation test failed: {e}")
    all_passed = False

print()

# Test 5: Edge case - zero goals
print("[5] Edge Case: Zero Expected Goals")
try:
    result = engine.calculate_match_probabilities(0.0, 0.0)
    
    # Should predict 0-0 draw
    if result['most_likely_scorelines'][0]['scoreline'] == '0-0':
        print("    ✓ Correctly predicts 0-0")
    else:
        print(f"    ✗ Incorrect prediction: {result['most_likely_scorelines'][0]['scoreline']}")
        all_passed = False
    
    # Draw should be very likely
    if result['draw_prob'] > 0.9:
        print(f"    ✓ High draw probability: {result['draw_prob']:.1%}")
    else:
        print(f"    ✗ Low draw probability: {result['draw_prob']:.1%}")
        all_passed = False
        
except Exception as e:
    print(f"    ✗ Edge case test failed: {e}")
    all_passed = False

print()

# Test 6: Most likely result logic
print("[6] Most Likely Result Logic")
try:
    test_cases = [
        (3.0, 1.0, 'H'),  # Clear home win
        (1.0, 3.0, 'A'),  # Clear away win
        (1.5, 1.5, 'D'),  # Equal - draw likely
    ]
    
    logic_correct = True
    for exp_h, exp_a, expected_result in test_cases:
        result = engine.calculate_match_probabilities(exp_h, exp_a)
        probs = {
            'H': result['home_win_prob'],
            'D': result['draw_prob'],
            'A': result['away_win_prob']
        }
        
        max_prob_result = max(probs, key=probs.get)
        actual_result = result['most_likely_result']
        
        if actual_result != max_prob_result:
            print(f"    ✗ {exp_h:.1f}-{exp_a:.1f}: Predicted {actual_result}, "
                  f"but {max_prob_result} has highest probability")
            logic_correct = False
            all_passed = False
    
    if logic_correct:
        print("    ✓ Most likely result always matches highest probability")
        
except Exception as e:
    print(f"    ✗ Logic test failed: {e}")
    all_passed = False

print()

# Test 7: Scoreline sorting
print("[7] Scoreline Sorting")
try:
    result = engine.calculate_match_probabilities(1.8, 1.4)
    scorelines = result['most_likely_scorelines']
    
    is_sorted = True
    for i in range(len(scorelines) - 1):
        if scorelines[i]['probability'] < scorelines[i+1]['probability']:
            is_sorted = False
            break
    
    if is_sorted:
        print("    ✓ Scorelines sorted correctly")
    else:
        print("    ✗ Scorelines not sorted")
        all_passed = False
        
except Exception as e:
    print(f"    ✗ Sorting test failed: {e}")
    all_passed = False

print()

# Test 8: Validate method
print("[8] Validation Method")
try:
    result = engine.calculate_match_probabilities(1.6, 1.2)
    validations = engine.validate_probabilities(result)
    
    if all(validations.values()):
        print("    ✓ All validation checks pass")
    else:
        failed = [k for k, v in validations.items() if not v]
        print(f"    ✗ Failed validations: {failed}")
        all_passed = False
        
except Exception as e:
    print(f"    ✗ Validation method test failed: {e}")
    all_passed = False

print()

# Final result
print("=" * 70)
if all_passed:
    print("✅ PHASE 18 VERIFICATION PASSED")
    print("=" * 70)
    print()
    print("Match Probability Engine is working correctly!")
    print("All critical functionality verified.")
    print("Ready for integration with Season Oracle and Beat the AI API.")
    sys.exit(0)
else:
    print("❌ PHASE 18 VERIFICATION FAILED")
    print("=" * 70)
    print()
    print("Some tests failed. Review errors above.")
    sys.exit(1)
