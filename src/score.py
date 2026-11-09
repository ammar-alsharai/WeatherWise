import sqlite3
from datetime import date

import pandas as pd

DB_PATH = "data/weatherwise.db"

ACTIVITIES = {
    "running": {
        "feels_min": 5,
        "feels_max": 18,
        "max_rain_prob": 30,
        "max_wind_bft": 4,
        "max_gust_bft": 6,
    },
    "cycling": {
        "feels_min": 5,
        "feels_max": 25,
        "max_rain_prob": 20,
        "max_wind_bft": 3,
        "max_gust_bft": 5,
    },
    "walking": {
        "feels_min": 0,
        "feels_max": 26,
        "max_rain_prob": 40,
        "max_wind_bft": 5,
        "max_gust_bft": 7,
    },
}

# European AQI: upper limit of each band (same idea as your Beaufort list)
AQI_LIMITS = [20, 40, 60, 80, 100]
AQI_LABELS = ["good", "fair", "moderate", "poor", "very poor", "extremely poor"]


def load_latest_forecast(conn):
    sql = """
        SELECT * FROM forecasts
        WHERE fetched_date = (SELECT MAX(fetched_date) FROM forecasts)
    """
    df = pd.read_sql_query(sql, conn)

    df["forecast_time"] = pd.to_datetime(df["forecast_time"])

    return df


def aqi_label(aqi):

    for i, limit in enumerate(AQI_LIMITS):
        if aqi <= limit:
            return AQI_LABELS[i]
    return AQI_LABELS[-1]


def score_hour(row, rules):
    score = 100

    feels = row["apparent_temperature"]
    if feels < rules["feels_min"]:
        score -= 5 * (rules["feels_min"] - feels)
    elif feels > rules["feels_max"]:
        score -= 5 * (feels - rules["feels_max"])

    if row["precipitation_probability"] > rules["max_rain_prob"]:
        score -= row["precipitation_probability"] - rules["max_rain_prob"]

    if row["precipitation"] > 0.2:
        score -= 30

    if row["wind_bft"] > rules["max_wind_bft"]:
        score -= 15 * (row["wind_bft"] - rules["max_wind_bft"])

    if row["gust_bft"] > rules["max_gust_bft"]:
        score -= 10 * (row["gust_bft"] - rules["max_gust_bft"])

    if row["european_aqi"] > 60:
        score -= 30
    elif row["european_aqi"] > 40:
        score -= 10

    return max(score, 0)


def best_window(df, score_column):

    rolling = df[score_column].rolling(2).mean()

    pos = rolling.idxmax()
    start_time = df.loc[pos - 1, "forecast_time"]
    end_time = df.loc[pos, "forecast_time"] + pd.Timedelta(hours=1)
    average_score = rolling.loc[pos]
    return start_time, end_time, average_score


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        df = load_latest_forecast(conn)

    # Only today, between 07:00 and 22:00
    today = pd.Timestamp(date.today())
    now = pd.Timestamp.now().floor("h")
    df = df[
        (df["forecast_time"] >= now)
        & (df["forecast_time"].dt.normalize() == today)
        & (df["forecast_time"].dt.hour.between(7, 21))
    ]
    df = df.reset_index(drop=True)
    if len(df) < 2:
        print("Not enough hours left today. Try again tomorrow morning.")
        raise SystemExit

    for activity, rules in ACTIVITIES.items():
        df[f"score_{activity}"] = df.apply(score_hour, axis=1, args=(rules,))
        start, end, avg = best_window(df, f"score_{activity}")
        print(f"{activity:8} best: {start:%H:%M}–{end:%H:%M} (score {avg:.0f})")

    print(f"Air quality now: {aqi_label(df.loc[0, 'european_aqi'])}")
