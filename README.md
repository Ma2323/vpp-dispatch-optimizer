# Virtual Power Plant: Battery Dispatch Optimiser

A small end-to-end prototype of the decision chain behind a battery in a virtual power plant: pull weather data, forecast renewable output, then schedule when the battery should charge and discharge against hourly electricity prices.

The three stages are separate scripts. Each runs on its own, and the forecasting and optimisation stages currently use synthetic inputs so the results are reproducible.

![Optimised dispatch schedule](./dispatch_schedule.png)

## What each stage does

### 1. Weather ingestion (`ingestion/async_pipeline.py`)
Fetches hourly 100 m wind speed and direct normal irradiance for the past 7 days from the free [Open-Meteo](https://open-meteo.com/) API, using `asyncio` and `aiohttp`, and returns a pandas DataFrame. It queries one location (London); the async structure is there so more locations can be fetched concurrently.

### 2. Generation forecasting (`forecasting/ml_forecaster.py`)
Compares a Ridge regression baseline with a Random Forest for predicting solar irradiance (a proxy for solar yield) from hour of day, day of year and wind speed, using 3-fold time-series cross-validation.

On the bundled synthetic week of data, the Random Forest reaches an average R² of about 0.92, while Ridge scores below zero. That gap is expected: irradiance is zero at night and high during the day, a non-linear shape a linear model on raw hour cannot capture. The score shows the method works, not real-world accuracy.

### 3. Dispatch optimisation (`optimization/milp_optimizer.py`)
A linear programme in PuLP (CBC solver) that chooses hourly charge and discharge volumes for a 100 MWh / 25 MW battery to maximise trading margin over 24 hours of day-ahead prices.

- **Efficiency:** 90% of charged energy reaches storage, so cycling has a real cost.
- **Degradation:** a €5/MWh penalty on every MWh charged or discharged, so the battery stays idle when the price spread does not cover wear.
- **State of charge:** tracked hour by hour, bounded between empty and full capacity. The battery starts empty.

Because the objective is linear with fixed rate limits, the optimal schedule tends to run at full power or not at all. The sample price curve includes a negative-price night trough and an evening peak, which the solver charges into and sells into respectively.

## Run it

Requires Python 3.9 or later.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python ingestion/async_pipeline.py        # live weather pull
python forecasting/ml_forecaster.py       # model comparison
python optimization/milp_optimizer.py     # dispatch schedule and chart
```

## Limitations and next steps

- Connect the stages: feed the ingested weather into the forecaster, and the forecast into the optimiser.
- Replace synthetic prices with real day-ahead prices (for example ENTSO-E) and forecast prices, not just generation.
- Add an end-of-day state-of-charge target, and a binary variable to forbid simultaneous charge and discharge (making it a true MILP).
- Handle forecast uncertainty, for example with scenario-based (stochastic) optimisation.
