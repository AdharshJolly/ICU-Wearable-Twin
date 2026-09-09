import streamlit as st
import pandas as pd
import time
import os
import sys

# Add digital_twin to path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'digital_twin'))
from deterioration_simulator import DeteriorationSimulator
from pipeline import DigitalTwinPipeline

# Configure page
st.set_page_config(page_title="Patient Digital Twin Monitor", layout="wide", page_icon="🏥")

st.title("🏥 ICU / Wearable Patient Digital Twin")
st.markdown("Live monitoring simulation integrating **Clinical Rules** and **Unsupervised Machine Learning (Isolation Forest)**.")

# Load dataset
@st.cache_data
def load_data():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
    return pd.read_csv(dataset_path)

df = load_data()

# Select Patient
st.sidebar.header("Simulation Settings")
patient_index = st.sidebar.slider("Select Patient Baseline", 0, len(df)-1, 0)
patient_data = df.iloc[patient_index]

st.sidebar.markdown("---")
st.sidebar.write("**Patient Info:**")
st.sidebar.write(f"ID: {patient_data['Patient_ID']}")
st.sidebar.write(f"Age: {patient_data['Age']}")
st.sidebar.write(f"Gender: {patient_data['Gender']}")

if st.sidebar.button("▶️ Start Simulation", type="primary"):
    
    # Initialize Simulator and Pipeline
    simulator = DeteriorationSimulator(patient_data)
    readings = simulator.generate_scenario()
    
    pipeline = DigitalTwinPipeline(
        patient_id=patient_data["Patient_ID"],
        age=patient_data["Age"],
        gender=patient_data["Gender"],
        sustained_minutes=10
    )
    
    # UI Elements for live updates
    col1, col2, col3, col4 = st.columns(4)
    hr_metric = col1.empty()
    rr_metric = col2.empty()
    temp_metric = col3.empty()
    spo2_metric = col4.empty()
    
    status_alert = st.empty()
    reasons_box = st.empty()
    
    st.subheader("Live Vitals Trajectory")
    chart_spot = st.empty()
    
    trajectory_data = []
    
    # Start simulating time
    start_time = pd.Timestamp.now()
    
    for i, measurement in enumerate(readings):
        current_sim_time = start_time + pd.Timedelta(minutes=i*2)
        
        # Process through Digital Twin Pipeline (Rules + ML)
        result = pipeline.process_measurement(measurement, current_sim_time)
        trajectory_data.append(result)
        df_traj = pd.DataFrame(trajectory_data)
        
        # Update Metrics
        hr_metric.metric("Heart Rate (bpm)", f"{measurement['RestingHR']:.1f}")
        rr_metric.metric("Resp Rate", f"{measurement['RespRate']:.1f}")
        temp_metric.metric("Temperature (°C)", f"{measurement['BodyTemp_C']:.1f}")
        spo2_metric.metric("SpO2 (%)", f"{measurement['SpO2']:.1f}")
        
        # Update Status & Alerts
        state = result["Current_State"]
        if state == "STABLE":
            status_alert.success(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
        elif state == "WATCH":
            status_alert.info(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
        elif state == "HIGH RISK":
            status_alert.warning(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
        else:
            status_alert.error(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
            
        # Display Reasons
        if result["Reasons"]:
            reasons_box.error(f"⚠️ **Flags:** {result['Reasons']}")
        else:
            reasons_box.empty()
            
        # Update Chart
        if len(df_traj) > 0:
            chart_data = df_traj[['Timestamp', 'RestingHR', 'RespRate']].set_index('Timestamp')
            chart_spot.line_chart(chart_data)
            
        # Wait a second before next reading to simulate real-time
        time.sleep(1.2)
        
    st.success("Simulation Complete!")
    st.balloons()
    
else:
    st.info("👈 Click **Start Simulation** in the sidebar to watch the Digital Twin in action.")
