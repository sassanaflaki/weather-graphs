import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ----------------- HELPER FUNCTIONS -----------------
def geocode_zip(zip_code):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={zip_code}&count=1"
    resp = requests.get(url).json()
    if "results" not in resp:
        return None
    return resp["results"][0]["latitude"], resp["results"][0]["longitude"], resp["results"][0]["name"]

def get_weather_data(lat, lon, start_date, end_date):
    weather_url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        "precipitation_sum,sunshine_duration,cloudcover_mean"
        "&timezone=auto"
    )
    weather_resp = requests.get(weather_url).json()
    if "daily" not in weather_resp:
        return None

    df = pd.DataFrame(weather_resp["daily"])
    df["time"] = pd.to_datetime(df["time"])
    df["cumulative_precipitation"] = df["precipitation_sum"].cumsum()
    df["sunshine_duration_hr"] = df["sunshine_duration"] / 3600
    df["cumulative_sunshine_hr"] = df["sunshine_duration_hr"].cumsum()
    df["daily_solar_kwh_ft2"] = df["sunshine_duration_hr"] * (1000 / 10.7639) / 1000
    df["cumulative_solar_kwh_ft2"] = df["daily_solar_kwh_ft2"].cumsum()

    # Tree shade index (with leaf factor)
    def get_leaf_factor(date):
        month = date.month
        if month in [6, 7, 8]:     # Summer
            return 1.0
        elif month in [4, 5, 9]:   # Spring & early fall
            return 0.7
        else:                      # Winter
            return 0.3

    df["leaf_factor"] = df["time"].apply(get_leaf_factor)
    max_sun = df["sunshine_duration_hr"].max()
    df["tree_shade_index"] = (
        (df["sunshine_duration_hr"] / max_sun) *
        ((100 - df["cloudcover_mean"]) / 100) *
        df["leaf_factor"] * 100
    )
    return df

# ----------------- STREAMLIT APP -----------------
st.title("Weather Data & Tree Shade Analysis (ZIP Code)")

zip_code = st.text_input("Enter ZIP Code", "20001")
start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End date", datetime.now())

if st.button("Get Weather Data"):
    geocode = geocode_zip(zip_code)
    if geocode is None:
        st.error("Invalid ZIP code or location not found.")
        st.stop()
    lat, lon, location_name = geocode

    df = get_weather_data(lat, lon, start_date, end_date)
    if df is None:
        st.error("Could not fetch weather data for this location.")
    else:
        st.success(f"Weather data for {location_name}")
        st.dataframe(df)

        # ----------------- GRAPHS -----------------
        # Temperature
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(df["time"], df["temperature_2m_max"], label="Max Temp", color="red")
        ax1.plot(df["time"], df["temperature_2m_mean"], label="Mean Temp", color="orange")
        ax1.plot(df["time"], df["temperature_2m_min"], label="Min Temp", color="blue")
        ax1.set_ylabel("Temperature (°C)")
        ax1.set_title("Daily Temperatures")
        ax1.legend()
        st.pyplot(fig1)

        # Daily precipitation (mm & inch)
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df["time"], df["precipitation_sum"], color="blue")
        ax2.set_ylabel("Precipitation (mm)")
        ax2_inch = ax2.twinx()
        ax2_inch.set_ylabel("Precipitation (inches)")
        ax2_inch.set_ylim(ax2.get_ylim()[0]/25.4, ax2.get_ylim()[1]/25.4)
        ax2.set_title("Daily Precipitation (mm & inches)")
        st.pyplot(fig2)

        # Cumulative precipitation (mm & inch)
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        ax3.plot(df["time"], df["cumulative_precipitation"], color="green", linewidth=2)
        ax3.set_ylabel("Cumulative Precipitation (mm)")
        ax3_inch = ax3.twinx()
        ax3_inch.set_ylabel("Cumulative Precipitation (inches)")
        ax3_inch.set_ylim(ax3.get_ylim()[0]/25.4, ax3.get_ylim()[1]/25.4)
        ax3.set_title("Cumulative Precipitation (mm & inches)")
        st.pyplot(fig3)

        # Sunshine duration (daily & cumulative)
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        ax4.bar(df["time"], df["sunshine_duration_hr"], color="gold", label="Daily Sunshine (hr)")
        ax4.set_ylabel("Daily Sunshine (hours)")
        ax4_line = ax4.twinx()
        ax4_line.plot(df["time"], df["cumulative_sunshine_hr"], color="red", linewidth=2, label="Cumulative Sunshine (hr)")
        ax4_line.set_ylabel("Cumulative Sunshine (hours)")
        ax4.set_title("Daily & Cumulative Sunshine Duration")
        st.pyplot(fig4)

        # Solar power (daily & cumulative)
        fig5, ax5 = plt.subplots(figsize=(10, 4))
        ax5.bar(df["time"], df["daily_solar_kwh_ft2"], color="deepskyblue", label="Daily Solar Energy (kWh/ft²)")
        ax5.set_ylabel("Daily Solar (kWh/ft²)")
        ax5_line = ax5.twinx()
        ax5_line.plot(df["time"], df["cumulative_solar_kwh_ft2"], color="darkblue", linewidth=2, label="Cumulative Solar (kWh/ft²)")
        ax5_line.set_ylabel("Cumulative Solar (kWh/ft²)")
        ax5.set_title("Daily & Cumulative Solar Energy")
        st.pyplot(fig5)

        # Cloud cover
        fig6, ax6 = plt.subplots(figsize=(10, 4))
        ax6.bar(df["time"], df["cloudcover_mean"], color="gray")
        ax6.set_ylabel("Cloud Cover (%)")
        ax6.set_title("Daily Mean Cloud Cover")
        ax6.set_ylim(0, 100)
        st.pyplot(fig6)

        # Tree Shade Index
        fig7, ax7 = plt.subplots(figsize=(10, 4))
        ax7.plot(df["time"], df["tree_shade_index"], color="darkgreen", linewidth=2)
        ax7.set_ylabel("Tree Shade Index (0-100)")
        ax7.set_title("Daily Tree Shade Growth / Intensity Index")
        ax7.set_ylim(0, 100)
        st.pyplot(fig7)
