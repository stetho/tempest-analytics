"""
pressure.py — Pressure-based weather calculations.

Functions:
    pressure_change_rate    — Rate of pressure change in mb/hour
    zambretti_forecast      — Plain-English forecast from pressure + trend
"""

import datetime


def pressure_change_rate(observations: list[dict]) -> float:
    """
    Calculate the rate of pressure change in mb/hour.

    Takes a list of observations ordered oldest to newest,
    each with 'timestamp' (unix) and 'sea_level_pressure' (mb).

    Returns a positive value for rising pressure, negative for falling.

    Raises:
        ValueError: If fewer than 2 observations are provided.
    """
    if len(observations) < 2:
        raise ValueError("Need at least 2 observations to calculate rate of change")

    oldest = observations[0]
    newest = observations[-1]

    pressure_diff = newest["sea_level_pressure"] - oldest["sea_level_pressure"]
    time_diff_hours = (newest["timestamp"] - oldest["timestamp"]) / 3600

    return round(pressure_diff / time_diff_hours, 3)


def zambretti_forecast(
    sea_level_pressure: float,
    pressure_trend: str,
    month: int = None
) -> dict:
    """
    Zambretti weather forecaster.

    Based on the Zambretti Forecaster (1920), which uses current sea level
    pressure, whether it is rising or falling, and the season to produce
    a plain-English weather forecast.

    Args:
        sea_level_pressure: Current sea level pressure in mb.
        pressure_trend: 'rising', 'falling', or 'steady'.
        month: Month as integer (1-12). Defaults to current month.

    Returns:
        dict with keys:
            letter    — Zambretti letter (A-Z)
            forecast  — Plain-English forecast string
            trend     — The pressure trend passed in
            pressure  — The pressure passed in
    """
    if month is None:
        month = datetime.datetime.now().month

    is_winter = month in (10, 11, 12, 1, 2, 3)

    forecasts = {
        "A": "Settled fine",
        "B": "Fine weather",
        "C": "Becoming fine",
        "D": "Fine, becoming less settled",
        "E": "Fine, possible showers",
        "F": "Fairly fine, improving",
        "G": "Fairly fine, possible showers early",
        "H": "Fairly fine, showery later",
        "I": "Showery early, improving",
        "J": "Changeable, improving",
        "K": "Fairly fine, showers likely",
        "L": "Rather unsettled, clearing later",
        "M": "Unsettled, probably improving",
        "N": "Showery, bright intervals",
        "O": "Showery, becoming less settled",
        "P": "Changeable, some rain",
        "Q": "Unsettled, short fine intervals",
        "R": "Unsettled, rain later",
        "S": "Unsettled, some rain",
        "T": "Mostly very unsettled",
        "U": "Occasional rain, worsening",
        "V": "Rain at times, very unsettled",
        "W": "Rain at frequent intervals",
        "X": "Very unsettled, rain",
        "Y": "Stormy, possibly improving",
        "Z": "Stormy, much rain",
    }

    if pressure_trend == "rising":
        if sea_level_pressure >= 1029.5:
            letter = "A"
        elif sea_level_pressure >= 1026.0:
            letter = "B"
        elif sea_level_pressure >= 1022.5:
            letter = "C"
        elif sea_level_pressure >= 1019.0:
            letter = "F"
        elif sea_level_pressure >= 1015.5:
            letter = "G" if not is_winter else "I"
        elif sea_level_pressure >= 1012.0:
            letter = "I" if not is_winter else "J"
        elif sea_level_pressure >= 1008.5:
            letter = "J" if not is_winter else "L"
        elif sea_level_pressure >= 1005.0:
            letter = "L" if not is_winter else "M"
        else:
            letter = "M"

    elif pressure_trend == "falling":
        if sea_level_pressure >= 1029.5:
            letter = "D"
        elif sea_level_pressure >= 1026.0:
            letter = "E"
        elif sea_level_pressure >= 1022.5:
            letter = "H"
        elif sea_level_pressure >= 1019.0:
            letter = "O"
        elif sea_level_pressure >= 1015.5:
            letter = "R"
        elif sea_level_pressure >= 1012.0:
            letter = "U"
        elif sea_level_pressure >= 1008.5:
            letter = "V"
        elif sea_level_pressure >= 1005.0:
            letter = "X"
        else:
            letter = "Z"

    else:  # steady
        if sea_level_pressure >= 1029.5:
            letter = "A"
        elif sea_level_pressure >= 1026.0:
            letter = "B"
        elif sea_level_pressure >= 1022.5:
            letter = "C" if not is_winter else "D"
        elif sea_level_pressure >= 1019.0:
            letter = "E" if not is_winter else "F"
        elif sea_level_pressure >= 1015.5:
            letter = "K"
        elif sea_level_pressure >= 1012.0:
            letter = "N"
        elif sea_level_pressure >= 1008.5:
            letter = "S"
        elif sea_level_pressure >= 1005.0:
            letter = "W"
        else:
            letter = "X"

    return {
        "letter": letter,
        "forecast": forecasts[letter],
        "trend": pressure_trend,
        "pressure": sea_level_pressure,
    }

