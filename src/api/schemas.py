# =============================================================================
# schemas.py
# =============================================================================
# Phase 14: FastAPI Schemas
#
# Pydantic models for request/response validation
# =============================================================================

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import numpy as np


class HealthResponse(BaseModel):
    """
    Health check response indicating API operational status.
    
    Used for monitoring and health checks. Returns basic status information
    and timestamps for system monitoring purposes.
    """
    status: str = Field(
        ..., 
        description="Current API operational status",
        example="healthy"
    )
    timestamp: str = Field(
        ..., 
        description="Current server timestamp in ISO 8601 format",
        example="2026-08-12T14:30:00.123456"
    )
    version: str = Field(
        ..., 
        description="API version number",
        example="1.0.0"
    )


class ModelInfoResponse(BaseModel):
    """
    Information about the currently loaded ML model.
    
    Provides metadata about the active prediction model including
    version, performance metrics, and training information.
    """
    model_version: str = Field(
        ..., 
        description="Version of the currently active model",
        example="1.0.0"
    )
    model_type: str = Field(
        ..., 
        description="Machine learning algorithm used",
        example="Random_Forest"
    )
    training_date: str = Field(
        ..., 
        description="Date when the model was trained (ISO 8601 format)",
        example="2026-08-12T21:29:14"
    )
    metrics: Dict[str, float] = Field(
        ..., 
        description="Model performance metrics on validation data",
        example={
            "val_mae_avg": 0.8889,
            "val_r2_avg": 0.0569,
            "val_mae_home": 0.8889,
            "val_mae_away": 0.8889
        }
    )
    feature_count: int = Field(
        ..., 
        description="Number of input features used by the model",
        example=372,
        ge=1
    )
    description: str = Field(
        ..., 
        description="Human-readable description of the model",
        example="Initial production model - Phase 9 training"
    )


class MatchFeatures(BaseModel):
    """
    Input features for Premier League match prediction.
    
    This model contains all the statistical features needed to predict match outcomes.
    Features are grouped by time period (last 3, 5, 10 matches) and include both
    home and away team statistics plus head-to-head history.
    
    All goal-related fields represent totals (not averages) for the specified period.
    """
    
    # Team identifiers
    home_team_name: str = Field(
        ..., 
        description="Name of the home team",
        example="Arsenal",
        min_length=1,
        max_length=50
    )
    away_team_name: str = Field(
        ..., 
        description="Name of the away team", 
        example="Chelsea",
        min_length=1,
        max_length=50
    )
    
    # Rolling form features (last 3 matches)
    home_goals_last3: float = Field(
        ..., 
        description="Total goals scored by home team in their last 3 matches",
        example=5.0,
        ge=0,
        le=30
    )
    home_conceded_last3: float = Field(
        ..., 
        description="Total goals conceded by home team in their last 3 matches",
        example=2.0,
        ge=0,
        le=30
    )
    away_goals_last3: float = Field(
        ..., 
        description="Total goals scored by away team in their last 3 matches",
        example=4.0,
        ge=0,
        le=30
    )
    away_conceded_last3: float = Field(
        ..., 
        description="Total goals conceded by away team in their last 3 matches",
        example=3.0,
        ge=0,
        le=30
    )
    
    # Rolling form features (last 5 matches)
    home_goals_last5: float = Field(
        ..., 
        description="Total goals scored by home team in their last 5 matches",
        example=8.0,
        ge=0,
        le=50
    )
    home_conceded_last5: float = Field(
        ..., 
        description="Total goals conceded by home team in their last 5 matches",
        example=4.0,
        ge=0,
        le=50
    )
    away_goals_last5: float = Field(
        ..., 
        description="Total goals scored by away team in their last 5 matches",
        example=7.0,
        ge=0,
        le=50
    )
    away_conceded_last5: float = Field(
        ..., 
        description="Total goals conceded by away team in their last 5 matches",
        example=5.0,
        ge=0,
        le=50
    )
    
    # Rolling form features (last 10 matches)
    home_goals_last10: float = Field(
        ..., 
        description="Total goals scored by home team in their last 10 matches",
        example=15.0,
        ge=0,
        le=100
    )
    home_conceded_last10: float = Field(
        ..., 
        description="Total goals conceded by home team in their last 10 matches",
        example=8.0,
        ge=0,
        le=100
    )
    away_goals_last10: float = Field(
        ..., 
        description="Total goals scored by away team in their last 10 matches",
        example=13.0,
        ge=0,
        le=100
    )
    away_conceded_last10: float = Field(
        ..., 
        description="Total goals conceded by away team in their last 10 matches",
        example=10.0,
        ge=0,
        le=100
    )
    
    # Season statistics (cumulative for current season)
    home_season_goals: float = Field(
        ..., 
        description="Total goals scored by home team in current season",
        example=45.0,
        ge=0,
        le=200
    )
    home_season_conceded: float = Field(
        ..., 
        description="Total goals conceded by home team in current season",
        example=25.0,
        ge=0,
        le=200
    )
    away_season_goals: float = Field(
        ..., 
        description="Total goals scored by away team in current season",
        example=38.0,
        ge=0,
        le=200
    )
    away_season_conceded: float = Field(
        ..., 
        description="Total goals conceded by away team in current season",
        example=30.0,
        ge=0,
        le=200
    )
    
    # Head-to-head statistics (historical matchups between these teams)
    h2h_home_wins: int = Field(
        default=0, 
        description="Number of times home team has won against away team historically",
        example=5,
        ge=0,
        le=100
    )
    h2h_away_wins: int = Field(
        default=0, 
        description="Number of times away team has won against home team historically",
        example=3,
        ge=0,
        le=100
    )
    h2h_draws: int = Field(
        default=0, 
        description="Number of draws between these teams historically",
        example=2,
        ge=0,
        le=100
    )
    
    # Optional advanced features (automatically calculated if not provided)
    home_form_points: Optional[float] = Field(
        None, 
        description="Home team form points (3 for win, 1 for draw, 0 for loss) - optional",
        example=7.0,
        ge=0,
        le=30
    )
    away_form_points: Optional[float] = Field(
        None, 
        description="Away team form points (3 for win, 1 for draw, 0 for loss) - optional",
        example=5.0,
        ge=0,
        le=30
    )
    
    class Config:
        schema_extra = {
            "example": {
                "home_team_name": "Arsenal",
                "away_team_name": "Chelsea",
                "home_goals_last3": 5.0,
                "home_conceded_last3": 2.0,
                "away_goals_last3": 4.0,
                "away_conceded_last3": 3.0,
                "home_goals_last5": 8.0,
                "home_conceded_last5": 4.0,
                "away_goals_last5": 7.0,
                "away_conceded_last5": 5.0,
                "home_goals_last10": 15.0,
                "home_conceded_last10": 8.0,
                "away_goals_last10": 13.0,
                "away_conceded_last10": 10.0,
                "home_season_goals": 45.0,
                "home_season_conceded": 25.0,
                "away_season_goals": 38.0,
                "away_season_conceded": 30.0,
                "h2h_home_wins": 5,
                "h2h_away_wins": 3,
                "h2h_draws": 2
            }
        }
    
    @validator('*', pre=True)
    def convert_nan_to_none(cls, v):
        """Convert NaN values to None for proper JSON handling."""
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
        return v


