#!/usr/bin/env python3
"""
Example: Using Match Explanation System.

Shows how to generate and use explainable predictions.
"""

import os
import sys
import warnings
import pandas as pd

warnings.filterwarnings('ignore')

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.predictions.match_explanation import MatchExplainer


def example_1_single_match():
    """Example 1: Explain a single match."""
    print("=" * 70)
    print("EXAMPLE 1: Single Match Explanation")
    print("=" * 70)
    print()
    
    # Initialize
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations_example")
    
    explainer = MatchExplainer(models_dir, features_path, output_dir)
    
    # Initialize SHAP
    explainer._initialize_shap_explainers()
    
    # Get a fixture
    fixtures = explainer.features_df[
        (explainer.features_df['season'] == '2026/27') & 
        (explainer.features_df['is_fixture'] == True)
    ].head(1)
    
    fixture = fixtures.iloc[0]
    
    # Prepare data
    metadata = {
        'home_team': fixture['home_team_name'],
        'away_team': fixture['away_team_name'],
        'match_date': str(fixture['match_date'])
    }
    
    features = fixture[explainer.feature_cols].to_frame().T
    
    # Generate explanation
    explanation = explainer.explain_prediction(features, metadata)
    
    # Print
    explainer.print_explanation(explanation)


def example_2_multiple_fixtures():
    """Example 2: Explain multiple fixtures."""
    print("=" * 70)
    print("EXAMPLE 2: Multiple Fixtures")
    print("=" * 70)
    print()
    
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations_example")
    
    explainer = MatchExplainer(models_dir, features_path, output_dir)
    
    # Generate explanations for 5 fixtures
    explanations = explainer.explain_fixtures(season='2026/27', n_fixtures=5, save=False)
    
    print(f"Generated {len(explanations)} explanations\n")
    
    # Show summaries
    for i, exp in enumerate(explanations, 1):
        meta = exp['metadata']
        summary = exp['summary']
        
        print(f"[{i}] {meta['home_team']} vs {meta['away_team']}")
        print(f"    {summary['short_explanation']}")
        print()


def example_3_analyzing_factors():
    """Example 3: Analyze supporting/opposing factors."""
    print("=" * 70)
    print("EXAMPLE 3: Analyzing Prediction Factors")
    print("=" * 70)
    print()
    
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations_example")
    
    explainer = MatchExplainer(models_dir, features_path, output_dir)
    explainer._initialize_shap_explainers()
    
    # Get a fixture
    fixtures = explainer.features_df[
        (explainer.features_df['season'] == '2026/27') & 
        (explainer.features_df['is_fixture'] == True)
    ].head(1)
    
    fixture = fixtures.iloc[0]
    metadata = {
        'home_team': fixture['home_team_name'],
        'away_team': fixture['away_team_name']
    }
    features = fixture[explainer.feature_cols].to_frame().T
    
    explanation = explainer.explain_prediction(features, metadata)
    
    print(f"{metadata['home_team']} vs {metadata['away_team']}")
    print()
    
    # Analyze home factors
    home_exp = explanation['home_explanation']
    if home_exp.get('method') == 'SHAP':
        print("HOME GOALS ANALYSIS:")
        print()
        print("Supporting factors (increase prediction):")
        for i, factor in enumerate(home_exp['supporting_factors'][:3], 1):
            print(f"  {i}. {factor['readable_name']}")
            print(f"     Contribution: {factor['contribution']:+.3f}")
            print(f"     Value: {factor['value']}")
            print()
        
        print("Opposing factors (decrease prediction):")
        for i, factor in enumerate(home_exp['opposing_factors'][:3], 1):
            print(f"  {i}. {factor['readable_name']}")
            print(f"     Contribution: {factor['contribution']:+.3f}")
            print(f"     Value: {factor['value']}")
            print()


def main():
    """Run all examples."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "MATCH EXPLANATION EXAMPLES" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    examples = [
        example_1_single_match,
        example_2_multiple_fixtures,
        example_3_analyzing_factors
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Example failed: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
