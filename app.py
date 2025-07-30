import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ----------------- FUNCTIONS -----------------
def get_weather_data(zip_code, start_date, end_date):
    # Geocode to get lat/lon
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={zip_code}&count=1"
    geo_resp = requests.get(geocode_url).json()
    if "results" not in geo_resp:
        return None, None, None
    location = geo_resp["results"][0]["name"]
    lat = geo_resp["results"][0]["latitude"]
    lon = geo_resp["results"][0]["longitude"]

    # Weather API request
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
        return None, None, None

    df = pd.DataFrame(weather_resp["daily"])
    df["time"] = pd.to_datetime(df["time"])

    # Process metrics
    df["cumulative_precipitation"] = df["precipitation_sum"].cumsum()
    df["sunshine_duration_hr"] = df["sunshine_duration"] / 3600  # seconds -> hours
    df["cumulative_sunshine_hr"] = df["sunshine_duration_hr"].cumsum()
    df["daily_solar_kwh_ft2"] = df["sunshine_duration_hr"] * (1000 / 10.7639) / 1000
    df["cumulative_solar_kwh_ft2"] = df["daily_solar_kwh_ft2"].cumsum()

    return df, location, (lat, lon)

def plot_temperature(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["temperature_2m_max"], mode="lines+markers",
                             name="Max Temp (°C)", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df["time"], y=df["temperature_2m_mean"], mode="lines+markers",
                             name="Mean Temp (°C)", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["time"], y=df["temperature_2m_min"], mode="lines+markers",
                             name="Min Temp (°C)", line=dict(color="blue")))
    fig.update_layout(title="Daily Temperatures", yaxis_title="Temperature (°C)", xaxis_title="Date")
    return fig

def plot_precipitation(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["time"], y=df["precipitation_sum"], name="Daily Precipitation (mm)", marker_color="blue", yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["precipitation_sum"] / 25.4, name="Daily Precipitation (in)", yaxis="y2", mode="lines+markers", line=dict(color="darkblue")))
    fig.update_layout(
        title="Daily Precipitation (Dual Axis)",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Precipitation (mm)", side="left"),
        yaxis2=dict(title="Precipitation (inches)", overlaying="y", side="right")
    )
    return fig

def plot_cumulative_precipitation(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["cumulative_precipitation"], name="Cumulative Precip (mm)", line=dict(color="green"), yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["cumulative_precipitation"]/25.4, name="Cumulative Precip (in)", line=dict(color="darkgreen", dash="dot"), yaxis="y2"))
    fig.update_layout(
        title="Cumulative Precipitation",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Precipitation (mm)", side="left"),
        yaxis2=dict(title="Precipitation (inches)", overlaying="y", side="right")
    )
    return fig

def plot_sunshine(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["time"], y=df["sunshine_duration_hr"], name="Daily Sunshine (hr)", marker_color="gold", yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["cumulative_sunshine_hr"], name="Cumulative Sunshine (hr)",
                             mode="lines+markers", line=dict(color="orange"), yaxis="y2"))
    fig.update_layout(
        title="Daily & Cumulative Sunshine",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Daily Sunshine (hr)", side="left"),
        yaxis2=dict(title="Cumulative Sunshine (hr)", overlaying="y", side="right")
    )
    return fig

def plot_solar_energy(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["time"], y=df["daily_solar_kwh_ft2"], name="Daily Solar Energy (kWh/ft²)", marker_color="deepskyblue", yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["time"], y=df["cumulative_solar_kwh_ft2"], name="Cumulative Solar Energy (kWh/ft²)",
                             mode="lines+markers", line=dict(color="darkblue"), yaxis="y2"))
    fig.update_layout(
        title="Daily & Cumulative Solar Energy (per ft²)",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Daily Solar (kWh/ft²)", side="left"),
        yaxis2=dict(title="Cumulative Solar (kWh/ft²)", overlaying="y", side="right")
    )
    return fig

def plot_cloud_cover(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["time"], y=df["cloudcover_mean"], name="Cloud Cover (%)", marker_color="gray"))
    fig.update_layout(title="Daily Mean Cloud Cover", xaxis_title="Date", yaxis_title="Cloud Cover (%)", yaxis=dict(range=[0, 100]))
    return fig

# ----------------- STREAMLIT APP -----------------
st.title("Weather Data Analysis with Solar & Cloud Metrics")

zip_code = st.text_input("Enter ZIP Code:", "20001")
start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
end_date = st.date_input("End date", datetime.now())

if st.button("Get Weather Data"):
    df, location, coords = get_weather_data(zip_code, start_date, end_date)
    if df is None:
        st.error("Could not fetch weather data. Check ZIP code or date range.")
    else:
        st.success(f"Weather data for {location} (Lat: {coords[0]:.2f}, Lon: {coords[1]:.2f})")
        st.dataframe(df)

        st.plotly_chart(plot_temperature(df), use_container_width=True)
        st.plotly_chart(plot_precipitation(df), use_container_width=True)
        st.plotly_chart(plot_cumulative_precipitation(df), use_container_width=True)
        st.plotly_chart(plot_sunshine(df), use_container_width=True)
        st.plotly_chart(plot_solar_energy(df), use_container_width=True)
        st.plotly_chart(plot_cloud_cover(df), use_container_width=True)
