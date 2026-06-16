"""
evapotranspiration.py — Reference evapotranspiration using the FAO-56
Penman-Monteith equation.

Functions:
    penman_monteith_et  — Daily ET₀ from a full day of observations
"""

import math
import datetime


def penman_monteith_et(
    observations: list[dict],
    latitude: float,
    date: datetime.date
) -> dict:
    """
    Calculate reference evapotranspiration (ET₀) using the FAO-56
    Penman-Monteith equation.

    ET₀ represents the evapotranspiration from a hypothetical reference
    crop (well-watered grass). Multiply by a crop coefficient to get
    actual ET for specific plants:
        - Grass/lawn:     Kc ≈ 1.0
        - Vegetables:     Kc ≈ 1.05
        - Trees/shrubs:   Kc ≈ 0.85

    All inputs are derived from standard weather station measurements.
    Suitable for daily calculations only — not sub-daily.

    Args:
        observations: List of dicts with 'timestamp', 'air_temperature',
                      'relative_humidity', 'wind_avg' (mph),
                      'solar_radiation' (W/m²), 'sea_level_pressure' (mb).
                      Should cover one full day.
        latitude: Station latitude in decimal degrees.
        date: Date of the observations.

    Returns:
        dict with 'et0_mm', 'interpretation', 'date', and 'components'

    Raises:
        ValueError: If no observations are provided.
    """
    if not observations:
        raise ValueError("No observations provided")

    # Daily aggregates
    temps = [o["air_temperature"] for o in observations]
    t_max = max(temps)
    t_min = min(temps)
    t_mean = sum(temps) / len(temps)

    rh_values = [o["relative_humidity"] for o in observations]
    rh_mean = sum(rh_values) / len(rh_values)

    # Convert wind from mph to m/s
    wind_values = [o["wind_avg"] * 0.44704 for o in observations]
    wind_mean = sum(wind_values) / len(wind_values)

    # Solar radiation: average W/m², convert to MJ/m²/day
    solar_values = [o["solar_radiation"] for o in observations]
    solar_mean = sum(solar_values) / len(solar_values)
    rs = solar_mean * 0.0864

    pressure_mb = sum(o["sea_level_pressure"] for o in observations) / len(observations)
    pressure_kpa = pressure_mb * 0.1

    # Psychrometric constant
    gamma = 0.000665 * pressure_kpa

    # Saturation vapour pressure
    def svp(t: float) -> float:
        return 0.6108 * math.exp(17.27 * t / (t + 237.3))

    e_s = (svp(t_max) + svp(t_min)) / 2
    e_a = e_s * (rh_mean / 100)

    # Slope of saturation vapour pressure curve
    delta = 4098 * svp(t_mean) / (t_mean + 237.3) ** 2

    # Net radiation
    day_of_year = date.timetuple().tm_yday
    lat_rad = math.radians(latitude)

    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    solar_dec = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    ws = math.acos(-math.tan(lat_rad) * math.tan(solar_dec))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat_rad) * math.sin(solar_dec) +
        math.cos(lat_rad) * math.cos(solar_dec) * math.sin(ws)
    )

    rso = (0.75 + 2e-5 * 52) * ra

    rns = (1 - 0.23) * rs

    sigma = 4.903e-9
    t_max_k = t_max + 273.16
    t_min_k = t_min + 273.16
    rnl = sigma * ((t_max_k**4 + t_min_k**4) / 2) * (
        0.34 - 0.14 * math.sqrt(e_a)
    ) * (1.35 * min(rs / rso, 1.0) - 0.35)

    rn = rns - rnl
    g = 0

    # Penman-Monteith ET₀
    numerator = (0.408 * delta * (rn - g) +
                 gamma * (900 / (t_mean + 273)) * wind_mean * (e_s - e_a))
    denominator = delta + gamma * (1 + 0.34 * wind_mean)
    et0 = round(max(0, numerator / denominator), 2)

    if et0 < 1:
        interpretation = "Very low — minimal watering needed"
    elif et0 < 2:
        interpretation = "Low — light watering may be beneficial"
    elif et0 < 4:
        interpretation = "Moderate — regular watering recommended"
    elif et0 < 6:
        interpretation = "High — plants need watering"
    else:
        interpretation = "Very high — water daily"

    return {
        "et0_mm": et0,
        "interpretation": interpretation,
        "date": date.isoformat(),
        "components": {
            "t_max": round(t_max, 1),
            "t_min": round(t_min, 1),
            "t_mean": round(t_mean, 1),
            "rh_mean": round(rh_mean, 1),
            "wind_mean_ms": round(wind_mean, 3),
            "solar_radiation_mj": round(rs, 2),
            "net_radiation_mj": round(rn, 2),
            "e_s_kpa": round(e_s, 3),
            "e_a_kpa": round(e_a, 3),
        }
    }
