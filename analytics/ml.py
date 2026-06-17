"""
ml.py — Machine learning and probabilistic weather prediction.

Classes:
    NaiveBayesRainPredictor — Naive Bayes classifier for 3-hour rain prediction

Functions:
    categorise_humidity         — Bin relative humidity into named categories
    predict_from_observation    — Generate prediction from live Tempest observations
"""

import math
import datetime
import pandas as pd
from pathlib import Path


def categorise_humidity(rh: float) -> str:
    """
    Bin relative humidity into named categories.

    Args:
        rh: Relative humidity percentage (0-100)

    Returns:
        One of: 'very_dry', 'dry', 'moderate', 'humid', 'very_humid'
    """
    if rh < 55: return 'very_dry'
    if rh < 70: return 'dry'
    if rh < 80: return 'moderate'
    if rh < 90: return 'humid'
    return 'very_humid'


class NaiveBayesRainPredictor:
    """
    Naive Bayes classifier for 3-hour rain prediction.

    Predicts whether rain will occur in the next 3 hours based on
    three features derived from Tempest station observations:

        humidity_cat:     binned relative humidity (very_dry → very_humid)
        pressure_trend:   rising / steady / falling (from Tempest API)
        humidity_rising:  whether humidity has increased in the last hour

    Assumes conditional independence between features given the class.
    Uses Laplace smoothing to handle zero probabilities for unseen
    feature combinations — essential for a small training dataset.

    The model improves as more observations accumulate. With only a few
    days of data, predictions at the extremes (very dry/rising pressure,
    very humid/falling pressure) are reliable; mid-range predictions
    will stabilise over weeks of data.

    Example:
        >>> model = NaiveBayesRainPredictor()
        >>> model.fit(df)
        >>> result = model.predict_proba('very_humid', 'falling', False)
        >>> print(result['rain_probability'])
        0.54
    """

    def __init__(self, smoothing: float = 1.0):
        """
        Args:
            smoothing: Laplace smoothing parameter. Higher values push
                       probabilities toward the prior. Default 1.0.
        """
        self.smoothing = smoothing
        self.prior_rain = None
        self.prior_dry = None
        self.likelihoods = {}
        self.feature_values = {}
        self.n_train = 0

    def fit(self, df: pd.DataFrame) -> 'NaiveBayesRainPredictor':
        """
        Train the model on historical observations.

        Args:
            df: DataFrame with columns 'humidity_cat', 'pressure_trend',
                'humidity_rising' (bool), and 'rain_next_3h' (bool target).

        Returns:
            self (for method chaining)
        """
        self.n_train = len(df)

        n_rain = df['rain_next_3h'].sum()
        n_dry = len(df) - n_rain
        self.prior_rain = n_rain / len(df)
        self.prior_dry = n_dry / len(df)

        features = ['humidity_cat', 'pressure_trend', 'humidity_rising']

        for feature in features:
            values = df[feature].unique()
            self.feature_values[feature] = values
            self.likelihoods[feature] = {}

            for value in values:
                k = self.smoothing
                n_values = len(values)

                n_feature_rain = ((df[feature] == value) & df['rain_next_3h']).sum()
                self.likelihoods[feature][(value, True)] = (
                    (n_feature_rain + k) / (n_rain + k * n_values)
                )

                n_feature_dry = ((df[feature] == value) & ~df['rain_next_3h']).sum()
                self.likelihoods[feature][(value, False)] = (
                    (n_feature_dry + k) / (n_dry + k * n_values)
                )

        return self

    def predict_proba(self, humidity_cat: str, pressure_trend: str,
                      humidity_rising: bool) -> dict:
        """
        Predict rain probability for given conditions.

        Uses log probabilities for numerical stability.

        Args:
            humidity_cat:    Humidity category from categorise_humidity()
            pressure_trend:  'rising', 'steady', or 'falling'
            humidity_rising: True if humidity has risen in the last hour

        Returns:
            dict with 'rain_probability', 'dry_probability', 'log_odds'
        """
        if self.prior_rain is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        features = {
            'humidity_cat': humidity_cat,
            'pressure_trend': pressure_trend,
            'humidity_rising': humidity_rising,
        }

        log_prob_rain = math.log(self.prior_rain)
        log_prob_dry = math.log(self.prior_dry)

        for feature, value in features.items():
            if (value, True) in self.likelihoods[feature]:
                log_prob_rain += math.log(self.likelihoods[feature][(value, True)])
                log_prob_dry += math.log(self.likelihoods[feature][(value, False)])

        max_log = max(log_prob_rain, log_prob_dry)
        prob_rain = math.exp(log_prob_rain - max_log)
        prob_dry = math.exp(log_prob_dry - max_log)
        total = prob_rain + prob_dry

        rain_probability = prob_rain / total

        return {
            'rain_probability': round(rain_probability, 4),
            'dry_probability': round(1 - rain_probability, 4),
            'log_odds': round(log_prob_rain - log_prob_dry, 3),
        }

    def explain(self, humidity_cat: str, pressure_trend: str,
                humidity_rising: bool) -> str:
        """
        Return a plain-English explanation of the prediction.

        Args:
            humidity_cat:    Humidity category
            pressure_trend:  Pressure trend
            humidity_rising: Whether humidity is rising

        Returns:
            Human-readable prediction string
        """
        result = self.predict_proba(humidity_cat, pressure_trend, humidity_rising)
        prob = result['rain_probability'] * 100

        factors = []
        if humidity_cat in ('very_humid', 'humid'):
            factors.append("high humidity")
        elif humidity_cat == 'very_dry':
            factors.append("very dry air")

        if pressure_trend == 'falling':
            factors.append("falling pressure")
        elif pressure_trend == 'rising':
            factors.append("rising pressure")

        if humidity_rising:
            factors.append("rising humidity")
        else:
            factors.append("stable or falling humidity")

        factor_str = ", ".join(factors)

        if prob >= 60:
            outlook = "Rain likely"
        elif prob >= 35:
            outlook = "Rain possible"
        elif prob >= 15:
            outlook = "Rain unlikely but possible"
        else:
            outlook = "Rain very unlikely"

        return f"{outlook} ({prob:.0f}%) — {factor_str}"


