import asyncio
import aiohttp
import pandas as pd
import time

class WeatherGridIngestor:
    """
    Concurrent data pipeline to fetch physical weather variables
    required for Virtual Power Plant (VPP) generation forecasting.
    """
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        # Using London coordinates for the initial test grid
        self.params = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "hourly": ["wind_speed_100m", "direct_normal_irradiance"],
            "timezone": "Europe/London",
            "past_days": 7
        }

    async def fetch_node_data(self, session: aiohttp.ClientSession) -> dict:
        """Asynchronously executes the HTTP GET request to the weather grid."""
        print(f"[{time.strftime('%X')}] Dispatching async request to Open-Meteo...")
        async with session.get(self.base_url, params=self.params) as response:
            response.raise_for_status()
            return await response.json()

    async def run_pipeline(self) -> pd.DataFrame:
        """Manages the asynchronous event loop and processes the JSON payload."""
        async with aiohttp.ClientSession() as session:
            raw_data = await self.fetch_node_data(session)
            
            # Extract hourly time series into a pandas DataFrame
            hourly_data = raw_data.get("hourly", {})
            df = pd.DataFrame({
                "timestamp": pd.to_datetime(hourly_data.get("time")),
                "wind_speed_100m": hourly_data.get("wind_speed_100m"),
                "solar_irradiance": hourly_data.get("direct_normal_irradiance")
            })
            df.set_index("timestamp", inplace=True)
            return df

if __name__ == "__main__":
    # Initialize the ingestor and trigger the event loop
    ingestor = WeatherGridIngestor()
    
    start_time = time.time()
    df_weather = asyncio.run(ingestor.run_pipeline())
    execution_time = time.time() - start_time
    
    print(f"Pipeline executed in {execution_time:.3f} seconds.")
    print(df_weather.head())