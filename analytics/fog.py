"""
fog.py — Radiation fog risk assessment.

Radiation fog forms when the ground cools overnight by radiating heat
into a clear sky, chilling the air near the surface to its dew point.
Conditions that favour formation: high humidity, small temperature/dew
point spread, light winds, clear sky, and high pressure.

Two assessments are provided:
    current:  Is fog present or imminent right now?
    tonight:  How likely is fog to form overnight/early morning?
"""


def _dew_point_spread(air_temperature: float, dew_point: float) -> float:
    """Difference between air temperature and dew point in °C."""
    return round(air_temperature - dew_point, 1)


def current_fog_risk(
    air_temperature: float,
    dew_point: float,
    relative_humidity: float,
    wind_avg: float,
    solar_radiation: float,
    hour: int,
) -> dict:
    """
    Assess current fog risk based on present conditions.

    Args:
        air_temperature:   Air temperature in °C
        dew_point:         Dew point temperature in °C
        relative_humidity: Relative humidity as a percentage
        wind_avg:          Average wind speed in mph
        solar_radiation:   Solar radiation in W/m²
        hour:              Current hour (0-23, local time)

    Returns:
        dict with 'risk_level', 'description', and 'factors'
    """
    spread = _dew_point_spread(air_temperature, dew_point)
    score = 0
    factors = []

    # Dew point spread — primary indicator
    if spread <= 1.0:
        score += 4
        factors.append(f"Temperature/dew point spread only {spread}°C — saturation imminent")
    elif spread <= 2.0:
        score += 3
        factors.append(f"Temperature/dew point spread {spread}°C — very close to saturation")
    elif spread <= 4.0:
        score += 2
        factors.append(f"Temperature/dew point spread {spread}°C — elevated humidity")
    elif spread <= 6.0:
        score += 1
        factors.append(f"Temperature/dew point spread {spread}°C — moderate humidity")

    # Relative humidity
    if relative_humidity >= 95:
        score += 3
        factors.append(f"Humidity {relative_humidity}% — near saturation")
    elif relative_humidity >= 90:
        score += 2
        factors.append(f"Humidity {relative_humidity}% — very high")
    elif relative_humidity >= 80:
        score += 1
        factors.append(f"Humidity {relative_humidity}% — elevated")

    # Wind — high wind disperses fog
    if wind_avg <= 2:
        score += 2
        factors.append("Calm conditions — no dispersal")
    elif wind_avg <= 5:
        score += 1
        factors.append(f"Light wind {wind_avg} mph — limited dispersal")
    elif wind_avg > 10:
        score -= 2
        factors.append(f"Wind {wind_avg} mph — dispersing any fog")

    # Time of day — fog most likely pre-dawn
    if 0 <= hour <= 7:
        score += 2
        factors.append("Pre-dawn hours — peak fog formation period")
    elif hour >= 22 or hour <= 9:
        score += 1
        factors.append("Night or early morning — elevated fog risk period")
    elif 10 <= hour <= 16:
        score -= 1  # Daytime heating burns fog off

    # Solar radiation — if sun is up and strong, fog is unlikely
    if solar_radiation > 200:
        score -= 2
        factors.append("Strong solar radiation — fog unlikely in current conditions")
    elif solar_radiation > 50:
        score -= 1
        factors.append("Some solar radiation — fog burning off")

    score = max(0, score)

    if score >= 8:
        risk_level = "High"
        description = "Fog present or imminent — visibility likely reduced"
    elif score >= 5:
        risk_level = "Moderate"
        description = "Conditions favourable for fog formation"
    elif score >= 3:
        risk_level = "Low"
        description = "Some fog risk but conditions not ideal for formation"
    else:
        risk_level = "None"
        description = "No significant fog risk"

    return {
        "risk_level": risk_level,
        "score": score,
        "description": description,
        "factors": [f for f in factors if f],
    }


def tonight_fog_forecast(
    relative_humidity: float,
    dew_point: float,
    air_temperature: float,
    sea_level_pressure: float,
    wind_avg: float,
    solar_radiation: float,
) -> dict:
    """
    Forecast likelihood of fog forming overnight or early morning.

    Uses current afternoon/evening conditions to predict overnight fog risk.
    High afternoon humidity means the air will reach saturation easily
    as temperatures drop overnight.

    Args:
        relative_humidity:   Current relative humidity as a percentage
        dew_point:           Current dew point in °C
        air_temperature:     Current air temperature in °C
        sea_level_pressure:  Sea level pressure in mb
        wind_avg:            Current average wind speed in mph
        solar_radiation:     Current solar radiation in W/m²

    Returns:
        dict with 'risk_level', 'probability', 'description', and 'factors'
    """
    spread = _dew_point_spread(air_temperature, dew_point)
    score = 0
    factors = []

    # Current humidity — high afternoon humidity almost guarantees overnight fog
    if relative_humidity >= 90:
        score += 4
        factors.append(f"Humidity already {relative_humidity}% — will reach saturation overnight")
    elif relative_humidity >= 80:
        score += 3
        factors.append(f"Humidity {relative_humidity}% — likely to reach saturation as temperatures drop")
    elif relative_humidity >= 70:
        score += 2
        factors.append(f"Humidity {relative_humidity}% — moderate overnight fog risk")
    elif relative_humidity >= 60:
        score += 1
        factors.append(f"Humidity {relative_humidity}% — low overnight fog risk")

    # Dew point spread
    if spread <= 3.0:
        score += 3
        factors.append(f"Dew point only {spread}°C below air temperature — will close overnight")
    elif spread <= 6.0:
        score += 2
        factors.append(f"Dew point {spread}°C below air temperature — may close overnight")
    elif spread <= 10.0:
        score += 1
        factors.append(f"Dew point {spread}°C below air temperature — unlikely to close overnight")

    # High pressure — promotes clear skies and radiative cooling
    if sea_level_pressure >= 1025:
        score += 3
        factors.append(f"High pressure {sea_level_pressure}mb — promotes clear skies and radiative cooling")
    elif sea_level_pressure >= 1015:
        score += 2
        factors.append(f"Pressure {sea_level_pressure}mb — favourable for overnight cooling")
    elif sea_level_pressure <= 1005:
        score -= 1
        factors.append(f"Low pressure {sea_level_pressure}mb — cloud cover may limit radiative cooling")

    # Wind — light winds favour fog
    if wind_avg <= 3:
        score += 2
        factors.append("Calm conditions — ideal for fog formation overnight")
    elif wind_avg <= 8:
        score += 1
        factors.append(f"Light wind {wind_avg} mph — some mixing but fog still possible")
    else:
        score -= 1
        factors.append(f"Wind {wind_avg} mph — may prevent fog formation")

    # Clear sky indicator — high solar radiation now suggests clear sky = fog risk tonight
    if solar_radiation > 400:
        score += 2
        factors.append("Clear sky now — radiative cooling overnight likely")
    elif solar_radiation > 100:
        score += 1
        factors.append("Partly clear — some radiative cooling possible overnight")

    score = max(0, min(12, score))
    probability = min(95, round(score / 12 * 100))

    if score >= 10:
        risk_level = "High"
        description = "Fog very likely overnight or early morning"
    elif score >= 7:
        risk_level = "Moderate"
        description = "Fog possible overnight — check before early morning travel"
    elif score >= 4:
        risk_level = "Low"
        description = "Slight chance of patchy fog overnight"
    else:
        risk_level = "None"
        description = "Fog unlikely overnight"

    return {
        "risk_level": risk_level,
        "score": score,
        "probability": probability,
        "description": description,
        "factors": factors,
    }
