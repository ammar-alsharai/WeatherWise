import os
import sqlite3

import requests
from dotenv import load_dotenv

from score import DB_PATH, recommend

load_dotenv()  # reads your .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EMOJI = {"skating": "⛸", "cycling": "🚲", "walking": "🚶"}


def build_message(result):
    if result is None:
        return "🌙 No good hours left today. Check again tomorrow morning."

    lines = ["☀️ WeatherWise: The Hague today", ""]

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
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    if not TOKEN or not CHAT_ID:
            raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing. Check your .env file.")
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=30)
    response.raise_for_status()


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        message = build_message(recommend(conn))
    print(message)
    send_telegram(message)
