#!/usr/bin/env python3
"""Quick test of Season Oracle - minimal version."""

import os
import sys
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("QUICK ORACLE TEST")
print("=" * 60)

try:
    # Test import
    print("\n[1] Testing import...")
    from src.simulation.season_simulator import SeasonOracle
    print("✓ Import successful")
    
    # Test initialization
    print("\n[2] Testing initialization...")
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "season_simulations_test")
    
    oracle = SeasonOracle(models_dir, features_path, output_dir)
    print(f"✓ Oracle initialized")
    print(f"  - Teams: {len(oracle.teams)}")
    print(f"  - Fixtures: {len(oracle.fixtures_df)}")
    
    # Test predictions
    print("\n[3] Testing AI predictions...")
    preds = oracle.generate_ai_predictions()
    print(f"✓ Generated {len(preds)} predictions")
    print(f"\nFirst prediction:")
    print(f"  {preds.iloc[0]['home_team']} vs {preds.iloc[0]['away_team']}")
    print(f"  Predicted: {preds.iloc[0]['pred_home_goals']:.2f} - {preds.iloc[0]['pred_away_goals']:.2f}")
    print(f"  Result: {preds.iloc[0]['predicted_result']}")
    
    # Test single simulation
    print("\n[4] Testing single season simulation...")
    table = oracle.simulate_single_season()
    print(f"✓ Simulated season")
    print(f"\nTop 3:")
    for i in range(3):
        row = table.iloc[i]
        print(f"  {row['position']}. {row['team']} - {row['points']} pts")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nPhase 17 is working correctly!")
    print("Ready for full simulation.")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
