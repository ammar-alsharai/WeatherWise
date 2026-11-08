import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
# Beaufort scale: the upper limit in km/h for each force (0 to 11).
# Anything above the last number is force 12.
BEAUFORT_LIMITS_KMH = [1, 5, 11, 19, 28, 38, 49, 61, 74, 88, 102, 117]

# WMO weather codes used by Open-Meteo
WEATHER_CODES = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light showers",
    81: "showers",
    82: "heavy showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def load_latest_raw(name):
    sorted_files = sorted(RAW_DIR.glob(f"{name}_*.json"))
    latest_file = sorted_files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)


def kmh_to_beaufort(speed_kmh):

    for force, limit in enumerate(BEAUFORT_LIMITS_KMH):
        if speed_kmh <= limit:
            return force
    return 12


def build_hourly_table(data):
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df["wind_bft"] = df["wind_speed_10m"].apply(kmh_to_beaufort)
    df["gust_bft"] = df["wind_gusts_10m"].apply(kmh_to_beaufort)
    df["weather"] = df["weather_code"].map(WEATHER_CODES)
    return df


def build_air_quality_table(aq_data):
    df = pd.DataFrame(aq_data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    weather_df = build_hourly_table(load_latest_raw("forecast"))
    aq_df = build_air_quality_table(load_latest_raw("air_quality"))
    df = weather_df.merge(aq_df, on="time", how="left")
    print(df.head(10))
    print(df.dtypes)
