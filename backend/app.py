"""
SmartTrip AI — Flask Backend Application
REST API for crowd prediction, recommendations, and trip planning.
"""
import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)


# ──────────────────────────────────────────────
# Static file serving (frontend)
# ──────────────────────────────────────────────

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ──────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────

@app.route('/api/places', methods=['GET'])
def api_places():
    """Return list of known destinations."""
    try:
        from ml.predict import get_places
        places = get_places()
        return jsonify({'places': places})
    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet. Use POST /api/train first.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metadata', methods=['GET'])
def api_metadata():
    """Return model metadata and evaluation metrics."""
    try:
        from ml.predict import get_metadata
        metadata = get_metadata()
        return jsonify(metadata)
    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Predict crowd for a single destination/date/time."""
    try:
        from ml.predict import predict_crowd
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body required.'}), 400

        place = data.get('place')
        date_str = data.get('date')
        time_str = data.get('time', '12:00')
        weather = data.get('weather', 'Clear')
        temperature = data.get('temperature', 29)
        holiday = data.get('holiday', 'No')
        event = data.get('event', 'Regular Day')
        transportation = data.get('transportation_type', 'Private')

        if not place or not date_str:
            return jsonify({'error': 'place and date are required.'}), 400

        result = predict_crowd(
            place=place, date_str=date_str, time_str=time_str,
            weather=weather, temperature=temperature,
            holiday=holiday, event=event, transportation=transportation
        )

        return jsonify(result)

    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet. Use POST /api/train first.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """Get smart recommendation for a destination."""
    try:
        from agents.recommendation_engine import recommend_single
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body required.'}), 400

        place = data.get('place')
        date_str = data.get('date')
        time_str = data.get('time', '12:00')
        max_crowd = data.get('max_crowd', 'MEDIUM')
        weather = data.get('weather', 'Clear')
        temperature = data.get('temperature', 29)
        holiday = data.get('holiday', 'No')
        event = data.get('event', 'Regular Day')
        transportation = data.get('transportation_type', 'Private')

        if not place or not date_str:
            return jsonify({'error': 'place and date are required.'}), 400

        result = recommend_single(
            place=place, date_str=date_str, time_str=time_str,
            max_crowd=max_crowd, weather=weather, temperature=temperature,
            holiday=holiday, event=event, transportation=transportation
        )

        return jsonify(result)

    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plan-trip', methods=['POST'])
def api_plan_trip():
    """Plan optimized multi-destination itinerary."""
    try:
        from agents.trip_planner import plan_trip
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body required.'}), 400

        destinations = data.get('destinations', [])
        date_str = data.get('date')
        start_time = data.get('start_time', '09:00')
        end_time = data.get('end_time', '20:00')
        max_crowd = data.get('max_crowd', 'MEDIUM')
        weather = data.get('weather', 'Clear')
        temperature = data.get('temperature', 29)
        holiday = data.get('holiday', 'No')
        event = data.get('event', 'Regular Day')
        transportation = data.get('transportation_type', 'Private')

        if not destinations or not date_str:
            return jsonify({'error': 'destinations and date are required.'}), 400

        result = plan_trip(
            destinations=destinations, date_str=date_str,
            start_time=start_time, end_time=end_time,
            max_crowd=max_crowd, weather=weather, temperature=temperature,
            holiday=holiday, event=event, transportation=transportation
        )

        return jsonify(result)

    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/train', methods=['POST'])
def api_train():
    """Train/retrain the ML model."""
    try:
        from ml.train import train_and_evaluate
        from ml.predict import reload_model

        metadata = train_and_evaluate()
        reload_model()

        return jsonify({
            'success': True,
            'message': 'Model trained successfully.',
            'metadata': metadata
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather', methods=['GET'])
def api_weather():
    """Get weather forecast for a destination."""
    try:
        from services.weather_service import get_weather_forecast

        place = request.args.get('place')
        date_str = request.args.get('date')

        if not place or not date_str:
            return jsonify({'error': 'place and date query params required.'}), 400

        result = get_weather_forecast(place, date_str)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  SmartTrip AI — Backend Server")
    print("=" * 50)
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
