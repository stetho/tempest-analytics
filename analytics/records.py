"""
records.py — All-time and daily records from the observation database.

Functions:
    get_all_time_records    — All-time highs and lows across all observations
    get_daily_records       — Best and worst values aggregated by day
    get_station_info        — Basic station statistics and data coverage
"""

import sqlite3
import datetime
from pathlib import Path


def _get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_time_records(db_path: Path) -> dict:
    """
    Query the database for all-time records across all observations.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict of record categories, each with value, unit,
        description, timestamp, and formatted datetime.
    """
    queries = {
        "hottest": (
            "SELECT MAX(air_temperature), timestamp FROM observations",
            "°C", "Hottest temperature"
        ),
        "coldest": (
            "SELECT MIN(air_temperature), timestamp FROM observations",
            "°C", "Coldest temperature"
        ),
        "highest_pressure": (
            "SELECT MAX(sea_level_pressure), timestamp FROM observations",
            "mb", "Highest pressure"
        ),
        "lowest_pressure": (
            "SELECT MIN(sea_level_pressure), timestamp FROM observations",
            "mb", "Lowest pressure"
        ),
        "strongest_gust": (
            "SELECT MAX(wind_gust), timestamp FROM observations",
            "mph", "Strongest gust"
        ),
        "highest_wind_avg": (
            "SELECT MAX(wind_avg), timestamp FROM observations",
            "mph", "Highest average wind"
        ),
        "highest_uv": (
            "SELECT MAX(uv), timestamp FROM observations",
            "", "Highest UV index"
        ),
        "highest_solar": (
            "SELECT MAX(solar_radiation), timestamp FROM observations",
            "W/m²", "Highest solar radiation"
        ),
        "wettest_hour": (
            "SELECT MAX(precip), timestamp FROM observations",
            "mm", "Wettest hour"
        ),
        "most_lightning": (
            "SELECT MAX(lightning_strike_count), timestamp FROM observations",
            "", "Most lightning strikes"
        ),
    }

    records = {}

    with _get_connection(db_path) as conn:
        for key, (query, unit, description) in queries.items():
            row = conn.execute(query).fetchone()
            value = row[0]
            timestamp = row[1]
            dt = datetime.datetime.fromtimestamp(timestamp, datetime.UTC)

            records[key] = {
                "value": value,
                "unit": unit,
                "description": description,
                "timestamp": timestamp,
                "datetime": dt.strftime("%Y-%m-%d %H:%M UTC"),
            }

    return records


def get_daily_records(db_path: Path) -> dict:
    """
    Query daily aggregated records from the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict with wettest, hottest, coldest and windiest day records.
    """
    with _get_connection(db_path) as conn:
        wettest = conn.execute("""
            SELECT
                date(timestamp, 'unixepoch') as date,
                MAX(precip_accum_local_day) as total
            FROM observations
            GROUP BY date(timestamp, 'unixepoch')
            ORDER BY total DESC
            LIMIT 1
        """).fetchone()

        hottest_day = conn.execute("""
            SELECT
                date(timestamp, 'unixepoch') as date,
                MAX(air_temperature) as max_temp
            FROM observations
            GROUP BY date(timestamp, 'unixepoch')
            ORDER BY max_temp DESC
            LIMIT 1
        """).fetchone()

        coldest_night = conn.execute("""
            SELECT
                date(timestamp, 'unixepoch') as date,
                MIN(air_temperature) as min_temp
            FROM observations
            GROUP BY date(timestamp, 'unixepoch')
            ORDER BY min_temp ASC
            LIMIT 1
        """).fetchone()

        windiest = conn.execute("""
            SELECT
                date(timestamp, 'unixepoch') as date,
                MAX(wind_gust) as max_gust
            FROM observations
            GROUP BY date(timestamp, 'unixepoch')
            ORDER BY max_gust DESC
            LIMIT 1
        """).fetchone()

    return {
        "wettest_day": {
            "value": round(wettest["total"], 2),
            "unit": "mm",
            "date": wettest["date"],
            "description": "Wettest day",
        },
        "hottest_day": {
            "value": hottest_day["max_temp"],
            "unit": "°C",
            "date": hottest_day["date"],
            "description": "Hottest day",
        },
        "coldest_night": {
            "value": coldest_night["min_temp"],
            "unit": "°C",
            "date": coldest_night["date"],
            "description": "Coldest night",
        },
        "windiest_day": {
            "value": windiest["max_gust"],
            "unit": "mph",
            "date": windiest["date"],
            "description": "Windiest day",
        },
    }


def get_station_info(db_path: Path) -> dict:
    """
    Return basic station statistics — first observation date,
    total observations, and days of data.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict with station statistics.
    """
    with _get_connection(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM observations"
        ).fetchone()[0]

        first_ts = conn.execute(
            "SELECT MIN(timestamp) FROM observations"
        ).fetchone()[0]

        last_ts = conn.execute(
            "SELECT MAX(timestamp) FROM observations"
        ).fetchone()[0]

    first_dt = datetime.datetime.fromtimestamp(first_ts, datetime.UTC)
    last_dt = datetime.datetime.fromtimestamp(last_ts, datetime.UTC)
    days = (last_dt - first_dt).days + 1

    return {
        "first_observation": first_dt.strftime("%Y-%m-%d"),
        "latest_observation": last_dt.strftime("%Y-%m-%d %H:%M UTC"),
        "total_observations": count,
        "days_of_data": days,
        "observations_per_day": round(count / days),
    }