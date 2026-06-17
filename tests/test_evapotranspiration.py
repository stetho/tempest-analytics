"""Tests for evapotranspiration.py"""

import datetime
import math
import pytest
from analytics.evapotranspiration import penman_monteith_et

LATITUDE = 51.4
DATE = datetime.date(2026, 6, 15)

# Realistic summer day observations
SUMMER_OBS = [
    {
        "timestamp": 1781481936 + i * 600,
        "air_temperature": 15.0 + 8.0 * math.sin(math.pi * i / 144),
        "relative_humidity": 75.0,
        "wind_avg": 3.0,
        "solar_radiation": max(0, 600 * math.sin(math.pi * i / 144)),
        "sea_level_pressure": 1015.0,
    }
    for i in range(144)
]

# Winter day — cold, low solar
WINTER_OBS = [
    {
        "timestamp": 1781481936 + i * 600,
        "air_temperature": 5.0 + 3.0 * math.sin(math.pi * i / 144),
        "relative_humidity": 85.0,
        "wind_avg": 8.0,
        "solar_radiation": max(0, 150 * math.sin(math.pi * i / 144)),
        "sea_level_pressure": 1010.0,
    }
    for i in range(144)
]


class TestPenmanMonteithEt:

    def test_raises_on_empty_observations(self):
        with pytest.raises(ValueError):
            penman_monteith_et([], LATITUDE, DATE)

    def test_returns_required_keys(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert "et0_mm" in result
        assert "interpretation" in result
        assert "date" in result
        assert "components" in result

    def test_et0_positive(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert result["et0_mm"] >= 0

    def test_summer_higher_than_winter(self):
        summer = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        winter = penman_monteith_et(WINTER_OBS, LATITUDE, datetime.date(2026, 1, 15))
        assert summer["et0_mm"] > winter["et0_mm"]

    def test_date_in_result(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert result["date"] == "2026-06-15"

    def test_components_present(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        components = result["components"]
        assert "t_max" in components
        assert "t_min" in components
        assert "t_mean" in components
        assert "rh_mean" in components
        assert "wind_mean_ms" in components
        assert "solar_radiation_mj" in components
        assert "net_radiation_mj" in components

    def test_t_max_greater_than_t_min(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert result["components"]["t_max"] > result["components"]["t_min"]

    def test_realistic_summer_range(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert 1.0 <= result["et0_mm"] <= 8.0

    def test_interpretation_returned(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        assert len(result["interpretation"]) > 0

    def test_wind_in_ms_not_mph(self):
        result = penman_monteith_et(SUMMER_OBS, LATITUDE, DATE)
        # 3 mph = 1.34 m/s — wind_mean_ms should be around that
        assert result["components"]["wind_mean_ms"] < 2.0