class BulkMatchFeatures(BaseModel):
    """Multiple matches for bulk prediction."""
    matches: List[MatchFeatures] = Field(..., description="List of matches to predict")
    
    @validator('matches')
    def validate_match_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one match is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 matches allowed per request")
        return v


class PredictionResponse(BaseModel):
    """
    Match prediction result with goals, outcome, and confidence.
    
    Contains the ML model's prediction for a Premier League match including
    predicted goal counts, match result, and confidence scores for each outcome.
    """
    home_team: str = Field(
        ..., 
        description="Name of the home team",
        example="Arsenal"
    )
    away_team: str = Field(
        ..., 
        description="Name of the away team",
        example="Chelsea"
    )
    predicted_home_goals: float = Field(
        ..., 
        description="Predicted number of goals for the home team (0-10 range)",
        example=1.85,
        ge=0,
        le=10
    )
    predicted_away_goals: float = Field(
        ..., 
        description="Predicted number of goals for the away team (0-10 range)",
        example=1.42,
        ge=0,
        le=10
    )
    predicted_result: str = Field(
        ..., 
        description="Predicted match result: H (Home win), D (Draw), or A (Away win)",
        example="H",
        regex="^[HDA]$"
    )
    confidence: Dict[str, float] = Field(
        ..., 
        description="Confidence scores for each possible outcome (probabilities sum to ~1.0)",
        example={
            "home_win": 0.70,
            "draw": 0.15,
            "away_win": 0.15
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "predicted_home_goals": 1.85,
                "predicted_away_goals": 1.42,
                "predicted_result": "H",
                "confidence": {
                    "home_win": 0.70,
                    "draw": 0.15,
                    "away_win": 0.15
                }
            }
        }
    
    @validator('predicted_home_goals', 'predicted_away_goals')
    def validate_goal_predictions(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Goal predictions must be between 0 and 10")
        return round(v, 2)
    
    @validator('predicted_result')
    def validate_result(cls, v):
        if v not in ['H', 'D', 'A']:
            raise ValueError("Result must be H (home win), D (draw), or A (away win)")
        return v


class BulkPredictionResponse(BaseModel):
    """Bulk prediction response."""
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")
    summary: Dict[str, Any] = Field(..., description="Prediction summary statistics")


class ErrorResponse(BaseModel):
    """
    Standard error response format for all API errors.
    
    Provides structured error information including type, message,
    and optional additional details for debugging.
    """
    error: str = Field(
        ..., 
        description="Error type or category",
        example="validation_error"
    )
    message: str = Field(
        ..., 
        description="Human-readable error message",
        example="Input validation failed"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details for debugging",
        example={"field": "home_goals_last3", "issue": "must be >= 0"}
    )


class ValidationError(BaseModel):
    """
    Individual field validation error details.
    
    Contains specific information about a single validation failure
    including the field name, error message, and invalid value.
    """
    field: str = Field(
        ..., 
        description="Name of the field with validation error",
        example="home_goals_last3"
    )
    message: str = Field(
        ..., 
        description="Validation error message for this field",
        example="ensure this value is greater than or equal to 0"
    )
    value: Any = Field(
        ..., 
        description="The invalid value that was provided",
        example=-1.0
    )


class ValidationErrorResponse(BaseModel):
    """
    Response for HTTP 422 validation errors.
    
    Returned when request data fails Pydantic model validation.
    Contains a list of all validation errors found.
    """
    error: str = Field(
        default="validation_error",
        description="Error type identifier"
    )
    message: str = Field(
        default="Input validation failed",
        description="General error message"
    )
    validation_errors: List[ValidationError] = Field(
        ..., 
        description="List of specific validation errors",
        example=[
            {
                "field": "home_goals_last3",
                "message": "ensure this value is greater than or equal to 0",
                "value": -1.0
            }
        ]
    )