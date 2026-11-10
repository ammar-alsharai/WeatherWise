import os
import time

import requests
from dotenv import load_dotenv

from briefing import (
    clothes_line,
    greeting_line,
    rain_line,
    summary_line,
    sunscreen_line,
)

load_dotenv()  # reads your .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EMOJI = {"skating": "⛸️", "cycling": "🚲", "walking": "🚶"}


def build_message(df, result):
    if result is None:
        return "🌙 No good hours left today. Check again tomorrow morning."

    lines = [
        greeting_line(),
        "",
        summary_line(df),
        rain_line(df),
        sunscreen_line(df),
        clothes_line(df),
        "",
        "Best times today",
    ]

    for w in result["windows"]:
        lines.append(
            f"{EMOJI[w['activity']]} {w['activity'].capitalize()}: "
            f"{w['start']:%H:%M}–{w['end']:%H:%M} (score {w['score']:.0f})"
        )

    lines.append("")
    lines.append(f"Air quality: {result['air_quality']}")
    lines.append("Weather data by Open-Meteo.com")
    return "\n".join(lines)


def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing. Check your .env file.")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    for attempt in range(1, 4):
        try:
            response = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=30)
            response.raise_for_status()
            return
        except requests.exceptions.ConnectionError:
            if attempt == 3:
                raise
            print(f"Telegram connection failed (attempt {attempt}), retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    # Preview only: builds the message from the database without sending it.
    import sqlite3

    from score import DB_PATH, recommend, todays_hours

    with sqlite3.connect(DB_PATH) as conn:
        df = todays_hours(conn)
    print(build_message(df, recommend(df)))