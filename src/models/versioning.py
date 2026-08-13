# =============================================================================
# versioning.py
# =============================================================================
# Phase 12: Model Versioning System
#
# Tracks model versions, metadata, and lineage:
# - Version numbering (semantic versioning)
# - Training metadata (date, duration, data version)
# - Evaluation metrics (MAE, RMSE, R²)
# - Feature version tracking
# - Model lineage and comparison
# - Version registry
# =============================================================================

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
VERSIONS_DIR = os.path.join(MODELS_DIR, "versions")
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")

os.makedirs(VERSIONS_DIR, exist_ok=True)


class ModelVersion:
    """
    Represents a single model version with complete metadata.
    
    Tracks:
    - Version number (semantic versioning: major.minor.patch)
    - Model type and architecture
    - Training timestamp and duration
    - Dataset version and size
    - Evaluation metrics (train/val)
    - Feature configuration
    - File paths and checksums
    """
    
    def __init__(
        self,
        version: str,
        model_type: str,
        training_date: str,
        dataset_version: str,
        metrics: Dict[str, float],
        feature_version: str,
        **kwargs
    ):
        """
        Initialize ModelVersion.
        
        Args:
            version: Semantic version string (e.g., "1.0.0")
            model_type: Model algorithm name (e.g., "XGBoost", "RandomForest")
            training_date: ISO timestamp of training completion
            dataset_version: Dataset identifier or hash
            metrics: Dictionary of evaluation metrics
            feature_version: Feature engineering version/hash
            **kwargs: Additional metadata
        """
        self.version = version
        self.model_type = model_type
        self.training_date = training_date
        self.dataset_version = dataset_version
        self.metrics = metrics
        self.feature_version = feature_version
        self.metadata = kwargs
        
        # Auto-populate standard fields
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.description = kwargs.get("description", "")
        self.tags = kwargs.get("tags", [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "model_type": self.model_type,
            "training_date": self.training_date,
            "dataset_version": self.dataset_version,
            "metrics": self.metrics,
            "feature_version": self.feature_version,
            "created_at": self.created_at,
            "description": self.description,
            "tags": self.tags,
            **self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        """Create ModelVersion from dictionary."""
        return cls(
            version=data["version"],
            model_type=data["model_type"],
            training_date=data["training_date"],
            dataset_version=data["dataset_version"],
            metrics=data["metrics"],
            feature_version=data["feature_version"],
            **{k: v for k, v in data.items() if k not in [
                "version", "model_type", "training_date", 
                "dataset_version", "metrics", "feature_version"
            ]}
        )


class ModelRegistry:
    """
    Central registry for all model versions.
    
    Maintains:
    - Version history
    - Active/production model
    - Model comparison
    - Version lineage
    """
    
    def __init__(self, registry_path: str = REGISTRY_PATH):
        """
        Initialize ModelRegistry.
        
        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = registry_path
        self.versions: List[ModelVersion] = []
        self.active_version: Optional[str] = None
        
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from disk."""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r") as f:
                data = json.load(f)
                self.versions = [
                    ModelVersion.from_dict(v) for v in data.get("versions", [])
                ]
                self.active_version = data.get("active_version")
        else:
            self.versions = []
            self.active_version = None
    
    def _save_registry(self):
        """Save registry to disk."""
        data = {
            "active_version": self.active_version,
            "versions": [v.to_dict() for v in self.versions],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def register_version(
        self,
        version: str,
        model_type: str,
        training_date: str,
        dataset_version: str,
        metrics: Dict[str, float],
        feature_version: str,
        set_active: bool = False,
        **kwargs
    ) -> ModelVersion:
        """
        Register a new model version.
        
        Args:
            version: Version string
            model_type: Model algorithm
            training_date: Training completion timestamp
            dataset_version: Dataset identifier
            metrics: Evaluation metrics
            feature_version: Feature configuration version
            set_active: Whether to set as active version
            **kwargs: Additional metadata
            
        Returns:
            Created ModelVersion instance
        """
        # Check if version already exists
        if self.get_version(version):
            raise ValueError(f"Version {version} already exists")
        
        # Create version
        model_version = ModelVersion(
            version=version,
            model_type=model_type,
            training_date=training_date,
            dataset_version=dataset_version,
            metrics=metrics,
            feature_version=feature_version,
            **kwargs
        )
        
        # Add to registry
        self.versions.append(model_version)
        
        # Set as active if requested or if it's the first version
        if set_active or len(self.versions) == 1:
            self.active_version = version
        
        # Save registry
        self._save_registry()
        
        return model_version
    
    def get_version(self, version: str) -> Optional[ModelVersion]:
        """Get specific version by version string."""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def get_active_version(self) -> Optional[ModelVersion]:
        """Get currently active version."""
        if self.active_version:
            return self.get_version(self.active_version)
        return None
    
    def set_active_version(self, version: str):
        """Set active/production version."""
        if not self.get_version(version):
            raise ValueError(f"Version {version} not found")
        
        self.active_version = version
        self._save_registry()
    
    def list_versions(self) -> List[ModelVersion]:
        """List all registered versions."""
        return self.versions
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two model versions.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version(version1)
        v2 = self.get_version(version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Compare metrics
        metric_comparison = {}
        for metric in set(list(v1.metrics.keys()) + list(v2.metrics.keys())):
            val1 = v1.metrics.get(metric, None)
            val2 = v2.metrics.get(metric, None)
            
            if val1 is not None and val2 is not None:
                diff = val2 - val1
                pct_change = (diff / val1 * 100) if val1 != 0 else 0
                metric_comparison[metric] = {
                    "v1": val1,
                    "v2": val2,
                    "diff": diff,
                    "pct_change": pct_change
                }
        
        return {
            "version1": v1.to_dict(),
            "version2": v2.to_dict(),
            "metric_comparison": metric_comparison,
            "model_type_changed": v1.model_type != v2.model_type,
            "dataset_version_changed": v1.dataset_version != v2.dataset_version,
            "feature_version_changed": v1.feature_version != v2.feature_version
        }
    
    def get_best_version(self, metric: str = "val_mae_avg", lower_is_better: bool = True) -> Optional[ModelVersion]:
        """
        Get best performing version by metric.
        
        Args:
            metric: Metric name to compare
            lower_is_better: Whether lower values are better
            
        Returns:
            Best ModelVersion or None
        """
        versions_with_metric = [v for v in self.versions if metric in v.metrics]
        
        if not versions_with_metric:
            return None
        
        if lower_is_better:
            return min(versions_with_metric, key=lambda v: v.metrics[metric])
        else:
            return max(versions_with_metric, key=lambda v: v.metrics[metric])


def compute_file_hash(filepath: str) -> str:
    """
    Compute SHA256 hash of file.
    
    Args:
        filepath: Path to file
        
    Returns:
        Hex digest of file hash
    """
    sha256 = hashlib.sha256()
    
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def compute_dataset_version(features_path: str) -> str:
    """
    Compute dataset version from features file.
    
    Args:
        features_path: Path to features CSV
        
    Returns:
        Dataset version string (hash + timestamp)
    """
    if not os.path.exists(features_path):
        return "unknown"
    
    # Hash file
    file_hash = compute_file_hash(features_path)[:8]
    
    # Get modification time
    mtime = os.path.getmtime(features_path)
    timestamp = datetime.fromtimestamp(mtime).strftime("%Y%m%d")
    
    return f"{timestamp}_{file_hash}"


def create_model_metadata(
    version: str,
    model_type: str,
    model_files: Dict[str, str],
    metrics: Dict[str, float],
    training_config: Dict[str, Any],
    dataset_info: Dict[str, Any],
    feature_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create comprehensive model metadata.
    
    Args:
        version: Model version string
        model_type: Model algorithm name
        model_files: Dictionary of model file paths
        metrics: Evaluation metrics
        training_config: Training configuration
        dataset_info: Dataset information
        feature_info: Feature information
        
    Returns:
        Complete metadata dictionary
    """
    metadata = {
        "version": version,
        "model_type": model_type,
        "training_date": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        
        # Model files
        "model_files": model_files,
        "file_hashes": {
            name: compute_file_hash(path) if os.path.exists(path) else "missing"
            for name, path in model_files.items()
        },
        
        # Metrics
        "metrics": metrics,
        
        # Training configuration
        "training_config": training_config,
        
        # Dataset information
        "dataset_info": dataset_info,
        "dataset_version": dataset_info.get("version", "unknown"),
        
        # Feature information
        "feature_info": feature_info,
        "feature_version": feature_info.get("version", "unknown"),
        
        # System information
        "python_version": sys.version,
        "environment": {
            "cwd": os.getcwd(),
            "user": os.environ.get("USERNAME", "unknown")
        }
    }
    
    return metadata


def save_model_metadata(metadata: Dict[str, Any], output_path: str):
    """
    Save model metadata to JSON file.
    
    Args:
        metadata: Metadata dictionary
        output_path: Output file path
    """
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)


def load_model_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load model metadata from JSON file.
    
    Args:
        metadata_path: Metadata file path
        
    Returns:
        Metadata dictionary
    """
    with open(metadata_path, "r") as f:
        return json.load(f)


def version_current_models():
    """
    Create version metadata for currently trained models.
    
    Reads existing model files and creates version 1.0.0 entry.
    """
    print("=" * 70)
    print("MODEL VERSIONING: Creating Version 1.0.0")
    print("=" * 70)
    print()
    
    # Check if models exist
    best_model_json = os.path.join(MODELS_DIR, "best_model.json")
    if not os.path.exists(best_model_json):
        print("✗ No trained models found")
        print("  Please run Phase 9 training first")
        return
    
    # Load existing model metadata
    with open(best_model_json, "r") as f:
        existing_metadata = json.load(f)
    
    print("[1] Loading existing model metadata...")
    print(f"  Model: {existing_metadata.get('best_model_name', 'Unknown')}")
    print(f"  Training date: {existing_metadata.get('timestamp', 'Unknown')}")
    print()
    
    # Compute dataset version
    features_path = os.path.join(PROJECT_ROOT, "data", "features", "match_features.csv")
    dataset_version = compute_dataset_version(features_path)
    
    print(f"[2] Computing versions...")
    print(f"  Dataset version: {dataset_version}")
    
    # Compute feature version (hash of feature columns)
    if os.path.exists(features_path):
        import pandas as pd
        df = pd.read_csv(features_path, nrows=1)
        feature_cols = sorted([c for c in df.columns if c not in [
            "match_id", "row_id", "season", "match_date", "is_fixture",
            "home_team_id", "away_team_id", "home_team_name", "away_team_name",
            "result", "home_goals", "away_goals"
        ]])
        feature_hash = hashlib.sha256(
            ",".join(feature_cols).encode()
        ).hexdigest()[:8]
        feature_version = f"v1_{feature_hash}"
    else:
        feature_version = "v1_unknown"
    
    print(f"  Feature version: {feature_version}")
    print()
    
    # Create comprehensive metadata
    print("[3] Creating version metadata...")
    
    model_files = {
        "home_model": os.path.join(MODELS_DIR, "best_model_home.pkl"),
        "away_model": os.path.join(MODELS_DIR, "best_model_away.pkl"),
        "metadata": best_model_json
    }
    
    metrics = {
        "val_mae_avg": existing_metadata.get("val_mae_avg", 0.0),
        "val_r2_avg": existing_metadata.get("val_r2_avg", 0.0),
        "val_mae_home": existing_metadata.get("val_mae_home", 0.0),
        "val_rmse_home": existing_metadata.get("val_rmse_home", 0.0),
        "val_r2_home": existing_metadata.get("val_r2_home", 0.0),
        "val_mae_away": existing_metadata.get("val_mae_away", 0.0),
        "val_rmse_away": existing_metadata.get("val_rmse_away", 0.0),
        "val_r2_away": existing_metadata.get("val_r2_away", 0.0)
    }
    
    training_config = {
        "algorithm": existing_metadata.get("best_model_name", "Unknown"),
        "target": "regression (home_goals, away_goals)",
        "train_seasons": ["2018/19", "2019/20", "2020/21", "2021/22", "2022/23", "2023/24", "2024/25"],
        "val_seasons": ["2025/26"],
        "train_samples": existing_metadata.get("train_samples", 2660),
        "val_samples": existing_metadata.get("val_samples", 380),
        "features_count": existing_metadata.get("features_count", 372)
    }
    
    dataset_info = {
        "version": dataset_version,
        "features_file": "match_features.csv",
        "seasons": "2018/19 - 2025/26",
        "historical_matches": 3040,
        "fixtures": 380
    }
    
    feature_info = {
        "version": feature_version,
        "count": training_config["features_count"],
        "categories": [
            "rolling_form (last3, last5, last10, last38)",
            "season_stats (prior season aggregates)",
            "head_to_head (historical matchups)",
            "relative_features (home - away)",
            "venue_splits (home vs away performance)"
        ]
    }
    
    metadata = create_model_metadata(
        version="1.0.0",
        model_type=existing_metadata.get("best_model_name", "Unknown"),
        model_files=model_files,
        metrics=metrics,
        training_config=training_config,
        dataset_info=dataset_info,
        feature_info=feature_info
    )
    
    # Add additional metadata
    metadata["description"] = "Initial production model - Phase 9 training"
    metadata["tags"] = ["production", "baseline", "phase-9"]
    metadata["note"] = existing_metadata.get("note", "")
    
    # Save version metadata
    version_metadata_path = os.path.join(VERSIONS_DIR, "version_1.0.0.json")
    save_model_metadata(metadata, version_metadata_path)
    print(f"  ✓ Saved: {version_metadata_path}")
    print()
    
    # Register in registry
    print("[4] Registering version in model registry...")
    registry = ModelRegistry()
    registry.register_version(
        version="1.0.0",
        model_type=metadata["model_type"],
        training_date=metadata["training_date"],
        dataset_version=metadata["dataset_version"],
        metrics=metadata["metrics"],
        feature_version=metadata["feature_version"],
        set_active=True,
        description=metadata["description"],
        tags=metadata["tags"],
        model_files=metadata["model_files"],
        file_hashes=metadata["file_hashes"],
        training_config=metadata["training_config"],
        dataset_info=metadata["dataset_info"],
        feature_info=metadata["feature_info"]
    )
    print(f"  ✓ Registered version 1.0.0")
    print(f"  ✓ Set as active version")
    print()
    
    # Generate summary report
    print("[5] Generating version summary...")
    summary_path = os.path.join(VERSIONS_DIR, "VERSION_SUMMARY.md")
    
    summary = f"""# Model Version Summary

**Version**: 1.0.0  
**Status**: Active  
**Model Type**: {metadata['model_type']}  
**Training Date**: {metadata['training_date']}  

---

## Version Information

- **Version**: 1.0.0 (Semantic versioning)
- **Status**: Active/Production
- **Description**: {metadata['description']}
- **Tags**: {', '.join(metadata['tags'])}

---

## Model Files

| File | Path | Hash |
|------|------|------|
| Home Model | {model_files['home_model']} | {metadata['file_hashes']['home_model'][:16]}... |
| Away Model | {model_files['away_model']} | {metadata['file_hashes']['away_model'][:16]}... |
| Metadata | {model_files['metadata']} | {metadata['file_hashes']['metadata'][:16]}... |

---

## Performance Metrics

### Overall
- **Validation MAE (avg)**: {metrics['val_mae_avg']:.4f} goals
- **Validation R² (avg)**: {metrics['val_r2_avg']:.4f}

### Home Goals Model
- **MAE**: {metrics['val_mae_home']:.4f}
- **RMSE**: {metrics['val_rmse_home']:.4f}
- **R²**: {metrics['val_r2_home']:.4f}

### Away Goals Model
- **MAE**: {metrics['val_mae_away']:.4f}
- **RMSE**: {metrics['val_rmse_away']:.4f}
- **R²**: {metrics['val_r2_away']:.4f}

---

## Training Configuration

- **Algorithm**: {training_config['algorithm']}
- **Target**: {training_config['target']}
- **Train Seasons**: {', '.join(training_config['train_seasons'])}
- **Validation Seasons**: {', '.join(training_config['val_seasons'])}
- **Training Samples**: {training_config['train_samples']:,}
- **Validation Samples**: {training_config['val_samples']:,}
- **Features**: {training_config['features_count']}

---

## Dataset Information

- **Dataset Version**: {dataset_info['version']}
- **Features File**: {dataset_info['features_file']}
- **Seasons Covered**: {dataset_info['seasons']}
- **Historical Matches**: {dataset_info['historical_matches']:,}
- **Future Fixtures**: {dataset_info['fixtures']}

---

## Feature Configuration

- **Feature Version**: {feature_info['version']}
- **Feature Count**: {feature_info['count']}
- **Feature Categories**:
{chr(10).join(f"  - {cat}" for cat in feature_info['categories'])}

---

## Version History

| Version | Date | Model Type | MAE | R² | Status |
|---------|------|------------|-----|----|----|
| 1.0.0 | {metadata['training_date'][:10]} | {metadata['model_type']} | {metrics['val_mae_avg']:.4f} | {metrics['val_r2_avg']:.4f} | Active |

---

## Usage

### Loading Model

```python
from src.models.model_loader import load_best_models

models_dir = "models"
home_model, away_model, metadata = load_best_models(models_dir)
```

### Checking Version

```python
from src.models.versioning import ModelRegistry

registry = ModelRegistry()
active_version = registry.get_active_version()
print(f"Active version: {{active_version.version}}")
print(f"Model type: {{active_version.model_type}}")
print(f"MAE: {{active_version.metrics['val_mae_avg']:.4f}}")
```

---

## Next Version

To create version 1.1.0:
1. Retrain model with same architecture on updated data
2. Update `version_current_models()` with new version number
3. Register in model registry
4. Compare with version 1.0.0

To create version 2.0.0:
1. Change model architecture or training approach
2. Document breaking changes
3. Register as major version update

---
"""
    
    with open(summary_path, "w") as f:
        f.write(summary)
    
    print(f"  ✓ Saved: {summary_path}")
    print()
    
    print("=" * 70)
    print("MODEL VERSIONING COMPLETE")
    print("=" * 70)
    print()
    print("Created:")
    print(f"  - {version_metadata_path}")
    print(f"  - {REGISTRY_PATH}")
    print(f"  - {summary_path}")
    print()
    print("Version 1.0.0 registered and set as active")
    print()


if __name__ == "__main__":
    version_current_models()
