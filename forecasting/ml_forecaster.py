import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score

class GenerationForecaster:
    """
    Evaluates a classical statistical baseline against a Machine Learning
    regressor to predict renewable energy generation.
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.prepare_features()

    def prepare_features(self):
        """Engineers time-based features from the raw timestamp."""
        self.data['hour'] = self.data.index.hour
        self.data['day_of_year'] = self.data.index.dayofyear
        
        # Target variable: we will forecast solar irradiance as a proxy for solar yield
        self.X = self.data[['hour', 'day_of_year', 'wind_speed_100m']]
        self.y = self.data['solar_irradiance']

    def evaluate_models(self):
        """Executes a Champion vs Challenger time-series backtest."""
        tscv = TimeSeriesSplit(n_splits=3)
        
        models = {
            "Statistical Baseline (Ridge)": Ridge(),
            "ML Champion (Random Forest)": RandomForestRegressor(n_estimators=100, random_state=42)
        }

        print("--- Model Validation Metrics ---")
        for name, model in models.items():
            rmse_scores = []
            r2_scores = []
            
            for train_idx, test_idx in tscv.split(self.X):
                X_train, X_test = self.X.iloc[train_idx], self.X.iloc[test_idx]
                y_train, y_test = self.y.iloc[train_idx], self.y.iloc[test_idx]
                
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                rmse_scores.append(np.sqrt(mean_squared_error(y_test, predictions)))
                r2_scores.append(r2_score(y_test, predictions))
                
            print(f"{name}:")
            print(f"  Average RMSE: {np.mean(rmse_scores):.2f}")
            print(f"  Average R²:   {np.mean(r2_scores):.3f}\n")

if __name__ == "__main__":
    # Simulate data handoff from the ingestion pipeline
    # In a live environment, this would be passed directly in memory
    np.random.seed(42)
    dates = pd.date_range(start="2026-08-01", periods=168, freq="h")
    mock_data = pd.DataFrame({
        "wind_speed_100m": np.random.normal(15, 5, 168),
        "solar_irradiance": np.where((dates.hour > 6) & (dates.hour < 18), np.random.normal(500, 100, 168), 0)
    }, index=dates)
    
    forecaster = GenerationForecaster(mock_data)
    forecaster.evaluate_models()