import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import random

# Load static and generated data
with open('data/static_battery_data.json') as f:
    static_data = json.load(f)

def safe_convert(value):
    """Handle all JSON serialization cases in one function"""
    if pd.isna(value):
        return None
    if isinstance(value, (np.generic, np.ndarray)):
        return value.item() if np.isscalar(value) else value.tolist()
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        json.dumps(value)
        return value
    except TypeError:
        pass
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    try:
        return str(value)
    except:
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

def load_generated_data(start_date, end_date):
    data = []
    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day)
    
    current_year = start_date.year
    while current_year <= end_date.year:
        year_dir = os.path.join("data", str(current_year))
        if not os.path.exists(year_dir):
            current_year += 1
            continue
            
        for quarter in os.listdir(year_dir):
            quarter_dir = os.path.join(year_dir, quarter)
            for month_file in os.listdir(quarter_dir):
                file_path = os.path.join(quarter_dir, month_file)
                with open(file_path) as f:
                    monthly_data = json.load(f)
                    for entry in monthly_data:
                        if 'date' in entry:
                            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
                            if start_dt <= entry_date <= end_dt:
                                data.append(entry)
        current_year += 1
    
    df = pd.DataFrame(data)
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

def generate_realtime_data():
    return {
        "voltage": round(random.uniform(45.0, 50.0), 2),
        "current": round(random.uniform(10.0, 15.0), 2),
        "temperature": random.randint(25, 35),
        "soc": random.randint(50, 100)
    }

def generate_report(df):
    if df.empty or 'date' not in df.columns:
        raise ValueError("Invalid data for report generation")
    
    df = df.replace([np.inf, -np.inf], np.nan).fillna(method='ffill')
    
    numeric_cols = ['voltage', 'current', 'temperature', 'state_of_charge', 
                   'cycles', 'capacity_ah', 'internal_resistance']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return {
        "summary": {
            "total_cycles": int(df['cycles'].max()),
            "avg_temperature": float(df['temperature'].mean()),
            "capacity_fade": float(1 - df['capacity_ah'].iloc[-1]/df['capacity_ah'].iloc[0]),
            "max_resistance": float(df['internal_resistance'].max())
        },
        "detailed_metrics": {
            "daily": [safe_convert(row) for row in df.to_dict('records')],
            "monthly_avg": df.resample('M', on='date')
                            .mean(numeric_only=True)
                            .reset_index()
                            .applymap(safe_convert)
                            .to_dict('list')
        }
    }

# Streamlit UI Configuration
st.set_page_config(page_title="Battery Digital Twin Dashboard", layout="wide")
st.sidebar.header("Navigation")
view = st.sidebar.selectbox("Select View", [
    "Real-time Monitoring",
    "Historical Analysis", 
    "Health Analytics"
])

# Main display logic
if view == "Real-time Monitoring":
    st.title("🔋 Real-time Battery Monitoring")
    realtime_data = generate_realtime_data()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Voltage (V)", value=realtime_data["voltage"], delta="±0.2V")
    col2.metric("Current (A)", value=realtime_data["current"], delta="-0.5A")
    col3.metric("Temperature (°C)", value=realtime_data["temperature"], delta="+2°C")
    col4.metric("State of Charge (%)", value=realtime_data["soc"], delta="-5%")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig = px.line(title="Voltage Trend")
        fig.add_scatter(y=[realtime_data["voltage"]], mode="lines", name="Voltage")
        st.plotly_chart(fig, use_container_width=True)
    with chart_col2:
        fig = px.bar(title="Current Draw")
        fig.add_bar(y=[realtime_data["current"]], name="Current")
        st.plotly_chart(fig, use_container_width=True)

elif view == "Historical Analysis":
    st.title("🔋 Historical Battery Analysis")
    start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2024, 12, 31))
    
    try:
        df = load_generated_data(start_date, end_date)
        if df.empty:
            st.error("No data found for selected date range")
            st.stop()
        
        report = generate_report(df)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Capacity", "Temperature", "Full Report"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cycles", report['summary']['total_cycles'])
        col2.metric("Capacity Fade", f"{report['summary']['capacity_fade']:.2f}%")
        col3.metric("Avg Temp", f"{report['summary']['avg_temperature']:.1f}°C")
        col4.metric("Max Resistance", f"{report['summary']['max_resistance']:.4f}Ω")
        
        fig = px.line(df, x='date', y=['voltage', 'current'], title="Voltage/Current Trends")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.line(df, x='date', y='capacity_ah', title="Capacity Degradation")
        st.plotly_chart(fig, use_container_width=True)
        fig = px.histogram(df, x='state_of_charge', title="Charge Distribution", nbins=20)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.density_heatmap(df, x='date', y='temperature', title="Temperature Heatmap")
        st.plotly_chart(fig, use_container_width=True)
        fig = px.box(df, y='temperature', title="Temperature Statistics")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        monthly_avg = pd.DataFrame(report['detailed_metrics']['monthly_avg'])
        if not monthly_avg.empty:
            if 'date' in monthly_avg.columns:
                monthly_avg['date'] = pd.to_datetime(monthly_avg['date']).dt.strftime('%Y-%m')
            numeric_cols = monthly_avg.select_dtypes(include=[np.number]).columns
            styled_df = monthly_avg.style.format("{:.2f}", subset=numeric_cols)
            st.dataframe(styled_df)
        st.download_button("Download Report", json.dumps(report, default=safe_convert, indent=2),
                         f"battery_report_{start_date}_{end_date}.json")

elif view == "Health Analytics":
    st.title("🔋 Battery Health Diagnostics")
    health = static_data['health_metrics']
    
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

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Battery Digital Twin**  
Combined static and historical analysis  
Version 2.0.0
""")