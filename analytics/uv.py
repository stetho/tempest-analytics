"""
uv.py — UV exposure and burn time calculations.

Calculates cumulative daily UV dose in Standard Erythemal Dose (SED)
units from a series of observations, and estimates time to sunburn
for different skin types.

1 SED = 100 J/m²
UV index to erythemal irradiance: 1 UV index unit ≈ 25 mW/m²
"""


# Skin type burn thresholds in SED (WHO standard, unprotected skin)
SKIN_TYPES = {
    "I":   {"label": "Type I (very fair/pale)",  "threshold_sed": 67},
    "II":  {"label": "Type II (fair)",            "threshold_sed": 100},
    "III": {"label": "Type III (medium)",         "threshold_sed": 133},
}

UV_TO_MW_M2 = 25.0  # mW/m² per UV index unit
SED = 100.0          # J/m² per SED


def calculate_uv_dose(observations: list[dict], poll_interval_seconds: int = 600) -> dict:
    """
    Calculate cumulative UV dose for today from a list of observations.

    Args:
        observations:          List of dicts with 'timestamp' and 'uv' keys,
                               ordered oldest first, covering today only.
        poll_interval_seconds: Polling interval in seconds. Used to calculate
                               exposure duration per reading.

    Returns:
        dict with:
            sed_today:         Total SED accumulated today
            percent_of_day:    Percentage of typical peak UV day accumulated
            skin_types:        List of dicts per skin type with burn info
            current_uv:        Most recent UV index reading
            peak_uv:           Highest UV index recorded today
    """
    if not observations:
        return {
            "sed_today": 0.0,
            "percent_of_day": 0.0,
            "skin_types": _skin_type_summary(0.0, None),
            "current_uv": 0.0,
            "peak_uv": 0.0,
        }

    # Accumulate dose using midpoint rule
    # Each reading represents poll_interval_seconds of exposure
    total_j_m2 = 0.0
    for obs in observations:
        uv = obs.get("uv", 0.0) or 0.0
        irradiance_w_m2 = (uv * UV_TO_MW_M2) / 1000.0  # convert mW to W
        total_j_m2 += irradiance_w_m2 * poll_interval_seconds

    sed_today = round(total_j_m2 / SED, 2)

    current_uv = observations[-1].get("uv", 0.0) or 0.0
    peak_uv = max((obs.get("uv", 0.0) or 0.0) for obs in observations)

    # Remaining UV hours today — rough estimate assuming current UV holds
    # Used to project whether burn threshold will be reached
    remaining_observations = _estimate_remaining_observations(
        observations, poll_interval_seconds
    )

    return {
        "sed_today": sed_today,
        "current_uv": round(current_uv, 2),
        "peak_uv": round(peak_uv, 2),
        "skin_types": _skin_type_summary(sed_today, current_uv, remaining_observations, poll_interval_seconds),
    }


def _estimate_remaining_observations(observations: list[dict], poll_interval_seconds: int) -> int:
    """
    Estimate how many more daylight observations remain today,
    based on the last non-zero UV reading.
    UV is effectively zero after sunset so we use a simple heuristic:
    assume daylight ends at the latest timestamp with UV > 0, plus a buffer.
    """
    # Find the last observation with UV > 0
    last_uv_ts = None
    for obs in reversed(observations):
        if (obs.get("uv") or 0.0) > 0:
            last_uv_ts = obs["timestamp"]
            break

    if last_uv_ts is None:
        return 0

    # Assume roughly 2 more hours of meaningful UV after current time
    # (conservative — actual depends on season and location)
    return int(7200 / poll_interval_seconds)


def _skin_type_summary(
    sed_today: float,
    current_uv: float | None,
    remaining_obs: int = 0,
    poll_interval_seconds: int = 600,
) -> list[dict]:
    """Build per-skin-type burn risk summary."""
    results = []

    for key, skin in SKIN_TYPES.items():
        threshold = skin["threshold_sed"]
        percent_used = round((sed_today / threshold) * 100, 1)
        sed_remaining = max(0.0, threshold - sed_today)

        # Estimate minutes to burn at current UV
        if current_uv and current_uv > 0:
            irradiance_w_m2 = (current_uv * UV_TO_MW_M2) / 1000.0
            sed_per_second = irradiance_w_m2 / SED
            if sed_per_second > 0 and sed_remaining > 0:
                seconds_to_burn = sed_remaining / sed_per_second
                minutes_to_burn = int(seconds_to_burn / 60)
            else:
                minutes_to_burn = None
        else:
            minutes_to_burn = None

        if percent_used >= 100:
            status = "Burn threshold reached"
            risk = "danger"
        elif percent_used >= 75:
            status = "Approaching limit"
            risk = "warning"
        elif percent_used >= 50:
            status = "Caution"
            risk = "moderate"
        else:
            status = "Safe"
            risk = "safe"

        results.append({
            "key": key,
            "label": skin["label"],
            "threshold_sed": threshold,
            "sed_accumulated": sed_today,
            "percent_used": percent_used,
            "minutes_to_burn": minutes_to_burn,
            "status": status,
            "risk": risk,
        })

    return results
