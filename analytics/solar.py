"""
solar.py — Solar and UV calculations.

Functions:
    theoretical_solar_radiation  — Clear sky radiation for a given location and time
    clear_sky_index              — Ratio of actual to theoretical solar radiation
    uv_dose_accumulator          — Cumulative UV dose and burn risk over a period
"""

import math
import datetime


def theoretical_solar_radiation(
    timestamp: int,
    latitude: float,
    longitude: float,
    utc_offset_hours: float = 0.0
) -> float:
    """
    Calculate the theoretical maximum solar radiation (W/m²) for a given
    location and time, assuming a perfectly clear sky.

    Based on the solar position algorithm using day of year and hour angle.

    Args:
        timestamp: Unix timestamp
        latitude: Station latitude in decimal degrees
        longitude: Station longitude in decimal degrees
        utc_offset_hours: UTC offset in hours (1.0 for BST, 0.0 for GMT)

    Returns:
        Theoretical solar radiation in W/m². Returns 0.0 at night.
    """
    SOLAR_CONSTANT = 1361

    local_timestamp = timestamp + int(utc_offset_hours * 3600)
    dt = datetime.datetime.fromtimestamp(local_timestamp, datetime.UTC)

    day_of_year = dt.timetuple().tm_yday

    distance_factor = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)

    declination = math.radians(23.45 * math.sin(
        math.radians(360 / 365 * (day_of_year - 81))
    ))

    time_correction = 4 * longitude + 9.87 * math.sin(
        math.radians(2 * 360 / 365 * (day_of_year - 81))
    ) - 7.53 * math.cos(
        math.radians(360 / 365 * (day_of_year - 81))
    ) - 1.5 * math.sin(
        math.radians(360 / 365 * (day_of_year - 81))
    )

    utc_hour = dt.hour + dt.minute / 60
    solar_time = utc_hour + time_correction / 60

    hour_angle = math.radians(15 * (solar_time - 12))

    lat_rad = math.radians(latitude)

    sin_elevation = (
        math.sin(lat_rad) * math.sin(declination) +
        math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
    )

    elevation_angle = math.asin(sin_elevation)

    if elevation_angle <= 0:
        return 0.0

    atmospheric_transmission = 0.75

    theoretical = (
        SOLAR_CONSTANT *
        distance_factor *
        atmospheric_transmission *
        math.sin(elevation_angle)
    )

    return round(max(0.0, theoretical), 1)


def clear_sky_index(
    solar_radiation: float,
    timestamp: int,
    latitude: float,
    longitude: float,
    utc_offset_hours: float = 0.0
) -> dict:
    """
    Calculate the clear sky index — ratio of actual to theoretical solar radiation.

    A value near 1.0 indicates clear sky. Lower values indicate cloud cover.
    Returns None during nighttime hours when theoretical radiation is zero.

    Args:
        solar_radiation: Actual solar radiation in W/m²
        timestamp: Unix timestamp
        latitude: Station latitude in decimal degrees
        longitude: Station longitude in decimal degrees
        utc_offset_hours: UTC offset in hours (1.0 for BST, 0.0 for GMT)

    Returns:
        dict with 'index', 'theoretical', 'actual', and 'description'
    """
    theoretical = theoretical_solar_radiation(
        timestamp, latitude, longitude, utc_offset_hours
    )

    if theoretical == 0:
        return {
            "index": None,
            "theoretical": 0,
            "actual": solar_radiation,
            "description": "Night — clear sky index not applicable",
        }

    index = round(solar_radiation / theoretical, 2)

    if index >= 0.85:
        description = "Clear sky"
    elif index >= 0.65:
        description = "Mostly clear, some haze or thin cloud"
    elif index >= 0.45:
        description = "Partly cloudy"
    elif index >= 0.25:
        description = "Mostly cloudy"
    else:
        description = "Overcast"

    return {
        "index": index,
        "theoretical": theoretical,
        "actual": solar_radiation,
        "description": description,
    }