def storm_predictor(observations: list[dict]) -> dict:
    """
    Predict rain probability based on pressure trend over recent observations.

    Uses rate of pressure change combined with current pressure level
    to produce a rain probability and plain-English description.

    Args:
        observations: List of dicts with 'timestamp' and 'sea_level_pressure',
                      ordered oldest to newest. Should cover at least 1 hour.

    Returns:
        dict with 'probability', 'category', 'description',
        'change_rate', 'current_pressure', 'period_hours', and 'advice'

    Raises:
        ValueError: If fewer than 2 observations are provided.
    """
    if len(observations) < 2:
        raise ValueError("Need at least 2 observations")

    first = observations[0]
    last = observations[-1]

    pressure_diff = last["sea_level_pressure"] - first["sea_level_pressure"]
    time_hours = (last["timestamp"] - first["timestamp"]) / 3600
    rate = round(pressure_diff / time_hours, 3)

    current_pressure = last["sea_level_pressure"]

    if rate <= -2.0:
        base_prob = 90
        category = "Very High"
        description = "Rapid pressure fall — storm likely"
        advice = "Expect significant deterioration. Strong winds and heavy rain probable."
    elif rate <= -1.0:
        base_prob = 75
        category = "High"
        description = "Pressure falling quickly — rain likely"
        advice = "Weather likely to worsen within a few hours. Take an umbrella."
    elif rate <= -0.5:
        base_prob = 55
        category = "Moderate"
        description = "Pressure falling — rain possible"
        advice = "Conditions may deteriorate. Keep an eye on the sky."
    elif rate <= -0.1:
        base_prob = 30
        category = "Low"
        description = "Pressure easing slightly — settled for now"
        advice = "No immediate concern but monitor pressure trend."
    elif rate >= 1.0:
        base_prob = 5
        category = "Very Low"
        description = "Pressure rising quickly — improving weather"
        advice = "Conditions improving. Dry weather expected."
    elif rate >= 0.5:
        base_prob = 10
        category = "Very Low"
        description = "Pressure rising — weather improving"
        advice = "Settling down. Rain unlikely in the near term."
    elif rate >= 0.1:
        base_prob = 15
        category = "Very Low"
        description = "Pressure rising slightly — stable conditions"
        advice = "No rain expected in the near term."
    else:
        base_prob = 20
        category = "Low"
        description = "Pressure steady — settled conditions"
        advice = "No significant change expected."

    if current_pressure < 1005:
        base_prob = min(95, base_prob + 20)
        description += " — very low pressure"
    elif current_pressure < 1010:
        base_prob = min(95, base_prob + 10)
    elif current_pressure > 1025:
        base_prob = max(5, base_prob - 15)
        description += " — high pressure system"

    return {
        "probability": base_prob,
        "category": category,
        "description": description,
        "advice": advice,
        "change_rate": rate,
        "current_pressure": current_pressure,
        "period_hours": round(time_hours, 1),
    }
