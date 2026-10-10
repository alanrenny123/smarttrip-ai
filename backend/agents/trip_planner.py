"""
SmartTrip AI — Trip Planner
Optimizes multi-destination itineraries using greedy optimization.
"""
from ml.predict import predict_crowd, predict_crowd_for_times, get_places
from services.weather_service import get_weather_forecast

CANDIDATE_TIMES = [
    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00'
]

CROWD_PRIORITY = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}

# Approximate visit duration in hours per destination
DEFAULT_VISIT_DURATION = 2
# Approximate travel time between destinations (hours)
DEFAULT_TRAVEL_TIME = 1


def plan_trip(destinations, date_str, start_time='09:00', end_time='20:00',
              max_crowd='MEDIUM', weather='Clear', temperature=29,
              holiday='No', event='Regular Day', transportation='Private'):
    """
    Plan an optimized itinerary for multiple destinations.

    Algorithm:
    1. For each destination, predict crowd at all candidate times
    2. Score each (destination, time) pair
    3. Greedy assignment: pick best available slot for each destination
    4. Local swap optimization to improve total score
    """

    # Validate destinations
    known_places = get_places()
    valid_destinations = []
    invalid_destinations = []

    for dest in destinations:
        if dest in known_places:
            valid_destinations.append(dest)
        else:
            invalid_destinations.append(dest)

    if not valid_destinations:
        return {
            'error': True,
            'message': 'None of the selected destinations have historical data.',
            'invalid_destinations': invalid_destinations,
            'known_places': known_places,
        }

    # Parse time range
    start_h = _parse_hour(start_time)
    end_h = _parse_hour(end_time)

    # Filter candidate times within user's range
    available_times = [t for t in CANDIDATE_TIMES if start_h <= _parse_hour(t) <= end_h - DEFAULT_VISIT_DURATION]

    if not available_times:
        return {
            'error': True,
            'message': 'The selected time range is too narrow to fit any visits.',
        }

    # Step 1: Get all predictions
    all_predictions = {}
    for dest in valid_destinations:
        preds = predict_crowd_for_times(
            place=dest, date_str=date_str, times=available_times,
            weather=weather, temperature=temperature,
            holiday=holiday, event=event, transportation=transportation
        )
        all_predictions[dest] = {p['time']: p for p in preds}

    # Step 2: Score each (destination, time) pair
    # Lower score = better
    scored_pairs = []
    for dest in valid_destinations:
        for time_str, pred in all_predictions[dest].items():
            crowd_score = CROWD_PRIORITY.get(pred['crowd_level'], 2)
            crowd_normalized = pred['predicted_crowd'] / 50000  # Normalize
            score = crowd_score * 3 + crowd_normalized
            scored_pairs.append({
                'place': dest,
                'time': time_str,
                'hour': _parse_hour(time_str),
                'predicted_crowd': pred['predicted_crowd'],
                'crowd_level': pred['crowd_level'],
                'score': score,
            })

    # Step 3: Greedy assignment
    itinerary = _greedy_assign(scored_pairs, valid_destinations, start_h, end_h)

    # Step 4: Try to improve with local swaps
    itinerary = _local_swap_optimization(itinerary, all_predictions)

    # Step 5: Get weather for each slot
    for item in itinerary:
        weather_info = get_weather_forecast(item['place'], date_str)
        item['weather'] = weather_info

    # Step 6: Calculate totals
    total_crowd = sum(item['predicted_crowd'] for item in itinerary)
    avg_crowd = total_crowd / len(itinerary) if itinerary else 0
    crowd_levels = [item['crowd_level'] for item in itinerary]

    result = {
        'error': False,
        'date': date_str,
        'start_time': start_time,
        'end_time': end_time,
        'itinerary': itinerary,
        'total_destinations': len(itinerary),
        'average_crowd': round(avg_crowd),
        'crowd_summary': {
            'LOW': crowd_levels.count('LOW'),
            'MEDIUM': crowd_levels.count('MEDIUM'),
            'HIGH': crowd_levels.count('HIGH'),
        },
        'invalid_destinations': invalid_destinations,
        'optimization_notes': [],
    }

    if invalid_destinations:
        result['optimization_notes'].append(
            f"Could not include {', '.join(invalid_destinations)} - no historical data available."
        )

    return result


def _greedy_assign(scored_pairs, destinations, start_h, end_h):
    """Greedy assignment: for each destination, pick best non-conflicting time."""
    # Sort by score (best first)
    scored_pairs.sort(key=lambda x: x['score'])

    assigned = []
    assigned_hours = set()
    assigned_places = set()

    for pair in scored_pairs:
        if pair['place'] in assigned_places:
            continue

        # Check for time conflict (need DEFAULT_VISIT_DURATION + DEFAULT_TRAVEL_TIME gap)
        slot_start = pair['hour']
        slot_end = slot_start + DEFAULT_VISIT_DURATION

        conflict = False
        for existing in assigned:
            existing_start = existing['hour']
            existing_end = existing_start + DEFAULT_VISIT_DURATION + DEFAULT_TRAVEL_TIME
            if not (slot_end + DEFAULT_TRAVEL_TIME <= existing_start or slot_start >= existing_end):
                conflict = True
                break

        if not conflict:
            assigned.append({
                'place': pair['place'],
                'time': pair['time'],
                'hour': pair['hour'],
                'predicted_crowd': pair['predicted_crowd'],
                'crowd_level': pair['crowd_level'],
                'visit_duration': DEFAULT_VISIT_DURATION,
            })
            assigned_places.add(pair['place'])

        if len(assigned_places) == len(destinations):
            break

    # Sort by time
    assigned.sort(key=lambda x: x['hour'])
    return assigned


def _local_swap_optimization(itinerary, all_predictions):
    """Try swapping time slots to reduce total crowd."""
    if len(itinerary) < 2:
        return itinerary

    best_itinerary = itinerary[:]
    best_score = _total_score(best_itinerary)

    improved = True
    max_iterations = 20
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(len(best_itinerary)):
            for j in range(i + 1, len(best_itinerary)):
                # Try swapping times
                new_itin = best_itinerary[:]
                new_itin[i] = new_itin[i].copy()
                new_itin[j] = new_itin[j].copy()

                # Swap times
                new_itin[i]['time'], new_itin[j]['time'] = new_itin[j]['time'], new_itin[i]['time']
                new_itin[i]['hour'], new_itin[j]['hour'] = new_itin[j]['hour'], new_itin[i]['hour']

                # Update predictions with swapped times
                for item in [new_itin[i], new_itin[j]]:
                    if item['time'] in all_predictions.get(item['place'], {}):
                        pred = all_predictions[item['place']][item['time']]
                        item['predicted_crowd'] = pred['predicted_crowd']
                        item['crowd_level'] = pred['crowd_level']

                new_score = _total_score(new_itin)
                if new_score < best_score:
                    best_itinerary = new_itin
                    best_score = new_score
                    improved = True

    best_itinerary.sort(key=lambda x: x['hour'])
    return best_itinerary


def _total_score(itinerary):
    """Calculate total crowd score for an itinerary."""
    return sum(
        CROWD_PRIORITY.get(item['crowd_level'], 2) * 10000 + item['predicted_crowd']
        for item in itinerary
    )


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
