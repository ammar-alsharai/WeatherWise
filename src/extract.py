import json
from datetime import date
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

PARAMS = {
    "latitude": 52.08,
    "longitude": 4.31,
    "hourly": ",".join([
        "temperature_2m", "apparent_temperature",
        "precipitation_probability", "precipitation",
        "wind_speed_10m", "wind_gusts_10m",
        "uv_index", "weather_code",
    ]),
    "timezone": "Europe/Amsterdam",
    "forecast_days": 2,
}

AQ_PARAMS = {
    "latitude": 52.08,
    "longitude": 4.31,
    "hourly": ",".join([
    "european_aqi", "pm2_5", "grass_pollen", "birch_pollen",
]),
    "timezone": "Europe/Amsterdam",
    "forecast_days": 2,
}

def fetch_forecast():
    response = requests.get(URL, params=PARAMS, timeout=30)
    response.raise_for_status()  
    data = response.json()
    return data

def fetch_air_quality():
    response = requests.get(AQ_URL, params=AQ_PARAMS, timeout=30)
    response.raise_for_status()  
    aq_data = response.json()
    return aq_data


def save_raw(data, name):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}_{date.today().isoformat()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)    


if __name__ == "__main__":
    data = fetch_forecast()
    aq_data = fetch_air_quality()
    hourly = data["hourly"]
    for i in range(5):
     print(f"{hourly['time'][i]} | {hourly['temperature_2m'][i]} °C | rain {hourly['precipitation_probability'][i]}%")
    save_raw(data, "forecast")
    save_raw(aq_data, "air_quality")