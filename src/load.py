import sqlite3
from datetime import date
from pathlib import Path

from transform import build_air_quality_table, build_hourly_table, load_latest_raw

DB_PATH = Path("data/weatherwise.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS forecasts (
    fetched_date              TEXT NOT NULL,
    forecast_time             TEXT NOT NULL,
    temperature_2m            REAL,
    apparent_temperature      REAL,
    precipitation_probability INTEGER,
    precipitation             REAL,
    wind_speed_10m            REAL,
    wind_gusts_10m            REAL,
    uv_index                  REAL,
    weather_code              INTEGER,
    wind_bft                  INTEGER,
    gust_bft                  INTEGER,
    weather                   TEXT,
    european_aqi              INTEGER,
    pm2_5                     REAL,
    grass_pollen              REAL,
    birch_pollen              REAL,
    PRIMARY KEY (fetched_date, forecast_time)
);
"""


def prepare_for_db(df):
    df = df.copy()
    df = df.rename(columns={"time": "forecast_time"})
    df["forecast_time"] = df["forecast_time"].dt.strftime("%Y-%m-%d %H:%M")
    df["fetched_date"] = date.today().isoformat()
    return df


def save_forecast(conn, df):
    df.to_sql("staging", conn, if_exists="replace", index=False)
    cols = ", ".join(df.columns)
    conn.execute(
        f"INSERT OR REPLACE INTO forecasts ({cols}) SELECT {cols} FROM staging"
    )
    conn.commit()


def load_latest(conn):
    weather_df = build_hourly_table(load_latest_raw("forecast"))
    aq_df = build_air_quality_table(load_latest_raw("air_quality"))
    df = prepare_for_db(weather_df.merge(aq_df, on="time", how="left"))
    conn.execute(CREATE_TABLE_SQL)
    save_forecast(conn, df)


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        load_latest(conn)
        print(
            conn.execute(
                "SELECT fetched_date, COUNT(*) FROM forecasts GROUP BY fetched_date"
            ).fetchall()
        )
