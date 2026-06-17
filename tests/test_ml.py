"""Tests for ml.py"""

import pytest
import pandas as pd
from analytics.ml import (
    NaiveBayesRainPredictor,
    categorise_humidity,
    predict_from_observation,
)

# ── Sample training data ───────────────────────────────────────

def make_training_df(n_rain=20, n_dry=180):
    """Create a minimal training DataFrame."""
    rain_rows = [{
        'humidity_cat': 'very_humid',
        'pressure_trend': 'falling',
        'humidity_rising': False,
        'rain_next_3h': True,
    }] * n_rain

    dry_rows = [{
        'humidity_cat': 'dry',
        'pressure_trend': 'rising',
        'humidity_rising': False,
        'rain_next_3h': False,
    }] * n_dry

    return pd.DataFrame(rain_rows + dry_rows)


# ── categorise_humidity ────────────────────────────────────────

class TestCategoriseHumidity:

    def test_very_dry(self):
        assert categorise_humidity(40) == 'very_dry'
        assert categorise_humidity(54) == 'very_dry'

    def test_dry(self):
        assert categorise_humidity(55) == 'dry'
        assert categorise_humidity(69) == 'dry'

    def test_moderate(self):
        assert categorise_humidity(70) == 'moderate'
        assert categorise_humidity(79) == 'moderate'

    def test_humid(self):
        assert categorise_humidity(80) == 'humid'
        assert categorise_humidity(89) == 'humid'

    def test_very_humid(self):
        assert categorise_humidity(90) == 'very_humid'
        assert categorise_humidity(100) == 'very_humid'


# ── NaiveBayesRainPredictor ────────────────────────────────────

class TestNaiveBayesRainPredictor:

    def test_fit_sets_priors(self):
        model = NaiveBayesRainPredictor()
        df = make_training_df(n_rain=20, n_dry=80)
        model.fit(df)
        assert abs(model.prior_rain - 0.2) < 0.01
        assert abs(model.prior_dry - 0.8) < 0.01

    def test_predict_returns_required_keys(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        result = model.predict_proba('humid', 'steady', True)
        assert 'rain_probability' in result
        assert 'dry_probability' in result
        assert 'log_odds' in result

    def test_probabilities_sum_to_one(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        result = model.predict_proba('humid', 'falling', True)
        assert abs(result['rain_probability'] + result['dry_probability'] - 1.0) < 0.001

    def test_rain_conditions_higher_than_dry_conditions(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        rain_result = model.predict_proba('very_humid', 'falling', False)
        dry_result = model.predict_proba('very_dry', 'rising', False)
        assert rain_result['rain_probability'] > dry_result['rain_probability']

    def test_rising_pressure_reduces_rain_probability(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        rising = model.predict_proba('moderate', 'rising', False)
        falling = model.predict_proba('moderate', 'falling', False)
        assert rising['rain_probability'] < falling['rain_probability']

    def test_unfitted_model_raises(self):
        model = NaiveBayesRainPredictor()
        with pytest.raises(RuntimeError):
            model.predict_proba('humid', 'steady', True)

    def test_explain_returns_string(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        result = model.explain('very_humid', 'falling', False)
        assert isinstance(result, str)
        assert '%' in result

    def test_n_train_set_after_fit(self):
        model = NaiveBayesRainPredictor()
        df = make_training_df(n_rain=20, n_dry=80)
        model.fit(df)
        assert model.n_train == 100


# ── predict_from_observation ───────────────────────────────────

class TestPredictFromObservation:

    def test_returns_required_keys(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        current = {'relative_humidity': 85.0, 'pressure_trend': 'falling'}
        previous = {'relative_humidity': 80.0}
        result = predict_from_observation(model, current, previous)
        assert 'rain_probability' in result
        assert 'explanation' in result
        assert 'features' in result
        assert 'trained_on' in result

    def test_humidity_rising_detected(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        current = {'relative_humidity': 85.0, 'pressure_trend': 'steady'}
        previous = {'relative_humidity': 75.0}
        result = predict_from_observation(model, current, previous)
        assert result['features']['humidity_rising'] is True

    def test_humidity_falling_detected(self):
        model = NaiveBayesRainPredictor()
        model.fit(make_training_df())
        current = {'relative_humidity': 65.0, 'pressure_trend': 'steady'}
        previous = {'relative_humidity': 75.0}
        result = predict_from_observation(model, current, previous)
        assert result['features']['humidity_rising'] is False
