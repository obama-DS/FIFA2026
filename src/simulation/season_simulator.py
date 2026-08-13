# =============================================================================
# season_simulator.py
# =============================================================================
# Phase 17: Season Oracle Engine
#
# Monte Carlo simulation of 2026/27 Premier League season
# Uses trained models to generate predictions and simulate outcomes
# =============================================================================

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict
import json
import warnings

# Suppress sklearn warnings about feature names
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from src.models.model_loader import load_best_models


# Fixed random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


class SeasonOracle:
    """
    2026/27 Premier League Season Oracle Engine.
    
    Generates AI predictions for all fixtures and simulates complete seasons
    using Monte Carlo method with Poisson-distributed scorelines.
    """
    
    def __init__(self, models_dir: str, features_path: str, output_dir: str):
        """
        Initialize Season Oracle.
        
        Args:
            models_dir: Path to trained models directory
            features_path: Path to match features CSV
            output_dir: Path to save simulation outputs
        """
        self.models_dir = models_dir
        self.features_path = features_path
        self.output_dir = output_dir
        
        # Load models
        print("Loading trained models...")
        self.home_model, self.away_model, self.metadata = load_best_models(models_dir)
        print(f"✓ Models loaded: {self.metadata.get('best_model_name')}")
        
        # Load features
        print("Loading match features...")
        self.features_df = pd.read_csv(features_path, low_memory=False)
        print(f"✓ Features loaded: {len(self.features_df)} matches")
        
        # Filter to 2026/27 fixtures only
        self.fixtures_df = self.features_df[
            (self.features_df['season'] == '2026/27') & 
            (self.features_df['is_fixture'] == True)
        ].copy()
        
        print(f"✓ Found {len(self.fixtures_df)} fixtures for 2026/27 season")
        
        # Get all teams
        home_teams = set(self.fixtures_df['home_team_name'].unique())
        away_teams = set(self.fixtures_df['away_team_name'].unique())
        self.teams = sorted(list(home_teams | away_teams))
        print(f"✓ Found {len(self.teams)} teams")
        
        # Feature columns (exclude metadata columns)
        self.feature_cols = [col for col in self.features_df.columns if col not in [
            'match_id', 'row_id', 'season', 'match_date', 'is_fixture',
            'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name',
            'result', 'home_goals', 'away_goals'
        ]]
        
        # Storage for AI predictions
        self.ai_predictions = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_ai_predictions(self):
        """
        Generate AI predictions for all 2026/27 fixtures.
        
        Returns:
            DataFrame with match details and predicted goals
        """
        print("\nGenerating AI predictions for all fixtures...")
        
        predictions = []
        
        # Prepare all features at once for better performance
        features_df = self.fixtures_df[self.feature_cols].copy()
        
        # Make predictions in batch
        pred_home_all = self.home_model.predict(features_df)
        pred_away_all = self.away_model.predict(features_df)
        
        for idx, (_, row) in enumerate(self.fixtures_df.iterrows()):
            # Get predictions
            pred_home = np.clip(pred_home_all[idx], 0, 10)
            pred_away = np.clip(pred_away_all[idx], 0, 10)
            
            # Determine most likely result
            if pred_home - pred_away > 0.5:
                predicted_result = 'H'
            elif pred_away - pred_home > 0.5:
                predicted_result = 'A'
            else:
                predicted_result = 'D'
            
            predictions.append({
                'match_id': row['match_id'],
                'home_team': row['home_team_name'],
                'away_team': row['away_team_name'],
                'match_date': row['match_date'],
                'pred_home_goals': round(pred_home, 2),
                'pred_away_goals': round(pred_away, 2),
                'predicted_result': predicted_result
            })
        
        self.ai_predictions = pd.DataFrame(predictions)
        
        print(f"✓ Generated {len(self.ai_predictions)} AI predictions")
        
        return self.ai_predictions
    
    def sample_scoreline_from_poisson(self, lambda_home: float, lambda_away: float) -> Tuple[int, int]:
        """
        Sample a scoreline from Poisson distributions.
        
        Args:
            lambda_home: Expected home goals
            lambda_away: Expected away goals
            
        Returns:
            Tuple of (home_goals, away_goals)
        """
        home_goals = np.random.poisson(lambda_home)
        away_goals = np.random.poisson(lambda_away)
        
        # Cap at 10 goals (extremely rare but possible)
        home_goals = min(home_goals, 10)
        away_goals = min(away_goals, 10)
        
        return home_goals, away_goals
    
    def simulate_single_season(self) -> pd.DataFrame:
        """
        Simulate a complete season using Poisson sampling.
        
        Returns:
            DataFrame with final league table
        """
        # Initialize standings
        standings = {team: {
            'played': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'gf': 0,
            'ga': 0,
            'gd': 0,
            'points': 0
        } for team in self.teams}
        
        # Simulate each match
        for _, pred in self.ai_predictions.iterrows():
            # Sample scoreline from Poisson
            home_goals, away_goals = self.sample_scoreline_from_poisson(
                pred['pred_home_goals'],
                pred['pred_away_goals']
            )
            
            home_team = pred['home_team']
            away_team = pred['away_team']
            
            # Update standings
            standings[home_team]['played'] += 1
            standings[away_team]['played'] += 1
            
            standings[home_team]['gf'] += home_goals
            standings[home_team]['ga'] += away_goals
            standings[away_team]['gf'] += away_goals
            standings[away_team]['ga'] += home_goals
            
            if home_goals > away_goals:
                # Home win
                standings[home_team]['wins'] += 1
                standings[home_team]['points'] += 3
                standings[away_team]['losses'] += 1
            elif away_goals > home_goals:
                # Away win
                standings[away_team]['wins'] += 1
                standings[away_team]['points'] += 3
                standings[home_team]['losses'] += 1
            else:
                # Draw
                standings[home_team]['draws'] += 1
                standings[away_team]['draws'] += 1
                standings[home_team]['points'] += 1
                standings[away_team]['points'] += 1
            
            # Update goal difference
            standings[home_team]['gd'] = standings[home_team]['gf'] - standings[home_team]['ga']
            standings[away_team]['gd'] = standings[away_team]['gf'] - standings[away_team]['ga']
        
        # Convert to DataFrame
        table = pd.DataFrame.from_dict(standings, orient='index')
        table['team'] = table.index
        
        # Sort by points, then goal difference, then goals for
        table = table.sort_values(
            by=['points', 'gd', 'gf'],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        table['position'] = range(1, len(table) + 1)
        
        return table[['position', 'team', 'played', 'wins', 'draws', 'losses', 
                     'gf', 'ga', 'gd', 'points']]
    
    def run_monte_carlo_simulation(self, n_simulations: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation of complete seasons.
        
        Args:
            n_simulations: Number of seasons to simulate
            
        Returns:
            Dictionary with simulation results and probabilities
        """
        print(f"\nRunning {n_simulations:,} season simulations...")
        print("This may take a few minutes...")
        
        # Storage for results
        position_counts = {team: defaultdict(int) for team in self.teams}
        points_history = {team: [] for team in self.teams}
        
        # Counters for specific outcomes
        title_wins = defaultdict(int)
        top4_finishes = defaultdict(int)
        top6_finishes = defaultdict(int)
        relegation_finishes = defaultdict(int)
        
        # Track most common final table
        final_tables = []
        
        # Run simulations
        for i in range(n_simulations):
            if (i + 1) % 1000 == 0:
                print(f"  Completed {i + 1:,} / {n_simulations:,} simulations")
            
            # Simulate season
            table = self.simulate_single_season()
            
            # Store final table for mode calculation
            final_tables.append(table.copy())
            
            # Record results
            for _, row in table.iterrows():
                team = row['team']
                position = row['position']
                points = row['points']
                
                position_counts[team][position] += 1
                points_history[team].append(points)
                
                # Count specific outcomes
                if position == 1:
                    title_wins[team] += 1
                if position <= 4:
                    top4_finishes[team] += 1
                if position <= 6:
                    top6_finishes[team] += 1
                if position >= 18:
                    relegation_finishes[team] += 1
        
        print(f"✓ Completed {n_simulations:,} simulations")
        
        # Calculate probabilities and statistics
        results = {
            'n_simulations': n_simulations,
            'teams': {}
        }
        
        for team in self.teams:
            results['teams'][team] = {
                'title_prob': title_wins[team] / n_simulations * 100,
                'top4_prob': top4_finishes[team] / n_simulations * 100,
                'top6_prob': top6_finishes[team] / n_simulations * 100,
                'relegation_prob': relegation_finishes[team] / n_simulations * 100,
                'expected_points': np.mean(points_history[team]),
                'expected_position': np.mean([pos for pos, count in position_counts[team].items() 
                                             for _ in range(count)]),
                'median_position': np.median([pos for pos, count in position_counts[team].items() 
                                              for _ in range(count)]),
                'position_distribution': dict(position_counts[team])
            }
        
        # Find most likely final table (mode)
        # Use most common position for each team
        most_likely_table = []
        for team in self.teams:
            most_common_pos = max(position_counts[team].items(), key=lambda x: x[1])[0]
            expected_points = results['teams'][team]['expected_points']
            
            most_likely_table.append({
                'position': most_common_pos,
                'team': team,
                'expected_points': round(expected_points, 1)
            })
        
        # Sort by most common position
        most_likely_table = sorted(most_likely_table, key=lambda x: x['position'])
        results['most_likely_table'] = most_likely_table
        
        return results
    
    def validate_probabilities(self, results: Dict) -> Dict[str, bool]:
        """
        Validate simulation results.
        
        Args:
            results: Simulation results dictionary
            
        Returns:
            Dictionary of validation checks
        """
        print("\nValidating simulation results...")
        
        validations = {}
        
        # Check: All title probabilities sum to ~100%
        title_probs = [results['teams'][team]['title_prob'] for team in self.teams]
        title_sum = sum(title_probs)
        validations['title_probs_sum'] = 99 < title_sum < 101
        print(f"  Title probabilities sum: {title_sum:.2f}% {'✓' if validations['title_probs_sum'] else '✗'}")
        
        # Check: All relegation probabilities are reasonable
        relegation_probs = [results['teams'][team]['relegation_prob'] for team in self.teams]
        relegation_sum = sum(relegation_probs)
        validations['relegation_probs_sum'] = 290 < relegation_sum < 310  # Should be ~300% (3 teams)
        print(f"  Relegation probabilities sum: {relegation_sum:.2f}% {'✓' if validations['relegation_probs_sum'] else '✗'}")
        
        # Check: Expected positions are in valid range
        expected_positions = [results['teams'][team]['expected_position'] for team in self.teams]
        validations['positions_valid'] = all(1 <= pos <= 20 for pos in expected_positions)
        print(f"  Expected positions in range: {'✓' if validations['positions_valid'] else '✗'}")
        
        # Check: Most likely table has all teams
        most_likely_teams = [row['team'] for row in results['most_likely_table']]
        validations['all_teams_present'] = set(most_likely_teams) == set(self.teams)
        print(f"  All teams in most likely table: {'✓' if validations['all_teams_present'] else '✗'}")
        
        # Check: Most likely table positions are 1-20
        most_likely_positions = [row['position'] for row in results['most_likely_table']]
        validations['positions_unique'] = len(most_likely_positions) == len(set(most_likely_positions))
        print(f"  All positions unique: {'✓' if validations['positions_unique'] else '✗'}")
        
        return validations
    
    def save_results(self, results: Dict, validations: Dict):
        """
        Save simulation results to files.
        
        Args:
            results: Simulation results
            validations: Validation results
        """
        print("\nSaving simulation results...")
        
        # Save AI predictions
        predictions_path = os.path.join(self.output_dir, 'ai_fixture_predictions.csv')
        self.ai_predictions.to_csv(predictions_path, index=False)
        print(f"✓ Saved AI predictions: {predictions_path}")
        
        # Save full results as JSON
        results_path = os.path.join(self.output_dir, 'season_simulation_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✓ Saved full results: {results_path}")
        
        # Save probabilities summary as CSV
        prob_summary = []
        for team in sorted(self.teams):
            team_data = results['teams'][team]
            prob_summary.append({
                'team': team,
                'title_prob_%': round(team_data['title_prob'], 2),
                'top4_prob_%': round(team_data['top4_prob'], 2),
                'top6_prob_%': round(team_data['top6_prob'], 2),
                'relegation_prob_%': round(team_data['relegation_prob'], 2),
                'expected_points': round(team_data['expected_points'], 1),
                'expected_position': round(team_data['expected_position'], 1)
            })
        
        prob_df = pd.DataFrame(prob_summary)
        prob_path = os.path.join(self.output_dir, 'team_probabilities.csv')
        prob_df.to_csv(prob_path, index=False)
        print(f"✓ Saved probabilities: {prob_path}")
        
        # Save most likely table
        likely_table_df = pd.DataFrame(results['most_likely_table'])
        table_path = os.path.join(self.output_dir, 'most_likely_final_table.csv')
        likely_table_df.to_csv(table_path, index=False)
        print(f"✓ Saved most likely table: {table_path}")
        
        # Save validation results
        validation_path = os.path.join(self.output_dir, 'validation_results.json')
        with open(validation_path, 'w') as f:
            json.dump(validations, f, indent=2)
        print(f"✓ Saved validation results: {validation_path}")
    
    def print_summary(self, results: Dict):
        """
        Print simulation summary.
        
        Args:
            results: Simulation results
        """
        print("\n" + "=" * 70)
        print("SEASON ORACLE SUMMARY")
        print("=" * 70)
        
        print(f"\nSimulations: {results['n_simulations']:,}")
        print(f"Fixtures: {len(self.ai_predictions)}")
        print(f"Teams: {len(self.teams)}")
        
        # Top title contenders
        print("\n" + "-" * 70)
        print("TITLE RACE")
        print("-" * 70)
        
        title_probs = [(team, results['teams'][team]['title_prob']) 
                       for team in self.teams]
        title_probs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (team, prob) in enumerate(title_probs[:5], 1):
            print(f"{i}. {team:.<30} {prob:>6.2f}%")
        
        # Relegation battle
        print("\n" + "-" * 70)
        print("RELEGATION BATTLE")
        print("-" * 70)
        
        relegation_probs = [(team, results['teams'][team]['relegation_prob']) 
                            for team in self.teams]
        relegation_probs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (team, prob) in enumerate(relegation_probs[:5], 1):
            print(f"{i}. {team:.<30} {prob:>6.2f}%")
        
        # Most likely final table
        print("\n" + "-" * 70)
        print("MOST LIKELY FINAL TABLE")
        print("-" * 70)
        print(f"{'Pos':<5} {'Team':<30} {'Exp Pts':<10}")
        print("-" * 70)
        
        for row in results['most_likely_table'][:10]:
            print(f"{row['position']:<5} {row['team']:<30} {row['expected_points']:<10.1f}")
        
        print("\n...")


def main():
    """Run Season Oracle simulation."""
    print("=" * 70)
    print("SEASON ORACLE ENGINE - 2026/27 PREMIER LEAGUE")
    print("=" * 70)
    
    # Paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "season_simulations")
    
    # Initialize oracle
    oracle = SeasonOracle(models_dir, features_path, output_dir)
    
    # Generate AI predictions
    oracle.generate_ai_predictions()
    
    # Run Monte Carlo simulation
    results = oracle.run_monte_carlo_simulation(n_simulations=10000)
    
    # Validate results
    validations = oracle.validate_probabilities(results)
    
    # Save results
    oracle.save_results(results, validations)
    
    # Print summary
    oracle.print_summary(results)
    
    print("\n" + "=" * 70)
    print("SEASON ORACLE COMPLETE")
    print("=" * 70)
    print("\nAll results saved to: outputs/season_simulations/")
    print("\nFiles created:")
    print("  • ai_fixture_predictions.csv - AI predictions for all fixtures")
    print("  • season_simulation_results.json - Complete simulation results")
    print("  • team_probabilities.csv - Title/Top-4/Relegation probabilities")
    print("  • most_likely_final_table.csv - Most probable final standings")
    print("  • validation_results.json - Validation checks")
    
    if all(validations.values()):
        print("\n✓ All validation checks passed")
    else:
        print("\n⚠ Some validation checks failed - review validation_results.json")


if __name__ == "__main__":
    main()