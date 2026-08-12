# Premier League Player Performance Prediction - Random Forest

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load Data

df = pd.read_csv("players_data_light-2025_2026.csv")

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

# Create Performance Score

performance_columns = [
    "Gls",
    "Ast",
    "xG",
    "xAG",
    "PrgC",
    "PrgP",
    "PrgR",
    "SCA",
    "GCA",
    "Tkl",
    "TklW",
    "Int",
    "Clr",
    "Carries",
    "Succ"
]

performance_columns = [
    col for col in performance_columns
    if col in df.columns
]

df["Performance_Score"] = (
    df[performance_columns]
    .fillna(0)
    .rank(pct=True)
    .mean(axis=1)
)

# Remove Very Low-Minute Players

if "Min" in df.columns:
    df = df[df["Min"] >= 450].copy()

# Define Target

target = "Performance_Score"

# Remove Leakage Columns

drop_columns = [
    "Performance_Score",
    "Rk",
    "Player",
    "Gls",
    "Ast",
    "xG",
    "xAG",
    "G+A",
    "G-PK",
    "G+A-PK",
    "G/Sh",
    "G/SoT",
    "G-xG",
    "np:G-xG"
]

drop_columns = [
    col for col in drop_columns
    if col in df.columns
]

X = df.drop(columns=drop_columns)
y = df[target]

# Identify Features

numeric_features = X.select_dtypes(
    include=["int64", "float64"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object"]
).columns.tolist()

print("\nNumeric features:", len(numeric_features))
print("Categorical features:", len(categorical_features))

# Preprocessing

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features)
])

# Random Forest

model = RandomForestRegressor(
    n_estimators=400,
    max_depth=18,
    min_samples_split=4,
    min_samples_leaf=2,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

# Train Test Split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))

# Train

pipeline.fit(X_train, y_train)

# Predict

y_pred = pipeline.predict(X_test)

# Evaluation

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\nModel Performance")
print("============================")
print("MAE :", round(mae, 4))
print("RMSE:", round(rmse, 4))
print("R²  :", round(r2, 4))

# Prediction Table

results = X_test.copy()

results["Actual_Performance"] = y_test.values
results["Predicted_Performance"] = y_pred
results["Prediction_Error"] = (
    results["Actual_Performance"]
    - results["Predicted_Performance"]
)

results = results.sort_values(
    "Predicted_Performance",
    ascending=False
)

print("\nTop Predicted Players")
print("============================")

display_columns = [
    col for col in ["Player", "Squad", "Pos"]
    if col in results.columns
]

display_columns += [
    "Actual_Performance",
    "Predicted_Performance",
    "Prediction_Error"
]

print(
    results[display_columns].head(20)
)

# Feature Importance

feature_names = (
    pipeline
    .named_steps["preprocessor"]
    .get_feature_names_out()
)

importance = (
    pipeline
    .named_steps["model"]
    .feature_importances_
)

feature_importance = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importance
})
feature_importance = feature_importance.sort_values(
    "Importance",
    ascending=False
)

print("\nTop Features")
print("============================")
print(feature_importance.head(20))

# Save Model

joblib.dump(
    pipeline,
    "premier_league_player_model.pkl"
)

print("\nModel saved as:")
print("premier_league_player_model.pkl")
df.head()
df.info()