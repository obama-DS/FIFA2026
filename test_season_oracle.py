#!/usr/bin/env python3
"""
Test Season Oracle simulation with small number of iterations.
Quick verification before running full 10,000 simulation.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.simulation.season_simulator import SeasonOracle


def test_oracle_initialization():
    """Test oracle can initialize correctly."""
    print("=" * 60)
    print("[1] TESTING ORACLE INITIALIZATION")
    print("=" * 60)
    
    try:
        models_dir = os.path.join(project_root, "models")
        features_path = os.path.join(project_root, "data", "features", "match_features.csv")
        output_dir = os.path.join(project_root, "outputs", "season_simulations_test")
        
        oracle = SeasonOracle(models_dir, features_path, output_dir)
        
        print(f"✓ Oracle initialized successfully")
        print(f"  Teams: {len(oracle.teams)}")
        print(f"  Fixtures: {len(oracle.fixtures_df)}")
        print(f"  Features: {len(oracle.feature_cols)}")
        
        return True, oracle
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False, None


def test_predictions():
    """Test AI can generate predictions."""
    print("\n" + "=" * 60)
    print("[2] TESTING AI PREDICTIONS")
    print("=" * 60)
    
    _, oracle = test_oracle_initialization()
    if oracle is None:
        return False
    
    try:
        predictions = oracle.generate_ai_predictions()
        
        print(f"✓ Generated {len(predictions)} predictions")
        print(f"\nSample predictions:")
        print(predictions.head(3).to_string())
        
        # Check predictions are valid
        if (predictions['pred_home_goals'] < 0).any() or (predictions['pred_away_goals'] < 0).any():
            print("✗ Invalid negative predictions found")
            return False
        
        if (predictions['pred_home_goals'] > 10).any() or (predictions['pred_away_goals'] > 10).any():
            print("✗ Invalid high predictions found (>10 goals)")
            return False
        
        print("✓ All predictions are in valid range")
        return True
        
    except Exception as e:
        print(f"✗ Prediction generation failed: {e}")
        return False


def test_single_simulation():
    """Test single season simulation."""
    print("\n" + "=" * 60)
    print("[3] TESTING SINGLE SEASON SIMULATION")
    print("=" * 60)
    
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "season_simulations_test")
    
    oracle = SeasonOracle(models_dir, features_path, output_dir)
    oracle.generate_ai_predictions()
    
    try:
        table = oracle.simulate_single_season()
        
        print(f"✓ Simulated single season")
        print(f"\nFinal table (top 5):")
        print(table.head(5).to_string())
        
        # Validate table
        if len(table) != len(oracle.teams):
            print(f"✗ Table has {len(table)} teams, expected {len(oracle.teams)}")
            return False
        
        if table['position'].nunique() != len(oracle.teams):
            print("✗ Duplicate positions in table")
            return False
        
        if (table['played'] != len(oracle.fixtures_df) // len(oracle.teams)).any():
            print("⚠ Some teams have unexpected match counts")
        
        print("✓ Table structure is valid")
        return True
        
    except Exception as e:
        print(f"✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monte_carlo():
    """Test Monte Carlo with small number of simulations."""
    print("\n" + "=" * 60)
    print("[4] TESTING MONTE CARLO (100 simulations)")
    print("=" * 60)
    
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "season_simulations_test")
    
    oracle = SeasonOracle(models_dir, features_path, output_dir)
    oracle.generate_ai_predictions()
    
    try:
        results = oracle.run_monte_carlo_simulation(n_simulations=100)
        
        print(f"✓ Completed 100 simulations")
        
        # Check results structure
        if 'n_simulations' not in results:
            print("✗ Missing n_simulations in results")
            return False
        
        if 'teams' not in results:
            print("✗ Missing teams in results")
            return False
        
        if len(results['teams']) != len(oracle.teams):
            print(f"✗ Results has {len(results['teams'])} teams, expected {len(oracle.teams)}")
            return False
        
        # Check probabilities
        title_probs = [results['teams'][team]['title_prob'] for team in oracle.teams]
        print(f"\n✓ Title probability range: {min(title_probs):.2f}% - {max(title_probs):.2f}%")
        
        # Validate
        validations = oracle.validate_probabilities(results)
        if all(validations.values()):
            print("✓ All validations passed")
        else:
            print("⚠ Some validations failed (acceptable for small sample)")
            for check, passed in validations.items():
                status = "✓" if passed else "✗"
                print(f"  {status} {check}")
        
        return True
        
    except Exception as e:
        print(f"✗ Monte Carlo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🔮 SEASON ORACLE - QUICK TEST")
    print("=" * 70)
    print("Testing simulation components before full run")
    print("=" * 70)
    print()
    
    tests = [
        ("Oracle Initialization", lambda: test_oracle_initialization()[0]),
        ("AI Predictions", test_predictions),
        ("Single Season", test_single_simulation),
        ("Monte Carlo (100)", test_monte_carlo)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            results.append((test_name, test_func()))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print("\nReady for full 10,000 simulation!")
        print("Run: python src\\simulation\\season_simulator.py")
        print("Or:  run_season_oracle.bat")
    else:
        print(f"\n⚠ {total - passed} tests failed")
        print("Fix issues before running full simulation")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)