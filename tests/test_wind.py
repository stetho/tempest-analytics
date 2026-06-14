"""Tests for wind.py"""

import pytest
from analytics.wind import beaufort_scale, gust_factor, wind_direction_compass, wind_run


class TestBeaufortScale:

    def test_calm(self):
        result = beaufort_scale(0)
        assert result["force"] == 0
        assert result["description"] == "Calm"

    def test_light_breeze(self):
        result = beaufort_scale(8.5)
        assert result["force"] == 3
        assert result["description"] == "Light breeze"

    def test_hurricane_force(self):
        result = beaufort_scale(90)
        assert result["force"] == 13

    def test_returns_required_keys(self):
        result = beaufort_scale(10)
        assert "force" in result
        assert "description" in result
        assert "sea_state" in result
        assert "wind_mph" in result

    def test_force_increases_with_speed(self):
        slow = beaufort_scale(5)
        fast = beaufort_scale(50)
        assert fast["force"] > slow["force"]


class TestGustFactor:

    def test_calm_returns_none_factor(self):
        result = gust_factor(0, 0)
        assert result["factor"] is None
        assert result["turbulent"] is False

    def test_turbulent_conditions(self):
        result = gust_factor(10, 22)
        assert result["turbulent"] is True

    def test_steady_conditions(self):
        result = gust_factor(10, 12)
        assert result["turbulent"] is False

    def test_returns_required_keys(self):
        result = gust_factor(10, 15)
        assert "factor" in result
        assert "description" in result
        assert "turbulent" in result

    def test_factor_calculation(self):
        result = gust_factor(10, 20)
        assert result["factor"] == 2.0


class TestWindDirectionCompass:

    def test_north(self):
        result = wind_direction_compass(0)
        assert result["abbreviation"] == "N"

    def test_east(self):
        result = wind_direction_compass(90)
        assert result["abbreviation"] == "E"

    def test_south(self):
        result = wind_direction_compass(180)
        assert result["abbreviation"] == "S"

    def test_west(self):
        result = wind_direction_compass(270)
        assert result["abbreviation"] == "W"

    def test_360_is_north(self):
        result = wind_direction_compass(360)
        assert result["abbreviation"] == "N"

    def test_southwest(self):
        result = wind_direction_compass(225)
        assert result["abbreviation"] == "SW"

    def test_returns_required_keys(self):
        result = wind_direction_compass(180)
        assert "degrees" in result
        assert "compass" in result
        assert "abbreviation" in result
        assert "description" in result


class TestWindRun:

    def test_basic_wind_run(self):
        obs = [
            {"timestamp": 1781353324, "wind_avg": 10.0},
            {"timestamp": 1781356924, "wind_avg": 10.0},
        ]
        result = wind_run(obs)
        assert result["miles"] == 10.0

    def test_requires_two_observations(self):
        with pytest.raises(ValueError):
            wind_run([{"timestamp": 1781353324, "wind_avg": 10.0}])

    def test_returns_required_keys(self):
        obs = [
            {"timestamp": 1781353324, "wind_avg": 10.0},
            {"timestamp": 1781356924, "wind_avg": 10.0},
        ]
        result = wind_run(obs)
        assert "miles" in result
        assert "km" in result
        assert "duration_hours" in result

    def test_km_conversion(self):
        obs = [
            {"timestamp": 1781353324, "wind_avg": 10.0},
            {"timestamp": 1781356924, "wind_avg": 10.0},
        ]
        result = wind_run(obs)
        assert result["km"] == round(result["miles"] * 1.60934, 2)