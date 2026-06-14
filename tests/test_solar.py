"""Tests for solar.py"""

import pytest
from analytics.solar import theoretical_solar_radiation, clear_sky_index, uv_dose_accumulator

LATITUDE = 51.389
LONGITUDE = -0.087

# Midday summer timestamp (13:00 local, 12:00 UTC)
MIDDAY_TS = 1781359200

# Night timestamp (02:00 UTC)
NIGHT_TS = 1781316000


class TestTheoreticalSolarRadiation:

    def test_returns_zero_at_night(self):
        result = theoretical_solar_radiation(NIGHT_TS, LATITUDE, LONGITUDE)
        assert result == 0.0

    def test_returns_positive_at_midday(self):
        result = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert result > 0

    def test_midday_higher_than_morning(self):
        solar_noon_ts = 1781355600   # 12:00 UTC = 13:00 BST, solar noon for Selhurst
        morning_ts = solar_noon_ts - 3600 * 4  # 08:00 UTC = 09:00 BST
        midday = theoretical_solar_radiation(solar_noon_ts, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        morning = theoretical_solar_radiation(morning_ts, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert midday > morning

    def test_does_not_exceed_solar_constant(self):
        result = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert result < 1361

    def test_bst_higher_than_gmt_at_same_utc_midday(self):
        # At 12:00 UTC in summer, BST (UTC+1) puts solar time closer to noon
        gmt = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=0.0)
        bst = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert bst != gmt


class TestClearSkyIndex:

    def test_night_returns_none_index(self):
        result = clear_sky_index(0, NIGHT_TS, LATITUDE, LONGITUDE)
        assert result["index"] is None
        assert "Night" in result["description"]

    def test_clear_sky(self):
        theory = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        actual = theory * 0.88
        result = clear_sky_index(actual, MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert result["description"] == "Clear sky"

    def test_overcast(self):
        theory = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        actual = theory * 0.15
        result = clear_sky_index(actual, MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert result["description"] == "Overcast"

    def test_partly_cloudy(self):
        theory = theoretical_solar_radiation(MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        actual = theory * 0.50
        result = clear_sky_index(actual, MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert result["description"] == "Partly cloudy"

    def test_returns_required_keys(self):
        result = clear_sky_index(500, MIDDAY_TS, LATITUDE, LONGITUDE, utc_offset_hours=1.0)
        assert "index" in result
        assert "theoretical" in result
        assert "actual" in result
        assert "description" in result


class TestUvDoseAccumulator:

    def test_requires_two_observations(self):
        with pytest.raises(ValueError):
            uv_dose_accumulator([{"timestamp": 1781359200, "uv": 5.0}])

    def test_zero_uv_gives_zero_dose(self):
        obs = [
            {"timestamp": 1781359200, "uv": 0.0},
            {"timestamp": 1781366400, "uv": 0.0},
        ]
        result = uv_dose_accumulator(obs)
        assert result["total_sed"] == 0.0
        assert result["burn_risk"] == "Low"

    def test_high_uv_gives_high_risk(self):
        obs = [
            {"timestamp": 1781359200, "uv": 7.0},
            {"timestamp": 1781366400, "uv": 7.0},
        ]
        result = uv_dose_accumulator(obs)
        assert result["burn_risk"] == "High"

    def test_extreme_uv(self):
        obs = [
            {"timestamp": 1781359200, "uv": 12.0},
            {"timestamp": 1781366400, "uv": 12.0},
        ]
        result = uv_dose_accumulator(obs)
        assert result["burn_risk"] == "Extreme"

    def test_peak_uv_tracked_correctly(self):
        obs = [
            {"timestamp": 1781352000, "uv": 2.0},
            {"timestamp": 1781359200, "uv": 6.5},
            {"timestamp": 1781366400, "uv": 3.0},
        ]
        result = uv_dose_accumulator(obs)
        assert result["peak_uv"] == 6.5

    def test_hours_above_3_calculated(self):
        obs = [
            {"timestamp": 1781352000, "uv": 1.0},   # below 3
            {"timestamp": 1781359200, "uv": 5.0},   # above 3
            {"timestamp": 1781366400, "uv": 5.0},   # above 3
        ]
        result = uv_dose_accumulator(obs)
        assert result["hours_above_3"] > 0

    def test_returns_required_keys(self):
        obs = [
            {"timestamp": 1781359200, "uv": 5.0},
            {"timestamp": 1781366400, "uv": 5.0},
        ]
        result = uv_dose_accumulator(obs)
        assert "total_sed" in result
        assert "peak_uv" in result
        assert "hours_above_3" in result
        assert "burn_risk" in result