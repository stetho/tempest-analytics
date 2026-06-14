# Tempest Analytics

A pure Python library of meteorological calculations built around data from the
[WeatherFlow Tempest](https://weatherflow.com/tempest-weather-system/) personal
weather station API.

Each module takes plain numbers in and returns structured results — no database
dependencies, no API calls, no side effects. Designed to be imported by the
[tempest-dashboard](https://github.com/stetho/tempest-dashboard) and
[tempest-alerts](https://github.com/stetho/tempest-alerts) projects, but usable
independently with any weather data source.

## Modules

### `pressure.py`
Pressure-based forecasting and trend analysis.

- **`pressure_change_rate`** — Rate of pressure change in mb/hour from a series
  of observations. Positive values indicate rising pressure, negative indicate falling.
- **`zambretti_forecast`** — The Zambretti Forecaster (1920): uses sea level pressure,
  trend, and season to produce a plain-English forecast. Seasonally adjusted for
  Northern Europe. Returns a forecast letter (A–Z) and description such as
  "Unsettled, rain later" or "Settled fine".

### `wind.py`
Wind speed, direction and turbulence calculations.

- **`beaufort_scale`** — Converts wind speed in mph to the Beaufort scale force
  (0–13) with description and sea state.
- **`gust_factor`** — Ratio of gust speed to average wind speed. Values above 2.0
  indicate turbulent conditions, common in urban environments.
- **`wind_direction_compass`** — Converts degrees (0–360) to a 16-point compass
  direction with abbreviation and plain-English description.
- **`wind_run`** — Total distance wind has travelled past the station over a period,
  in miles and km. Used in evapotranspiration calculations.

### `solar.py`
Solar radiation and UV calculations.

- **`theoretical_solar_radiation`** — Calculates the theoretical maximum solar
  radiation (W/m²) for a given location, date, and time using the solar position
  algorithm. Accounts for UTC offset (GMT/BST).
- **`clear_sky_index`** — Ratio of actual to theoretical solar radiation. Values
  near 1.0 indicate clear sky; lower values indicate cloud cover. Returns a
  plain-English description from "Clear sky" to "Overcast".
- **`uv_dose_accumulator`** — Integrates UV index over time to calculate cumulative
  UV dose in Standard Erythemal Dose (SED) units, peak UV index, hours above UV
  index 3, and WHO burn risk category.

### `temperature.py`
Temperature, humidity and human comfort calculations.

- **`absolute_humidity`** — Actual mass of water vapour per cubic metre of air
  (g/m³), derived using the Magnus formula. More meaningful than relative humidity
  for assessing mould risk and comfort.
- **`frost_risk`** — Multi-factor frost risk assessment combining air temperature,
  dew point, wind speed, and time of day. Returns a risk level, score, plain-English
  description, and list of contributing factors.
- **`thermal_comfort`** — Simplified Universal Thermal Climate Index (UTCI) combining
  temperature, humidity, wind, and solar radiation into a single comfort temperature
  and stress category.

### `rain.py`
Rainfall intensity and accumulation analysis.

- **`rain_intensity`** — Classifies precipitation rate (mm/hour) using the UK Met
  Office system: Trace, Light, Moderate, Heavy, or Violent.
- **`spell_tracker`** — Analyses daily rainfall totals to identify current dry or
  wet spell length, longest spells in the dataset, and total wet/dry day counts.
- **`antecedent_rainfall_index`** — Weighted sum of recent rainfall (ARI) where
  recent days count more than older days. Used in hydrology to estimate ground
  saturation and surface flood risk.

### `lightning.py`
Storm tracking and lightning safety.

- **`storm_approach_speed`** — Calculates storm approach or departure speed (mph)
  from a series of lightning strike distance readings. Identifies the storm's closest
  point and current direction of travel.
- **`lightning_safety`** — Safety risk assessment based on strike distance and
  hourly strike frequency. Implements the 30-30 rule with five risk levels from
  "Very Low" to "Extreme", with plain-English safety advice at each level.

## Installation

```bash
git clone https://github.com/stetho/tempest-analytics.git
cd tempest-analytics
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

All functions accept plain Python numbers and return dictionaries:

```python
from analytics.pressure import zambretti_forecast
from analytics.wind import beaufort_scale, wind_direction_compass
from analytics.lightning import lightning_safety

# Zambretti forecast from current station reading
forecast = zambretti_forecast(
    sea_level_pressure=1019.7,
    pressure_trend="steady"
)
print(forecast["forecast"])  # "Fine, possible showers"

# Wind conditions
wind = beaufort_scale(wind_avg_mph=12.4)
print(f"Force {wind['force']} — {wind['description']}")  # "Force 4 — Gentle breeze"

direction = wind_direction_compass(degrees=265)
print(direction["compass"])  # "West"

# Lightning safety check
safety = lightning_safety(distance_miles=8, strike_count_last_hour=6)
print(safety["advice"])  # "Move indoors or to a hard-topped vehicle..."
```

## Running the Tests

```bash
pytest -v
```

105 tests across 6 modules, all passing.

## Part of a Larger Project

This library is Phase 2 of a multi-part personal weather station project built
around a Tempest station mounted on a house in Selhurst, South London.

| Phase | Repo | Description | Status |
|---|---|---|---|
| 1 | `tempest-logger` | Data collection service | ✅ Complete |
| 2 | `tempest-analytics` | Derived calculations library | ✅ Complete |
| 3 | `tempest-dashboard` | Web visualisation | 🚧 In progress |
| 4 | — | Camera integration | 📋 Planned |
| 5 | `tempest-alerts` | Threshold alerting service (Go) | 📋 Planned |

## License

MIT
