"""
temperature.py — Temperature, humidity and comfort calculations.

Functions:
    absolute_humidity   — Actual water vapour mass per cubic metre of air
    frost_risk          — Multi-factor frost risk assessment
    thermal_comfort     — Universal Thermal Climate Index (simplified)
"""

import math


def absolute_humidity(air_temperature: float, relative_humidity: float) -> dict:
    """
    Calculate absolute humidity — the actual mass of water vapour
    in a cubic metre of air, regardless of temperature.

    Unlike relative humidity (which is a percentage of capacity),
    absolute humidity tells you how much water is actually in the air.
    Useful for mould risk assessment and comfort calculations.

    Uses the Magnus formula to calculate saturation vapour pressure.

    Args:
        air_temperature: Air temperature in °C
        relative_humidity: Relative humidity as a percentage (0-100)

    Returns:
        dict with 'absolute_humidity_g_m3', 'saturation_vapour_pressure',
        'actual_vapour_pressure', and 'description'
    """
    saturation_vp = 6.1078 * math.exp(
        17.27 * air_temperature / (air_temperature + 237.3)
    )

    actual_vp = saturation_vp * (relative_humidity / 100)

    abs_humidity = 216.7 * (actual_vp / (air_temperature + 273.15))

    if abs_humidity < 4:
        description = "Very dry air"
    elif abs_humidity < 7:
        description = "Dry air"
    elif abs_humidity < 11:
        description = "Comfortable"
    elif abs_humidity < 15:
        description = "Humid"
    else:
        description = "Very humid"

    return {
        "absolute_humidity_g_m3": round(abs_humidity, 2),
        "saturation_vapour_pressure": round(saturation_vp, 2),
        "actual_vapour_pressure": round(actual_vp, 2),
        "description": description,
    }


def frost_risk(
    air_temperature: float,
    dew_point: float,
    wind_avg: float,
    hour: int
) -> dict:
    """
    Calculate frost risk based on temperature, dew point, wind speed
    and time of day.

    Frost forms when the surface temperature drops to 0°C or below.
    Still, clear nights with dew points near 0°C are most dangerous
    as radiative cooling can drop surface temps well below air temp.

    Args:
        air_temperature: Air temperature in °C
        dew_point: Dew point temperature in °C
        wind_avg: Average wind speed in mph
        hour: Hour of day (0-23) in local time

    Returns:
        dict with 'risk_level', 'risk_score', 'description', and 'factors'
    """
    risk_score = 0
    factors = []

    if air_temperature <= 0:
        risk_score += 4
        factors.append("Air temperature at or below freezing")
    elif air_temperature <= 2:
        risk_score += 3
        factors.append("Air temperature dangerously close to freezing")
    elif air_temperature <= 4:
        risk_score += 2
        factors.append("Air temperature within frost range")
    elif air_temperature <= 7:
        risk_score += 1
        factors.append("Air temperature cool")

    if dew_point <= 0:
        risk_score += 3
        factors.append("Dew point at or below freezing — ground frost likely")
    elif dew_point <= 2:
        risk_score += 2
        factors.append("Dew point near freezing")
    elif dew_point <= 4:
        risk_score += 1
        factors.append("Dew point cool")

    if wind_avg < 2:
        risk_score += 2
        factors.append("Very light wind — radiative cooling risk")
    elif wind_avg < 5:
        risk_score += 1
        factors.append("Light wind — some radiative cooling possible")

    if 0 <= hour <= 6:
        risk_score += 2
        factors.append("Early hours — coldest part of the day")
    elif hour >= 22 or hour <= 8:
        risk_score += 1
        factors.append("Night or early morning")

    if risk_score >= 8:
        risk_level = "High"
        description = "High frost risk — expect frost, take precautions"
    elif risk_score >= 5:
        risk_level = "Moderate"
        description = "Moderate frost risk — protect sensitive plants"
    elif risk_score >= 2:
        risk_level = "Low"
        description = "Low frost risk — unlikely but monitor overnight"
    else:
        risk_level = "None"
        description = "No frost risk"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "description": description,
        "factors": factors,
    }


def thermal_comfort(
    air_temperature: float,
    relative_humidity: float,
    wind_avg: float,
    solar_radiation: float
) -> dict:
    """
    Calculate a thermal comfort index combining temperature, humidity,
    wind speed and solar radiation into a single human comfort score.

    Based on the Universal Thermal Climate Index (UTCI) simplified model.
    Gives a practical "how does it actually feel outside" assessment.

    Args:
        air_temperature: Air temperature in °C
        relative_humidity: Relative humidity as a percentage (0-100)
        wind_avg: Average wind speed in mph
        solar_radiation: Solar radiation in W/m²

    Returns:
        dict with 'comfort_temp', 'category', and 'description'
    """
    wind_ms = wind_avg * 0.44704

    svp = 6.105 * math.exp(17.27 * air_temperature / (air_temperature + 237.3))
    actual_vp = svp * (relative_humidity / 100)

    mean_radiant_temp = air_temperature + (0.0014 * solar_radiation)
    wind_chill_effect = 3.5 * math.sqrt(wind_ms)
    humidity_effect = 0.1 * actual_vp

    comfort_temp = round(mean_radiant_temp - wind_chill_effect + humidity_effect, 1)

    if comfort_temp < -13:
        category = "Extreme cold stress"
    elif comfort_temp < 0:
        category = "Strong cold stress"
    elif comfort_temp < 9:
        category = "Moderate cold stress"
    elif comfort_temp < 18:
        category = "Slight cold stress"
    elif comfort_temp < 26:
        category = "No thermal stress — comfortable"
    elif comfort_temp < 32:
        category = "Moderate heat stress"
    elif comfort_temp < 38:
        category = "Strong heat stress"
    else:
        category = "Extreme heat stress"

    return {
        "comfort_temp": comfort_temp,
        "category": category,
        "description": f"Feels like {comfort_temp}°C — {category.lower()}",
    }