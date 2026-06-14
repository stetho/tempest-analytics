"""Tests for records.py"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from analytics.records import get_all_time_records, get_daily_records, get_station_info


@pytest.fixture
def test_db():
    """Create a temporary test database with sample observations."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER UNIQUE,
            air_temperature REAL,
            feels_like REAL,
            relative_humidity REAL,
            barometric_pressure REAL,
            sea_level_pressure REAL,
            pressure_trend TEXT,
            wind_avg REAL,
            wind_gust REAL,
            wind_lull REAL,
            wind_direction INTEGER,
            solar_radiation REAL,
            uv REAL,
            brightness INTEGER,
            precip REAL,
            precip_accum_local_day REAL,
            precip_accum_local_yesterday REAL,
            lightning_strike_count INTEGER,
            lightning_strike_last_distance REAL,
            dew_point REAL,
            wet_bulb_temperature REAL,
            air_density REAL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert sample observations across two days
    observations = [
        (1781316000, 12.0, 11.0, 80, 1015.0, 1021.0, "steady", 3.0, 5.0, 1.0, 180, 0.0,   0.0, 0,      0.0, 0.00, 0.0, 0, 10.0, 8.0, 10.0, 1.21),
        (1781330400, 18.0, 17.5, 65, 1014.0, 1020.5, "steady", 4.0, 8.0, 2.0, 225, 450.0,  3.5, 45000,  0.0, 0.00, 0.0, 0, 10.0, 10.0, 13.0, 1.20),
        (1781344800, 21.0, 20.5, 58, 1013.5, 1020.0, "falling",5.0, 9.0, 2.5, 270, 850.0,  7.2, 95000,  0.0, 0.00, 0.0, 0, 10.0, 12.0, 15.0, 1.19),
        (1781402400, 11.8, 11.0, 82, 1016.0, 1022.0, "rising", 2.0, 4.0, 0.5,  90, 0.0,   0.0, 0,      0.2, 2.50, 0.0, 2, 8.0,  7.0,  9.5, 1.22),
        (1781416800, 19.5, 19.0, 62, 1015.5, 1021.5, "steady", 6.0, 12.0,3.0, 315, 750.0,  6.8, 85000,  0.5, 8.92, 0.0, 0, 10.0, 11.0, 14.0, 1.20),
    ]

    conn.executemany("""
        INSERT INTO observations (
            timestamp, air_temperature, feels_like, relative_humidity,
            barometric_pressure, sea_level_pressure, pressure_trend,
            wind_avg, wind_gust, wind_lull, wind_direction,
            solar_radiation, uv, brightness,
            precip, precip_accum_local_day, precip_accum_local_yesterday,
            lightning_strike_count, lightning_strike_last_distance,
            dew_point, wet_bulb_temperature, air_density
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, observations)
    conn.commit()
    conn.close()

    yield db_path
    db_path.unlink()


class TestGetAllTimeRecords:

    def test_returns_required_keys(self, test_db):
        records = get_all_time_records(test_db)
        assert "hottest" in records
        assert "coldest" in records
        assert "strongest_gust" in records
        assert "highest_uv" in records

    def test_hottest_correct(self, test_db):
        records = get_all_time_records(test_db)
        assert records["hottest"]["value"] == 21.0

    def test_coldest_correct(self, test_db):
        records = get_all_time_records(test_db)
        assert records["coldest"]["value"] == 11.8

    def test_strongest_gust_correct(self, test_db):
        records = get_all_time_records(test_db)
        assert records["strongest_gust"]["value"] == 12.0

    def test_highest_uv_correct(self, test_db):
        records = get_all_time_records(test_db)
        assert records["highest_uv"]["value"] == 7.2

    def test_record_has_datetime(self, test_db):
        records = get_all_time_records(test_db)
        assert "datetime" in records["hottest"]
        assert "UTC" in records["hottest"]["datetime"]


class TestGetDailyRecords:

    def test_returns_required_keys(self, test_db):
        records = get_daily_records(test_db)
        assert "wettest_day" in records
        assert "hottest_day" in records
        assert "coldest_night" in records
        assert "windiest_day" in records

    def test_wettest_day_correct(self, test_db):
        records = get_daily_records(test_db)
        assert records["wettest_day"]["value"] == 8.92

    def test_hottest_day_correct(self, test_db):
        records = get_daily_records(test_db)
        assert records["hottest_day"]["value"] == 21.0

    def test_coldest_night_correct(self, test_db):
        records = get_daily_records(test_db)
        assert records["coldest_night"]["value"] == 11.8

    def test_windiest_day_correct(self, test_db):
        records = get_daily_records(test_db)
        assert records["windiest_day"]["value"] == 12.0

    def test_records_have_dates(self, test_db):
        records = get_daily_records(test_db)
        assert "date" in records["hottest_day"]


class TestGetStationInfo:

    def test_returns_required_keys(self, test_db):
        info = get_station_info(test_db)
        assert "first_observation" in info
        assert "latest_observation" in info
        assert "total_observations" in info
        assert "days_of_data" in info
        assert "observations_per_day" in info

    def test_total_observations_correct(self, test_db):
        info = get_station_info(test_db)
        assert info["total_observations"] == 5

    def test_days_of_data_correct(self, test_db):
        info = get_station_info(test_db)
        assert info["days_of_data"] >= 1