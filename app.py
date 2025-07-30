import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Streamlit UI ---
st.title("Weather Data Viewer (ZIP Code) with Solar Power")

zip_code = st.text_input("Enter ZIP Code:", "20001")
start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End date", datetime.now())

if st.button("Get Weather Data"):
    # --- Geocoding using ZIP code ---
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={zip_code}&count=1"
    geo_resp = requests.get(geocode_url).json()
    if "results" not in geo_resp:
        st.error("Location not found!")
    else:
        location = geo_resp["results"][0]["name"]
        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]

        # --- Weather API ---
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

        # --- Process Data ---
        df["time"] = pd.to_datetime(df["time"])
        df["cumulative_precipitation"] = df["precipitation_sum"].cumsum()
        df["sunshine_duration_hr"] = df["sunshine_duration"] / 3600  # sec → hr
        df["cumulative_sunshine_hr"] = df["sunshine_duration_hr"].cumsum()

        # --- Solar energy (kWh/ft²) ---
        df["daily_solar_kwh_ft2"] = df["sunshine_duration_hr"] * (1000 / 10.7639) / 1000
        df["cumulative_solar_kwh_ft2"] = df["daily_solar_kwh_ft2"].cumsum()

        st.subheader(f"Weather Data for {location}")
        st.dataframe(df)

        # --- Existing Graphs ---
        # Daily temp
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(df["time"], df["temperature_2m_max"], label="Max Temp", color="red")
        ax1.plot(df["time"], df["temperature_2m_mean"], label="Mean Temp", color="orange")
        ax1.plot(df["time"], df["temperature_2m_min"], label="Min Temp", color="blue")
        ax1.set_ylabel("Temperature (°C)")
        ax1.set_title("Daily Temperatures")
        ax1.legend()
        st.pyplot(fig1)

        # Daily precipitation dual axis
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df["time"], df["precipitation_sum"], color="blue")
        ax2.set_ylabel("Precipitation (mm)")
        ax2.set_title("Daily Precipitation")
        ax2_inch = ax2.twinx()
        ax2_inch.set_ylabel("Precipitation (inches)")
        ax2_inch.set_ylim(ax2.get_ylim()[0] / 25.4, ax2.get_ylim()[1] / 25.4)
        st.pyplot(fig2)

        # Cumulative precipitation dual axis
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        ax3.plot(df["time"], df["cumulative_precipitation"], color="green", linewidth=2)
        ax3.set_ylabel("Cumulative Precipitation (mm)")
        ax3.set_title("Cumulative Precipitation")
        ax3_inch = ax3.twinx()
        ax3_inch.set_ylabel("Cumulative Precipitation (inches)")
        ax3_inch.set_ylim(ax3.get_ylim()[0] / 25.4, ax3.get_ylim()[1] / 25.4)
        st.pyplot(fig3)

        # Sunshine duration dual axis (daily bar + cumulative line)
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        ax4.bar(df["time"], df["sunshine_duration_hr"], color="gold", label="Daily Sunshine (hr)")
        ax4.set_ylabel("Daily Sunshine (hr)")
        ax4.set_title("Daily & Cumulative Sunshine")
        ax4_line = ax4.twinx()
        ax4_line.plot(df["time"], df["cumulative_sunshine_hr"], color="red", linewidth=2, label="Cumulative Sunshine (hr)")
        ax4_line.set_ylabel("Cumulative Sunshine (hr)")
        lines_labels = [ax4.get_legend_handles_labels(), ax4_line.get_legend_handles_labels()]
        handles = lines_labels[0][0] + lines_labels[1][0]
        labels = lines_labels[0][1] + lines_labels[1][1]
        fig4.legend(handles, labels, loc="upper left")
        st.pyplot(fig4)

        # Solar power dual axis (daily bar + cumulative line)
        fig5, ax5 = plt.subplots(figsize=(10, 4))
        ax5.bar(df["time"], df["daily_solar_kwh_ft2"], color="deepskyblue", label="Daily Solar Energy (kWh/ft²)")
        ax5.set_ylabel("Daily Solar (kWh/ft²)")
        ax5.set_title("Daily & Cumulative Solar Energy (per ft²)")
        ax5_line = ax5.twinx()
        ax5_line.plot(df["time"], df["cumulative_solar_kwh_ft2"], color="darkblue", linewidth=2,
                      label="Cumulative Solar Energy (kWh/ft²)")
        ax5_line.set_ylabel("Cumulative Solar (kWh/ft²)")

        lines_labels = [ax5.get_legend_handles_labels(), ax5_line.get_legend_handles_labels()]
        handles = lines_labels[0][0] + lines_labels[1][0]
        labels = lines_labels[0][1] + lines_labels[1][1]
        fig5.legend(handles, labels, loc="upper left")

        st.pyplot(fig5)
