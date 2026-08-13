#!/usr/bin/env python3
"""
Test edge cases for Match Probability Engine.
Specifically tests mathematical edge cases.
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_probabilities import MatchProbabilityEngine
import numpy as np

print("=" * 70)
print("EDGE CASE TESTING - MATHEMATICAL VALIDATION")
print("=" * 70)
print()

engine = MatchProbabilityEngine(max_goals=10)

# Test 1: Zero goals expected for both teams
print("[1] Zero goals expected (0.0 - 0.0)")
try:
    result = engine.calculate_match_probabilities(0.0, 0.0)
    print(f"    Home: {result['home_win_prob']:.4f}")
    print(f"    Draw: {result['draw_prob']:.4f}")
    print(f"    Away: {result['away_win_prob']:.4f}")
    print(f"    Most likely: {result['most_likely_result']}")
    print(f"    Most likely scoreline: {result['most_likely_scorelines'][0]['scoreline']}")
    
    # With lambda=0, Poisson gives P(X=0)=1, so 0-0 should be 100%
    if result['most_likely_scorelines'][0]['scoreline'] == '0-0':
        print("    ✓ Correct: 0-0 is most likely")
    else:
        print("    ✗ Error: 0-0 should be most likely")
    
    if result['draw_prob'] > 0.99:
        print("    ✓ Correct: Draw probability is ~1.0")
    else:
        print(f"    ✗ Error: Draw prob should be ~1.0, got {result['draw_prob']}")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

print()

# Test 2: Very small non-zero values
print("[2] Very small values (0.01 - 0.01)")
try:
    result = engine.calculate_match_probabilities(0.01, 0.01)
    print(f"    Home: {result['home_win_prob']:.4f}")
    print(f"    Draw: {result['draw_prob']:.4f}")
    print(f"    Away: {result['away_win_prob']:.4f}")
    print(f"    Most likely scoreline: {result['most_likely_scorelines'][0]['scoreline']}")
    
    # Should still be mostly 0-0
    if result['most_likely_scorelines'][0]['scoreline'] == '0-0':
        print("    ✓ Correct: 0-0 is most likely")
    else:
        print("    ✗ Error: 0-0 should be most likely")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

print()

# Test 3: Equal high expected goals
print("[3] Equal high goals (3.0 - 3.0)")
try:
    result = engine.calculate_match_probabilities(3.0, 3.0)
    print(f"    Home: {result['home_win_prob']:.4f}")
    print(f"    Draw: {result['draw_prob']:.4f}")
    print(f"    Away: {result['away_win_prob']:.4f}")
    print(f"    Most likely: {result['most_likely_result']}")
    
    # Should be symmetric
    if abs(result['home_win_prob'] - result['away_win_prob']) < 0.001:
        print("    ✓ Correct: Symmetric probabilities")
    else:
        print(f"    ✗ Error: Should be symmetric")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

print()

# Test 4: Asymmetric - home heavily favored
print("[4] Home heavily favored (4.0 - 0.5)")
try:
    result = engine.calculate_match_probabilities(4.0, 0.5)
    print(f"    Home: {result['home_win_prob']:.4f}")
    print(f"    Draw: {result['draw_prob']:.4f}")
    print(f"    Away: {result['away_win_prob']:.4f}")
    print(f"    Most likely: {result['most_likely_result']}")
    
    if result['home_win_prob'] > 0.7:
        print("    ✓ Correct: Home win probability is high")
    else:
        print(f"    ✗ Error: Home should have high win probability")
    
    if result['most_likely_result'] == 'H':
        print("    ✓ Correct: Home is most likely result")
    else:
        print(f"    ✗ Error: Home should be most likely")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

print()

# Test 5: Probability sum validation across range
print("[5] Probability sum validation (10 random scenarios)")
test_scenarios = [
    (0.5, 1.2), (1.0, 1.0), (1.5, 0.8), (2.3, 1.9),
    (0.3, 2.5), (3.5, 2.0), (1.8, 1.8), (0.7, 0.9),
    (2.8, 1.3), (1.2, 2.4)
]

all_valid = True
for exp_h, exp_a in test_scenarios:
    result = engine.calculate_match_probabilities(exp_h, exp_a)
    prob_sum = result['home_win_prob'] + result['draw_prob'] + result['away_win_prob']
    
    if 0.999 < prob_sum < 1.001:
        print(f"    ✓ {exp_h:.1f}-{exp_a:.1f}: sum={prob_sum:.6f}")
    else:
        print(f"    ✗ {exp_h:.1f}-{exp_a:.1f}: sum={prob_sum:.6f} INVALID")
        all_valid = False

if all_valid:
    print("    ✓ All probability sums are valid")

print()

# Test 6: Most likely result consistency
print("[6] Most likely result consistency")
test_cases = [
    (2.5, 0.8, 'H'),  # Clear home win
    (0.8, 2.5, 'A'),  # Clear away win
    (1.5, 1.5, 'D'),  # Equal - draw most likely for low scoring
]

consistent = True
for exp_h, exp_a, expected_result in test_cases:
    result = engine.calculate_match_probabilities(exp_h, exp_a)
    probs = {
        'H': result['home_win_prob'],
        'D': result['draw_prob'],
        'A': result['away_win_prob']
    }
    
    actual_max = max(probs.values())
    predicted = result['most_likely_result']
    
    if probs[predicted] == actual_max:
        print(f"    ✓ {exp_h:.1f}-{exp_a:.1f}: Predicted {predicted}, correct")
    else:
        print(f"    ✗ {exp_h:.1f}-{exp_a:.1f}: Predicted {predicted}, but {max(probs, key=probs.get)} has highest prob")
        consistent = False

if consistent:
    print("    ✓ Most likely result is always consistent with probabilities")

print()

# Test 7: Scoreline probability distribution
print("[7] Scoreline distribution validation")
result = engine.calculate_match_probabilities(1.5, 1.2)
scoreline_sum = np.sum(result['scoreline_distribution'])

print(f"    Scoreline distribution sum: {scoreline_sum:.6f}")
if 0.999 < scoreline_sum < 1.001:
    print("    ✓ Scoreline distribution sums to 1.0")
else:
    print(f"    ✗ Scoreline distribution sum invalid: {scoreline_sum}")

# Check if scoreline probs match outcome probs
manual_home = 0
manual_draw = 0
manual_away = 0

for i in range(result['scoreline_distribution'].shape[0]):
    for j in range(result['scoreline_distribution'].shape[1]):
        prob = result['scoreline_distribution'][i, j]
        if i > j:
            manual_home += prob
        elif i == j:
            manual_draw += prob
        else:
            manual_away += prob

diff_h = abs(manual_home - result['home_win_prob'])
diff_d = abs(manual_draw - result['draw_prob'])
diff_a = abs(manual_away - result['away_win_prob'])

if diff_h < 0.0001 and diff_d < 0.0001 and diff_a < 0.0001:
    print("    ✓ Outcome probabilities match scoreline distribution")
else:
    print(f"    ✗ Mismatch: H={diff_h:.6f}, D={diff_d:.6f}, A={diff_a:.6f}")

print()

# Test 8: Sorting of scorelines
print("[8] Scoreline sorting validation")
result = engine.calculate_match_probabilities(1.8, 1.4)
scorelines = result['most_likely_scorelines']

is_sorted = True
for i in range(len(scorelines) - 1):
    if scorelines[i]['probability'] < scorelines[i+1]['probability']:
        print(f"    ✗ Not sorted: {scorelines[i]['scoreline']} ({scorelines[i]['probability']:.4f}) < {scorelines[i+1]['scoreline']} ({scorelines[i+1]['probability']:.4f})")
        is_sorted = False
        break

if is_sorted:
    print("    ✓ Scorelines are correctly sorted by probability")
    print(f"    Top 3: {scorelines[0]['scoreline']} ({scorelines[0]['probability']:.1%}), "
          f"{scorelines[1]['scoreline']} ({scorelines[1]['probability']:.1%}), "
          f"{scorelines[2]['scoreline']} ({scorelines[2]['probability']:.1%})")

print()

print("=" * 70)
print("✓ EDGE CASE TESTING COMPLETE")
print("=" * 70)
