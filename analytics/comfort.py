"""
comfort.py — Outdoor comfort score.

Combines temperature, humidity, wind, UV index and pollen into a
single 0-10 score representing how pleasant conditions are for
spending time outside.

Designed for temperate UK conditions — optimum ranges reflect
what feels comfortable in SE England rather than Mediterranean norms.
"""


def outdoor_comfort_score(
    air_temperature: float,
    relative_humidity: float,
    wind_avg: float,
    uv: float,
    pollen_risk: str = "low",
) -> dict:
    """
    Calculate an outdoor comfort score from current conditions.

    Args:
        air_temperature:   Air temperature in °C
        relative_humidity: Relative humidity as a percentage (0-100)
        wind_avg:          Average wind speed in mph
        uv:                UV index
        pollen_risk:       Pollen risk level: 'low', 'moderate', 'high', 'very-high'

    Returns:
        dict with 'score', 'label', 'description', and 'factors'
    """
    factors = []
    score = 0.0

    # ── Temperature (0-3 points) ──────────────────────────────
    # Ideal range 18-24°C. Scores fall off either side.
    if 18 <= air_temperature <= 24:
        temp_score = 3.0
        factors.append(f"Temperature {air_temperature}°C — ideal")
    elif 14 <= air_temperature < 18:
        temp_score = 2.0
        factors.append(f"Temperature {air_temperature}°C — a little cool")
    elif 24 < air_temperature <= 28:
        temp_score = 2.0
        factors.append(f"Temperature {air_temperature}°C — warm")
    elif 10 <= air_temperature < 14:
        temp_score = 1.0
        factors.append(f"Temperature {air_temperature}°C — cool")
    elif 28 < air_temperature <= 33:
        temp_score = 1.0
        factors.append(f"Temperature {air_temperature}°C — hot")
    else:
        temp_score = 0.0
        if air_temperature < 10:
            factors.append(f"Temperature {air_temperature}°C — cold")
        else:
            factors.append(f"Temperature {air_temperature}°C — very hot")
    score += temp_score

    # ── Humidity (0-2 points) ────────────────────────────────
    if relative_humidity <= 60:
        hum_score = 2.0
        factors.append(f"Humidity {relative_humidity}% — comfortable")
    elif relative_humidity <= 70:
        hum_score = 1.5
        factors.append(f"Humidity {relative_humidity}% — slightly humid")
    elif relative_humidity <= 80:
        hum_score = 1.0
        factors.append(f"Humidity {relative_humidity}% — humid")
    elif relative_humidity <= 90:
        hum_score = 0.5
        factors.append(f"Humidity {relative_humidity}% — very humid")
    else:
        hum_score = 0.0
        factors.append(f"Humidity {relative_humidity}% — oppressively humid")
    score += hum_score

    # ── Wind (0-2 points) ────────────────────────────────────
    # Light breeze is pleasant; calm and strong wind both reduce comfort
    if 5 <= wind_avg <= 15:
        wind_score = 2.0
        factors.append(f"Wind {wind_avg} mph — pleasant breeze")
    elif 2 <= wind_avg < 5:
        wind_score = 1.5
        factors.append(f"Wind {wind_avg} mph — light air")
    elif 15 < wind_avg <= 25:
        wind_score = 1.0
        factors.append(f"Wind {wind_avg} mph — breezy")
    elif wind_avg < 2:
        wind_score = 1.0
        factors.append(f"Wind {wind_avg} mph — calm, still air")
    else:
        wind_score = 0.0
        factors.append(f"Wind {wind_avg} mph — strong wind")
    score += wind_score

    # ── UV (0-2 points) ──────────────────────────────────────
    if uv <= 2:
        uv_score = 2.0
        factors.append(f"UV index {uv} — no sun protection needed")
    elif uv <= 5:
        uv_score = 1.5
        factors.append(f"UV index {uv} — moderate, protection advisable")
    elif uv <= 7:
        uv_score = 1.0
        factors.append(f"UV index {uv} — high, limit midday exposure")
    elif uv <= 10:
        uv_score = 0.5
        factors.append(f"UV index {uv} — very high, seek shade")
    else:
        uv_score = 0.0
        factors.append(f"UV index {uv} — extreme UV")
    score += uv_score

    # ── Pollen (0-1 point) ───────────────────────────────────
    pollen_map = {
        "low":       (1.0,  "Low pollen — no impact on comfort"),
        "moderate":  (0.5,  "Moderate pollen — may affect hayfever sufferers"),
        "high":      (0.0,  "High pollen — significant hayfever risk"),
        "very-high": (0.0,  "Very high pollen — severe hayfever risk"),
    }
    pollen_score, pollen_factor = pollen_map.get(
        pollen_risk.lower(), (1.0, "Pollen data unavailable")
    )
    score += pollen_score
    factors.append(pollen_factor)

    # ── Final score and label ────────────────────────────────
    score = round(min(10.0, score), 1)

    if score >= 9.0:
        label = "Excellent"
        description = "Perfect conditions for outdoor activities"
    elif score >= 7.5:
        label = "Very Good"
        description = "Great conditions to be outside"
    elif score >= 6.0:
        label = "Good"
        description = "Comfortable conditions outside"
    elif score >= 4.5:
        label = "Fair"
        description = "Acceptable outdoor conditions with some caveats"
    elif score >= 3.0:
        label = "Poor"
        description = "Outdoor activities may be uncomfortable"
    else:
        label = "Unpleasant"
        description = "Conditions are not conducive to being outside"

    return {
        "score": score,
        "label": label,
        "description": description,
        "factors": factors,
    }
