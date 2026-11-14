# WeatherWise 🌤️

**A daily data pipeline that sends me a personal weather briefing for The Hague: what to wear, whether I need an umbrella or sunscreen, and the best time to skate, cycle or walk outside.**

Every morning, WeatherWise fetches the weather and air quality forecast, stores it in a database, scores every hour for each activity, and sends a briefing to my phone on Telegram. It runs automatically in the cloud with GitHub Actions.

```
☀️ Good morning Ammar! Here's Tuesday in The Hague.

🌤️ Mostly overcast, 4–9 °C (feels like 0–5 °C)
☔ No rain expected today.
🧴 No sunscreen needed today (UV max 2).
🧥 Wear a winter coat, hat and gloves.

Best times today
⛸️ Skating: 13:00–15:00 (score 77)
🚲 Cycling: 13:00–15:00 (score 90)
🚶 Walking: 11:00–13:00 (score 90)

Air quality: moderate
Weather data by Open-Meteo.com
```

---

## How it works

```mermaid
flowchart LR
    A[Open-Meteo<br/>Forecast API] --> C[Extract<br/>raw JSON]
    B[Open-Meteo<br/>Air Quality API] --> C
    C --> D[Transform<br/>clean hourly table]
    D --> E[Load<br/>SQLite history]
    E --> F[Score<br/>skate · cycle · walk]
    E --> H[Briefing<br/>rain · sunscreen · clothes]
    F --> G[Telegram<br/>morning message]
    H --> G
```

| Step | File | What it does |
|---|---|---|
| Extract | `src/extract.py` | Calls both APIs and saves the raw JSON responses to `data/raw/` |
| Transform | `src/transform.py` | Builds an hourly pandas table, converts wind to Beaufort and weather codes to words, joins air quality on the hour |
| Load | `src/load.py` | Upserts the table into SQLite through a staging table |
| Score | `src/score.py` | Selects today's hours, scores each hour from 0–100 per activity and finds the best 2-hour window |
| Briefing | `src/briefing.py` | Writes the summary, rain, sunscreen and clothing lines, one small function per line |
| Digest | `src/digest.py` | Builds the message and sends it with the Telegram Bot API, with retries |
| Pipeline | `src/pipeline.py` | Runs all steps in order |

The workflow in `.github/workflows/daily.yml` runs the pipeline every morning and commits the updated database back to the repository, so the forecast history grows day by day.

---

## Design decisions

- **Raw data is kept untouched.** Every API response is saved before any processing, so the cleaning logic can be fixed and re-run without calling the API again.
- **Idempotent loads.** Each row is identified by `(fetched_date, forecast_time)`. Loading uses `INSERT OR REPLACE` from a staging table, so running the pipeline twice on the same day never creates duplicates.
- **Building my own history.** The free API only returns the current forecast. Storing one forecast per day creates a dataset for measuring forecast accuracy over time.
- **Logic separated from output.** `todays_hours()` prepares the data, `recommend()` scores it and returns results instead of printing them, and `digest.py` only formats and sends. The same logic can feed the terminal, Telegram or a future dashboard.
- **One function per briefing line.** Each line (rain, sunscreen, clothes) is a small function that returns text, so every rule can be tested and tuned on its own.
- **Resilient delivery.** Sending to Telegram retries up to three times on connection errors, then fails loudly so a broken run is visible in GitHub Actions.
- **Fail fast on configuration.** Missing secrets stop the run with a clear error instead of a confusing API failure.
- **Dutch time everywhere.** GitHub's runners use UTC, so the workflow sets `TZ=Europe/Amsterdam` to keep "today" and "now" correct.

---

## Scoring

Each hour starts at 100 and loses points for bad conditions. The limits per activity live in one config dictionary (`ACTIVITIES` in `score.py`).

| Condition | Penalty |
|---|---|
| Feels-like temperature outside the activity's range | −5 per °C |
| Rain chance above the activity's limit | −1 per % |
| Rain expected (> 0.2 mm) | −30 |
| Wind above the limit | −15 per Beaufort force |
| Gusts above the limit | −10 per Beaufort force |
| Air quality moderate / poor (European AQI > 40 / > 60) | −10 / −30 |
| **Skating only:** rain in the previous 2 hours (wet road) | −40 |

