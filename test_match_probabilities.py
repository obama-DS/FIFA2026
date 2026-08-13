#!/usr/bin/env python3
"""
Test Match Probability Engine with 2026/27 fixtures.

Uses actual AI predictions from trained models to verify probability calculations.
"""

import os
import sys
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_probabilities import MatchProbabilityEngine, calculate_match_probability
from src.models.model_loader import load_best_models


def test_probability_engine_standalone():
    """Test the probability engine with example values."""
    print("=" * 70)
    print("[1] TESTING PROBABILITY ENGINE - STANDALONE")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    test_cases = [
        ("Balanced match", 1.5, 1.5),
        ("Home favored", 2.3, 1.1),
        ("Away favored", 1.0, 2.0),
        ("Low scoring", 0.8, 0.7),
        ("High scoring", 3.2, 2.8),
    ]
    
    all_valid = True
    
    for name, exp_home, exp_away in test_cases:
        print(f"{name}: {exp_home:.2f} - {exp_away:.2f}")
        
        try:
            result = engine.calculate_match_probabilities(exp_home, exp_away)
            
            print(f"  Home: {result['home_win_prob']:.1%}")
            print(f"  Draw: {result['draw_prob']:.1%}")
            print(f"  Away: {result['away_win_prob']:.1%}")
            print(f"  Result: {result['most_likely_result']}")
            print(f"  Top scoreline: {result['most_likely_scorelines'][0]['scoreline']} ({result['most_likely_scorelines'][0]['probability']:.1%})")
            
            # Validate
            validations = engine.validate_probabilities(result)
            if all(validations.values()):
                print(f"  ✓ Valid")
            else:
                print(f"  ✗ Invalid: {[k for k, v in validations.items() if not v]}")
                all_valid = False
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_valid = False
        
        print()
    
    return all_valid


