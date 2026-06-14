"""
lightning.py — Lightning and storm tracking calculations.

Functions:
    storm_approach_speed    — Calculate storm approach or departure speed
    lightning_safety        — Safety risk assessment based on strike distance
"""

import datetime


def storm_approach_speed(strike_events: list[dict]) -> dict:
    """
    Calculate storm approach or departure speed from a series of
    lightning strike distance readings.

    A negative speed means the storm is approaching.
    A positive speed means the storm is departing.

    Args:
        strike_events: List of dicts with 'timestamp' and 'distance' (miles),
                       ordered oldest to newest.

    Returns:
        dict with 'speed_mph', 'direction', 'closest_distance',
        'closest_timestamp', and 'description'

    Raises:
        ValueError: If fewer than 2 strike events are provided.
    """
    if len(strike_events) < 2:
        raise ValueError("Need at least 2 strike events to calculate approach speed")

    closest = min(strike_events, key=lambda e: e["distance"])

    first = strike_events[0]
    last = strike_events[-1]

    distance_change = last["distance"] - first["distance"]
    time_change_hours = (last["timestamp"] - first["timestamp"]) / 3600

    speed_mph = round(distance_change / time_change_hours, 1)

    recent = strike_events[-3:]
    if len(recent) >= 2:
        recent_change = recent[-1]["distance"] - recent[0]["distance"]
        if recent_change < 0:
            direction = "approaching"
        elif recent_change > 0:
            direction = "departing"
        else:
            direction = "stationary"
    else:
        direction = "approaching" if speed_mph < 0 else "departing"

    abs_speed = abs(speed_mph)
    if direction == "approaching":
        description = f"Storm approaching at {abs_speed} mph"
    elif direction == "departing":
        description = f"Storm departing at {abs_speed} mph"
    else:
        description = "Storm stationary"

    return {
        "speed_mph": speed_mph,
        "direction": direction,
        "closest_distance": closest["distance"],
        "closest_timestamp": closest["timestamp"],
        "description": description,
    }


def lightning_safety(distance_miles: float, strike_count_last_hour: int) -> dict:
    """
    Calculate lightning safety risk based on current strike distance
    and recent strike frequency.

    Uses the 30-30 rule as a baseline:
        If thunder is heard within 30 seconds of lightning (6 miles),
        seek shelter immediately. Wait 30 minutes after the last strike
        before going back outside.

    Args:
        distance_miles: Distance to last lightning strike in miles
        strike_count_last_hour: Number of strikes detected in the last hour

    Returns:
        dict with 'risk_level', 'safe_to_be_outside', 'description',
        and 'advice'
    """
    if distance_miles <= 3:
        risk_level = "Extreme"
        safe_to_be_outside = False
        description = "Lightning overhead — immediate danger"
        advice = "Seek substantial shelter immediately. Stay away from windows, trees and water."
    elif distance_miles <= 6:
        risk_level = "High"
        safe_to_be_outside = False
        description = "Lightning within 6 miles — dangerous"
        advice = "Go indoors now. The 30-30 rule applies — if you can hear thunder, you're at risk."
    elif distance_miles <= 12:
        risk_level = "Moderate"
        safe_to_be_outside = False
        description = "Lightning within 12 miles — be cautious"
        advice = "Move indoors or to a hard-topped vehicle. Storm may be approaching."
    elif distance_miles <= 20:
        risk_level = "Low"
        safe_to_be_outside = True
        description = "Lightning within 20 miles — monitor conditions"
        advice = "Be aware of the storm. Have a plan to get indoors quickly if it approaches."
    else:
        risk_level = "Very Low"
        safe_to_be_outside = True
        description = "Lightning distant — low immediate risk"
        advice = "Monitor conditions. No immediate action required."

    if strike_count_last_hour >= 10 and risk_level in ("Low", "Very Low"):
        risk_level = "Moderate"
        safe_to_be_outside = False
        description += " — but high strike frequency detected"
        advice = "High storm activity detected nearby. Consider moving indoors."

    return {
        "risk_level": risk_level,
        "safe_to_be_outside": safe_to_be_outside,
        "description": description,
        "advice": advice,
    }