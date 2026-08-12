# Model Selection Report
## Phase 9: Model Comparison

**Date**: 2026-08-12 21:29  
**Target**: Goal prediction (home_goals, away_goals)  
**Evaluation Metrics**: MAE, RMSE, R²

---

## Models Trained

4 models were trained and evaluated:

- Linear_Regression
- Ridge
- Random_Forest
- Gradient_Boosting

---

## Validation Performance

| Model | MAE (avg) | RMSE (avg) | R² (avg) | Overfit (MAE) |
|-------|-----------|------------|----------|---------------|
| Random_Forest | 0.8889 | 1.0928 | 0.0569 | -0.3288 |
| Ridge | 0.9137 | 1.1393 | -0.0256 | -0.0274 |
| Linear_Regression | 0.9197 | 1.1466 | -0.0388 | -0.0370 |
| Gradient_Boosting | 0.9492 | 1.1595 | -0.0634 | -0.7191 |

---

## Best Model

**Winner**: Random_Forest

**Performance**:
- Validation MAE (average): 0.8889
- Validation RMSE (average): 1.0928
- Validation R² (average): 0.0569

**Home Goals Prediction**:
- MAE: 0.9335
- RMSE: 1.1225
- R²: 0.0771

**Away Goals Prediction**:
- MAE: 0.8443
- RMSE: 1.0632
- R²: 0.0368

---

## Overfitting Analysis

Overfitting is measured as (train_metric - val_metric):
- Negative MAE diff = good (val better than expected)
- Positive R² diff = overfitting

| Model | MAE Overfit | R² Overfit | Assessment |
|-------|-------------|------------|------------|
| Random_Forest | -0.3288 | 0.5691 | Moderate |
| Ridge | -0.0274 | 0.2124 | Good |
| Linear_Regression | -0.0370 | 0.2291 | Good |
| Gradient_Boosting | -0.7191 | 0.9542 | High |

---

## Conclusion

The Random_Forest model was selected based on validation performance. It achieves an average MAE of 0.8889 goals per match, meaning predictions are typically within 0.89 goals of the actual score.

**Saved Models**:
- `models/best_model_home.pkl` (home goals predictor)
- `models/best_model_away.pkl` (away goals predictor)
- `models/best_model.json` (metadata)

**Next Steps**:
- Use best model for 2026/27 predictions
- Consider ensemble methods
- Add player features for improvement

---

Generated: 2026-08-12T21:29:14.396158
