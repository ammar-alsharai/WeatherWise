import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
pd.set_option("display.max_columns", None)
# Beaufort scale: the upper limit in km/h for each force (0 to 11).
# Anything above the last number is force 12.
BEAUFORT_LIMITS_KMH = [1, 5, 11, 19, 28, 38, 49, 61, 74, 88, 102, 117]

# WMO weather codes used by Open-Meteo
WEATHER_CODES = {
    0: "clear", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    56: "freezing drizzle", 57: "freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    66: "freezing rain", 67: "freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
    80: "light showers", 81: "showers", 82: "heavy showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


def load_latest_raw():
    # TODO 1: find all files matching "forecast_*.json" in RAW_DIR
    #         (hint: sorted(RAW_DIR.glob("forecast_*.json")))
    sorted_files = sorted(RAW_DIR.glob("forecast_*.json"))
    # TODO 2: pick the newest one (hint: the last item in a sorted list is [-1])
    latest_file = sorted_files[-1]
    # TODO 3: open it and return json.load(f)
    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)
    


def kmh_to_beaufort(speed_kmh):
            
    for force, limit in enumerate(BEAUFORT_LIMITS_KMH):
        if speed_kmh <= limit:
            return force
    return 12
    # TODO 4: loop over BEAUFORT_LIMITS_KMH with enumerate().
    #         Return the position (force) of the first limit where speed_kmh <= limit.
    #         If none matches, return 12.
    


def build_hourly_table(data):
             df = pd.DataFrame(data["hourly"])
             df["time"] = pd.to_datetime(df["time"])
             df["wind_bft"] = df["wind_speed_10m"].apply(kmh_to_beaufort)
             df["gust_bft"] = df["wind_gusts_10m"].apply(kmh_to_beaufort)
             df["weather"] = df["weather_code"].map(WEATHER_CODES)    
             return df
    # TODO 5: create a DataFrame from data["hourly"] (hint: pd.DataFrame(...))
    # TODO 6: convert the "time" column to real datetimes (hint: pd.to_datetime)
    # TODO 7: add a column "wind_bft" by applying kmh_to_beaufort to "wind_speed_10m"
    #         (hint: df["wind_speed_10m"].apply(kmh_to_beaufort))
    # TODO 8: do the same for gusts → "gust_bft"
    # TODO 9: add a column "weather" by mapping "weather_code" with WEATHER_CODES
    #         (hint: df["weather_code"].map(WEATHER_CODES))
    # TODO 10: return the DataFrame



if __name__ == "__main__":
    data = load_latest_raw()
    df = build_hourly_table(data)
    print(df.head(10))
    print(df.dtypes)