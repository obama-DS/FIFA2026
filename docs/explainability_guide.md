# Model Explainability Quick Reference Guide

## Phase 11: Understanding Your Predictions

**Audience**: End users, analysts, stakeholders  
**Purpose**: Quickly understand why models predict certain scores

---

## Quick Start

### What is Model Explainability?

Model explainability answers: **"Why did the model predict this score?"**

For every match prediction (e.g., Arsenal 2.1 - 0.9 Wolves), the explainability layer shows:
1. **Which features** influenced the prediction
2. **How much** each feature contributed
3. **In what direction** (increased or decreased the prediction)

---

## Reading Feature Importance

### Global Feature Importance

Shows which features are most important **across all predictions**.

**Example - Home Goals Top 5:**
```
1. gf_last5_home       (0.082) - Goals scored in last 5 home matches
2. gf_last3_home       (0.071) - Goals scored in last 3 home matches  
3. ga_last5_away       (0.065) - Opponent's away goals conceded
4. home_ppg_last10     (0.059) - Points per game in last 10
5. xg_per_match_home   (0.054) - Expected goals per match at home
```

**Interpretation**:
- Recent goal-scoring form (#1, #2) is most predictive
- Opponent's defensive weakness (#3) matters
- Overall form (#4) and quality (#5) also important

**Rule of Thumb**:
- Importance >0.05 = **Critical feature**
- Importance 0.02-0.05 = **High importance**
- Importance 0.01-0.02 = **Moderate importance**
- Importance <0.01 = **Low importance**

---

## Reading SHAP Values (Individual Matches)

SHAP values explain **specific predictions** for individual matches.

### Example: Arsenal vs Wolves

**Prediction**: Arsenal 2.14 - 0.87 Wolves

#### Arsenal Home Goals (2.14)

**Top Features Increasing Prediction:**
```
Feature                    SHAP      Value   Interpretation
gf_last5_home             +0.35     8.5     Arsenal scored 8.5 goals in last 5 home matches
xg_per_match_home         +0.29     2.1     Arsenal creates 2.1 xG per home match
home_ppg_last10           +0.23     2.4     Arsenal earning 2.4 pts/game (winning form)
```

**Top Features Decreasing Prediction:**
```
Feature                    SHAP      Value   Interpretation
ga_last5_away             -0.10     3.2     Wolves only conceded 3.2 away goals (decent defense)
```

**How to Read**:
- **SHAP = +0.35**: This feature adds ~0.35 goals to the prediction
- **Value = 8.5**: Arsenal scored 8.5 goals in their last 5 home matches
- **Interpretation**: Strong recent form boosts prediction significantly

**Total Effect**:
```
Base prediction:       ~1.50 goals (average across all matches)
+ gf_last5_home:       +0.35
+ xg_per_match_home:   +0.29
+ home_ppg_last10:     +0.23
- ga_last5_away:       -0.10
+ ... other features
= Final prediction:     2.14 goals
```

---

## SHAP Value Interpretation Table

| SHAP Value | Effect Size | Real-World Example |
|------------|-------------|-------------------|
| **+0.50 or more** | **Very Strong Positive** | Man City at home after scoring 12 goals in 5 matches |
| **+0.20 to +0.49** | **Moderate Positive** | Liverpool at home with 8 goals in 5 matches |
| **+0.01 to +0.19** | **Small Positive** | Slight above-average recent form |
| **0.00** | **No Effect** | Average feature value for this position |
| **-0.01 to -0.19** | **Small Negative** | Slightly below-average performance |
| **-0.20 to -0.49** | **Moderate Negative** | Poor recent form (2-3 goals in 5 matches) |
| **-0.50 or less** | **Very Strong Negative** | Terrible form facing elite defense |

---

## Common Feature Patterns

### 1. Recent Form Features

**Pattern**: `_last3`, `_last5`, `_last10`

| Feature | Meaning | When It's High | When It's Low |
|---------|---------|----------------|---------------|
| `gf_last5_home` | Goals scored in last 5 home matches | Team in hot scoring form | Team struggling to score |
| `ga_last5_away` | Opponent's goals conceded away | Opponent has weak defense | Opponent has strong defense |
| `ppg_last10` | Points per game in last 10 | Team winning consistently | Team in poor form |

**Example**:
- Arsenal: `gf_last5_home = 10` → SHAP = +0.40 (very positive)
- Wolves: `ga_last5_away = 2` → SHAP = -0.15 (hurts Arsenal's prediction)

### 2. Expected Goals (xG)

**Pattern**: `xg_per_match`, `xg_last5`

| Feature | Meaning | Interpretation |
|---------|---------|----------------|
| `xg_per_match_home = 2.5` | Creates high-quality chances | Strong underlying performance |
| `xg_per_match_away = 0.8` | Creates few chances | Weak underlying performance |

**Why It Matters**: xG validates whether goals are sustainable or lucky.

### 3. Head-to-Head (H2H)

**Pattern**: `h2h_home_gf_avg`, `h2h_away_gf_avg`

| Feature | Meaning | Example |
|---------|---------|---------|
| `h2h_home_gf_avg = 3.2` | Home team historically scores 3.2 vs this opponent | Arsenal averages 3.2 vs Wolves at Emirates |
| `h2h_away_gf_avg = 0.5` | Away team historically scores 0.5 at this venue | Wolves rarely score at Emirates |

**When Important**: For rivals (e.g., Man Utd vs Liverpool) or lopsided matchups.

### 4. Season Statistics

**Pattern**: `prior_season_gf`, `prior_season_ppg`

| Feature | Meaning | Weight |
|---------|---------|--------|
| `prior_season_gf_home = 75` | Scored 75 goals at home last season | Moderate (15% of top 20) |
| `prior_season_ppg = 2.1` | Averaged 2.1 pts/game last season | Moderate |

**Note**: Season stats matter less than recent 3-5 match form.

---

## Real-World Scenarios

### Scenario 1: Clear Favorite

**Match**: Man City (home) vs Burnley (away)  
**Prediction**: 3.2 - 0.6

**Why?**
- Man City: `gf_last5_home = 12` (SHAP: +0.50) - Elite form
- Man City: `xg_per_match_home = 3.0` (SHAP: +0.35) - Dominant quality
- Burnley: `ga_last5_away = 10` (SHAP: +0.25) - Terrible away defense
- Burnley: `gf_last5_away = 2` (SHAP: -0.30 for their prediction) - Poor attack

**Confidence**: **High** - All features point same direction

---

### Scenario 2: Close Match

**Match**: Liverpool (home) vs Arsenal (away)  
**Prediction**: 1.8 - 1.6

**Why?**
- Liverpool: `gf_last5_home = 7` (SHAP: +0.20) - Good form
- Arsenal: `ga_last5_home = 3` (SHAP: -0.18) - Strong defense
- Arsenal: `gf_last5_away = 6` (SHAP: +0.18 for away pred) - Good away form
- Liverpool: `ga_last5_home = 4` (SHAP: -0.15 for away pred) - Decent defense

**Confidence**: **Moderate** - Features mostly cancel out

---

### Scenario 3: Surprising Prediction

**Match**: Chelsea (home) vs Brentford (away)  
**Prediction**: 1.2 - 1.4 (away favored)

**Why?**
- Chelsea: `gf_last5_home = 3` (SHAP: -0.25) - Poor recent form
- Chelsea: `ga_last5_home = 6` (SHAP: +0.20 for Brentford) - Weak defense
- Brentford: `gf_last5_away = 8` (SHAP: +0.30) - Excellent away form
- Brentford: `xg_per_match_away = 1.9` (SHAP: +0.22) - Quality validated

**Confidence**: **Moderate-High** - Form outweighs home advantage

---

## How to Use Explanations

### For Pre-Match Analysis

1. **Check prediction**: Does the score make sense?
2. **Review top features**: Do they align with your knowledge?
3. **Look for conflicts**: Are any features surprising?
4. **Assess confidence**: Do features all point same direction?

### Red Flags (Question the Model)

⚠️ **Single feature dominance**: Prediction relies on one feature
- Example: Only `h2h_home_gf_avg` drives prediction
- Risk: Not robust, may be overfitting

⚠️ **Conflicting features**: Top features cancel out
- Example: Strong attack (+0.30) vs strong defense (-0.28)
- Risk: Uncertain prediction, coin flip

⚠️ **Obscure features**: Important features you don't recognize
- Example: `expanding_std_ga_away` is top feature
- Risk: May be spurious correlation

⚠️ **Missing context**: Model doesn't know about key events
- Example: Star striker injured but model predicts 3 goals
- Risk: Prediction outdated

### Green Lights (Trust the Model)

✅ **Multiple aligned features**: 3+ features point same direction
- Example: Recent form, xG, and H2H all favor home team
- Trust: High confidence

✅ **Sensible features**: Top features match your intuition
- Example: Goal-scoring form, opponent weakness, home advantage
- Trust: Model learned correct patterns

✅ **Magnitude makes sense**: SHAP values match feature extremity
- Example: 15 goals in 5 matches → SHAP = +0.60 (very high)
- Trust: Model is well-calibrated

---

## Feature Categories Cheat Sheet

| Category | Example Features | Weight | Interpretation |
|----------|------------------|--------|----------------|
| **Recent Form** | `gf_last3`, `gf_last5`, `ppg_last10` | ~45% | Last 3-5 matches most predictive |
| **Expected Goals** | `xg_per_match`, `xg_last5` | ~15% | Validates quality vs luck |
| **Head-to-Head** | `h2h_home_gf_avg`, `h2h_away_gf_avg` | ~10% | Historical matchup patterns |
| **Season Stats** | `prior_season_gf`, `prior_season_ppg` | ~15% | Baseline team quality |
| **Match Stats** | `shots_per_match`, `corners_per_match` | ~15% | Playing style, dominance |

---

## Common Questions

### Q: Why is recent form so important?

**A**: The model learned that last 3-5 matches predict next match better than season-long averages. Teams in hot/cold streaks tend to continue.

### Q: Why do opponent features matter?

**A**: Facing a weak defense increases goal expectations. The model learned to account for opponent quality, not just your team's form.

### Q: Can I trust predictions with low SHAP values?

**A**: Predictions with all SHAP values <0.10 indicate no strong signals. These are **low confidence** and closer to the average (~1.5 goals).

### Q: What if the model ignores key context (injuries)?

**A**: The model doesn't know about injuries, tactics, or motivation. Use your judgment to adjust predictions based on context the model can't see.

### Q: Why are away goals predicted lower?

**A**: Away teams score ~1.2 goals/match vs ~1.5 at home (historical data). The model learned this via venue-specific features.

---

## Quick Interpretation Workflow

```
Step 1: Check Prediction
├─ Does the score seem reasonable?
└─ If not, investigate why

Step 2: Review Top 3 Features
├─ Do they make football sense?
├─ Are SHAP values plausible?
└─ Do they align with your knowledge?

Step 3: Check Opposing Features
├─ Are there strong negative SHAP values?
├─ Do they represent opponent strength?
└─ Do they contradict your expectations?

Step 4: Assess Confidence
├─ Multiple features aligned → High confidence
├─ Features cancel out → Low confidence
└─ Single feature dominates → Question robustness

Step 5: Apply Domain Knowledge
├─ Consider injuries, tactics, motivation
├─ Adjust prediction if needed
└─ Use explanation + context for final view
```

---

## Examples by Match Type

### Derby Match (Liverpool vs Man Utd)

**Key Feature**: `h2h_count`, `h2h_home_gf_avg`
- Historical rivalry patterns influence predictions
- Recent form still matters more than history

### Relegation Battle (Burnley vs Luton)

**Key Feature**: `ppg_last10`, `gf_last5`
- Desperation/motivation not explicitly modeled
- Form and quality still drive predictions

### Top vs Bottom (Man City vs Sheffield Utd)

**Key Feature**: `gf_last5_home`, `ga_last5_away`
- Extreme feature values → Large SHAP values
- High confidence in lopsided prediction

### Mid-Table Clash (Brentford vs Crystal Palace)

**Key Feature**: Multiple features with moderate SHAP
- No extreme values → Moderate prediction
- Lower confidence due to balanced features

---

## Limitations to Remember

1. **Model doesn't know**: Injuries, suspensions, manager changes, tactics
2. **Historical bias**: Trained on past data, may not capture new trends
3. **Randomness exists**: Football has inherent unpredictability
4. **Correlation ≠ Causation**: Features are correlated with outcomes, not necessarily causal

**Best Practice**: Use explanations + your domain knowledge = Better predictions

---

## Summary

✅ **Global importance**: Shows most important features model-wide  
✅ **SHAP values**: Explain individual match predictions  
✅ **Feature direction**: Positive = increases, negative = decreases  
✅ **Confidence assessment**: Multiple aligned features = high confidence  
✅ **Domain validation**: Always combine explanations with your knowledge  

**Bottom Line**: Explainability helps you understand, trust, and validate model predictions.

---

**For More Details**: See `outputs/explainability/explainability_report.md`

---

Generated: 2026-08-12
