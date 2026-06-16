"""Tests for microclimate.py"""

import pytest
from unittest.mock import patch
import datetime
from analytics.microclimate import is_daytime, compare_microclimate

SAMPLE_TEMPEST = {
    "air_temperature": 22.0,
    "relative_humidity": 65.0,
    "wind_avg": 4.0,
    "wind_direction": 225,
    "uv": 5.0,
    "feels_like": 21.5,
}

SAMPLE_OPEN_METEO = {
    "temperature_2m": 20.0,
    "relative_humidity_2m": 60,
    "wind_speed_10m": 6.0,
    "wind_direction_10m": 210,
    "uv_index": 4.5,
    "apparent_temperature": 19.5,
    "time": "2026-06-15T14:00",
}


class TestIsDaytime:

    def test_midday_is_daytime(self):
        assert is_daytime(12) is True

    def test_midnight_is_not_daytime(self):
        assert is_daytime(0) is False

    def test_early_morning_boundary(self):
        assert is_daytime(4) is True
        assert is_daytime(3) is False

    def test_evening_boundary(self):
        assert is_daytime(21) is True
        assert is_daytime(22) is False


class TestCompareMicroclimate:

    def test_returns_required_keys(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert "tempest" in result
        assert "open_meteo" in result
        assert "deltas" in result
        assert "interpretation" in result
        assert "open_meteo_time" in result

    def test_temperature_delta_correct(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert result["deltas"]["temperature"] == 2.0

    def test_humidity_delta_correct(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert result["deltas"]["humidity"] == 5.0

    def test_wind_delta_correct(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert result["deltas"]["wind"] == -2.0

    def test_uv_valid_during_daytime(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert result["deltas"]["uv_valid"] is True
        assert result["deltas"]["uv"] is not None

    def test_uv_invalid_at_night(self):
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 1, 0)
            result = compare_microclimate(SAMPLE_TEMPEST, SAMPLE_OPEN_METEO)
        assert result["deltas"]["uv_valid"] is False
        assert result["deltas"]["uv"] is None

    def test_warmer_than_model_interpretation(self):
        warm_tempest = {**SAMPLE_TEMPEST, "air_temperature": 24.0}
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(warm_tempest, SAMPLE_OPEN_METEO)
        assert "warmer" in result["interpretation"]["temperature"]

    def test_cooler_than_model_interpretation(self):
        cool_tempest = {**SAMPLE_TEMPEST, "air_temperature": 17.0}
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(cool_tempest, SAMPLE_OPEN_METEO)
        assert "cooler" in result["interpretation"]["temperature"]

    def test_sheltered_wind_interpretation(self):
        calm_tempest = {**SAMPLE_TEMPEST, "wind_avg": 0.5}
        with patch("analytics.microclimate.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 6, 15, 12, 0)
            result = compare_microclimate(calm_tempest, SAMPLE_OPEN_METEO)
        assert "calmer" in result["interpretation"]["wind"]
