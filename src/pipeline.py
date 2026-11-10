import sqlite3

from digest import build_message, send_telegram
from extract import fetch_air_quality, fetch_forecast, save_raw
from load import DB_PATH, load_latest
from score import recommend, todays_hours


def main():
    save_raw(fetch_forecast(), "forecast")
    save_raw(fetch_air_quality(), "air_quality")

    with sqlite3.connect(DB_PATH) as conn:
        load_latest(conn)
        df = todays_hours(conn)

    message = build_message(df, recommend(df))
    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()