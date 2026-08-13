# =============================================================================
# match_explanation.py
# =============================================================================
# Phase 19: The Machine - Explainable Predictions
#
# Connects SHAP system to match predictions to generate human-readable explanations
# Identifies top supporting/opposing factors for each prediction
# =============================================================================

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from src.models.model_loader import load_best_models

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠ SHAP not available - will use feature importance only")


class MatchExplainer:
    """
    Generates human-readable explanations for match predictions.
    
    Connects SHAP values to predictions and identifies:
    - Top factors supporting the prediction
    - Top factors opposing it
    - Main reason for the predicted outcome
    """
    
    def __init__(self, models_dir: str, features_path: str, output_dir: str):
        """
        Initialize Match Explainer.
        
        Args:
            models_dir: Path to trained models
            features_path: Path to match features CSV
            output_dir: Path to save explanations
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
        
        # Get feature columns
        self.feature_cols = [col for col in self.features_df.columns if col not in [
            'match_id', 'row_id', 'season', 'match_date', 'is_fixture',
            'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name',
            'result', 'home_goals', 'away_goals'
        ]]
        
        # Remove any duplicate columns
        duplicate_cols = ['sca_per_90_calc', 'gca_per_90_calc']
        self.feature_cols = [c for c in self.feature_cols if c not in duplicate_cols]
        
        print(f"✓ Feature columns: {len(self.feature_cols)}")
        
        # SHAP explainers (initialized on demand)
        self.home_explainer = None
        self.away_explainer = None
        self.explainer_sample = None
        
        # Feature importance (fallback)
        self.home_importance = None
        self.away_importance = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print("✓ Match Explainer initialized")
        print()
    
    def _initialize_shap_explainers(self, sample_size: int = 100):
        """
        Initialize SHAP explainers with background data.
        
        Args:
            sample_size: Number of samples for SHAP background
        """
        if not SHAP_AVAILABLE:
            print("⚠ SHAP not available, using feature importance fallback")
            self._load_feature_importance()
            return
        
        print("Initializing SHAP explainers...")
        
        try:
            # Get sample data for SHAP background
            sample_df = self.features_df[
                (self.features_df['season'] == '2025/26') & 
                (self.features_df['is_fixture'] == False)
            ].copy()
            
            if len(sample_df) > sample_size:
                sample_df = sample_df.sample(n=sample_size, random_state=42)
            
            sample_features = sample_df[self.feature_cols]
            
            # Store sample for later use
            self.explainer_sample = sample_features
            
            # Initialize home explainer
            print("  Creating home goals explainer...")
            home_preprocessed = self.home_model.named_steps["preprocessing"].transform(sample_features)
            home_regressor = self.home_model.named_steps["regressor"]
            self.home_explainer = shap.Explainer(home_regressor, home_preprocessed)
            print("  ✓ Home explainer ready")
            
            # Initialize away explainer
            print("  Creating away goals explainer...")
            away_preprocessed = self.away_model.named_steps["preprocessing"].transform(sample_features)
            away_regressor = self.away_model.named_steps["regressor"]
            self.away_explainer = shap.Explainer(away_regressor, away_preprocessed)
            print("  ✓ Away explainer ready")
            
            print("✓ SHAP explainers initialized")
            
        except Exception as e:
            print(f"⚠ SHAP initialization failed: {e}")
            print("  Falling back to feature importance...")
            self._load_feature_importance()
    
    def _load_feature_importance(self):
        """Load pre-computed feature importance as fallback."""
        try:
            importance_dir = os.path.join(project_root, "outputs", "explainability")
            
            home_path = os.path.join(importance_dir, "feature_importance_home.csv")
            away_path = os.path.join(importance_dir, "feature_importance_away.csv")
            
            if os.path.exists(home_path):
                self.home_importance = pd.read_csv(home_path)
                print(f"  ✓ Loaded home feature importance")
            
            if os.path.exists(away_path):
                self.away_importance = pd.read_csv(away_path)
                print(f"  ✓ Loaded away feature importance")
                
        except Exception as e:
            print(f"  ⚠ Could not load feature importance: {e}")
    
    def explain_prediction(
        self,
        match_features: pd.DataFrame,
        match_metadata: Optional[Dict] = None,
        top_n: int = 5
    ) -> Dict:
        """
        Generate explanation for a single match prediction.
        
        Args:
            match_features: Feature DataFrame for the match (single row)
            match_metadata: Optional metadata dict (teams, date, etc.)
            top_n: Number of top features to identify
            
        Returns:
            Dictionary with prediction and explanation
        """
        # Get predictions
        pred_home = self.home_model.predict(match_features)[0]
        pred_away = self.away_model.predict(match_features)[0]
        
        # Clip to valid range
        pred_home = np.clip(pred_home, 0, 10)
        pred_away = np.clip(pred_away, 0, 10)
        
        explanation = {
            'prediction': {
                'home_goals': round(float(pred_home), 2),
                'away_goals': round(float(pred_away), 2)
            },
            'home_explanation': {},
            'away_explanation': {},
            'summary': {}
        }
        
        # Add metadata
        if match_metadata:
            explanation['metadata'] = match_metadata
        
        # Try SHAP explanation
        if SHAP_AVAILABLE and self.home_explainer is not None:
            try:
                explanation['home_explanation'] = self._explain_with_shap(
                    match_features, 
                    self.home_model,
                    self.home_explainer,
                    top_n
                )
                explanation['away_explanation'] = self._explain_with_shap(
                    match_features,
                    self.away_model,
                    self.away_explainer,
                    top_n
                )
            except Exception as e:
                print(f"⚠ SHAP explanation failed: {e}")
                explanation['home_explanation'] = self._explain_with_importance(match_features, 'home', top_n)
                explanation['away_explanation'] = self._explain_with_importance(match_features, 'away', top_n)
        else:
            # Fallback to feature importance
            explanation['home_explanation'] = self._explain_with_importance(match_features, 'home', top_n)
            explanation['away_explanation'] = self._explain_with_importance(match_features, 'away', top_n)
        
        # Generate human-readable summary
        explanation['summary'] = self._generate_summary(explanation)
        
        return explanation
    
    def _explain_with_shap(
        self,
        match_features: pd.DataFrame,
        model,
        explainer,
        top_n: int
    ) -> Dict:
        """
        Generate explanation using SHAP values.
        
        Args:
            match_features: Feature DataFrame
            model: Trained model pipeline
            explainer: SHAP explainer
            top_n: Number of top features
            
        Returns:
            Explanation dictionary
        """
        # Preprocess features
        X = model.named_steps["preprocessing"].transform(match_features)
        
        # Get SHAP values
        shap_values = explainer(X)
        values = shap_values.values[0]
        
        # Get feature names
        feature_names = self.feature_cols[:len(values)]
        
        # Get actual feature values
        feature_values = match_features[self.feature_cols].iloc[0].values[:len(values)]
        
        # Create contribution dataframe
        contrib_df = pd.DataFrame({
            'feature': feature_names,
            'shap_value': values,
            'feature_value': feature_values
        })
        
        # Sort by absolute contribution
        contrib_df['abs_shap'] = np.abs(contrib_df['shap_value'])
        contrib_df = contrib_df.sort_values('abs_shap', ascending=False)
        
        # Top supporting factors (positive SHAP)
        supporting = contrib_df[contrib_df['shap_value'] > 0].head(top_n)
        
        # Top opposing factors (negative SHAP)
        opposing = contrib_df[contrib_df['shap_value'] < 0].head(top_n)
        
        return {
            'method': 'SHAP',
            'supporting_factors': [
                {
                    'feature': row['feature'],
                    'contribution': round(float(row['shap_value']), 4),
                    'value': round(float(row['feature_value']), 2) if not pd.isna(row['feature_value']) else None,
                    'readable_name': self._make_readable(row['feature'])
                }
                for _, row in supporting.iterrows()
            ],
            'opposing_factors': [
                {
                    'feature': row['feature'],
                    'contribution': round(float(row['shap_value']), 4),
                    'value': round(float(row['feature_value']), 2) if not pd.isna(row['feature_value']) else None,
                    'readable_name': self._make_readable(row['feature'])
                }
                for _, row in opposing.iterrows()
            ],
            'net_contribution': round(float(contrib_df['shap_value'].sum()), 4)
        }
    
    def _explain_with_importance(
        self,
        match_features: pd.DataFrame,
        model_type: str,
        top_n: int
    ) -> Dict:
        """
        Generate explanation using feature importance (fallback).
        
        Args:
            match_features: Feature DataFrame
            model_type: 'home' or 'away'
            top_n: Number of top features
            
        Returns:
            Explanation dictionary
        """
        importance_df = self.home_importance if model_type == 'home' else self.away_importance
        
        if importance_df is None:
            return {
                'method': 'none',
                'error': 'Feature importance not available'
            }
        
        # Get top important features
        top_features = importance_df.head(top_n)
        
        # Get feature values from match
        feature_values = match_features[self.feature_cols].iloc[0]
        
        factors = []
        for _, row in top_features.iterrows():
            feature_name = row['feature']
            if feature_name in feature_values.index:
                factors.append({
                    'feature': feature_name,
                    'importance': round(float(row['importance']), 4),
                    'value': round(float(feature_values[feature_name]), 2) if not pd.isna(feature_values[feature_name]) else None,
                    'readable_name': self._make_readable(feature_name)
                })
        
        return {
            'method': 'feature_importance',
            'top_factors': factors,
            'note': 'Using global feature importance - not match-specific'
        }
    
    def _make_readable(self, feature_name: str) -> str:
        """
        Convert feature name to human-readable format.
        
        Args:
            feature_name: Raw feature name
            
        Returns:
            Human-readable name
        """
        # Common abbreviations
        replacements = {
            'gf': 'goals for',
            'ga': 'goals against',
            'ppg': 'points per game',
            'xg': 'expected goals',
            'pct': 'percentage',
            'avg': 'average',
            'h2h': 'head-to-head',
            'last3': 'last 3 games',
            'last5': 'last 5 games',
            'last10': 'last 10 games',
            '_home': ' (home)',
            '_away': ' (away)',
            '_per_': ' per ',
            '_': ' '
        }
        
        readable = feature_name.lower()
        for old, new in replacements.items():
            readable = readable.replace(old, new)
        
        return readable.strip().capitalize()
    
    def _generate_summary(self, explanation: Dict) -> Dict:
        """
        Generate human-readable summary of the explanation.
        
        Args:
            explanation: Full explanation dictionary
            
        Returns:
            Summary dictionary with readable text
        """
        pred_home = explanation['prediction']['home_goals']
        pred_away = explanation['prediction']['away_goals']
        
        # Determine predicted outcome
        if pred_home - pred_away > 0.5:
            predicted_outcome = 'home_win'
            outcome_text = 'Home win'
        elif pred_away - pred_home > 0.5:
            predicted_outcome = 'away_win'
            outcome_text = 'Away win'
        else:
            predicted_outcome = 'draw'
            outcome_text = 'Draw'
        
        # Get main reason (top supporting factor for higher-scoring team)
        main_reason = "Model prediction based on multiple factors"
        
        if predicted_outcome == 'home_win':
            factors = explanation['home_explanation'].get('supporting_factors', [])
            if factors:
                top = factors[0]
                main_reason = f"Strong {top['readable_name'].lower()}"
        elif predicted_outcome == 'away_win':
            factors = explanation['away_explanation'].get('supporting_factors', [])
            if factors:
                top = factors[0]
                main_reason = f"Strong {top['readable_name'].lower()}"
        else:
            # Draw - look at balancing factors
            home_factors = explanation['home_explanation'].get('supporting_factors', [])
            away_factors = explanation['away_explanation'].get('supporting_factors', [])
            if home_factors and away_factors:
                main_reason = f"Balanced teams - similar recent form"
        
        # Build short explanation
        if 'metadata' in explanation:
            home_team = explanation['metadata'].get('home_team', 'Home')
            away_team = explanation['metadata'].get('away_team', 'Away')
            short_explanation = f"{outcome_text} predicted ({pred_home:.1f}-{pred_away:.1f}). {main_reason}."
        else:
            short_explanation = f"{outcome_text} ({pred_home:.1f}-{pred_away:.1f}). {main_reason}."
        
        return {
            'predicted_outcome': predicted_outcome,
            'predicted_scoreline': f"{pred_home:.1f}-{pred_away:.1f}",
            'main_reason': main_reason,
            'short_explanation': short_explanation
        }
    
    def explain_fixtures(
        self,
        season: str = '2026/27',
        n_fixtures: Optional[int] = None,
        save: bool = True
    ) -> List[Dict]:
        """
        Generate explanations for fixtures.
        
        Args:
            season: Season to explain (default: 2026/27)
            n_fixtures: Number of fixtures to explain (None = all)
            save: Whether to save explanations to file
            
        Returns:
            List of explanation dictionaries
        """
        print(f"Generating explanations for {season} fixtures...")
        
        # Initialize SHAP if needed
        if self.home_explainer is None:
            self._initialize_shap_explainers()
        
        # Get fixtures
        fixtures = self.features_df[
            (self.features_df['season'] == season) & 
            (self.features_df['is_fixture'] == True)
        ].copy()
        
        if n_fixtures and len(fixtures) > n_fixtures:
            fixtures = fixtures.head(n_fixtures)
        
        print(f"✓ Found {len(fixtures)} fixtures to explain")
        print()
        
        explanations = []
        
        for idx, (_, row) in enumerate(fixtures.iterrows(), 1):
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(fixtures)}")
            
            # Prepare metadata
            metadata = {
                'match_id': row['match_id'],
                'home_team': row['home_team_name'],
                'away_team': row['away_team_name'],
                'match_date': str(row['match_date']),
                'season': row['season']
            }
            
            # Get features
            features = row[self.feature_cols].to_frame().T
            
            # Generate explanation
            explanation = self.explain_prediction(features, metadata, top_n=5)
            explanations.append(explanation)
        
        print(f"✓ Generated {len(explanations)} explanations")
        
        # Save if requested
        if save:
            output_path = os.path.join(self.output_dir, f'fixture_explanations_{season.replace("/", "_")}.json')
            with open(output_path, 'w') as f:
                json.dump(explanations, f, indent=2)
            print(f"✓ Saved: {output_path}")
        
        print()
        return explanations
    
    def print_explanation(self, explanation: Dict):
        """
        Print a human-readable explanation.
        
        Args:
            explanation: Explanation dictionary
        """
        print("=" * 70)
        
        if 'metadata' in explanation:
            meta = explanation['metadata']
            print(f"{meta.get('home_team', 'Home')} vs {meta.get('away_team', 'Away')}")
            print(f"Date: {meta.get('match_date', 'N/A')}")
            print("-" * 70)
        
        pred = explanation['prediction']
        print(f"Predicted Score: {pred['home_goals']:.2f} - {pred['away_goals']:.2f}")
        
        summary = explanation['summary']
        print(f"Outcome: {summary['predicted_outcome'].replace('_', ' ').title()}")
        print(f"Main Reason: {summary['main_reason']}")
        print()
        print(f"Explanation: {summary['short_explanation']}")
        print()
        
        # Home factors
        home_exp = explanation['home_explanation']
        if home_exp.get('method') == 'SHAP':
            print("Home Goals - Supporting Factors:")
            for i, factor in enumerate(home_exp['supporting_factors'][:3], 1):
                print(f"  {i}. {factor['readable_name']}: {factor['contribution']:+.3f}")
            
            if home_exp['opposing_factors']:
                print("\nHome Goals - Opposing Factors:")
                for i, factor in enumerate(home_exp['opposing_factors'][:3], 1):
                    print(f"  {i}. {factor['readable_name']}: {factor['contribution']:+.3f}")
        
        print()
        
        # Away factors
        away_exp = explanation['away_explanation']
        if away_exp.get('method') == 'SHAP':
            print("Away Goals - Supporting Factors:")
            for i, factor in enumerate(away_exp['supporting_factors'][:3], 1):
                print(f"  {i}. {factor['readable_name']}: {factor['contribution']:+.3f}")
            
            if away_exp['opposing_factors']:
                print("\nAway Goals - Opposing Factors:")
                for i, factor in enumerate(away_exp['opposing_factors'][:3], 1):
                    print(f"  {i}. {factor['readable_name']}: {factor['contribution']:+.3f}")
        
        print("=" * 70)
        print()


def main():
    """Run match explanation system."""
    print("=" * 70)
    print("PHASE 19: EXPLAINABLE MATCH PREDICTIONS")
    print("=" * 70)
    print()
    
    # Paths
    models_dir = os.path.join(project_root, "models")
    features_path = os.path.join(project_root, "data", "features", "match_features.csv")
    output_dir = os.path.join(project_root, "outputs", "explanations")
    
    # Initialize explainer
    explainer = MatchExplainer(models_dir, features_path, output_dir)
    
    # Generate explanations for first 10 fixtures
    print("Testing with first 10 fixtures...")
    print()
    explanations = explainer.explain_fixtures(season='2026/27', n_fixtures=10, save=True)
    
    # Print first 3 examples
    print("=" * 70)
    print("SAMPLE EXPLANATIONS")
    print("=" * 70)
    print()
    
    for i in range(min(3, len(explanations))):
        explainer.print_explanation(explanations[i])
    
    print("=" * 70)
    print("PHASE 19 COMPLETE")
    print("=" * 70)
    print()
    print(f"Generated {len(explanations)} explanations")
    print(f"Output: {output_dir}/fixture_explanations_2026_27.json")
    print()


if __name__ == "__main__":
    main()
