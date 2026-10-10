"""
SmartTrip AI — Weather Service
Clean interface for weather data. Uses Open-Meteo (free, no API key needed).
"""
import os
import json
from datetime import datetime, timedelta

# Destination coordinates for weather lookups
DESTINATION_COORDS = {
    'Taj Mahal, Agra': {'lat': 27.1751, 'lon': 78.0421},
    'Red Fort, Delhi': {'lat': 28.6562, 'lon': 77.2410},
    'India Gate, Delhi': {'lat': 28.6129, 'lon': 77.2295},
    'Qutub Minar, Delhi': {'lat': 28.5245, 'lon': 77.1855},
    'Gateway of India, Mumbai': {'lat': 18.9220, 'lon': 72.8347},
    'Varanasi Ghats, Varanasi': {'lat': 25.3176, 'lon': 83.0130},
    'Mecca Masjid, Hyderabad': {'lat': 17.3604, 'lon': 78.4736},
    'Sanchi Stupa, Madhya Pradesh': {'lat': 23.4793, 'lon': 77.7397},
}


def get_weather_forecast(place, date_str):
    """
    Get weather forecast for a destination on a given date.
    Uses Open-Meteo free API (no key required).
    Falls back gracefully if unavailable.
    """
    coords = DESTINATION_COORDS.get(place)
    if not coords:
        return {
            'available': False,
            'message': 'Weather data unavailable for this destination.',
        }

    try:
        import urllib.request
        import urllib.error

        dt = datetime.strptime(date_str, '%Y-%m-%d')

        # Open-Meteo supports forecasts up to 16 days ahead
        days_ahead = (dt - datetime.now()).days
        if days_ahead < 0 or days_ahead > 16:
            return {
                'available': False,
                'message': 'Weather forecast only available for dates within the next 16 days.',
            }

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&timezone=Asia/Kolkata"
            f"&start_date={date_str}&end_date={date_str}"
        )

        req = urllib.request.Request(url, headers={'User-Agent': 'SmartTripAI/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if 'daily' not in data:
            return {'available': False, 'message': 'Weather data unavailable.'}

        daily = data['daily']
        wmo_code = daily.get('weathercode', [None])[0]
        temp_max = daily.get('temperature_2m_max', [None])[0]
        temp_min = daily.get('temperature_2m_min', [None])[0]
        rain_prob = daily.get('precipitation_probability_max', [None])[0]

        # Map WMO weather code to condition
        condition = _wmo_to_condition(wmo_code)

        return {
            'available': True,
            'condition': condition,
            'temperature_max': temp_max,
            'temperature_min': temp_min,
            'rain_probability': rain_prob,
            'wmo_code': wmo_code,
            'source': 'Open-Meteo',
        }

    except Exception as e:
        return {
            'available': False,
            'message': f'Live weather forecast unavailable. Crowd prediction is still available using historical data.',
        }


def _wmo_to_condition(code):
    """Convert WMO weather code to simple condition string."""
    if code is None:
        return 'Unknown'
    code = int(code)
    if code == 0:
        return 'Clear'
    elif code in [1, 2, 3]:
        return 'Cloudy'
    elif code in [45, 48]:
        return 'Foggy'
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return 'Rainy'
    elif code in [71, 73, 75, 77, 85, 86]:
        return 'Snowy'
    elif code in [95, 96, 99]:
        return 'Stormy'
    else:
        return 'Cloudy'


def get_historical_weather_summary(place):
    """Return summary of weather patterns from dataset for a place."""
    # This would query the dataset for historical weather patterns
    # Placeholder returning a simple summary
    return {
        'available': True,
        'source': 'historical_dataset',
        'note': 'Based on historical data patterns.',
    }
