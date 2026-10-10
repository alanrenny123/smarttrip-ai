"""
SmartTrip AI — Recommendation Engine
Evaluates crowd predictions and finds alternative times/destinations.
"""
from ml.predict import predict_crowd, predict_crowd_for_times, get_places
from services.weather_service import get_weather_forecast

# Candidate time slots for evaluation
CANDIDATE_TIMES = [
    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00'
]

CROWD_PRIORITY = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}


def recommend_single(place, date_str, time_str, max_crowd='MEDIUM',
                     weather='Clear', temperature=29, holiday='No',
                     event='Regular Day', transportation='Private'):
    """
    Full recommendation flow for a single destination.
    1. Predict selected time
    2. If acceptable, return
    3. If not, search alternative times
    4. If no good time, search alternative destinations
    """

    # Step 1: Predict for selected time
    prediction = predict_crowd(
        place=place, date_str=date_str, time_str=time_str,
        weather=weather, temperature=temperature,
        holiday=holiday, event=event, transportation=transportation
    )

    if prediction.get('error'):
        return prediction

    # Get weather forecast
    weather_info = get_weather_forecast(place, date_str)

    # Use live weather if available
    if weather_info.get('available') and weather_info.get('condition'):
        prediction['live_weather'] = weather_info

    result = {
        'selected_destination': place,
        'requested_time': time_str,
        'predicted_crowd': prediction['predicted_crowd'],
        'crowd_level': prediction['crowd_level'],
        'confidence': prediction.get('confidence', 'Medium'),
        'weather': weather_info,
        'recommended_action': 'KEEP',
        'recommended_time': time_str,
        'alternative_times': [],
        'alternative_destinations': [],
        'explanation': '',
        'hourly_predictions': [],
    }

    max_level = CROWD_PRIORITY.get(max_crowd, 1)

    # Step 2: Check if current selection is acceptable
    current_level = CROWD_PRIORITY.get(prediction['crowd_level'], 2)

    if current_level <= max_level:
        result['explanation'] = (
            f"Great news! {place} is predicted to have {prediction['crowd_level']} crowd "
            f"({prediction['predicted_crowd']:,} estimated visitors) at {time_str}. "
            f"This is within your acceptable crowd level."
        )
        if weather_info.get('available') and weather_info.get('rain_probability', 0) and weather_info['rain_probability'] > 60:
            result['explanation'] += f" Note: Rain is possible ({weather_info['rain_probability']}% probability). Carry an umbrella."

        # Still get hourly predictions for the chart
        hourly = _get_hourly_predictions(place, date_str, weather, temperature, holiday, event, transportation)
        result['hourly_predictions'] = hourly
        return result

    # Step 3: Search alternative times
    hourly = _get_hourly_predictions(place, date_str, weather, temperature, holiday, event, transportation)
    result['hourly_predictions'] = hourly

    # Find best alternative time
    acceptable_times = [h for h in hourly if CROWD_PRIORITY.get(h['crowd_level'], 2) <= max_level]

    if acceptable_times:
        # Sort by crowd level, then by proximity to requested time
        requested_hour = _parse_hour(time_str)
        acceptable_times.sort(key=lambda x: (
            CROWD_PRIORITY.get(x['crowd_level'], 2),
            abs(_parse_hour(x['time']) - requested_hour)
        ))

        best_time = acceptable_times[0]
        result['recommended_action'] = 'CHANGE_TIME'
        result['recommended_time'] = best_time['time']
        result['recommended_crowd'] = best_time['predicted_crowd']
        result['recommended_level'] = best_time['crowd_level']
        result['alternative_times'] = acceptable_times[:5]

        result['explanation'] = (
            f"{place} is predicted to have {prediction['crowd_level']} crowd "
            f"({prediction['predicted_crowd']:,} estimated visitors) at {time_str}. "
            f"We found a better time at {best_time['time']} with {best_time['crowd_level']} crowd "
            f"({best_time['predicted_crowd']:,} estimated visitors). "
            f"We recommend visiting then."
        )
        return result

    # Step 4: Search alternative destinations
    alternatives = _find_alternative_destinations(
        exclude_place=place, date_str=date_str,
        preferred_time=time_str, max_crowd=max_crowd,
        weather=weather, temperature=temperature,
        holiday=holiday, event=event, transportation=transportation
    )

    if alternatives:
        result['recommended_action'] = 'CHANGE_DESTINATION'
        result['alternative_destinations'] = alternatives
        best_alt = alternatives[0]
        result['explanation'] = (
            f"{place} is expected to remain highly crowded throughout the available time window. "
            f"We recommend {best_alt['place']} as an alternative based on available destination information, "
            f"with {best_alt['crowd_level']} predicted crowd ({best_alt['predicted_crowd']:,} estimated visitors) "
            f"at {best_alt['time']}."
        )
    else:
        result['recommended_action'] = 'NO_ALTERNATIVE'
        result['explanation'] = (
            f"{place} is predicted to have {prediction['crowd_level']} crowd at all available times. "
            f"No lower-crowd alternatives were found for the selected date. "
            f"Consider visiting on a different date."
        )

    return result


def _get_hourly_predictions(place, date_str, weather, temperature,
                            holiday, event, transportation):
    """Get predictions for all candidate time slots."""
    results = predict_crowd_for_times(
        place=place, date_str=date_str, times=CANDIDATE_TIMES,
        weather=weather, temperature=temperature,
        holiday=holiday, event=event, transportation=transportation
    )
    return results


def _find_alternative_destinations(exclude_place, date_str, preferred_time,
                                   max_crowd, weather, temperature,
                                   holiday, event, transportation):
    """Find alternative destinations with lower crowd."""
    places = get_places()
    alternatives = []
    max_level = CROWD_PRIORITY.get(max_crowd, 1)

    for place in places:
        if place == exclude_place:
            continue

        # Check at preferred time first
        pred = predict_crowd(
            place=place, date_str=date_str, time_str=preferred_time,
            weather=weather, temperature=temperature,
            holiday=holiday, event=event, transportation=transportation
        )

        if pred.get('error'):
            continue

        if CROWD_PRIORITY.get(pred['crowd_level'], 2) <= max_level:
            alternatives.append({
                'place': place,
                'time': preferred_time,
                'predicted_crowd': pred['predicted_crowd'],
                'crowd_level': pred['crowd_level'],
                'confidence': pred.get('confidence', 'Medium'),
            })
            continue

        # Try other times for this destination
        for t in CANDIDATE_TIMES:
            pred_t = predict_crowd(
                place=place, date_str=date_str, time_str=t,
                weather=weather, temperature=temperature,
                holiday=holiday, event=event, transportation=transportation
            )
            if not pred_t.get('error') and CROWD_PRIORITY.get(pred_t['crowd_level'], 2) <= max_level:
                alternatives.append({
                    'place': place,
                    'time': t,
                    'predicted_crowd': pred_t['predicted_crowd'],
                    'crowd_level': pred_t['crowd_level'],
                    'confidence': pred_t.get('confidence', 'Medium'),
                })
                break

    # Sort: LOW first, then by crowd count
    alternatives.sort(key=lambda x: (
        CROWD_PRIORITY.get(x['crowd_level'], 2),
        x['predicted_crowd']
    ))

    return alternatives[:5]


def _parse_hour(time_str):
    """Parse hour from time string."""
    try:
        parts = time_str.replace(' AM', '').replace(' PM', '').split(':')
        hour = int(parts[0])
        if 'PM' in time_str.upper() and hour != 12:
            hour += 12
        elif 'AM' in time_str.upper() and hour == 12:
            hour = 0
        return hour
    except:
        return 12
