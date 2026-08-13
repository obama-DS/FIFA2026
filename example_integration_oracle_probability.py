#!/usr/bin/env python3
"""
Example: Integration of Match Probability Engine with Season Oracle.

Shows how to use the probability engine alongside Oracle predictions
to get detailed match probabilities.
"""

import os
import sys
import warnings
import pandas as pd

warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_probabilities import MatchProbabilityEngine
from src.models.model_loader import load_best_models


def example_integration():
    """
    Show how Season Oracle predictions can be enhanced with
    detailed probability analysis.
    """
    print("=" * 70)
    print("INTEGRATION EXAMPLE: Season Oracle + Probability Engine")
    print("=" * 70)
    print()
    
    # Load models (same as Season Oracle does)
    print("[1] Loading trained models...")
    models_dir = os.path.join(project_root, "models")
    home_model, away_model, metadata = load_best_models(models_dir)
    print(f"✓ Models loaded: {metadata.get('best_model_name')}")
    print()
    
    # Load features
    print("[2] Loading 2026/27 fixtures...")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    df = pd.read_csv(features_path, low_memory=False)
    
    fixtures = df[(df['season'] == '2026/27') & (df['is_fixture'] == True)].copy()
    print(f"✓ Found {len(fixtures)} fixtures")
    print()
    
    # Get feature columns
    feature_cols = [col for col in df.columns if col not in [
        'match_id', 'row_id', 'season', 'match_date', 'is_fixture',
        'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name',
        'result', 'home_goals', 'away_goals'
    ]]
    
    # Initialize probability engine
    print("[3] Initializing Match Probability Engine...")
    prob_engine = MatchProbabilityEngine(max_goals=10)
    print("✓ Engine ready")
    print()
    
    # Analyze first 3 fixtures with full probability breakdown
    print("[4] Analyzing fixtures with detailed probabilities...")
    print()
    
    for idx in range(min(3, len(fixtures))):
        fixture = fixtures.iloc[idx]
        
        # Get model predictions (same as Oracle)
        features = fixtures[feature_cols].iloc[idx:idx+1]
        exp_home = max(0, min(10, home_model.predict(features)[0]))
        exp_away = max(0, min(10, away_model.predict(features)[0]))
        
        print("-" * 70)
        print(f"Fixture: {fixture['home_team_name']} vs {fixture['away_team_name']}")
        print(f"Date: {fixture['match_date']}")
        print(f"Expected goals: {exp_home:.2f} - {exp_away:.2f}")
        print()
        
        # Calculate detailed probabilities
        probs = prob_engine.calculate_match_probabilities(exp_home, exp_away)
        
        print("Match Outcome Probabilities:")
        print(f"  Home win: {probs['home_win_prob']:.1%}")
        print(f"  Draw:     {probs['draw_prob']:.1%}")
        print(f"  Away win: {probs['away_win_prob']:.1%}")
        print()
        
        print("Most likely result:", probs['most_likely_result'])
        print()
        
        print("Top 5 most likely scorelines:")
        for i, scoreline in enumerate(probs['most_likely_scorelines'][:5], 1):
            print(f"  {i}. {scoreline['scoreline']:<6} {scoreline['probability']:>6.1%}")
        print()
        
        # Validate
        validations = prob_engine.validate_probabilities(probs)
        if all(validations.values()):
            print("✓ Probabilities validated")
        else:
            print("✗ Validation issues:", [k for k, v in validations.items() if not v])
        print()
    
    print("=" * 70)
    print("INTEGRATION EXAMPLE COMPLETE")
    print("=" * 70)
    print()
    print("Key Points:")
    print("• Season Oracle generates expected goals using trained models")
    print("• Match Probability Engine converts these into full probability distributions")
    print("• Both use Poisson distributions for scoreline modeling")
    print("• Oracle simulates outcomes; Probability Engine calculates exact probabilities")
    print("• Together they provide predictions + confidence/uncertainty measures")
    print()
    print("Use Cases:")
    print("• Season Oracle: Simulate 10,000 seasons → championship probabilities")
    print("• Probability Engine: Per-match win/draw/loss probabilities for API")
    print("• Combined: Show users match predictions with confidence levels")
    print()


if __name__ == "__main__":
    example_integration()
