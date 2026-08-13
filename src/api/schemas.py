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
    """Health check response."""
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")


class ModelInfoResponse(BaseModel):
    """Model information response."""
    model_version: str = Field(..., description="Model version")
    model_type: str = Field(..., description="Model algorithm")
    training_date: str = Field(..., description="When model was trained")
    metrics: Dict[str, float] = Field(..., description="Model performance metrics")
    feature_count: int = Field(..., description="Number of features")
    description: str = Field(..., description="Model description")


class MatchFeatures(BaseModel):
    """Input features for match prediction."""
    
    # Team identifiers
    home_team_name: str = Field(..., description="Home team name", example="Arsenal")
    away_team_name: str = Field(..., description="Away team name", example="Chelsea")
    
    # Rolling form features (last 3 matches)
    home_goals_last3: float = Field(..., description="Home team goals in last 3 matches", ge=0)
    home_conceded_last3: float = Field(..., description="Home team goals conceded in last 3", ge=0)
    away_goals_last3: float = Field(..., description="Away team goals in last 3 matches", ge=0)
    away_conceded_last3: float = Field(..., description="Away team goals conceded in last 3", ge=0)
    
    # Rolling form features (last 5 matches)
    home_goals_last5: float = Field(..., description="Home team goals in last 5 matches", ge=0)
    home_conceded_last5: float = Field(..., description="Home team goals conceded in last 5", ge=0)
    away_goals_last5: float = Field(..., description="Away team goals in last 5 matches", ge=0)
    away_conceded_last5: float = Field(..., description="Away team goals conceded in last 5", ge=0)
    
    # Rolling form features (last 10 matches)
    home_goals_last10: float = Field(..., description="Home team goals in last 10 matches", ge=0)
    home_conceded_last10: float = Field(..., description="Home team goals conceded in last 10", ge=0)
    away_goals_last10: float = Field(..., description="Away team goals in last 10 matches", ge=0)
    away_conceded_last10: float = Field(..., description="Away team goals conceded in last 10", ge=0)
    
    # Season stats
    home_season_goals: float = Field(..., description="Home team total season goals", ge=0)
    home_season_conceded: float = Field(..., description="Home team total season conceded", ge=0)
    away_season_goals: float = Field(..., description="Away team total season goals", ge=0)
    away_season_conceded: float = Field(..., description="Away team total season conceded", ge=0)
    
    # Head-to-head stats
    h2h_home_wins: int = Field(0, description="Historical home wins in H2H", ge=0)
    h2h_away_wins: int = Field(0, description="Historical away wins in H2H", ge=0)
    h2h_draws: int = Field(0, description="Historical draws in H2H", ge=0)
    
    # Optional features with defaults
    home_form_points: Optional[float] = Field(None, description="Home team form points")
    away_form_points: Optional[float] = Field(None, description="Away team form points")
    
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
    """Single match prediction response."""
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    predicted_home_goals: float = Field(..., description="Predicted home team goals")
    predicted_away_goals: float = Field(..., description="Predicted away team goals")
    predicted_result: str = Field(..., description="Predicted result (H/D/A)")
    confidence: Dict[str, float] = Field(..., description="Prediction confidence scores")
    
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
    """Error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    message: str = "Input validation failed"
    validation_errors: List[ValidationError] = Field(..., description="List of validation errors")