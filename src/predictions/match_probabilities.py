# =============================================================================
# match_probabilities.py
# =============================================================================
# Phase 18: Beat the AI - Match Probability Engine
#
# Calculates match outcome probabilities using Poisson distribution
# Reusable by Season Oracle and Beat the AI API
# =============================================================================

import numpy as np
from scipy.stats import poisson
from typing import Dict, List, Tuple, Optional
import warnings

# Suppress runtime warnings for very small probabilities
warnings.filterwarnings('ignore', category=RuntimeWarning)


class MatchProbabilityEngine:
    """
    Calculates match outcome probabilities using Poisson distribution.
    
    Given expected home and away goals from ML models, computes:
    - Home win / Draw / Away win probabilities
    - Full scoreline probability distribution
    - Most likely scorelines
    - Expected goals
    """
    
    def __init__(self, max_goals: int = 10):
        """
        Initialize Match Probability Engine.
        
        Args:
            max_goals: Maximum goals to consider in distribution (default: 10)
                      Higher values = more accurate but slower
        """
        self.max_goals = max_goals
    
    def calculate_match_probabilities(
        self,
        expected_home_goals: float,
        expected_away_goals: float
    ) -> Dict:
        """
        Calculate all match probabilities for a single fixture.
        
        Args:
            expected_home_goals: Expected home team goals (from ML model)
            expected_away_goals: Expected away team goals (from ML model)
            
        Returns:
            Dictionary containing:
                - expected_home_goals: Input value
                - expected_away_goals: Input value
                - home_win_prob: Probability of home win
                - draw_prob: Probability of draw
                - away_win_prob: Probability of away win
                - scoreline_distribution: Full probability matrix
                - most_likely_scorelines: Top N most probable scorelines
                - most_likely_result: 'H', 'D', or 'A'
                
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        self._validate_inputs(expected_home_goals, expected_away_goals)
        
        # Calculate scoreline probability distribution
        scoreline_probs = self._calculate_scoreline_distribution(
            expected_home_goals,
            expected_away_goals
        )
        
        # Calculate outcome probabilities
        home_win_prob, draw_prob, away_win_prob = self._calculate_outcome_probabilities(
            scoreline_probs
        )
        
        # Get most likely scorelines
        most_likely_scorelines = self._get_most_likely_scorelines(
            scoreline_probs,
            top_n=10
        )
        
        # Determine most likely result
        if home_win_prob > draw_prob and home_win_prob > away_win_prob:
            most_likely_result = 'H'
        elif away_win_prob > draw_prob and away_win_prob > home_win_prob:
            most_likely_result = 'A'
        else:
            most_likely_result = 'D'
        
        return {
            'expected_home_goals': round(expected_home_goals, 3),
            'expected_away_goals': round(expected_away_goals, 3),
            'home_win_prob': round(home_win_prob, 4),
            'draw_prob': round(draw_prob, 4),
            'away_win_prob': round(away_win_prob, 4),
            'most_likely_result': most_likely_result,
            'scoreline_distribution': scoreline_probs,
            'most_likely_scorelines': most_likely_scorelines
        }
    
    def _validate_inputs(self, home_goals: float, away_goals: float):
        """
        Validate input parameters.
        
        Args:
            home_goals: Expected home goals
            away_goals: Expected away goals
            
        Raises:
            ValueError: If inputs are invalid
        """
        if home_goals is None or away_goals is None:
            raise ValueError("Expected goals cannot be None")
        
        if not isinstance(home_goals, (int, float)) or not isinstance(away_goals, (int, float)):
            raise ValueError("Expected goals must be numeric")
        
        if home_goals < 0 or away_goals < 0:
            raise ValueError("Expected goals cannot be negative")
        
        if home_goals > 20 or away_goals > 20:
            raise ValueError("Expected goals unreasonably high (>20)")
        
        if np.isnan(home_goals) or np.isnan(away_goals):
            raise ValueError("Expected goals cannot be NaN")
        
        if np.isinf(home_goals) or np.isinf(away_goals):
            raise ValueError("Expected goals cannot be infinite")
    
    def _calculate_scoreline_distribution(
        self,
        lambda_home: float,
        lambda_away: float
    ) -> np.ndarray:
        """
        Calculate probability distribution over all possible scorelines.
        
        Uses Poisson distribution for both teams, assuming independence.
        
        Args:
            lambda_home: Expected home goals (Poisson parameter)
            lambda_away: Expected away goals (Poisson parameter)
            
        Returns:
            2D numpy array of shape (max_goals+1, max_goals+1)
            where [i,j] = P(home scores i AND away scores j)
        """
        # Calculate probability mass function for each team
        home_probs = poisson.pmf(np.arange(self.max_goals + 1), lambda_home)
        away_probs = poisson.pmf(np.arange(self.max_goals + 1), lambda_away)
        
        # Outer product gives joint probability distribution
        # Assumes independence (reasonable for goal-scoring)
        scoreline_matrix = np.outer(home_probs, away_probs)
        
        return scoreline_matrix
    
    def _calculate_outcome_probabilities(
        self,
        scoreline_matrix: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Calculate home win, draw, and away win probabilities.
        
        Args:
            scoreline_matrix: 2D array of scoreline probabilities
            
        Returns:
            Tuple of (home_win_prob, draw_prob, away_win_prob)
        """
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0
        
        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                prob = scoreline_matrix[home_goals, away_goals]
                
                if home_goals > away_goals:
                    home_win_prob += prob
                elif home_goals == away_goals:
                    draw_prob += prob
                else:
                    away_win_prob += prob
        
        return home_win_prob, draw_prob, away_win_prob
    
    def _get_most_likely_scorelines(
        self,
        scoreline_matrix: np.ndarray,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Get the most likely scorelines.
        
        Args:
            scoreline_matrix: 2D array of scoreline probabilities
            top_n: Number of top scorelines to return
            
        Returns:
            List of dictionaries with scoreline and probability
        """
        scorelines = []
        
        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                prob = scoreline_matrix[home_goals, away_goals]
                scorelines.append({
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'probability': float(prob),
                    'scoreline': f"{home_goals}-{away_goals}"
                })
        
        # Sort by probability (descending)
        scorelines.sort(key=lambda x: x['probability'], reverse=True)
        
        # Return top N
        return scorelines[:top_n]
    
    def validate_probabilities(self, result: Dict) -> Dict[str, bool]:
        """
        Validate that calculated probabilities are mathematically correct.
        
        Args:
            result: Result dictionary from calculate_match_probabilities
            
        Returns:
            Dictionary of validation checks
        """
        validations = {}
        
        # Check probabilities are between 0 and 1
        home_win = result['home_win_prob']
        draw = result['draw_prob']
        away_win = result['away_win_prob']
        
        validations['home_win_in_range'] = 0 <= home_win <= 1
        validations['draw_in_range'] = 0 <= draw <= 1
        validations['away_win_in_range'] = 0 <= away_win <= 1
        
        # Check probabilities sum to ~1.0 (allowing for floating point error)
        prob_sum = home_win + draw + away_win
        validations['probabilities_sum_to_one'] = 0.99 < prob_sum < 1.01
        
        # Check scoreline probabilities sum to ~1.0
        scoreline_sum = np.sum(result['scoreline_distribution'])
        validations['scoreline_sum_to_one'] = 0.99 < scoreline_sum < 1.01
        
        # Check most likely scorelines are sorted
        scorelines = result['most_likely_scorelines']
        is_sorted = all(
            scorelines[i]['probability'] >= scorelines[i+1]['probability']
            for i in range(len(scorelines) - 1)
        )
        validations['scorelines_sorted'] = is_sorted
        
        # Check expected goals match input
        validations['expected_goals_preserved'] = (
            result['expected_home_goals'] >= 0 and
            result['expected_away_goals'] >= 0
        )
        
        return validations


def calculate_match_probability(
    expected_home_goals: float,
    expected_away_goals: float,
    max_goals: int = 10
) -> Dict:
    """
    Convenience function to calculate match probabilities.
    
    Args:
        expected_home_goals: Expected home team goals
        expected_away_goals: Expected away team goals
        max_goals: Maximum goals to consider (default: 10)
        
    Returns:
        Dictionary with all match probabilities
    """
    engine = MatchProbabilityEngine(max_goals=max_goals)
    return engine.calculate_match_probabilities(expected_home_goals, expected_away_goals)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("MATCH PROBABILITY ENGINE - TEST")
    print("=" * 70)
    print()
    
    # Create engine
    engine = MatchProbabilityEngine(max_goals=10)
    
    # Test fixtures with different expected goals
    test_fixtures = [
        {"home": "Man City", "away": "Sheffield Utd", "exp_home": 2.5, "exp_away": 0.8},
        {"home": "Arsenal", "away": "Liverpool", "exp_home": 1.8, "exp_away": 1.7},
        {"home": "Everton", "away": "Man United", "exp_home": 1.0, "exp_away": 1.5},
        {"home": "Brighton", "away": "Luton", "exp_home": 1.5, "exp_away": 1.0},
    ]
    
    print("Testing match probability calculations:\n")
    
    for i, fixture in enumerate(test_fixtures, 1):
        print(f"[{i}] {fixture['home']} vs {fixture['away']}")
        print(f"    Expected: {fixture['exp_home']:.2f} - {fixture['exp_away']:.2f}")
        
        try:
            result = engine.calculate_match_probabilities(
                fixture['exp_home'],
                fixture['exp_away']
            )
            
            print(f"    Home win: {result['home_win_prob']:.1%}")
            print(f"    Draw:     {result['draw_prob']:.1%}")
            print(f"    Away win: {result['away_win_prob']:.1%}")
            print(f"    Most likely result: {result['most_likely_result']}")
            print(f"    Most likely scoreline: {result['most_likely_scorelines'][0]['scoreline']} ({result['most_likely_scorelines'][0]['probability']:.1%})")
            
            # Validate
            validations = engine.validate_probabilities(result)
            if all(validations.values()):
                print(f"    ✓ All validations passed")
            else:
                print(f"    ✗ Validation failed: {validations}")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
        
        print()
    
    # Test edge cases
    print("=" * 70)
    print("EDGE CASE TESTS")
    print("=" * 70)
    print()
    
    edge_cases = [
        ("Very low scoring", 0.3, 0.3),
        ("Very high scoring", 4.0, 4.0),
        ("One-sided match", 3.0, 0.5),
        ("Zero goals expected", 0.0, 0.0),
    ]
    
    for name, exp_home, exp_away in edge_cases:
        print(f"{name}: {exp_home:.1f} - {exp_away:.1f}")
        try:
            result = engine.calculate_match_probabilities(exp_home, exp_away)
            print(f"  H: {result['home_win_prob']:.1%}, D: {result['draw_prob']:.1%}, A: {result['away_win_prob']:.1%}")
            
            validations = engine.validate_probabilities(result)
            if all(validations.values()):
                print(f"  ✓ Valid")
            else:
                failed = [k for k, v in validations.items() if not v]
                print(f"  ✗ Failed: {failed}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    # Test invalid inputs
    print("=" * 70)
    print("INVALID INPUT TESTS")
    print("=" * 70)
    print()
    
    invalid_cases = [
        ("Negative goals", -1.0, 1.0),
        ("None value", None, 1.0),
        ("NaN value", float('nan'), 1.0),
        ("Unreasonably high", 25.0, 1.0),
    ]
    
    for name, exp_home, exp_away in invalid_cases:
        print(f"{name}: {exp_home} - {exp_away}")
        try:
            result = engine.calculate_match_probabilities(exp_home, exp_away)
            print(f"  ✗ Should have raised ValueError but didn't")
        except ValueError as e:
            print(f"  ✓ Correctly rejected: {e}")
        except Exception as e:
            print(f"  ? Unexpected error: {e}")
        print()
    
    print("=" * 70)
    print("✓ MATCH PROBABILITY ENGINE TEST COMPLETE")
    print("=" * 70)