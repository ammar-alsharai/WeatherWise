import json
from datetime import date
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
URL = "https://api.open-meteo.com/v1/forecast"

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


def fetch_forecast():
    response = requests.get(URL, params=PARAMS, timeout=30)
    response.raise_for_status()  
    data = response.json()
    return data


def save_raw(data):
    path = RAW_DIR / f"forecast_{date.today().isoformat()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    data = fetch_forecast()
    hourly = data["hourly"]
    for i in range(5):
       print(f"{hourly['time'][i]} | {hourly['temperature_2m'][i]} °C | rain {hourly['precipitation_probability'][i]}%")
    save_raw(data)