def test_with_real_fixtures():
    """Test probability engine with real 2026/27 fixture predictions."""
    print("=" * 70)
    print("[2] TESTING WITH REAL 2026/27 FIXTURES")
    print("=" * 70)
    print()
    
    try:
        # Load models
        print("Loading trained models...")
        models_dir = os.path.join(project_root, "models")
        home_model, away_model, metadata = load_best_models(models_dir)
        print(f"✓ Loaded: {metadata.get('best_model_name')}\n")
        
        # Load features
        print("Loading 2026/27 fixtures...")
        features_path = os.path.join(project_root, "data", "features", "match_features.csv")
        df = pd.read_csv(features_path, low_memory=False)
        
        # Filter to fixtures
        fixtures = df[(df['season'] == '2026/27') & (df['is_fixture'] == True)].copy()
        print(f"✓ Found {len(fixtures)} fixtures\n")
        
        # Get feature columns
        feature_cols = [col for col in df.columns if col not in [
            'match_id', 'row_id', 'season', 'match_date', 'is_fixture',
            'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name',
            'result', 'home_goals', 'away_goals'
        ]]
        
        # Test first 5 fixtures
        print("Testing first 5 fixtures:\n")
        
        engine = MatchProbabilityEngine(max_goals=10)
        results = []
        
        for idx in range(min(5, len(fixtures))):
            fixture = fixtures.iloc[idx]
            
            # Get predictions
            features = fixtures[feature_cols].iloc[idx:idx+1]
            pred_home = home_model.predict(features)[0]
            pred_away = away_model.predict(features)[0]
            
            # Clip to valid range
            pred_home = max(0, min(10, pred_home))
            pred_away = max(0, min(10, pred_away))
            
            print(f"[{idx+1}] {fixture['home_team_name']} vs {fixture['away_team_name']}")
            print(f"    Date: {fixture['match_date']}")
            print(f"    Expected: {pred_home:.2f} - {pred_away:.2f}")
            
            # Calculate probabilities
            try:
                probs = engine.calculate_match_probabilities(pred_home, pred_away)
                
                print(f"    Home win: {probs['home_win_prob']:.1%}")
                print(f"    Draw:     {probs['draw_prob']:.1%}")
                print(f"    Away win: {probs['away_win_prob']:.1%}")
                print(f"    Most likely: {probs['most_likely_result']}")
                
                # Show top 3 scorelines
                print(f"    Top scorelines:")
                for i in range(3):
                    sc = probs['most_likely_scorelines'][i]
                    print(f"      {sc['scoreline']}: {sc['probability']:.1%}")
                
                # Validate
                validations = engine.validate_probabilities(probs)
                if all(validations.values()):
                    print(f"    ✓ Valid")
                else:
                    print(f"    ✗ Validation failed")
                
                results.append({
                    'fixture': f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                    'valid': all(validations.values()),
                    'probs': probs
                })
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results.append({
                    'fixture': f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                    'valid': False,
                    'error': str(e)
                })
            
            print()
        
        # Summary
        valid_count = sum(1 for r in results if r['valid'])
        print(f"Valid results: {valid_count}/{len(results)}")
        
        return valid_count == len(results)
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("=" * 70)
    print("[3] TESTING EDGE CASES")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    edge_cases = [
        ("Zero goals", 0.0, 0.0, True),
        ("Very low", 0.1, 0.1, True),
        ("Very high", 5.0, 5.0, True),
        ("Asymmetric", 0.3, 3.5, True),
        ("Negative (should fail)", -1.0, 1.0, False),
        ("None (should fail)", None, 1.0, False),
        ("Too high (should fail)", 25.0, 1.0, False),
    ]
    
    passed = 0
    failed = 0
    
    for name, exp_home, exp_away, should_succeed in edge_cases:
        print(f"{name}: {exp_home} - {exp_away}")
        
        try:
            result = engine.calculate_match_probabilities(exp_home, exp_away)
            
            if should_succeed:
                validations = engine.validate_probabilities(result)
                if all(validations.values()):
                    print(f"  ✓ Passed")
                    passed += 1
                else:
                    print(f"  ✗ Failed validation")
                    failed += 1
            else:
                print(f"  ✗ Should have raised error but didn't")
                failed += 1
                
        except ValueError as e:
            if not should_succeed:
                print(f"  ✓ Correctly rejected: {e}")
                passed += 1
            else:
                print(f"  ✗ Unexpected error: {e}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            failed += 1
        
        print()
    
    print(f"Passed: {passed}, Failed: {failed}")
    return failed == 0


def test_probability_sums():
    """Test that probabilities always sum correctly."""
    print("=" * 70)
    print("[4] TESTING PROBABILITY SUMS")
    print("=" * 70)
    print()
    
    engine = MatchProbabilityEngine(max_goals=10)
    
    # Test range of expected goals
    test_points = [
        (0.5, 0.5), (1.0, 1.0), (1.5, 1.5), (2.0, 2.0),
        (0.8, 1.5), (2.3, 0.9), (3.0, 2.5), (1.2, 2.8)
    ]
    
    all_valid = True
    
    for exp_home, exp_away in test_points:
        result = engine.calculate_match_probabilities(exp_home, exp_away)
        
        prob_sum = (result['home_win_prob'] + 
                   result['draw_prob'] + 
                   result['away_win_prob'])
        
        if 0.999 < prob_sum < 1.001:
            print(f"✓ {exp_home:.1f}-{exp_away:.1f}: sum = {prob_sum:.6f}")
        else:
            print(f"✗ {exp_home:.1f}-{exp_away:.1f}: sum = {prob_sum:.6f} (INVALID)")
            all_valid = False
    
    print()
    return all_valid


def main():
    """Run all tests."""
    print("🎲 MATCH PROBABILITY ENGINE - COMPREHENSIVE TEST")
    print("=" * 70)
    print("Testing Poisson-based probability calculations")
    print("=" * 70)
    print()
    
    tests = [
        ("Standalone Engine", test_probability_engine_standalone),
        ("Real 2026/27 Fixtures", test_with_real_fixtures),
        ("Edge Cases", test_edge_cases),
        ("Probability Sums", test_probability_sums),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED")
        print("\nMatch Probability Engine is working correctly!")
        print("Ready for integration with Season Oracle and Beat the AI API.")
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed")
        print("Review errors above before proceeding.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
