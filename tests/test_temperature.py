"""Tests for temperature.py"""

import pytest
from analytics.temperature import absolute_humidity, frost_risk, thermal_comfort


class TestAbsoluteHumidity:

    def test_returns_required_keys(self):
        result = absolute_humidity(20.0, 60.0)
        assert "absolute_humidity_g_m3" in result
        assert "saturation_vapour_pressure" in result
        assert "actual_vapour_pressure" in result
        assert "description" in result

    def test_higher_temp_higher_saturation(self):
        cold = absolute_humidity(5.0, 100.0)
        warm = absolute_humidity(25.0, 100.0)
        assert warm["saturation_vapour_pressure"] > cold["saturation_vapour_pressure"]

    def test_very_dry_air(self):
        result = absolute_humidity(-10.0, 20.0)
        assert result["description"] == "Very dry air"

    def test_humid_air(self):
        result = absolute_humidity(30.0, 90.0)
        assert result["description"] in ("Humid", "Very humid")

    def test_actual_vp_less_than_saturation(self):
        result = absolute_humidity(20.0, 60.0)
        assert result["actual_vapour_pressure"] < result["saturation_vapour_pressure"]

    def test_100_percent_humidity_equals_saturation(self):
        result = absolute_humidity(20.0, 100.0)
        assert result["actual_vapour_pressure"] == result["saturation_vapour_pressure"]


class TestFrostRisk:

    def test_returns_required_keys(self):
        result = frost_risk(5.0, 2.0, 5.0, 14)
        assert "risk_level" in result
        assert "risk_score" in result
        assert "description" in result
        assert "factors" in result

    def test_classic_frost_conditions(self):
        result = frost_risk(1.2, -0.5, 1.1, 3)
        assert result["risk_level"] == "High"

    def test_summer_afternoon_no_risk(self):
        result = frost_risk(21.0, 13.0, 7.8, 14)
        assert result["risk_level"] == "None"

    def test_windy_night_reduces_risk(self):
        still = frost_risk(3.0, 1.0, 1.0, 3)
        windy = frost_risk(3.0, 1.0, 15.0, 3)
        assert still["risk_score"] > windy["risk_score"]

    def test_early_hours_increases_risk(self):
        afternoon = frost_risk(3.0, 1.0, 2.0, 14)
        early_hours = frost_risk(3.0, 1.0, 2.0, 3)
        assert early_hours["risk_score"] > afternoon["risk_score"]

    def test_factors_list_not_empty_for_high_risk(self):
        result = frost_risk(1.0, -1.0, 1.0, 3)
        assert len(result["factors"]) > 0

    def test_below_zero_temp_highest_score_contribution(self):
        freezing = frost_risk(-1.0, 5.0, 10.0, 14)
        cold = frost_risk(3.0, 5.0, 10.0, 14)
        assert freezing["risk_score"] > cold["risk_score"]


class TestThermalComfort:

    def test_returns_required_keys(self):
        result = thermal_comfort(20.0, 60.0, 5.0, 400.0)
        assert "comfort_temp" in result
        assert "category" in result
        assert "description" in result

    def test_hot_sunny_calm_is_heat_stress(self):
        result = thermal_comfort(35.0, 80.0, 1.0, 900.0)
        assert "stress" in result["category"].lower()

    def test_cold_windy_is_cold_stress(self):
        result = thermal_comfort(2.0, 80.0, 25.0, 0.0)
        assert "cold stress" in result["category"].lower()

    def test_solar_radiation_increases_comfort_temp(self):
        no_sun = thermal_comfort(20.0, 60.0, 3.0, 0.0)
        full_sun = thermal_comfort(20.0, 60.0, 3.0, 900.0)
        assert full_sun["comfort_temp"] > no_sun["comfort_temp"]

    def test_wind_decreases_comfort_temp(self):
        calm = thermal_comfort(20.0, 60.0, 1.0, 400.0)
        windy = thermal_comfort(20.0, 60.0, 20.0, 400.0)
        assert calm["comfort_temp"] > windy["comfort_temp"]

    def test_description_contains_feels_like(self):
        result = thermal_comfort(20.0, 60.0, 5.0, 400.0)
        assert "Feels like" in result["description"]

    def test_comfortable_range(self):
        result = thermal_comfort(22.0, 55.0, 5.0, 500.0)
        assert result["category"] == "No thermal stress — comfortable"