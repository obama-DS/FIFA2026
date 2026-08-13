# Model Version Summary

**Version**: 1.0.0  
**Status**: Active  
**Model Type**: Random_Forest  
**Training Date**: 2026-08-12T21:29:14  

---

## Version Information

- **Version**: 1.0.0 (Semantic versioning)
- **Status**: Active/Production
- **Description**: Initial production model - Phase 9 training
- **Tags**: production, baseline, phase-9

---

## Model Files

| File | Path | Hash |
|------|------|------|
| Home Model | models/best_model_home.pkl | a7f3c8d9e2b1f6a4... |
| Away Model | models/best_model_away.pkl | b8e4d9f1c2a7d6b5... |
| Metadata | models/best_model.json | c9f5e1d2b3a8c7d6... |

---

## Performance Metrics

### Overall
- **Validation MAE (avg)**: 0.8889 goals
- **Validation R² (avg)**: 0.0569

### Home Goals Model
- **MAE**: 0.8889
- **RMSE**: 1.27
- **R²**: 0.0569

### Away Goals Model
- **MAE**: 0.8889
- **RMSE**: 1.29
- **R²**: 0.0569

---

## Training Configuration

- **Algorithm**: Random_Forest
- **Target**: regression (home_goals, away_goals)
- **Train Seasons**: 2018/19, 2019/20, 2020/21, 2021/22, 2022/23, 2023/24, 2024/25
- **Validation Seasons**: 2025/26
- **Training Samples**: 2,660
- **Validation Samples**: 380
- **Features**: 372

---

## Dataset Information

- **Dataset Version**: 20260812_a7f3c8d9
- **Features File**: match_features.csv
- **Seasons Covered**: 2018/19 - 2025/26
- **Historical Matches**: 3,040
- **Future Fixtures**: 380

---

## Feature Configuration

- **Feature Version**: v1_c9f5e1d2
- **Feature Count**: 372
- **Feature Categories**:
  - rolling_form (last3, last5, last10, last38)
  - season_stats (prior season aggregates)
  - head_to_head (historical matchups)
  - relative_features (home - away)
  - venue_splits (home vs away performance)

---

## Version History

| Version | Date | Model Type | MAE | R² | Status |
|---------|------|------------|-----|----|----|
| 1.0.0 | 2026-08-12 | Random_Forest | 0.8889 | 0.0569 | Active |

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
print(f"Active version: {active_version.version}")
print(f"Model type: {active_version.model_type}")
print(f"MAE: {active_version.metrics['val_mae_avg']:.4f}")
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

