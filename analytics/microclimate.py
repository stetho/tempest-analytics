"""
microclimate.py — Compare Tempest station readings against Open-Meteo
regional model data to quantify local microclimate effects.

Functions:
    fetch_open_meteo        — Fetch current conditions from Open-Meteo API
    compare_microclimate    — Compare Tempest readings against model data
"""

import datetime
import requests


def is_daytime(hour_utc: int) -> bool:
    """
    Simple daytime check for UV comparison validity.
    Returns True between 04:00 and 21:00 UTC.
    """
    return 4 <= hour_utc <= 21


def fetch_open_meteo(latitude: float, longitude: float) -> dict:
    """
    Fetch current conditions from Open-Meteo for a given location.

    Open-Meteo is a free weather API requiring no API key.
    Returns conditions interpolated to the exact coordinates provided.

    Args:
        latitude: Location latitude in decimal degrees
        longitude: Location longitude in decimal degrees

    Returns:
        dict of current conditions from Open-Meteo

    Raises:
        requests.HTTPError: If the API request fails
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
            "uv_index",
        ],
        "timezone": "Europe/London",
        "wind_speed_unit": "mph",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["current"]


def compare_microclimate(tempest_obs: dict, open_meteo: dict) -> dict:
    """
    Compare Tempest station readings against Open-Meteo model data
    for the same location and approximate time.

    Quantifies the difference between hyperlocal rooftop readings
    and regional model forecasts — a measure of microclimate effect.

    Positive deltas mean the Tempest reads higher than the model.
    Negative deltas mean the Tempest reads lower than the model.

    Note: Pressure comparison is excluded as Tempest reports sea level
    pressure while Open-Meteo reports surface pressure at ground level —
    these are fundamentally different measurements.

    Note: UV comparison is suppressed at night as Open-Meteo UV
    interpolation is unreliable between sunset and sunrise.

    Args:
        tempest_obs: Latest observation dict from the Tempest database.
                     Required keys: air_temperature, relative_humidity,
                     wind_avg, wind_direction, uv, feels_like
        open_meteo: Current conditions dict from Open-Meteo API

    Returns:
        dict with 'tempest', 'open_meteo', 'deltas', 'interpretation'
        and 'open_meteo_time' keys
    """
    temp_delta = round(tempest_obs["air_temperature"] - open_meteo["temperature_2m"], 2)
    humidity_delta = round(tempest_obs["relative_humidity"] - open_meteo["relative_humidity_2m"], 1)
    wind_delta = round(tempest_obs["wind_avg"] - open_meteo["wind_speed_10m"], 2)

    dt_now = datetime.datetime.utcnow()
    if is_daytime(dt_now.hour):
        uv_delta = round(tempest_obs["uv"] - open_meteo["uv_index"], 2)
        uv_valid = True
    else:
        uv_delta = None
        uv_valid = False

    if temp_delta >= 2.0:
        temp_interpretation = "Significantly warmer than regional model — strong urban heat island effect"
    elif temp_delta >= 0.5:
        temp_interpretation = "Slightly warmer than regional model — mild urban heat island effect"
    elif temp_delta <= -2.0:
        temp_interpretation = "Significantly cooler than regional model — possible rooftop cooling effect"
    elif temp_delta <= -0.5:
        temp_interpretation = "Slightly cooler than regional model"
    else:
        temp_interpretation = "Close agreement with regional model"

    if wind_delta >= 3.0:
        wind_interpretation = "Rooftop significantly windier than model — exposed location"
    elif wind_delta <= -3.0:
        wind_interpretation = "Rooftop significantly calmer than model — sheltered location"
    else:
        wind_interpretation = "Wind broadly in line with model"

    return {
        "tempest": {
            "temperature": tempest_obs["air_temperature"],
            "humidity": tempest_obs["relative_humidity"],
            "wind_avg": tempest_obs["wind_avg"],
            "wind_direction": tempest_obs["wind_direction"],
            "uv": tempest_obs["uv"],
            "feels_like": tempest_obs["feels_like"],
        },
        "open_meteo": {
            "temperature": open_meteo["temperature_2m"],
            "humidity": open_meteo["relative_humidity_2m"],
            "wind_avg": open_meteo["wind_speed_10m"],
            "wind_direction": open_meteo["wind_direction_10m"],
            "uv": open_meteo["uv_index"],
            "feels_like": open_meteo["apparent_temperature"],
        },
        "deltas": {
            "temperature": temp_delta,
            "humidity": humidity_delta,
            "wind": wind_delta,
            "uv": uv_delta,
            "uv_valid": uv_valid,
        },
        "interpretation": {
            "temperature": temp_interpretation,
            "wind": wind_interpretation,
        },
        "open_meteo_time": open_meteo["time"],
    }
