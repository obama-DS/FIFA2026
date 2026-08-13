# =============================================================================
# main.py
# =============================================================================
# Phase 14: FastAPI Main Application
#
# FastAPI backend for Premier League ML predictions
# Endpoints: /health, /model-info, /predict
# =============================================================================

import os
import sys
from datetime import datetime
from typing import Dict, Any
import logging

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from src.api.schemas import (
    HealthResponse, ModelInfoResponse, MatchFeatures, BulkMatchFeatures,
    PredictionResponse, BulkPredictionResponse, ErrorResponse, ValidationErrorResponse
)
from src.models.model_loader import load_best_models
from src.models.versioning import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Premier League ML Prediction API",
    description="FastAPI backend for Premier League match predictions using ML models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for loaded models
home_model = None
away_model = None
model_metadata = None
model_registry = None
feature_columns = None

def load_models_on_startup():
    """Load ML models and metadata on application startup."""
    global home_model, away_model, model_metadata, model_registry, feature_columns
    
    try:
        logger.info("Loading ML models...")
        
        # Load models
        models_dir = os.path.join(project_root, "models")
        home_model, away_model, model_metadata = load_best_models(models_dir)
        
        # Load model registry
        model_registry = ModelRegistry()
        
        # Load feature columns from sample data
        features_path = os.path.join(project_root, "data", "features", "match_features.csv")
        if os.path.exists(features_path):
            sample_df = pd.read_csv(features_path, nrows=1)
            feature_columns = [col for col in sample_df.columns if col not in [
                "match_id", "row_id", "season", "match_date", "is_fixture",
                "home_team_id", "away_team_id", "home_team_name", "away_team_name",
                "result", "home_goals", "away_goals"
            ]]
        else:
            # Fallback feature list based on actual dataset columns
            feature_columns = [
                "home_gf_last3", "home_ga_last3", "away_gf_last3", "away_ga_last3",
                "home_gf_last5", "home_ga_last5", "away_gf_last5", "away_ga_last5",
                "home_gf_last10", "home_ga_last10", "away_gf_last10", "away_ga_last10",
                "home_gf_season", "home_ga_season", "away_gf_season", "away_ga_season",
                "h2h_last3_home_wins", "h2h_last3_away_wins", "h2h_last3_draws"
            ]
        
        logger.info(f"Models loaded successfully. Feature count: {len(feature_columns)}")
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


def prepare_features(match_data: MatchFeatures) -> pd.DataFrame:
    """Convert match data to model features DataFrame."""
    # Extract features from match data
    features_dict = {}
    
    # Map schema fields to actual feature columns from training data
    field_mapping = {
        "home_goals_last3": "home_gf_last3",
        "home_conceded_last3": "home_ga_last3", 
        "away_goals_last3": "away_gf_last3",
        "away_conceded_last3": "away_ga_last3",
        "home_goals_last5": "home_gf_last5",
        "home_conceded_last5": "home_ga_last5",
        "away_goals_last5": "away_gf_last5", 
        "away_conceded_last5": "away_ga_last5",
        "home_goals_last10": "home_gf_last10",
        "home_conceded_last10": "home_ga_last10",
        "away_goals_last10": "away_gf_last10",
        "away_conceded_last10": "away_ga_last10",
        "home_season_goals": "home_gf_season",
        "home_season_conceded": "home_ga_season",
        "away_season_goals": "away_gf_season",
        "away_season_conceded": "away_ga_season",
        "h2h_home_wins": "h2h_last3_home_wins",
        "h2h_away_wins": "h2h_last3_away_wins", 
        "h2h_draws": "h2h_last3_draws"
    }
    
    # Extract available features
    for schema_field, feature_col in field_mapping.items():
        if hasattr(match_data, schema_field):
            value = getattr(match_data, schema_field)
            if value is not None:
                features_dict[feature_col] = value
    
    # Fill missing features with default values for all expected features
    for col in feature_columns:
        if col not in features_dict:
            features_dict[col] = 0.0
    
    # Create DataFrame with single row
    features_df = pd.DataFrame([features_dict])
    
    # Ensure all expected feature columns are present
    for col in feature_columns:
        if col not in features_df.columns:
            features_df[col] = 0.0
    
    # Select only the feature columns in correct order
    features_df = features_df[feature_columns]
    
    return features_df


def predict_result(home_goals: float, away_goals: float) -> str:
    """Determine match result from goal predictions."""
    goal_diff = home_goals - away_goals
    
    if goal_diff > 0.5:
        return "H"  # Home win
    elif goal_diff < -0.5:
        return "A"  # Away win
    else:
        return "D"  # Draw


