"""
pollen.py — Pollen forecast from Open-Meteo Air Quality API.

Fetches grass, birch and alder pollen forecasts from the Copernicus
Atmosphere Monitoring Service (CAMS) via Open-Meteo, and returns
current and today's peak values with UK Met Office risk categories.

Pollen season guide for SE England:
    Alder:  January - April
    Birch:  March - May
    Grass:  May - September  ← primary hayfever trigger
"""

import datetime
import requests


# UK Met Office grass pollen thresholds (grains/m³)
GRASS_THRESHOLDS = [
    (0,   29,  "Low",       "low"),
    (30,  49,  "Moderate",  "moderate"),
    (50,  149, "High",      "high"),
    (150, 9999,"Very High", "very-high"),
]

# Birch and alder use the same European standard thresholds
TREE_THRESHOLDS = [
    (0,   14,  "Low",       "low"),
    (15,  49,  "Moderate",  "moderate"),
    (50,  199, "High",      "high"),
    (200, 9999,"Very High", "very-high"),
]

# Approximate pollen seasons for SE England (month ranges, inclusive)
SEASONS = {
    "alder": (1, 4),
    "birch": (3, 5),
    "grass": (5, 9),
}


def _categorise(value: float, thresholds: list) -> tuple[str, str]:
    """Return (label, risk) for a pollen value."""
    for lo, hi, label, risk in thresholds:
        if lo <= value <= hi:
            return label, risk
    return "Very High", "very-high"


def _in_season(pollen_type: str, month: int) -> bool:
    lo, hi = SEASONS[pollen_type]
    return lo <= month <= hi


def fetch_pollen(latitude: float, longitude: float) -> dict:
    """
    Fetch today's pollen forecast from Open-Meteo Air Quality API.

    Args:
        latitude:  Location latitude in decimal degrees
        longitude: Location longitude in decimal degrees

    Returns:
        dict with current and peak values for each pollen type,
        plus an overall hayfever risk assessment.

    Raises:
        requests.HTTPError: If the API request fails
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["grass_pollen", "birch_pollen", "alder_pollen"],
        "timezone": "Europe/London",
        "forecast_days": 1,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    hourly = data["hourly"]
    times = hourly["time"]
    grass = hourly["grass_pollen"]
    birch = hourly["birch_pollen"]
    alder = hourly["alder_pollen"]

    # Find the current hour index
    now = datetime.datetime.now()
    current_hour_str = now.strftime("%Y-%m-%dT%H:00")
    try:
        idx = times.index(current_hour_str)
    except ValueError:
        idx = 0

    month = now.month

    def _summarise(values: list, thresholds: list, pollen_type: str) -> dict:
        current_val = values[idx] or 0.0
        peak_val = max((v for v in values if v is not None), default=0.0)
        label, risk = _categorise(current_val, thresholds)
        in_season = _in_season(pollen_type, month)
        return {
            "current": round(current_val, 1),
            "peak_today": round(peak_val, 1),
            "category": label,
            "risk": risk,
            "in_season": in_season,
        }

    grass_data = _summarise(grass, GRASS_THRESHOLDS, "grass")
    birch_data = _summarise(birch, TREE_THRESHOLDS, "birch")
    alder_data = _summarise(alder, TREE_THRESHOLDS, "alder")

    # Overall hayfever risk — driven by whichever in-season pollen is highest
    in_season_pollens = [
        p for p in [grass_data, birch_data, alder_data] if p["in_season"]
    ]
    if in_season_pollens:
        worst = max(in_season_pollens, key=lambda p: p["current"])
        overall_risk = worst["risk"]
        overall_category = worst["category"]
    else:
        overall_risk = "low"
        overall_category = "Low"

    return {
        "grass": grass_data,
        "birch": birch_data,
        "alder": alder_data,
        "overall_risk": overall_risk,
        "overall_category": overall_category,
        "month": month,
    }
