import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------------- UI ----------------
st.title("Weather Data Viewer")

location = st.text_input("Enter location (city name):", "Washington, DC")
start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End date", datetime.now())

if st.button("Get Weather Data"):
    # Get latitude and longitude from Open-Meteo Geocoding
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
    geo_resp = requests.get(geocode_url).json()
    if "results" not in geo_resp:
        st.error("Location not found!")
    else:
        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]

        # Fetch weather data
        weather_url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={end_date}"
            "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            "precipitation_sum,sunshine_duration"
            "&timezone=auto"
        )
        weather_resp = requests.get(weather_url).json()
        daily = weather_resp["daily"]
        df = pd.DataFrame(daily)

        # Convert time column to datetime
        df["time"] = pd.to_datetime(df["time"])
        df["cumulative_precipitation"] = df["precipitation_sum"].cumsum()
        df["sunshine_duration"] = df["sunshine_duration"] / 3600  # convert sec → hr

        # Display data
        st.subheader("Raw Weather Data")
        st.dataframe(df)

        # Plot
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(df["time"], df["cumulative_precipitation"], label="Cumulative Precipitation (mm)", color="blue")
        ax1.set_ylabel("Precipitation (mm)", color="blue")
        ax1.tick_params(axis='y', labelcolor="blue")

        ax2 = ax1.twinx()
        ax2.plot(df["time"], df["temperature_2m_max"], label="Max Temp", color="red", linestyle="--")
        ax2.plot(df["time"], df["temperature_2m_mean"], label="Mean Temp", color="orange", linestyle="-.")
        ax2.plot(df["time"], df["temperature_2m_min"], label="Min Temp", color="green", linestyle=":")
        ax2.set_ylabel("Temperature (°C)", color="red")
        ax2.tick_params(axis='y', labelcolor="red")

        fig.legend(loc="upper left")
        plt.title(f"Weather Data for {location}")
        st.pyplot(fig)
