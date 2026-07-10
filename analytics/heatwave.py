"""
heatwave.py — UK Met Office heatwave detection.

A heatwave is defined as a period of at least 3 consecutive days where
the daily maximum temperature meets or exceeds the regional threshold.
For London/SE England the threshold is 28°C.

Only completed days (yesterday and earlier) are counted toward the streak.
Today's current maximum is reported separately as context.
"""


def heatwave_status(
    daily_maxes: list[dict],
    todays_max: float | None,
    threshold: float = 28.0,
) -> dict:
    """
    Calculate current heatwave status.

    Args:
        daily_maxes:  List of dicts with 'day' (date string) and 'max_temp' (float),
                      ordered newest first, covering completed days only.
        todays_max:   Highest temperature recorded so far today, or None.
        threshold:    Daily max temperature threshold in °C. Defaults to 28.0.

    Returns a dict with:
        status:       'none' | 'monitoring' | 'heatwave'
        streak_days:  Number of consecutive completed days at or above threshold
        threshold:    The threshold used
        todays_max:   Today's highest temperature so far
        description:  Human-readable summary
        advice:       Contextual guidance
    """
    # Count consecutive completed days at or above threshold, starting from yesterday
    streak = 0
    for row in daily_maxes:
        if row["max_temp"] >= threshold:
            streak += 1
        else:
            break

    if streak >= 3:
        status = "heatwave"
        description = f"Heatwave — {streak} consecutive days at or above {threshold:.0f}°C"
        advice = (
            "Stay hydrated and keep out of the sun during the hottest part of the day. "
            "Check on elderly or vulnerable neighbours."
        )
    elif streak == 2:
        status = "monitoring"
        description = f"Possible heatwave developing — {streak} consecutive days at or above {threshold:.0f}°C"
        advice = (
            "A third consecutive day above the threshold would constitute "
            "an official Met Office heatwave."
        )
    else:
        status = "none"
        description = "No heatwave"
        advice = ""

    return {
        "status": status,
        "streak_days": streak,
        "threshold": threshold,
        "todays_max": todays_max,
        "description": description,
        "advice": advice,
    }