| Activity | Feels-like range | Max rain chance | Max wind | Max gusts | Wet-road rule |
|---|---|---|---|---|---|
| Skating | 8–25 °C | 10% | 3 Bft | 5 Bft | Yes |
| Cycling | 5–25 °C | 20% | 3 Bft | 5 Bft | No |
| Walking | 0–26 °C | 40% | 5 Bft | 7 Bft | No |

The wet-road rule uses pandas `shift()` to look at the rain in the two hours before each hour, because a road stays slippery after the rain stops.

---

## Morning briefing rules

| Line | Rule |
|---|---|
| Summary | Lowest and highest temperature and feels-like temperature of the remaining day, plus the most common weather |
| Rain | No hour above 0.2 mm → "No rain expected". Otherwise the first to last rainy hour, with "take a rain jacket, not an umbrella" when wind reaches 6 Bft |
| Sunscreen | UV index 3 or higher (the WHO threshold for sun protection) → the hours to use sunscreen |
| Clothes | Based on the coldest feels-like temperature: winter coat (≤ 0 °C), warm coat (≤ 8 °C), jacket (≤ 14 °C), light jacket or sweater (≤ 20 °C), t-shirt (≤ 25 °C), light clothes above that. Adds windproof or waterproof when needed |

---

## Data model

One SQLite table, `forecasts`, in `data/weatherwise.db`:

| Column | Description |
|---|---|
| `fetched_date` | Day the forecast was downloaded (part of the primary key) |
| `forecast_time` | Hour the forecast is about (part of the primary key) |
| `temperature_2m`, `apparent_temperature` | Temperature and feels-like temperature (°C) |
| `precipitation_probability`, `precipitation` | Rain chance (%) and amount (mm) |
| `wind_speed_10m`, `wind_gusts_10m` | Wind and gusts (km/h) |
| `wind_bft`, `gust_bft` | Wind and gusts on the Beaufort scale |
| `uv_index`, `weather_code`, `weather` | UV index, WMO weather code and its description |
| `european_aqi`, `pm2_5` | European Air Quality Index and fine dust (µg/m³) |
| `grass_pollen`, `birch_pollen` | Pollen (grains/m³) |

---

## Tech stack

Python · pandas · requests · SQLite · GitHub Actions · Telegram Bot API

---

## Run it yourself

**Requirements:** Python 3.12 or newer, Git, and a Telegram bot (create one with [@BotFather](https://t.me/BotFather)).

```bash
git clone https://github.com/ammar-alsharai/weatherwise.git
cd weatherwise
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create a `.env` file in the project folder:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Preview the message without sending it:

```bash
python src/digest.py
```

Run the full pipeline (fetch, store, score and send):

```bash
python src/pipeline.py
```

### Automate it

1. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` under **Settings → Secrets and variables → Actions**.
2. The workflow runs daily at 05:30 UTC (06:30 Dutch winter time) and can be started manually from the **Actions** tab.
3. Note: GitHub may delay or skip scheduled runs when it is busy, especially for new repositories.

---

## Project structure

```
weatherwise/
├── .github/workflows/daily.yml   # daily schedule
├── src/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── score.py
│   ├── briefing.py
│   ├── digest.py
│   └── pipeline.py
├── data/
│   ├── raw/                      # raw API responses (not committed)
│   └── weatherwise.db            # forecast history
├── requirements.txt
└── README.md
```

---



## Data sources and credits

- Weather data by [Open-Meteo.com](https://open-meteo.com/), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Free for non-commercial use.
- Air quality data from the [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api), based on the Copernicus Atmosphere Monitoring Service (CAMS).
- Sunscreen threshold based on the World Health Organization's advice to take sun-safety measures from UV index 3.

---

## Author

**Ammar Al-sharai** · The Hague, Netherlands
[LinkedIn](https://www.linkedin.com/in/ammar-al-sharai-00769a130/) · [GitHub](https://github.com/ammar-alsharai)