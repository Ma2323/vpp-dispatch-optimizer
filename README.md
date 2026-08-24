# Virtual Power Plant (VPP): Dispatch Optimizer

## Executive Summary
This repository contains an end-to-end quantitative pipeline designed for European power markets. It asynchronously ingests physical grid data, statistically forecasts renewable energy variables, and utilizes Mixed-Integer Linear Programming (MILP) to schedule optimal battery dispatch for maximum Profit & Loss (P&L).

## Core Architecture

### 1. Asynchronous Data Ingestion
* Engineered an event-driven `asyncio` and `aiohttp` pipeline to concurrently stream meteorological grid data (100m wind speed, solar irradiance) without blocking CPU resources.

### 2. Predictive Forecasting (Champion vs. Challenger)
* **Objective:** Forecast renewable yield availability to inform trading decisions.
* **Methodology:** Pitted a classical Ridge Regression baseline against an advanced Machine Learning ensemble.
* **Result:** Identified a **Random Forest Regressor** as the highly accurate champion ($0.919$ $R^2$), rigorously validated via time-series cross-validation.

### 3. MILP Stack Optimization (PuLP)
* **Objective:** Maximize daily trading revenue given volatile day-ahead electricity prices.
* **Thermodynamic Realism:** Implemented a 90% Round-Trip Efficiency penalty to simulate real-world heat loss, successfully preventing physically impossible simultaneous charge/discharge cycles.
* **Cycle Aging (Degradation):** Implemented a €5/MWh marginal penalty on all power flow. The solver actively avoids dispatching during low-volatility hours where the arbitrage spread fails to cover the physical wear-and-tear of the lithium-ion cells.
* **Bang-Bang Control Theory:** The linear objective function contains no variable marginal costs, dictating that the system operates strictly at its absolute boundary constraints (25 MW or 0 MW) to capture the maximum arbitrage spread.

## Optimization Visual
![Optimized VPP Dispatch Schedule](dispatch_schedule.png)

## Execution Guide
1. Run `python ingestion/async_pipeline.py` to test the concurrent network stream.
2. Run `python forecasting/ml_forecaster.py` to evaluate the Champion vs. Challenger model backtest.
3. Run `python optimization/milp_optimizer.py` to generate the hourly dispatch schedule.