def calculate_confidence(home_goals: float, away_goals: float) -> Dict[str, float]:
    """Calculate confidence scores for each outcome."""
    goal_diff = abs(home_goals - away_goals)
    
    # Simple confidence calculation based on goal difference
    if goal_diff > 2.0:
        high_conf = 0.85
        low_conf = 0.075
        mid_conf = 0.075
    elif goal_diff > 1.0:
        high_conf = 0.70
        low_conf = 0.15
        mid_conf = 0.15
    else:
        high_conf = 0.45
        low_conf = 0.30
        mid_conf = 0.25
    
    result = predict_result(home_goals, away_goals)
    
    if result == "H":
        return {"home_win": high_conf, "draw": mid_conf, "away_win": low_conf}
    elif result == "A":
        return {"home_win": low_conf, "draw": mid_conf, "away_win": high_conf}
    else:
        return {"home_win": low_conf, "draw": high_conf, "away_win": low_conf}


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error", 
            message="Internal server error",
            details={"error_type": type(exc).__name__}
        ).dict()
    )


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    load_models_on_startup()


# API Endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns API status, timestamp, and version information.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """
    Get information about the loaded ML model.
    
    Returns model version, type, training date, metrics, and description.
    """
    if model_registry is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        active_version = model_registry.get_active_version()
        
        if active_version is None:
            raise HTTPException(status_code=500, detail="No active model version")
        
        return ModelInfoResponse(
            model_version=active_version.version,
            model_type=active_version.model_type,
            training_date=active_version.training_date,
            metrics=active_version.metrics,
            feature_count=len(feature_columns) if feature_columns else 0,
            description=active_version.description
        )
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving model info: {str(e)}")


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_match(match: MatchFeatures):
    """
    Predict the outcome of a single match.
    
    Takes match features and returns predicted goals and result.
    """
    if home_model is None or away_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        # Prepare features
        features_df = prepare_features(match)
        
        # Generate predictions
        home_pred = home_model.predict(features_df)[0]
        away_pred = away_model.predict(features_df)[0]
        
        # Clip predictions to valid range
        home_pred = np.clip(home_pred, 0, 10)
        away_pred = np.clip(away_pred, 0, 10)
        
        # Determine result and confidence
        result = predict_result(home_pred, away_pred)
        confidence = calculate_confidence(home_pred, away_pred)
        
        return PredictionResponse(
            home_team=match.home_team_name,
            away_team=match.away_team_name,
            predicted_home_goals=round(home_pred, 2),
            predicted_away_goals=round(away_pred, 2),
            predicted_result=result,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/bulk", response_model=BulkPredictionResponse, tags=["Prediction"])
async def predict_bulk_matches(bulk_request: BulkMatchFeatures):
    """
    Predict outcomes for multiple matches.
    
    Takes a list of matches and returns predictions for all.
    """
    if home_model is None or away_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        predictions = []
        home_goals_total = 0
        away_goals_total = 0
        results_count = {"H": 0, "D": 0, "A": 0}
        
        for match in bulk_request.matches:
            # Prepare features
            features_df = prepare_features(match)
            
            # Generate predictions
            home_pred = home_model.predict(features_df)[0]
            away_pred = away_model.predict(features_df)[0]
            
            # Clip predictions
            home_pred = np.clip(home_pred, 0, 10)
            away_pred = np.clip(away_pred, 0, 10)
            
            # Determine result and confidence
            result = predict_result(home_pred, away_pred)
            confidence = calculate_confidence(home_pred, away_pred)
            
            prediction = PredictionResponse(
                home_team=match.home_team_name,
                away_team=match.away_team_name,
                predicted_home_goals=round(home_pred, 2),
                predicted_away_goals=round(away_pred, 2),
                predicted_result=result,
                confidence=confidence
            )
            
            predictions.append(prediction)
            home_goals_total += home_pred
            away_goals_total += away_pred
            results_count[result] += 1
        
        # Calculate summary statistics
        num_matches = len(predictions)
        summary = {
            "total_matches": num_matches,
            "avg_home_goals": round(home_goals_total / num_matches, 2),
            "avg_away_goals": round(away_goals_total / num_matches, 2),
            "predicted_results": results_count,
            "home_wins_percentage": round((results_count["H"] / num_matches) * 100, 1),
            "draws_percentage": round((results_count["D"] / num_matches) * 100, 1),
            "away_wins_percentage": round((results_count["A"] / num_matches) * 100, 1)
        }
        
        return BulkPredictionResponse(
            predictions=predictions,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Bulk prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk prediction failed: {str(e)}")


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )