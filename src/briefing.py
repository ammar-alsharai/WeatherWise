from datetime import date, timedelta

# Clothing by the coldest feels-like temperature of the day.
# Same pattern as your Beaufort and AQI lists: upper limit → advice.
CLOTHES_LIMITS = [0, 8, 14, 20, 25]
CLOTHES_ADVICE = [
    "a winter coat, hat and gloves",
    "a warm coat",
    "a jacket",
    "a light jacket or sweater",
    "a t-shirt",
    "light clothes, and bring water",
]


def greeting_line():
    return f"☀️ Good morning Ammar! Here's {date.today():%A} in The Hague."


def summary_line(df):
    t_min = df["temperature_2m"].min()
    t_max = df["temperature_2m"].max()
    feels_min = df["apparent_temperature"].min()
    feels_max = df["apparent_temperature"].max()
    main_weather = df["weather"].mode()[0]
    return (
        f"🌤️ Mostly {main_weather}, {t_min:.0f}–{t_max:.0f} °C "
        f"(feels like {feels_min:.0f}–{feels_max:.0f} °C)"
    )


def rain_line(df):
    rainy = df[df["precipitation"] > 0.2]
    if rainy.empty:
        return "☔ No rain expected today."

    start = rainy["forecast_time"].min()
    end = rainy["forecast_time"].max() + timedelta(hours=1)
    line = f"☔ Rain likely between {start:%H:%M} and {end:%H:%M}."

    if df["wind_bft"].max() >= 6:
        line += " Windy too, so take a rain jacket, not an umbrella."
    else:
        line += " Take an umbrella."
    return line


def sunscreen_line(df):
    sunny = df[df["uv_index"] >= 3]  # WHO: protect yourself from UV 3 and up
    if sunny.empty:
        return f"🧴 No sunscreen needed today (UV max {df['uv_index'].max():.0f})."

    start = sunny["forecast_time"].min()
    end = sunny["forecast_time"].max() + timedelta(hours=1)
    return (
        f"🧴 Use sunscreen between {start:%H:%M} and {end:%H:%M} "
        f"(UV up to {sunny['uv_index'].max():.0f})."
    )


def clothes_line(df):
    coldest = df["apparent_temperature"].min()

    advice = CLOTHES_ADVICE[-1]
    for i, limit in enumerate(CLOTHES_LIMITS):
        if coldest <= limit:
            advice = CLOTHES_ADVICE[i]
            break

    line = f"🧥 Wear {advice}"
    if df["wind_bft"].max() >= 5:
        line += ", windproof if you can"
    if (df["precipitation"] > 0.2).any():
        line += ", and something waterproof"
    return line + "."


if __name__ == "__main__":
    import sqlite3

    from score import DB_PATH, todays_hours

    with sqlite3.connect(DB_PATH) as conn:
        df = todays_hours(conn)

    if df.empty:
        print("No hours left today. Run this before 21:00.")
    else:
        print(greeting_line())
        print(summary_line(df))
        print(rain_line(df))
        print(sunscreen_line(df))
        print(clothes_line(df))