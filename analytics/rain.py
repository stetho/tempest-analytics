"""
rain.py — Rainfall analysis calculations.

Functions:
    rain_intensity          — Classify rainfall rate using Met Office categories
    spell_tracker           — Identify current and longest dry/wet spells
    antecedent_rainfall_index — Weighted recent rainfall for ground saturation estimate
"""


def rain_intensity(precip_mm_per_hour: float) -> dict:
    """
    Classify rainfall intensity based on mm/hour rate.

    Uses the UK Met Office classification system.

    Args:
        precip_mm_per_hour: Precipitation rate in mm/hour

    Returns:
        dict with 'intensity', 'description', and 'rate'
    """
    if precip_mm_per_hour == 0:
        return {
            "intensity": "None",
            "description": "Dry",
            "rate": 0.0,
        }
    elif precip_mm_per_hour < 0.5:
        intensity = "Trace"
        description = "Trace rainfall — barely measurable"
    elif precip_mm_per_hour < 2.0:
        intensity = "Light"
        description = "Light rain"
    elif precip_mm_per_hour < 10.0:
        intensity = "Moderate"
        description = "Moderate rain"
    elif precip_mm_per_hour < 50.0:
        intensity = "Heavy"
        description = "Heavy rain"
    else:
        intensity = "Violent"
        description = "Violent rain — flash flood risk"

    return {
        "intensity": intensity,
        "description": description,
        "rate": precip_mm_per_hour,
    }


def spell_tracker(daily_totals: list[dict], trace_threshold: float = 0.2) -> dict:
    """
    Analyse a series of daily rainfall totals to identify current
    dry and wet spells, and longest spells in the dataset.

    A dry day is defined as less than trace_threshold mm.
    A wet day is defined as trace_threshold mm or more.

    Args:
        daily_totals: List of dicts with 'date' and 'precip_total' (mm),
                      ordered oldest to newest.
        trace_threshold: Minimum mm to count as a wet day (default 0.2mm)

    Returns:
        dict with current and longest dry/wet spell information

    Raises:
        ValueError: If daily_totals is empty.
    """
    if not daily_totals:
        raise ValueError("Need at least one day of data")

    longest_dry = 0
    longest_wet = 0
    in_wet_spell = False
    current_wet = 0
    current_dry = 0

    for day in daily_totals:
        is_wet = day["precip_total"] >= trace_threshold

        if is_wet:
            current_wet += 1
            current_dry = 0
            in_wet_spell = True
            longest_wet = max(longest_wet, current_wet)
        else:
            current_dry += 1
            current_wet = 0
            in_wet_spell = False
            longest_dry = max(longest_dry, current_dry)

    current_length = 0
    if in_wet_spell:
        current_spell = "wet"
        for day in reversed(daily_totals):
            if day["precip_total"] >= trace_threshold:
                current_length += 1
            else:
                break
    else:
        current_spell = "dry"
        for day in reversed(daily_totals):
            if day["precip_total"] < trace_threshold:
                current_length += 1
            else:
                break

    return {
        "current_spell": current_spell,
        "current_spell_days": current_length,
        "longest_dry_days": longest_dry,
        "longest_wet_days": longest_wet,
        "total_days": len(daily_totals),
        "total_wet_days": sum(1 for d in daily_totals if d["precip_total"] >= trace_threshold),
        "total_dry_days": sum(1 for d in daily_totals if d["precip_total"] < trace_threshold),
    }


def antecedent_rainfall_index(daily_totals: list[dict], decay_factor: float = 0.85) -> dict:
    """
    Calculate the Antecedent Rainfall Index (ARI) — a weighted sum of
    recent rainfall where recent days count more than older days.

    Used in hydrology to estimate ground saturation. High ARI means
    the ground is likely saturated and surface flooding more probable.

    The decay factor controls how quickly older rainfall loses influence:
        0.85 = standard (each day's rainfall worth 85% of the previous)
        0.90 = slower decay, wetter climates
        0.80 = faster decay, drier climates

    Args:
        daily_totals: List of dicts with 'date' and 'precip_total' (mm),
                      ordered oldest to newest.
        decay_factor: Weight decay per day (default 0.85)

    Returns:
        dict with 'ari', 'saturation_risk', and 'description'

    Raises:
        ValueError: If daily_totals is empty.
    """
    if not daily_totals:
        raise ValueError("Need at least one day of data")

    ari = 0.0
    for i, day in enumerate(reversed(daily_totals)):
        weight = decay_factor ** i
        ari += day["precip_total"] * weight

    ari = round(ari, 2)

    if ari >= 30:
        saturation_risk = "Very High"
        description = "Ground likely saturated — high surface flood risk"
    elif ari >= 20:
        saturation_risk = "High"
        description = "Ground very wet — elevated flood risk"
    elif ari >= 10:
        saturation_risk = "Moderate"
        description = "Ground moderately wet"
    elif ari >= 5:
        saturation_risk = "Low"
        description = "Ground slightly wet"
    else:
        saturation_risk = "Very Low"
        description = "Ground dry — good absorption capacity"

    return {
        "ari": ari,
        "saturation_risk": saturation_risk,
        "description": description,
    }