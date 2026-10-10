"""
SmartTrip AI — Model Training Pipeline
Trains, evaluates, and selects the best regression model.
"""
import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ml.preprocessing import PreprocessingPipeline, load_dataset, FEATURE_COLUMNS, TARGET_COLUMN

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


def train_and_evaluate(dataset_path=None):
    """Train multiple models, evaluate, select best, save."""

    print("=" * 60)
    print("SMARTTRIP AI — MODEL TRAINING")
    print("=" * 60)

    # 1. Load data
    df = load_dataset(dataset_path)
    print(f"\nDataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    # 2. Fit preprocessing pipeline
    pipeline = PreprocessingPipeline()
    processed = pipeline.fit_transform(df)
    print(f"Processed dataset: {processed.shape}")
    print(f"Crowd thresholds: LOW <= {pipeline.crowd_thresholds['low']:.0f}, HIGH > {pipeline.crowd_thresholds['high']:.0f}")

    # 3. Split
    X = processed[FEATURE_COLUMNS]
    y = processed[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain: {X_train.shape[0]}, Test: {X_test.shape[0]}")

    # 4. Define models
    models = {
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeRegressor(random_state=42, max_depth=10),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=200, random_state=42, max_depth=5, learning_rate=0.1),
    }

    if HAS_XGBOOST:
        models['XGBoost'] = XGBRegressor(n_estimators=200, random_state=42, max_depth=5, learning_rate=0.1)

    # 5. Train and evaluate
    results = {}
    best_model_name = None
    best_r2 = -float('inf')

    print("\n" + "-" * 60)
    print(f"{'Model':<25} {'MAE':>10} {'RMSE':>10} {'R²':>10}")
    print("-" * 60)

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        results[name] = {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
        }

        print(f"{name:<25} {mae:>10.1f} {rmse:>10.1f} {r2:>10.4f}")

        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name

    print("-" * 60)
    print(f"\nBest model: {best_model_name} (R² = {best_r2:.4f})")

    # 6. Retrain best model on full dataset for production
    best_model = models[best_model_name]
    best_model.fit(X, y)
    print(f"Retrained {best_model_name} on full dataset ({len(X)} samples)")

    # 7. Calculate feature importance
    feature_importance = {}
    if hasattr(best_model, 'feature_importances_'):
        for feat, imp in zip(FEATURE_COLUMNS, best_model.feature_importances_):
            feature_importance[feat] = float(imp)
    elif hasattr(best_model, 'coef_'):
        for feat, coef in zip(FEATURE_COLUMNS, best_model.coef_):
            feature_importance[feat] = float(abs(coef))

    # 8. Save everything
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Save model
    model_path = os.path.join(MODELS_DIR, 'crowd_model.pkl')
    joblib.dump(best_model, model_path)
    print(f"Model saved: {model_path}")

    # Save pipeline
    pipeline.save()
    print(f"Pipeline saved")

    # Save metadata
    metadata = {
        'model_name': best_model_name,
        'trained_at': datetime.now().isoformat(),
        'dataset_rows': int(df.shape[0]),
        'feature_columns': FEATURE_COLUMNS,
        'target_column': TARGET_COLUMN,
        'places': pipeline.places,
        'crowd_thresholds': pipeline.crowd_thresholds,
        'evaluation_results': results,
        'best_model_metrics': results[best_model_name],
        'feature_importance': feature_importance,
        'train_size': int(X_train.shape[0]),
        'test_size': int(X_test.shape[0]),
    }

    meta_path = os.path.join(MODELS_DIR, 'metadata.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {meta_path}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    return metadata


if __name__ == '__main__':
    train_and_evaluate()
