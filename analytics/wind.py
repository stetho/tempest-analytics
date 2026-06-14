"""
wind.py — Wind-based weather calculations.

Functions:
    beaufort_scale          — Convert wind speed to Beaufort scale
    gust_factor             — Ratio of gust to average wind speed
    wind_direction_compass  — Convert degrees to compass point
    wind_run                — Total distance wind has travelled over a period
"""


def beaufort_scale(wind_avg_mph: float) -> dict:
    """
    Convert wind speed in mph to the Beaufort scale.

    Args:
        wind_avg_mph: Average wind speed in mph

    Returns:
        dict with 'force', 'description', 'sea_state', and 'wind_mph'
    """
    if wind_avg_mph == 0:
        return {
            "force": 0,
            "description": "Calm",
            "sea_state": "Sea like a mirror",
            "wind_mph": 0,
        }
    scale = [
        (1,  0,  "Calm",              "Sea like a mirror"),
        (2,  3,  "Light air",         "Ripples, no foam crests"),
        (3,  7,  "Light breeze",      "Small wavelets"),
        (4,  12, "Gentle breeze",     "Large wavelets, scattered whitecaps"),
        (5,  18, "Moderate breeze",   "Small waves, frequent whitecaps"),
        (6,  24, "Fresh breeze",      "Moderate waves, many whitecaps"),
        (7,  31, "Strong breeze",     "Large waves, foam, some spray"),
        (8,  38, "Near gale",         "Sea heaps up, foam blown in streaks"),
        (9,  46, "Gale",              "High waves, dense foam, spray"),
        (10, 54, "Strong gale",       "Very high waves, rolling sea"),
        (11, 63, "Storm",             "Exceptionally high waves"),
        (12, 72, "Violent storm",     "Sea completely white with foam"),
        (13, 83, "Hurricane force",   "Air filled with foam and spray"),
    ]

    for force, threshold, description, sea_state in reversed(scale):
        if wind_avg_mph >= threshold:
            return {
                "force": force,
                "description": description,
                "sea_state": sea_state,
                "wind_mph": wind_avg_mph,
            }

    return {
        "force": 0,
        "description": "Calm",
        "sea_state": "Sea like a mirror",
        "wind_mph": wind_avg_mph,
    }


def gust_factor(wind_avg_mph: float, wind_gust_mph: float) -> dict:
    """
    Calculate the gust factor — ratio of gust speed to average wind speed.

    A high gust factor indicates turbulent, gusty conditions even if the
    average wind speed seems modest. Values above 2.0 indicate significant
    turbulence.

    Args:
        wind_avg_mph: Average wind speed in mph
        wind_gust_mph: Gust speed in mph

    Returns:
        dict with 'factor', 'description', and 'turbulent'
    """
    if wind_avg_mph == 0:
        return {
            "factor": None,
            "description": "Calm — gust factor not meaningful",
            "turbulent": False,
        }

    factor = round(wind_gust_mph / wind_avg_mph, 2)

    if factor >= 2.5:
        description = "Highly turbulent — very gusty conditions"
        turbulent = True
    elif factor >= 2.0:
        description = "Turbulent — noticeably gusty"
        turbulent = True
    elif factor >= 1.5:
        description = "Moderately gusty"
        turbulent = False
    else:
        description = "Steady wind, low turbulence"
        turbulent = False

    return {
        "factor": factor,
        "description": description,
        "turbulent": turbulent,
    }


def wind_direction_compass(degrees: int) -> dict:
    """
    Convert wind direction in degrees to a compass point.

    Args:
        degrees: Wind direction in degrees (0-360)

    Returns:
        dict with 'degrees', 'compass', 'abbreviation', and 'description'
    """
    directions = [
        (0,     "North",           "N",   "coming from the north"),
        (22.5,  "North-northeast", "NNE", "coming from the north-northeast"),
        (45,    "Northeast",       "NE",  "coming from the northeast"),
        (67.5,  "East-northeast",  "ENE", "coming from the east-southeast"),
        (90,    "East",            "E",   "coming from the east"),
        (112.5, "East-southeast",  "ESE", "coming from the east-southeast"),
        (135,   "Southeast",       "SE",  "coming from the southeast"),
        (157.5, "South-southeast", "SSE", "coming from the south-southeast"),
        (180,   "South",           "S",   "coming from the south"),
        (202.5, "South-southwest", "SSW", "coming from the south-southwest"),
        (225,   "Southwest",       "SW",  "coming from the southwest"),
        (247.5, "West-southwest",  "WSW", "coming from the west-southwest"),
        (270,   "West",            "W",   "coming from the west"),
        (292.5, "West-northwest",  "WNW", "coming from the west-northwest"),
        (315,   "Northwest",       "NW",  "coming from the northwest"),
        (337.5, "North-northwest", "NNW", "coming from the north-northwest"),
    ]

    degrees = degrees % 360
    index = round(degrees / 22.5) % 16
    _, name, abbreviation, description = directions[index]

    return {
        "degrees": degrees,
        "compass": name,
        "abbreviation": abbreviation,
        "description": description,
    }


def wind_run(observations: list[dict]) -> dict:
    """
    Calculate wind run — the total distance the wind has travelled
    past the station over a period of observations.

    Used in evapotranspiration calculations and as a general measure
    of how much air mass has moved through a location.

    Args:
        observations: List of dicts with 'timestamp' and 'wind_avg' (mph)

    Returns:
        dict with 'miles', 'km', and 'duration_hours'

    Raises:
        ValueError: If fewer than 2 observations are provided.
    """
    if len(observations) < 2:
        raise ValueError("Need at least 2 observations to calculate wind run")

    total_miles = 0.0

    for i in range(1, len(observations)):
        prev = observations[i - 1]
        curr = observations[i]

        interval_hours = (curr["timestamp"] - prev["timestamp"]) / 3600
        avg_speed = (prev["wind_avg"] + curr["wind_avg"]) / 2
        total_miles += avg_speed * interval_hours

    duration_hours = (
        observations[-1]["timestamp"] - observations[0]["timestamp"]
    ) / 3600

    return {
        "miles": round(total_miles, 2),
        "km": round(total_miles * 1.60934, 2),
        "duration_hours": round(duration_hours, 2),
    }
