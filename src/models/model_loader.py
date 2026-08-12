# =============================================================================
# model_loader.py
# =============================================================================
# Phase 10: Model Loading and Validation
#
# Responsible for:
# - Loading trained models from disk
# - Validating model integrity
# - Managing model versioning and metadata
# - Providing safe access to prediction models
# =============================================================================

import os
import json
import joblib
from datetime import datetime
from typing import Dict, Tuple, Optional


class ModelLoadError(Exception):
    """Raised when model loading fails"""
    pass


class ModelLoader:
    """
    Loads and validates trained ML models for prediction.
    
    Handles:
    - Loading separate home/away goal prediction models
    - Validating model metadata
    - Version checking
    - Error handling for missing/corrupted models
    """
    
    def __init__(self, models_dir: str):
        """
        Initialize ModelLoader.
        
        Args:
            models_dir: Path to directory containing trained models
        """
        self.models_dir = models_dir
        self.metadata: Optional[Dict] = None
        self.home_model = None
        self.away_model = None
        self.loaded_at: Optional[datetime] = None
    
    def load_models(self) -> Tuple[object, object, Dict]:
        """
        Load the best trained models (home and away).
        
        Returns:
            Tuple of (home_model, away_model, metadata)
            
        Raises:
            ModelLoadError: If models cannot be loaded or are invalid
        """
        print("Loading trained models...")
        
        # Load metadata
        metadata_path = os.path.join(self.models_dir, "best_model.json")
        if not os.path.exists(metadata_path):
            raise ModelLoadError(
                f"Model metadata not found: {metadata_path}\n"
                "Please run Phase 9 (train_compare_models.py) first."
            )
        
        try:
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
        except json.JSONDecodeError as e:
            raise ModelLoadError(f"Invalid model metadata JSON: {e}")
        
        # Validate metadata structure
        required_keys = ["best_model_name", "home_model_path", "away_model_path"]
        missing = [k for k in required_keys if k not in self.metadata]
        if missing:
            raise ModelLoadError(f"Missing required metadata keys: {missing}")
        
        # Load home model
        home_path = os.path.join(self.models_dir, self.metadata["home_model_path"])
        if not os.path.exists(home_path):
            raise ModelLoadError(f"Home model not found: {home_path}")
        
        try:
            self.home_model = joblib.load(home_path)
        except Exception as e:
            raise ModelLoadError(f"Failed to load home model: {e}")
        
        # Load away model
        away_path = os.path.join(self.models_dir, self.metadata["away_model_path"])
        if not os.path.exists(away_path):
            raise ModelLoadError(f"Away model not found: {away_path}")
        
        try:
            self.away_model = joblib.load(away_path)
        except Exception as e:
            raise ModelLoadError(f"Failed to load away model: {e}")
        
        self.loaded_at = datetime.now()
        
        print(f"  ✓ Loaded model: {self.metadata['best_model_name']}")
        print(f"  ✓ Home model: {self.metadata['home_model_path']}")
        print(f"  ✓ Away model: {self.metadata['away_model_path']}")
        print(f"  ✓ Validation MAE: {self.metadata.get('val_mae_avg', 'N/A')}")
        print(f"  ✓ Loaded at: {self.loaded_at.isoformat()}")
        print()
        
        return self.home_model, self.away_model, self.metadata
    
    def validate_model(self) -> bool:
        """
        Validate that models are loaded and functional.
        
        Returns:
            True if models are valid, False otherwise
        """
        if self.home_model is None or self.away_model is None:
            return False
        
        # Check that models have predict method
        if not hasattr(self.home_model, "predict") or not hasattr(self.away_model, "predict"):
            return False
        
        return True
    
    def get_model_info(self) -> Dict:
        """
        Get model metadata and loading information.
        
        Returns:
            Dictionary with model information
        """
        if self.metadata is None:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": self.metadata.get("best_model_name", "Unknown"),
            "home_model_path": self.metadata.get("home_model_path"),
            "away_model_path": self.metadata.get("away_model_path"),
            "val_mae_avg": self.metadata.get("val_mae_avg"),
            "val_r2_avg": self.metadata.get("val_r2_avg"),
            "trained_timestamp": self.metadata.get("timestamp"),
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "features_count": self.metadata.get("features_count"),
            "train_samples": self.metadata.get("train_samples")
        }
    
    def get_feature_list(self) -> Optional[list]:
        """
        Extract feature names from trained model if available.
        
        Returns:
            List of feature names or None if not available
        """
        if self.home_model is None:
            return None
        
        # Try to get feature names from the pipeline
        try:
            # sklearn pipelines have a named_steps attribute
            if hasattr(self.home_model, "named_steps"):
                regressor = self.home_model.named_steps.get("regressor")
                if hasattr(regressor, "feature_names_in_"):
                    return list(regressor.feature_names_in_)
                # For tree-based models
                if hasattr(regressor, "n_features_in_"):
                    return [f"feature_{i}" for i in range(regressor.n_features_in_)]
        except Exception:
            pass
        
        return None


def load_best_models(models_dir: str) -> Tuple[object, object, Dict]:
    """
    Convenience function to load best models.
    
    Args:
        models_dir: Path to models directory
        
    Returns:
        Tuple of (home_model, away_model, metadata)
        
    Raises:
        ModelLoadError: If loading fails
    """
    loader = ModelLoader(models_dir)
    return loader.load_models()


if __name__ == "__main__":
    # Test model loading
    import sys
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    models_dir = os.path.join(project_root, "models")
    
    print("=" * 70)
    print("MODEL LOADER TEST")
    print("=" * 70)
    print()
    
    try:
        loader = ModelLoader(models_dir)
        home_model, away_model, metadata = loader.load_models()
        
        print("Model validation:")
        is_valid = loader.validate_model()
        print(f"  Valid: {is_valid}")
        print()
        
        print("Model info:")
        info = loader.get_model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        
        print("✓ Model loading test PASSED")
        
    except ModelLoadError as e:
        print(f"✗ Model loading test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
