"""Tests for lightning.py"""

import pytest
from analytics.lightning import storm_approach_speed, lightning_safety


APPROACHING_EVENTS = [
    {"timestamp": 1781330400, "distance": 28, "count": 1},
    {"timestamp": 1781331000, "distance": 24, "count": 2},
    {"timestamp": 1781332200, "distance": 14, "count": 3},
    {"timestamp": 1781333400, "distance": 6,  "count": 8},
    {"timestamp": 1781334000, "distance": 4,  "count": 12},
]

DEPARTING_EVENTS = [
    {"timestamp": 1781334000, "distance": 4,  "count": 12},
    {"timestamp": 1781334600, "distance": 6,  "count": 7},
    {"timestamp": 1781335200, "distance": 10, "count": 4},
    {"timestamp": 1781335800, "distance": 16, "count": 2},
    {"timestamp": 1781337000, "distance": 28, "count": 1},
]

FULL_STORM = APPROACHING_EVENTS + DEPARTING_EVENTS[1:]


class TestStormApproachSpeed:

    def test_requires_two_events(self):
        with pytest.raises(ValueError):
            storm_approach_speed([{"timestamp": 1781330400, "distance": 10}])

    def test_approaching_storm(self):
        result = storm_approach_speed(APPROACHING_EVENTS)
        assert result["direction"] == "approaching"

    def test_departing_storm(self):
        result = storm_approach_speed(DEPARTING_EVENTS)
        assert result["direction"] == "departing"

    def test_closest_distance_correct(self):
        result = storm_approach_speed(FULL_STORM)
        assert result["closest_distance"] == 4

    def test_returns_required_keys(self):
        result = storm_approach_speed(APPROACHING_EVENTS)
        assert "speed_mph" in result
        assert "direction" in result
        assert "closest_distance" in result
        assert "closest_timestamp" in result
        assert "description" in result

    def test_description_contains_speed(self):
        result = storm_approach_speed(APPROACHING_EVENTS)
        assert "mph" in result["description"]

    def test_approaching_speed_is_positive(self):
        result = storm_approach_speed(APPROACHING_EVENTS)
        # Speed is signed — negative means approaching
        assert result["speed_mph"] < 0

    def test_departing_speed_is_positive(self):
        result = storm_approach_speed(DEPARTING_EVENTS)
        assert result["speed_mph"] > 0


class TestLightningSafety:

    def test_extreme_risk_very_close(self):
        result = lightning_safety(2, 5)
        assert result["risk_level"] == "Extreme"
        assert result["safe_to_be_outside"] is False

    def test_high_risk_within_6_miles(self):
        result = lightning_safety(5, 4)
        assert result["risk_level"] == "High"
        assert result["safe_to_be_outside"] is False

    def test_moderate_risk_within_12_miles(self):
        result = lightning_safety(10, 3)
        assert result["risk_level"] == "Moderate"
        assert result["safe_to_be_outside"] is False

    def test_low_risk_within_20_miles(self):
        result = lightning_safety(15, 2)
        assert result["risk_level"] == "Low"
        assert result["safe_to_be_outside"] is True

    def test_very_low_risk_distant(self):
        result = lightning_safety(30, 1)
        assert result["risk_level"] == "Very Low"
        assert result["safe_to_be_outside"] is True

    def test_high_frequency_upgrades_risk(self):
        result = lightning_safety(25, 15)
        assert result["risk_level"] == "Moderate"
        assert result["safe_to_be_outside"] is False

    def test_returns_required_keys(self):
        result = lightning_safety(10, 5)
        assert "risk_level" in result
        assert "safe_to_be_outside" in result
        assert "description" in result
        assert "advice" in result

    def test_advice_not_empty(self):
        result = lightning_safety(4, 12)
        assert len(result["advice"]) > 0