def uv_dose_accumulator(observations: list[dict]) -> dict:
    """
    Calculate cumulative UV dose over a series of observations.

    Integrates UV index over time to produce a total UV dose in
    Standard Erythemal Dose (SED) units. 1 SED = 100 J/m².

    WHO burn risk thresholds:
        Low:       UV index 0-2
        Moderate:  UV index 3-5
        High:      UV index 6-7
        Very High: UV index 8-10
        Extreme:   UV index 11+

    Args:
        observations: List of dicts with 'timestamp' and 'uv' fields,
                      ordered oldest to newest.

    Returns:
        dict with 'total_sed', 'peak_uv', 'hours_above_3', and 'burn_risk'

    Raises:
        ValueError: If fewer than 2 observations are provided.
    """
    if len(observations) < 2:
        raise ValueError("Need at least 2 observations to calculate UV dose")

    total_sed = 0.0
    peak_uv = 0.0
    hours_above_3 = 0.0

    for i in range(1, len(observations)):
        prev = observations[i - 1]
        curr = observations[i]

        interval_hours = (curr["timestamp"] - prev["timestamp"]) / 3600
        avg_uv = (prev["uv"] + curr["uv"]) / 2

        watts_per_m2 = avg_uv * 0.025
        joules_per_m2 = watts_per_m2 * interval_hours * 3600
        sed = joules_per_m2 / 100

        total_sed += sed
        peak_uv = max(peak_uv, curr["uv"])

        if avg_uv >= 3:
            hours_above_3 += interval_hours

    if peak_uv >= 11:
        burn_risk = "Extreme"
    elif peak_uv >= 8:
        burn_risk = "Very High"
    elif peak_uv >= 6:
        burn_risk = "High"
    elif peak_uv >= 3:
        burn_risk = "Moderate"
    else:
        burn_risk = "Low"

    return {
        "total_sed": round(total_sed, 2),
        "peak_uv": round(peak_uv, 1),
        "hours_above_3": round(hours_above_3, 2),
        "burn_risk": burn_risk,
    }
def solar_energy_potential(observations: list[dict], poll_interval_seconds: int = 600) -> dict:
    """
    Calculate cumulative solar energy received today in kWh/m².

    Integrates solar radiation over time using the midpoint rule.
    1 W/m² sustained for 1 hour = 1 Wh/m² = 0.001 kWh/m².

    Args:
        observations:          List of dicts with 'solar_radiation' field,
                               ordered oldest first, covering today only.
        poll_interval_seconds: Polling interval in seconds.

    Returns:
        dict with 'kwh_m2_today', 'peak_w_m2', 'description', and 'context'
    """
    if not observations:
        return {
            "kwh_m2_today": 0.0,
            "peak_w_m2": 0.0,
            "description": "No data",
            "context": "",
        }

    total_wh = 0.0
    peak = 0.0

    for obs in observations:
        radiation = obs.get("solar_radiation", 0.0) or 0.0
        total_wh += radiation * (poll_interval_seconds / 3600)
        peak = max(peak, radiation)

    kwh_m2 = round(total_wh / 1000, 3)

    # Context based on typical SE England values
    if kwh_m2 >= 6.0:
        description = "Excellent solar day"
        context = "Exceptional irradiance — comparable to a Mediterranean summer day"
    elif kwh_m2 >= 4.0:
        description = "Good solar day"
        context = "Strong irradiance — good conditions for solar generation"
    elif kwh_m2 >= 2.0:
        description = "Moderate solar day"
        context = "Moderate irradiance — partial cloud reducing potential"
    elif kwh_m2 >= 0.5:
        description = "Poor solar day"
        context = "Low irradiance — heavy cloud cover limiting generation"
    else:
        description = "Minimal solar energy"
        context = "Very low irradiance — overcast or night-dominated period"

    return {
        "kwh_m2_today": kwh_m2,
        "peak_w_m2": round(peak, 1),
        "description": description,
        "context": context,
    }
