"""
SmartTrip AI — Prediction Service
Loads trained model and makes crowd predictions.
"""
import os
import json
import joblib
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

_model = None
_pipeline = None
_metadata = None


def _load_model():
    """Lazy-load model, pipeline, and metadata."""
    global _model, _pipeline, _metadata

    if _model is not None:
        return

    model_path = os.path.join(MODELS_DIR, 'crowd_model.pkl')
    pipeline_path = os.path.join(MODELS_DIR, 'preprocessing.pkl')
    meta_path = os.path.join(MODELS_DIR, 'metadata.json')

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "Trained model not found. Run training first (POST /api/train)."
        )

    _model = joblib.load(model_path)

    from ml.preprocessing import PreprocessingPipeline
    _pipeline = PreprocessingPipeline.load(pipeline_path)

    with open(meta_path, 'r') as f:
        _metadata = json.load(f)


def get_places():
    """Return list of known destinations."""
    _load_model()
    return _pipeline.places


def get_metadata():
    """Return model metadata."""
    _load_model()
    return _metadata


def predict_crowd(place, date_str, time_str, weather='Clear',
                  temperature=29, holiday='No', event='Regular Day',
                  transportation='Private', region=None):
    """Predict crowd count for a destination/date/time."""
    _load_model()

    # Validate place
    if place not in _pipeline.places:
        return {
            'error': True,
            'message': f"We don't currently have sufficient historical data for '{place}'.",
            'known_places': _pipeline.places
        }

    # Prepare features
    X = _pipeline.prepare_single_prediction(
        place=place, date_str=date_str, time_str=time_str,
        weather=weather, temperature=temperature,
        holiday=holiday, event=event,
        transportation=transportation, region=region
    )

    # Predict
    predicted = _model.predict(X)[0]
    predicted = max(0, predicted)  # Can't be negative
    predicted = round(predicted)

    # Classify
    crowd_level = _pipeline.classify_crowd(predicted)

    # Confidence estimation based on data density
    confidence = _estimate_confidence(place)

    return {
        'error': False,
        'place': place,
        'date': date_str,
        'time': time_str,
        'predicted_crowd': int(predicted),
        'crowd_level': crowd_level,
        'confidence': confidence,
        'weather': weather,
        'temperature': temperature,
        'thresholds': _pipeline.crowd_thresholds,
    }


def predict_crowd_for_times(place, date_str, times, weather='Clear',
                            temperature=29, holiday='No', event='Regular Day',
                            transportation='Private', region=None):
    """Predict crowd for multiple time slots at the same destination/date."""
    results = []
    for t in times:
        result = predict_crowd(
            place=place, date_str=date_str, time_str=t,
            weather=weather, temperature=temperature,
            holiday=holiday, event=event,
            transportation=transportation, region=region
        )
        if not result.get('error'):
            results.append(result)
    return results


def _estimate_confidence(place):
    """Estimate prediction confidence based on data availability."""
    _load_model()
    # Simple heuristic based on R² and data availability
    r2 = _metadata.get('best_model_metrics', {}).get('r2', 0)
    if r2 > 0.7:
        return 'High'
    elif r2 > 0.4:
        return 'Medium'
    else:
        return 'Low'


def reload_model():
    """Force reload of model (after retraining)."""
    global _model, _pipeline, _metadata
    _model = None
    _pipeline = None
    _metadata = None
    _load_model()
