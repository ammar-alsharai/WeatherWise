import sqlite3

from digest import build_message, send_telegram
from extract import fetch_air_quality, fetch_forecast, save_raw
from load import DB_PATH, load_latest
from score import recommend


def main():
    # 1. Extract: get fresh data from both APIs and keep the raw files
    save_raw(fetch_forecast(), "forecast")
    save_raw(fetch_air_quality(), "air_quality")

    # 2 + 3. Load into SQLite, then score from the database
    with sqlite3.connect(DB_PATH) as conn:
        load_latest(conn)
        message = build_message(recommend(conn))

    # 4. Send the result to your phone
    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()