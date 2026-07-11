"""
air_quality.py — Pollution dispersion index.

Calculates how effectively current meteorological conditions
are dispersing airborne pollutants, based on wind speed,
atmospheric stability (delta_t), pressure, and precipitation.
"""


def dispersion_index(
    wind_avg: float,
    delta_t: float,
    sea_level_pressure: float,
    precip: float,
) -> dict:
    """
    Calculate a pollution dispersion index from current weather conditions.

    Higher scores indicate better dispersion (pollutants being cleared).
    Lower scores indicate stagnant conditions (pollutants accumulating).

    Args:
        wind_avg:            Average wind speed in mph
        delta_t:             Dry bulb minus wet bulb temperature (°C).
                             Higher values indicate atmospheric instability
                             and better vertical mixing.
        sea_level_pressure:  Sea level pressure in mb. High pressure systems
                             suppress vertical mixing.
        precip:              Current precipitation rate in mm/hr.
                             Rain washes particulates from the air.

    Returns:
        dict with 'score', 'rating', 'description', and 'factors'
    """
    score = 0
    factors = []

    # Wind — primary disperser
    if wind_avg >= 15:
        score += 4
        factors.append("Strong wind — excellent dispersal")
    elif wind_avg >= 8:
        score += 3
        factors.append("Moderate wind — good dispersal")
    elif wind_avg >= 4:
        score += 2
        factors.append("Light wind — limited dispersal")
    elif wind_avg >= 1:
        score += 1
        factors.append("Very light wind — poor dispersal")
    else:
        factors.append("Calm — no wind dispersal")

    # Atmospheric stability via delta_t
    if delta_t >= 8:
        score += 3
        factors.append("Unstable atmosphere — good vertical mixing")
    elif delta_t >= 5:
        score += 2
        factors.append("Moderately stable atmosphere")
    elif delta_t >= 2:
        score += 1
        factors.append("Stable atmosphere — limited vertical mixing")
    else:
        score += 0
        factors.append("Very stable atmosphere — inversion risk")

    # Pressure — high pressure suppresses mixing
    if sea_level_pressure >= 1025:
        score -= 1
        factors.append("High pressure — suppressing atmospheric mixing")
    elif sea_level_pressure <= 1005:
        score += 1
        factors.append("Low pressure — promoting atmospheric mixing")

    # Rain — washout effect
    if precip >= 1.0:
        score += 2
        factors.append("Rain — washing particulates from the air")
    elif precip > 0:
        score += 1
        factors.append("Light rain — some particulate washout")

    # Clamp score to 0-10
    score = max(0, min(10, score))

    if score >= 8:
        rating = "Excellent"
        description = "Conditions are dispersing pollutants effectively"
    elif score >= 6:
        rating = "Good"
        description = "Reasonable dispersal conditions"
    elif score >= 4:
        rating = "Moderate"
        description = "Some dispersal but pollutants may accumulate"
    elif score >= 2:
        rating = "Poor"
        description = "Stagnant conditions — pollutants likely accumulating"
    else:
        rating = "Very Poor"
        description = "Very stagnant conditions — expect elevated pollution levels"

    return {
        "score": score,
        "rating": rating,
        "description": description,
        "factors": factors,
    }
