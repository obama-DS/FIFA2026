# =============================================================================
# gameweek_engine.py
# =============================================================================
# Phase 20: Gameweek Engine
#
# Reusable gameweek layer for Premier League AI platform
# Handles current gameweek detection, fixture grouping, deadlines, and status
# =============================================================================

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from src.models.model_loader import load_best_models
from src.predictions.match_probabilities import MatchProbabilityEngine
from src.predictions.match_explanation import MatchExplainer


class GameweekEngine:
    """
    Premier League Gameweek Management System.
    
    Features:
    - Current gameweek detection based on date
    - Fixture grouping by gameweek
    - Featured fixture selection
    - First-kickoff deadline calculation
    - Fixture status (upcoming/live/completed)
    - AI predictions with probabilities and explanations
    - Prediction locking after deadline
    - Safe handling of postponed/rescheduled fixtures
    """
    
    def __init__(
        self,
        fixtures_path: str,
        features_path: str,
        models_dir: str,
        season: str = '2026/27'
    ):
        """
        Initialize Gameweek Engine.
        
        Args:
            fixtures_path: Path to fixtures CSV
            features_path: Path to match features CSV
            models_dir: Path to trained models
            season: Season to manage (default: 2026/27)
        """
        self.fixtures_path = fixtures_path
        self.features_path = features_path
        self.models_dir = models_dir
        self.season = season
        
        # Load fixtures
        print(f"Loading {season} fixtures...")
        self.fixtures_df = pd.read_csv(fixtures_path)
        self.fixtures_df['kickoff'] = pd.to_datetime(self.fixtures_df['kickoff'])
        self.fixtures_df = self.fixtures_df[self.fixtures_df['season'] == season].copy()
        print(f"✓ Loaded {len(self.fixtures_df)} fixtures")
        
        # Load features
        print("Loading match features...")
        self.features_df = pd.read_csv(features_path, low_memory=False)
        self.features_df['match_date'] = pd.to_datetime(self.features_df['match_date'])
        print(f"✓ Loaded {len(self.features_df)} feature records")
        
        # Get feature columns
        self.feature_cols = [col for col in self.features_df.columns if col not in [
            'match_id', 'row_id', 'season', 'match_date', 'is_fixture',
            'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name',
            'result', 'home_goals', 'away_goals'
        ]]
        duplicate_cols = ['sca_per_90_calc', 'gca_per_90_calc']
        self.feature_cols = [c for c in self.feature_cols if c not in duplicate_cols]
        
        # Load models
        print("Loading trained models...")
        self.home_model, self.away_model, self.metadata = load_best_models(models_dir)
        print(f"✓ Models loaded: {self.metadata.get('best_model_name')}")
        
        # Initialize probability engine
        self.prob_engine = None
        
        # Initialize explainer (lazy loading)
        self.explainer = None
        
        print("✓ Gameweek Engine initialized")
        print()
    
    def _get_prob_engine(self) -> MatchProbabilityEngine:
        """Get or create probability engine (lazy loading)."""
        if self.prob_engine is None:
            self.prob_engine = MatchProbabilityEngine(max_goals=10)
        return self.prob_engine
    
    def _get_explainer(self) -> MatchExplainer:
        """Get or create explainer (lazy loading)."""
        if self.explainer is None:
            output_dir = os.path.join(project_root, "outputs", "explanations")
            self.explainer = MatchExplainer(
                self.models_dir,
                self.features_path,
                output_dir
            )
        return self.explainer
    
    def get_current_gameweek(self, reference_date: Optional[datetime] = None) -> int:
        """
        Detect current gameweek based on date.
        
        Args:
            reference_date: Date to check (default: now)
            
        Returns:
            Current gameweek number
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        # Find first fixture after reference date
        upcoming = self.fixtures_df[self.fixtures_df['kickoff'] > reference_date].copy()
        
        if len(upcoming) == 0:
            # Season complete - return last gameweek
            return int(self.fixtures_df['round_number'].max())
        
        # Check if we're in the middle of a gameweek
        # (some fixtures kicked off, some haven't)
        current_gw = int(upcoming.iloc[0]['round_number'])
        gw_fixtures = self.fixtures_df[self.fixtures_df['round_number'] == current_gw]
        
        # If any fixture in this gameweek has already started, we're in it
        if (gw_fixtures['kickoff'] <= reference_date).any():
            return current_gw
        
        # All fixtures upcoming - check if previous GW exists
        if current_gw > 1:
            prev_gw_fixtures = self.fixtures_df[self.fixtures_df['round_number'] == current_gw - 1]
            # If previous GW is complete, we're between gameweeks - return upcoming
            if (prev_gw_fixtures['kickoff'] < reference_date).all():
                return current_gw
        
        return current_gw
    
    def get_gameweek_fixtures(self, gameweek: int) -> pd.DataFrame:
        """
        Get all fixtures for a specific gameweek.
        
        Args:
            gameweek: Gameweek number
            
        Returns:
            DataFrame of fixtures
        """
        fixtures = self.fixtures_df[self.fixtures_df['round_number'] == gameweek].copy()
        fixtures = fixtures.sort_values('kickoff')
        return fixtures
    
    def get_gameweek_deadline(self, gameweek: int) -> datetime:
        """
        Get deadline for a gameweek (first kickoff time).
        
        Args:
            gameweek: Gameweek number
            
        Returns:
            Deadline datetime
        """
        fixtures = self.get_gameweek_fixtures(gameweek)
        
        if len(fixtures) == 0:
            raise ValueError(f"No fixtures found for gameweek {gameweek}")
        
        return fixtures['kickoff'].min()
    
    def is_deadline_passed(self, gameweek: int, reference_date: Optional[datetime] = None) -> bool:
        """
        Check if gameweek deadline has passed.
        
        Args:
            gameweek: Gameweek number
            reference_date: Date to check (default: now)
            
        Returns:
            True if deadline passed
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        deadline = self.get_gameweek_deadline(gameweek)
        return reference_date >= deadline
    
    def get_fixture_status(
        self,
        fixture_id: int,
        reference_date: Optional[datetime] = None
    ) -> str:
        """
        Get status of a fixture.
        
        Args:
            fixture_id: Fixture ID
            reference_date: Date to check (default: now)
            
        Returns:
            Status: 'upcoming', 'live', 'completed', 'postponed'
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        fixture = self.fixtures_df[self.fixtures_df['fixture_id'] == fixture_id]
        
        if len(fixture) == 0:
            raise ValueError(f"Fixture {fixture_id} not found")
        
        fixture = fixture.iloc[0]
        kickoff = fixture['kickoff']
        
        # Check if result exists (completed)
        if pd.notna(fixture['result']) and fixture['result'] != '':
            return 'completed'
        
        # Check time relative to kickoff
        if reference_date < kickoff:
            return 'upcoming'
        
        # Assume 2 hours for match duration
        match_end = kickoff + timedelta(hours=2)
        
        if reference_date < match_end:
            return 'live'
        
        # Kickoff passed but no result - likely postponed
        return 'postponed'
    
    def get_featured_fixture(self, gameweek: int) -> Optional[Dict]:
        """
        Select featured fixture for a gameweek.
        
        Selection criteria:
        1. First match chronologically (creates urgency)
        2. If multiple at same time, pick biggest teams
        
        Args:
            gameweek: Gameweek number
            
        Returns:
            Featured fixture dict or None
        """
        fixtures = self.get_gameweek_fixtures(gameweek)
        
        if len(fixtures) == 0:
            return None
        
        # Get first kickoff time
        first_kickoff = fixtures['kickoff'].min()
        first_matches = fixtures[fixtures['kickoff'] == first_kickoff]
        
        # If only one match at first kickoff, that's the featured one
        if len(first_matches) == 1:
            return first_matches.iloc[0].to_dict()
        
        # Multiple simultaneous - prioritize "big" teams
        # Simple heuristic: alphabetically first (could be enhanced with team rankings)
        featured = first_matches.sort_values(['home_team_name', 'away_team_name']).iloc[0]
        
        return featured.to_dict()
    
    def get_fixture_prediction(
        self,
        fixture_id: int,
        include_probabilities: bool = True,
        include_explanation: bool = False
    ) -> Dict:
        """
        Get AI prediction for a fixture.
        
        Args:
            fixture_id: Fixture ID
            include_probabilities: Include win/draw/loss probabilities
            include_explanation: Include SHAP explanation
            
        Returns:
            Prediction dictionary
        """
        # Get fixture
        fixture = self.fixtures_df[self.fixtures_df['fixture_id'] == fixture_id]
        
        if len(fixture) == 0:
            raise ValueError(f"Fixture {fixture_id} not found")
        
        fixture = fixture.iloc[0]
        
        # Find matching feature row
        feature_row = self.features_df[
            (self.features_df['season'] == self.season) &
            (self.features_df['home_team_name'] == fixture['home_team_name']) &
            (self.features_df['away_team_name'] == fixture['away_team_name']) &
            (self.features_df['is_fixture'] == True)
        ]
        
        if len(feature_row) == 0:
            raise ValueError(f"No features found for fixture {fixture_id}")
        
        feature_row = feature_row.iloc[0]
        
        # Get features
        features_df = pd.DataFrame([feature_row[self.feature_cols]])
        
        # Make prediction
        pred_home = self.home_model.predict(features_df)[0]
        pred_away = self.away_model.predict(features_df)[0]
        
        # Clip to valid range
        pred_home = np.clip(pred_home, 0, 10)
        pred_away = np.clip(pred_away, 0, 10)
        
        prediction = {
            'fixture_id': int(fixture_id),
            'home_team': fixture['home_team_name'],
            'away_team': fixture['away_team_name'],
            'kickoff': str(fixture['kickoff']),
            'predicted_home_goals': round(float(pred_home), 2),
            'predicted_away_goals': round(float(pred_away), 2)
        }
        
        # Add probabilities if requested
        if include_probabilities:
            prob_engine = self._get_prob_engine()
            probs = prob_engine.calculate_match_probabilities(pred_home, pred_away)
            
            prediction['home_win_probability'] = probs['home_win_prob']
            prediction['draw_probability'] = probs['draw_prob']
            prediction['away_win_probability'] = probs['away_win_prob']
            prediction['most_likely_result'] = probs['most_likely_result']
            prediction['most_likely_scorelines'] = probs['most_likely_scorelines'][:5]
        
        # Add explanation if requested
        if include_explanation:
            explainer = self._get_explainer()
            
            metadata = {
                'home_team': fixture['home_team_name'],
                'away_team': fixture['away_team_name'],
                'match_date': str(fixture['kickoff'])
            }
            
            explanation = explainer.explain_prediction(
                features_df,
                metadata,
                top_n=3
            )
            
            prediction['explanation'] = explanation['summary']
            prediction['supporting_factors'] = explanation['home_explanation'].get('supporting_factors', [])
            prediction['opposing_factors'] = explanation['home_explanation'].get('opposing_factors', [])
        
        return prediction
    
    def get_gameweek_predictions(
        self,
        gameweek: int,
        include_probabilities: bool = True,
        include_explanations: bool = False,
        locked_only: bool = False
    ) -> List[Dict]:
        """
        Get AI predictions for all fixtures in a gameweek.
        
        Args:
            gameweek: Gameweek number
            include_probabilities: Include win/draw/loss probabilities
            include_explanations: Include SHAP explanations
            locked_only: Only return predictions if deadline passed
            
        Returns:
            List of prediction dictionaries
        """
        fixtures = self.get_gameweek_fixtures(gameweek)
        
        if len(fixtures) == 0:
            return []
        
        # Check if predictions should be locked
        if locked_only and not self.is_deadline_passed(gameweek):
            return []
        
        predictions = []
        
        for _, fixture in fixtures.iterrows():
            try:
                prediction = self.get_fixture_prediction(
                    fixture['fixture_id'],
                    include_probabilities=include_probabilities,
                    include_explanation=include_explanations
                )
                predictions.append(prediction)
            except Exception as e:
                print(f"⚠ Could not predict fixture {fixture['fixture_id']}: {e}")
        
        return predictions
    
    def get_gameweek_summary(
        self,
        gameweek: int,
        reference_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get comprehensive gameweek summary.
        
        Args:
            gameweek: Gameweek number
            reference_date: Date for status calculation (default: now)
            
        Returns:
            Summary dictionary
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        fixtures = self.get_gameweek_fixtures(gameweek)
        
        if len(fixtures) == 0:
            return {
                'gameweek': gameweek,
                'error': 'No fixtures found'
            }
        
        # Get deadline
        deadline = self.get_gameweek_deadline(gameweek)
        deadline_passed = reference_date >= deadline
        
        # Count fixture statuses
        status_counts = {
            'upcoming': 0,
            'live': 0,
            'completed': 0,
            'postponed': 0
        }
        
        for _, fixture in fixtures.iterrows():
            status = self.get_fixture_status(fixture['fixture_id'], reference_date)
            status_counts[status] += 1
        
        # Get featured fixture
        featured = self.get_featured_fixture(gameweek)
        
        summary = {
            'gameweek': gameweek,
            'season': self.season,
            'deadline': str(deadline),
            'deadline_passed': deadline_passed,
            'fixtures_count': len(fixtures),
            'status': status_counts,
            'featured_fixture': featured,
            'kickoff_dates': {
                'first': str(fixtures['kickoff'].min()),
                'last': str(fixtures['kickoff'].max())
            }
        }
        
        return summary
    
    def print_gameweek_summary(self, gameweek: int, reference_date: Optional[datetime] = None):
        """Print human-readable gameweek summary."""
        summary = self.get_gameweek_summary(gameweek, reference_date)
        
        print("=" * 70)
        print(f"GAMEWEEK {summary['gameweek']} - {summary['season']}")
        print("=" * 70)
        print()
        
        print(f"Deadline: {summary['deadline']}")
        print(f"Status: {'🔒 LOCKED' if summary['deadline_passed'] else '🔓 OPEN'}")
        print()
        
        print(f"Fixtures: {summary['fixtures_count']}")
        print(f"  Upcoming: {summary['status']['upcoming']}")
        print(f"  Live: {summary['status']['live']}")
        print(f"  Completed: {summary['status']['completed']}")
        if summary['status']['postponed'] > 0:
            print(f"  Postponed: {summary['status']['postponed']}")
        print()
        
        if summary.get('featured_fixture'):
            featured = summary['featured_fixture']
            print("Featured Fixture:")
            print(f"  {featured['home_team_name']} vs {featured['away_team_name']}")
            print(f"  Kickoff: {featured['kickoff']}")
        
        print("=" * 70)
        print()


def main():
    """Test gameweek engine."""
    print("=" * 70)
    print("PHASE 20: GAMEWEEK ENGINE TEST")
    print("=" * 70)
    print()
    
    # Paths
    fixtures_path = os.path.join(project_root, "data", "master", "fixtures_2026_27.csv")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    models_dir = os.path.join(project_root, "models")
    
    # Initialize engine
    engine = GameweekEngine(fixtures_path, features_path, models_dir, season='2026/27')
    
    # Test gameweek detection
    print("[1] Testing Gameweek Detection")
    print("-" * 70)
    
    # Test with start of season
    test_date = datetime(2026, 8, 15)  # Before GW1
    gw = engine.get_current_gameweek(test_date)
    print(f"Date: {test_date.date()} → Gameweek {gw}")
    
    test_date = datetime(2026, 8, 22)  # During GW1
    gw = engine.get_current_gameweek(test_date)
    print(f"Date: {test_date.date()} → Gameweek {gw}")
    
    test_date = datetime(2026, 9, 1)  # Between GW2 and GW3
    gw = engine.get_current_gameweek(test_date)
    print(f"Date: {test_date.date()} → Gameweek {gw}")
    print()
    
    # Test gameweek 1
    print("[2] Gameweek 1 Summary")
    print("-" * 70)
    engine.print_gameweek_summary(1, datetime(2026, 8, 20))
    
    # Test predictions
    print("[3] Gameweek 1 Predictions (Sample)")
    print("-" * 70)
    predictions = engine.get_gameweek_predictions(1, include_probabilities=True, include_explanations=False)
    
    print(f"Generated {len(predictions)} predictions\n")
    
    for i, pred in enumerate(predictions[:3], 1):
        print(f"[{i}] {pred['home_team']} vs {pred['away_team']}")
        print(f"    Prediction: {pred['predicted_home_goals']:.2f} - {pred['predicted_away_goals']:.2f}")
        if 'home_win_probability' in pred:
            print(f"    Home: {pred['home_win_probability']:.1%}, "
                  f"Draw: {pred['draw_probability']:.1%}, "
                  f"Away: {pred['away_win_probability']:.1%}")
        print()
    
    print("=" * 70)
    print("GAMEWEEK ENGINE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
