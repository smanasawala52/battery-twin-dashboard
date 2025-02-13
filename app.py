import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
import random

# Load static data
with open('data/static_battery_data.json') as f:
    data = json.load(f)

# Page configuration
st.set_page_config(page_title="Battery Digital Twin Dashboard", layout="wide")

# Sidebar
st.sidebar.header("Battery Digital Twin Configuration")
selected_view = st.sidebar.selectbox("Select View", ["Real-time Monitoring", "Historical Analysis", "Health Analytics"])

# Main content
st.title("🔋 Battery Digital Twin Dashboard")

# Real-time simulation data
def generate_realtime_data():
    return {
        "voltage": round(random.uniform(45.0, 50.0), 2),
        "current": round(random.uniform(10.0, 15.0), 2),
        "temperature": random.randint(25, 35),
        "soc": random.randint(50, 100)
    }

# Dashboard views
if selected_view == "Real-time Monitoring":
    st.header("Real-time Battery Metrics")
    
    # Generate real-time data
    realtime_data = generate_realtime_data()
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Voltage (V)", value=realtime_data["voltage"], delta="±0.2V")
    with col2:
        st.metric("Current (A)", value=realtime_data["current"], delta="-0.5A")
    with col3:
        st.metric("Temperature (°C)", value=realtime_data["temperature"], delta="+2°C")
    with col4:
        st.metric("State of Charge (%)", value=realtime_data["soc"], delta="-5%")

    # Real-time charts
    st.subheader("Live Telemetry")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        fig = px.line(title="Voltage Trend")
        fig.add_scatter(y=[realtime_data["voltage"]], mode="lines", name="Voltage")
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        fig = px.bar(title="Current Draw")
        fig.add_bar(y=[realtime_data["current"]], name="Current")
        st.plotly_chart(fig, use_container_width=True)

elif selected_view == "Historical Analysis":
    st.header("Historical Battery Performance")
    # Extract time-series data
    time_series_keys = ["timestamps", "voltage", "current", "temperature", "state_of_charge", "cycle_count"]
    time_series_data = {key: data[key] for key in time_series_keys}

    # Convert time-series data to DataFrame
    df = pd.DataFrame(time_series_data)
    df['timestamps'] = pd.to_datetime(df['timestamps'])  # Ensure timestamps are in datetime format

    # Time series selector
    selected_metric = st.selectbox("Select Metric", ["voltage", "current", "temperature", "state_of_charge", "cycle_count"])
    
    # Plot historical data
    fig = px.line(df, x="timestamps", y=selected_metric, title=f"Historical {selected_metric.capitalize()} Trend")
    st.plotly_chart(fig, use_container_width=True)
    

elif selected_view == "Health Analytics":
    st.header("Battery Health Diagnostics")
    
    # Health metrics
    health = data['health_metrics']
    
    # Create health indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        fig = px.pie(values=[health['capacity_retention'], 100-health['capacity_retention']],
                     names=["Remaining", "Lost"], title="Capacity Retention")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(x=["Impedance"], y=[health['impedance_increase']],
                    title="Impedance Increase (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = px.line(title="Self-Discharge Rate", y=[health['self_discharge_rate']])
        st.plotly_chart(fig, use_container_width=True)