def build_training_dataframe(db_path: Path) -> pd.DataFrame:
    """
    Build a training DataFrame from the Tempest observation database.

    Derives features and target variable from raw observations:
        - humidity_cat:     binned humidity category
        - pressure_trend:   from the observation
        - humidity_rising:  comparison with observation 1 hour prior
        - rain_next_3h:     whether any rain occurred in the next 3 hours

    Args:
        db_path: Path to the SQLite database file

    Returns:
        DataFrame ready for model.fit()
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT
            timestamp,
            relative_humidity,
            sea_level_pressure,
            pressure_trend,
            precip
        FROM observations
        ORDER BY timestamp ASC
    """, conn)
    conn.close()

    LOOKAHEAD = 18  # 3 hours at 10-minute intervals

    rain_next_3h = []
    for i in range(len(df)):
        future = df['precip'].iloc[i+1:i+LOOKAHEAD+1]
        rain_next_3h.append(future.sum() > 0)
    df['rain_next_3h'] = rain_next_3h

    df['humidity_1h_ago'] = df['relative_humidity'].shift(6)
    df = df.dropna(subset=['humidity_1h_ago']).reset_index(drop=True)
    df['humidity_rising'] = df['relative_humidity'] > df['humidity_1h_ago']

    bins = [0, 55, 70, 80, 90, 100]
    labels = ['very_dry', 'dry', 'moderate', 'humid', 'very_humid']
    df['humidity_cat'] = pd.cut(
        df['relative_humidity'], bins=bins, labels=labels
    )

    return df


def predict_from_observation(model: NaiveBayesRainPredictor,
                              current_obs: dict,
                              previous_obs: dict) -> dict:
    """
    Generate a rain prediction from live Tempest observations.

    Args:
        model:        Trained NaiveBayesRainPredictor
        current_obs:  Latest observation dict from the database
        previous_obs: Observation from approximately 1 hour ago

    Returns:
        dict with 'rain_probability', 'dry_probability',
        'explanation', and 'features'
    """
    humidity_cat = categorise_humidity(current_obs['relative_humidity'])
    pressure_trend = current_obs['pressure_trend']
    humidity_rising = (
        current_obs['relative_humidity'] > previous_obs['relative_humidity']
    )

    result = model.predict_proba(humidity_cat, pressure_trend, humidity_rising)
    explanation = model.explain(humidity_cat, pressure_trend, humidity_rising)

    return {
        'rain_probability': result['rain_probability'],
        'dry_probability': result['dry_probability'],
        'log_odds': result['log_odds'],
        'explanation': explanation,
        'features': {
            'humidity': current_obs['relative_humidity'],
            'humidity_cat': humidity_cat,
            'pressure_trend': pressure_trend,
            'humidity_rising': humidity_rising,
            'humidity_1h_ago': previous_obs['relative_humidity'],
        },
        'trained_on': model.n_train,
    }
