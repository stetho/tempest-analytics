"""Tests for rain.py"""

import pytest
from analytics.rain import rain_intensity, spell_tracker, antecedent_rainfall_index


class TestRainIntensity:

    def test_dry(self):
        result = rain_intensity(0)
        assert result["intensity"] == "None"
        assert result["description"] == "Dry"

    def test_trace(self):
        result = rain_intensity(0.3)
        assert result["intensity"] == "Trace"

    def test_light(self):
        result = rain_intensity(1.0)
        assert result["intensity"] == "Light"

    def test_moderate(self):
        result = rain_intensity(5.0)
        assert result["intensity"] == "Moderate"

    def test_heavy(self):
        result = rain_intensity(25.0)
        assert result["intensity"] == "Heavy"

    def test_violent(self):
        result = rain_intensity(75.0)
        assert result["intensity"] == "Violent"

    def test_returns_required_keys(self):
        result = rain_intensity(5.0)
        assert "intensity" in result
        assert "description" in result
        assert "rate" in result


class TestSpellTracker:

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            spell_tracker([])

    def test_all_dry(self):
        days = [{"date": f"2026-06-0{i}", "precip_total": 0.0} for i in range(1, 8)]
        result = spell_tracker(days)
        assert result["current_spell"] == "dry"
        assert result["total_wet_days"] == 0

    def test_all_wet(self):
        days = [{"date": f"2026-06-0{i}", "precip_total": 5.0} for i in range(1, 8)]
        result = spell_tracker(days)
        assert result["current_spell"] == "wet"
        assert result["total_dry_days"] == 0

    def test_current_dry_spell_length(self):
        days = [
            {"date": "2026-06-01", "precip_total": 5.0},
            {"date": "2026-06-02", "precip_total": 5.0},
            {"date": "2026-06-03", "precip_total": 0.0},
            {"date": "2026-06-04", "precip_total": 0.0},
            {"date": "2026-06-05", "precip_total": 0.0},
        ]
        result = spell_tracker(days)
        assert result["current_spell"] == "dry"
        assert result["current_spell_days"] == 3

    def test_longest_wet_spell(self):
        days = [
            {"date": "2026-06-01", "precip_total": 5.0},
            {"date": "2026-06-02", "precip_total": 5.0},
            {"date": "2026-06-03", "precip_total": 5.0},
            {"date": "2026-06-04", "precip_total": 0.0},
            {"date": "2026-06-05", "precip_total": 5.0},
        ]
        result = spell_tracker(days)
        assert result["longest_wet_days"] == 3

    def test_returns_required_keys(self):
        days = [{"date": "2026-06-01", "precip_total": 0.0}]
        result = spell_tracker(days)
        assert "current_spell" in result
        assert "current_spell_days" in result
        assert "longest_dry_days" in result
        assert "longest_wet_days" in result
        assert "total_days" in result
        assert "total_wet_days" in result
        assert "total_dry_days" in result


class TestAntecedentRainfallIndex:

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            antecedent_rainfall_index([])

    def test_all_dry_gives_zero(self):
        days = [{"date": f"2026-06-0{i}", "precip_total": 0.0} for i in range(1, 8)]
        result = antecedent_rainfall_index(days)
        assert result["ari"] == 0.0
        assert result["saturation_risk"] == "Very Low"

    def test_heavy_recent_rain_high_risk(self):
        days = [
            {"date": "2026-06-01", "precip_total": 0.0},
            {"date": "2026-06-02", "precip_total": 25.0},
            {"date": "2026-06-03", "precip_total": 20.0},
        ]
        result = antecedent_rainfall_index(days)
        assert result["saturation_risk"] in ("High", "Very High")

    def test_recent_rain_weighs_more_than_old(self):
        old_rain = [
            {"date": "2026-06-01", "precip_total": 20.0},
            {"date": "2026-06-02", "precip_total": 0.0},
            {"date": "2026-06-03", "precip_total": 0.0},
        ]
        recent_rain = [
            {"date": "2026-06-01", "precip_total": 0.0},
            {"date": "2026-06-02", "precip_total": 0.0},
            {"date": "2026-06-03", "precip_total": 20.0},
        ]
        old_result = antecedent_rainfall_index(old_rain)
        recent_result = antecedent_rainfall_index(recent_rain)
        assert recent_result["ari"] > old_result["ari"]

    def test_returns_required_keys(self):
        days = [{"date": "2026-06-01", "precip_total": 5.0}]
        result = antecedent_rainfall_index(days)
        assert "ari" in result
        assert "saturation_risk" in result
        assert "description" in result

    def test_custom_decay_factor(self):
        days = [
            {"date": "2026-06-01", "precip_total": 10.0},
            {"date": "2026-06-02", "precip_total": 10.0},
        ]
        fast_decay = antecedent_rainfall_index(days, decay_factor=0.5)
        slow_decay = antecedent_rainfall_index(days, decay_factor=0.95)
        assert slow_decay["ari"] > fast_decay["ari"]