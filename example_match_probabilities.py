#!/usr/bin/env python3
"""
Example usage of Match Probability Engine.

Shows how to use the probability engine in different scenarios.
"""

import os
import sys
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_probabilities import (
    MatchProbabilityEngine,
    calculate_match_probability
)


def example_1_basic_usage():
    """Example 1: Basic probability calculation."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 70)
    print()
    
    # Simple calculation using convenience function
    result = calculate_match_probability(
        expected_home_goals=1.8,
        expected_away_goals=1.3
    )
    
    print("Man City (H) 1.8 - 1.3 (A) Liverpool")
    print()
    print(f"Home win probability: {result['home_win_prob']:.1%}")
    print(f"Draw probability:     {result['draw_prob']:.1%}")
    print(f"Away win probability: {result['away_win_prob']:.1%}")
    print()
    print(f"Most likely result: {result['most_likely_result']}")
    print()


def example_2_detailed_scorelines():
    """Example 2: Get detailed scoreline probabilities."""
    print("=" * 70)
    print("EXAMPLE 2: Detailed Scorelines")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    result = engine.calculate_match_probabilities(2.3, 1.1)
    
    print("Arsenal (H) 2.3 - 1.1 (A) Tottenham")
    print()
    print("Top 5 most likely scorelines:")
    print()
    
    for i, scoreline in enumerate(result['most_likely_scorelines'][:5], 1):
        print(f"{i}. {scoreline['scoreline']:<6} {scoreline['probability']:>6.1%}")
    
    print()


def example_3_multiple_fixtures():
    """Example 3: Calculate probabilities for multiple fixtures."""
    print("=" * 70)
    print("EXAMPLE 3: Multiple Fixtures")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    fixtures = [
        {"home": "Chelsea", "away": "Brighton", "exp_h": 2.1, "exp_a": 1.4},
        {"home": "Wolves", "away": "Newcastle", "exp_h": 1.2, "exp_a": 1.8},
        {"home": "Fulham", "away": "Luton", "exp_h": 1.6, "exp_a": 1.3},
    ]
    
    for fixture in fixtures:
        result = engine.calculate_match_probabilities(
            fixture['exp_h'],
            fixture['exp_a']
        )
        
        print(f"{fixture['home']} vs {fixture['away']}")
        print(f"  Expected: {fixture['exp_h']:.1f} - {fixture['exp_a']:.1f}")
        print(f"  Home: {result['home_win_prob']:>5.1%}  "
              f"Draw: {result['draw_prob']:>5.1%}  "
              f"Away: {result['away_win_prob']:>5.1%}")
        print(f"  Prediction: {result['most_likely_result']}")
        print()


def example_4_validation():
    """Example 4: Validate calculated probabilities."""
    print("=" * 70)
    print("EXAMPLE 4: Probability Validation")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    result = engine.calculate_match_probabilities(1.5, 1.5)
    
    print("Evenly matched fixture: 1.5 - 1.5")
    print()
    
    validations = engine.validate_probabilities(result)
    
    print("Validation checks:")
    for check, passed in validations.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(validations.values()):
        print()
        print("✓ All validations passed - probabilities are mathematically correct")
    
    print()


def example_5_edge_cases():
    """Example 5: Handle edge cases."""
    print("=" * 70)
    print("EXAMPLE 5: Edge Cases")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    edge_cases = [
        ("Very low scoring", 0.3, 0.3),
        ("High scoring", 4.0, 3.5),
        ("One-sided", 3.2, 0.7),
    ]
    
    for name, exp_h, exp_a in edge_cases:
        result = engine.calculate_match_probabilities(exp_h, exp_a)
        
        print(f"{name}: {exp_h:.1f} - {exp_a:.1f}")
        print(f"  H: {result['home_win_prob']:>5.1%}  "
              f"D: {result['draw_prob']:>5.1%}  "
              f"A: {result['away_win_prob']:>5.1%}")
        print(f"  Most likely scoreline: {result['most_likely_scorelines'][0]['scoreline']}")
        print()


def example_6_error_handling():
    """Example 6: Proper error handling."""
    print("=" * 70)
    print("EXAMPLE 6: Error Handling")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    invalid_inputs = [
        ("Negative goals", -1.0, 1.5),
        ("Too high", 25.0, 1.5),
    ]
    
    for name, exp_h, exp_a in invalid_inputs:
        print(f"Testing: {name}")
        try:
            result = engine.calculate_match_probabilities(exp_h, exp_a)
            print(f"  ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"  ✓ Correctly rejected: {e}")
        print()


def main():
    """Run all examples."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "MATCH PROBABILITY ENGINE EXAMPLES" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    examples = [
        example_1_basic_usage,
        example_2_detailed_scorelines,
        example_3_multiple_fixtures,
        example_4_validation,
        example_5_edge_cases,
        example_6_error_handling,
    ]
    
    for example_func in examples:
        example_func()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print()
    print("The Match Probability Engine is ready to use.")
    print()


if __name__ == "__main__":
    main()
