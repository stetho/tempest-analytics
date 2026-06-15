"""Tests for pressure.py"""

import pytest
from analytics.pressure import pressure_change_rate, zambretti_forecast


class TestPressureChangeRate:

    def test_falling_pressure(self):
        obs = [
            {"timestamp": 1781353324, "sea_level_pressure": 1021.6},
            {"timestamp": 1781357824, "sea_level_pressure": 1018.4},
        ]
        rate = pressure_change_rate(obs)
        assert rate < 0, "Falling pressure should return a negative rate"

    def test_rising_pressure(self):
        obs = [
            {"timestamp": 1781353324, "sea_level_pressure": 1010.0},
            {"timestamp": 1781357824, "sea_level_pressure": 1015.0},
        ]
        rate = pressure_change_rate(obs)
        assert rate > 0, "Rising pressure should return a positive rate"

    def test_steady_pressure(self):
        obs = [
            {"timestamp": 1781353324, "sea_level_pressure": 1020.0},
            {"timestamp": 1781357824, "sea_level_pressure": 1020.0},
        ]
        rate = pressure_change_rate(obs)
        assert rate == 0.0

    def test_requires_two_observations(self):
        with pytest.raises(ValueError):
            pressure_change_rate([{"timestamp": 1781353324, "sea_level_pressure": 1020.0}])

    def test_uses_oldest_and_newest(self):
        obs = [
            {"timestamp": 1781353324, "sea_level_pressure": 1020.0},
            {"timestamp": 1781355000, "sea_level_pressure": 1019.0},
            {"timestamp": 1781357824, "sea_level_pressure": 1018.0},
        ]
        rate = pressure_change_rate(obs)
        assert rate < 0


class TestZambrettiForecast:

    def test_returns_required_keys(self):
        result = zambretti_forecast(1020.0, "steady")
        assert "letter" in result
        assert "forecast" in result
        assert "trend" in result
        assert "pressure" in result

    def test_high_pressure_steady_is_settled(self):
        result = zambretti_forecast(1035.0, "steady")
        assert result["letter"] == "A"
        assert result["forecast"] == "Settled fine"

    def test_low_falling_pressure_is_stormy(self):
        result = zambretti_forecast(995.0, "falling")
        assert result["letter"] == "Z"

    def test_rising_pressure_better_than_falling_at_same_level(self):
        rising = zambretti_forecast(1015.0, "rising")
        falling = zambretti_forecast(1015.0, "falling")
        # Letters closer to A are better - rising should have an earlier letter
        assert rising["letter"] < falling["letter"]

    def test_valid_letter_returned(self):
        result = zambretti_forecast(1020.0, "steady")
        assert result["letter"] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def test_winter_month(self):
        result = zambretti_forecast(1015.0, "rising", month=1)
        assert result["letter"] is not None

    def test_summer_month(self):
        result = zambretti_forecast(1015.0, "rising", month=7)
        assert result["letter"] is not None

from analytics.pressure import storm_predictor

class TestStormPredictor:

    def test_requires_two_observations(self):
        with pytest.raises(ValueError):
            storm_predictor([{"timestamp": 1781363162, "sea_level_pressure": 1015.0}])

    def test_rapid_fall_very_high_probability(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1025.0},
            {"timestamp": 1781374162, "sea_level_pressure": 1018.0},
        ]
        result = storm_predictor(obs)
        assert result["probability"] >= 85
        assert result["category"] == "Very High"

    def test_rising_pressure_low_probability(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1010.0},
            {"timestamp": 1781374162, "sea_level_pressure": 1013.0},
        ]
        result = storm_predictor(obs)
        assert result["probability"] <= 15

    def test_very_low_pressure_increases_probability(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1004.0},
            {"timestamp": 1781374162, "sea_level_pressure": 1002.0},
        ]
        result = storm_predictor(obs)
        assert result["probability"] >= 75

    def test_high_pressure_reduces_probability(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1028.0},
            {"timestamp": 1781374162, "sea_level_pressure": 1029.0},
        ]
        result = storm_predictor(obs)
        assert result["probability"] <= 10

    def test_returns_required_keys(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1015.0},
            {"timestamp": 1781374162, "sea_level_pressure": 1014.0},
        ]
        result = storm_predictor(obs)
        assert "probability" in result
        assert "category" in result
        assert "description" in result
        assert "advice" in result
        assert "change_rate" in result
        assert "current_pressure" in result
        assert "period_hours" in result

    def test_change_rate_correct(self):
        obs = [
            {"timestamp": 1781363162, "sea_level_pressure": 1015.0},
            {"timestamp": 1781374762, "sea_level_pressure": 1013.0},
        ]
        result = storm_predictor(obs)
        assert result["change_rate"] < 0
