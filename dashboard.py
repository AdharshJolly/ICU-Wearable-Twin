import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import sys
import plotly.express as px
import plotly.graph_objects as go

# Add digital_twin to path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'digital_twin'))
from deterioration_simulator import DeteriorationSimulator
from pipeline import DigitalTwinPipeline

# =========================================================
# CONFIGURATION & STYLING
# =========================================================
st.set_page_config(page_title="ICU Digital Twin", layout="wide", page_icon="🏥", initial_sidebar_state="expanded")

# Custom CSS for UI enhancements
st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: bold; margin-bottom: 0rem; }
    .sub-header { font-size: 1.2rem; color: #6B7280; margin-bottom: 2rem; }
    .metric-card { background-color: #F3F4F6; padding: 1rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .alert-critical { background-color: #FEE2E2; border-left: 5px solid #EF4444; padding: 1rem; border-radius: 5px; color: #991B1B; font-weight: bold; }
    .alert-warning { background-color: #FEF3C7; border-left: 5px solid #F59E0B; padding: 1rem; border-radius: 5px; color: #92400E; font-weight: bold; }
    .alert-stable { background-color: #D1FAE5; border-left: 5px solid #10B981; padding: 1rem; border-radius: 5px; color: #065F46; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏥 ICU Wearable Patient Digital Twin</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live monitoring simulation driven by Clinical Rules & Unsupervised Machine Learning</div>', unsafe_allow_html=True)

# =========================================================
# DATA & INITIALIZATION
# =========================================================
@st.cache_data
def load_data():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
    return pd.read_csv(dataset_path)

df = load_data()

# Sidebar
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100)
st.sidebar.markdown("## ⚙️ Control Panel")
patient_index = st.sidebar.slider("Select Patient Baseline", 0, len(df)-1, 0)
patient_data = df.iloc[patient_index]

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Patient Profile")
st.sidebar.markdown(f"**ID:** `P00{patient_data['Patient_ID']}`")
st.sidebar.markdown(f"**Age:** `{patient_data['Age']} years`")
st.sidebar.markdown(f"**Gender:** `{patient_data['Gender']}`")
st.sidebar.markdown("---")

# ---------------------------------------------------------
# TABS SETUP
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🔴 Live ICU Monitor", "🔬 Interventional What-If Simulator"])

# ---------------------------------------------------------
# TAB 1: LIVE MONITOR
# ---------------------------------------------------------
with tab1:
    col_start, col_stop = st.sidebar.columns(2)
    start_btn = col_start.button("▶️ Start", type="primary")
    stop_btn = col_stop.button("⏹️ Stop")
    
    if start_btn:
        import itertools
        
        simulator = DeteriorationSimulator(patient_data)
        readings = simulator.generate_scenario()
        
        pipeline = DigitalTwinPipeline(
            patient_id=patient_data["Patient_ID"],
            age=patient_data["Age"],
            gender=patient_data["Gender"],
            sustained_minutes=10
        )
        
        # Placeholders
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        hr_metric = metrics_col1.empty()
        rr_metric = metrics_col2.empty()
        temp_metric = metrics_col3.empty()
        spo2_metric = metrics_col4.empty()
        
        st.markdown("---")
        col_status, col_reasons = st.columns([1, 1])
        with col_status:
            st.subheader("Current Risk State")
            status_alert = st.empty()
            risk_progress = st.empty()
            
        with col_reasons:
            st.subheader("AI Explainability (Why?)")
            reasons_box = st.empty()
        
        st.markdown("---")
        st.subheader("📈 Live Vitals Trajectory")
        chart_spot = st.empty()
        
        trajectory_data = []
        start_time = pd.Timestamp.now()
        
        prev_hr = patient_data["RestingHR"]
        prev_rr = patient_data["RespRate"]
        prev_temp = patient_data["BodyTemp_C"]
        prev_spo2 = patient_data["SpO2"]
        
        # Infinite Loop for Live Simulation
        for i, measurement in enumerate(itertools.cycle(readings)):
            current_sim_time = start_time + pd.Timedelta(minutes=i*2)
            result = pipeline.process_measurement(measurement, current_sim_time)
            trajectory_data.append(result)
            df_traj = pd.DataFrame(trajectory_data)
            
            # --- METRICS (with deltas) ---
            hr_metric.metric("Heart Rate", f"{measurement['RestingHR']:.0f} bpm", f"{measurement['RestingHR'] - prev_hr:.1f}", delta_color="inverse")
            rr_metric.metric("Respiratory Rate", f"{measurement['RespRate']:.0f} /min", f"{measurement['RespRate'] - prev_rr:.1f}", delta_color="inverse")
            temp_metric.metric("Temperature", f"{measurement['BodyTemp_C']:.1f} °C", f"{measurement['BodyTemp_C'] - prev_temp:.1f}", delta_color="inverse")
            spo2_metric.metric("SpO2", f"{measurement['SpO2']:.0f} %", f"{measurement['SpO2'] - prev_spo2:.1f}", delta_color="normal")
            
            prev_hr, prev_rr, prev_temp, prev_spo2 = measurement['RestingHR'], measurement['RespRate'], measurement['BodyTemp_C'], measurement['SpO2']
            
            # --- STATE ALERT ---
            state = result["Current_State"]
            alert_msg = result['Alert']
            if state == "STABLE":
                status_alert.markdown(f'<div class="alert-stable">✅ {state}<br><small>{alert_msg}</small></div>', unsafe_allow_html=True)
                risk_progress.progress(0, text="Risk Level: 0%")
            elif state in ["WATCH", "HIGH RISK"]:
                status_alert.markdown(f'<div class="alert-warning">⚠️ {state}<br><small>{alert_msg}</small></div>', unsafe_allow_html=True)
                risk_progress.progress(66, text="Risk Level: 66%")
            else:
                status_alert.markdown(f'<div class="alert-critical">🚨 {state}<br><small>{alert_msg}</small></div>', unsafe_allow_html=True)
                risk_progress.progress(100, text="Risk Level: 100%")
                
            # --- REASONS ---
            if result["Reasons"]:
                flags = "\n".join([f"- {r}" for r in result["Reasons"].split("; ")])
                reasons_box.error(f"**Flags detected:**\n{flags}", icon="🧠")
            else:
                reasons_box.success("All vitals within normal parameters. ML Model detects no anomalies.", icon="✨")
                
            # --- CHARTS ---
            if len(df_traj) > 0:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_traj['Timestamp'], y=df_traj['RestingHR'], mode='lines+markers', name='Heart Rate (bpm)', line=dict(color='#EF4444', width=3)))
                fig.add_trace(go.Scatter(x=df_traj['Timestamp'], y=df_traj['RespRate'], mode='lines+markers', name='Resp Rate (per min)', line=dict(color='#3B82F6', width=3)))
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor='#E5E7EB'),
                    yaxis=dict(showgrid=True, gridcolor='#E5E7EB'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                chart_spot.plotly_chart(fig, width="stretch")
                
            time.sleep(1.2)
            
    elif stop_btn:
        st.warning("Simulation Stopped.")
        
    else:
        st.info("👈 Click **Start** in the sidebar to watch the Digital Twin in action.")

# ---------------------------------------------------------
# TAB 2: WHAT-IF SIMULATOR
# ---------------------------------------------------------
with tab2:
    st.markdown("### 🔬 Interventional What-If Simulator")
    st.markdown("Adjust the patient's current vitals to simulate how clinical interventions (e.g., oxygen therapy, medication) instantly affect the ML Model's predicted risk state.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Cardiovascular Adjustments**")
        sim_hr = st.slider("Heart Rate (bpm)", 30, 200, int(patient_data["RestingHR"]))
        sim_sysbp = st.slider("Systolic BP", 70, 200, int(patient_data["SystolicBP"]))
        sim_diabp = st.slider("Diastolic BP", 40, 130, int(patient_data["DiastolicBP"]))
        
    with col_b:
        st.markdown("**Respiratory & Other Adjustments**")
        sim_rr = st.slider("Respiratory Rate", 5, 50, int(patient_data["RespRate"]))
        sim_spo2 = st.slider("SpO2 (%)", 70, 100, int(patient_data["SpO2"]))
        sim_temp = st.slider("Body Temperature (°C)", 35.0, 41.0, float(patient_data["BodyTemp_C"]))
        
    sim_hrv = int(patient_data["HRV"]) # Keep constant for simplicity in UI
        
    sim_measurement = {
        "RestingHR": sim_hr, "RespRate": sim_rr, "BodyTemp_C": sim_temp,
        "SpO2": sim_spo2, "SystolicBP": sim_sysbp, "DiastolicBP": sim_diabp,
        "HRV": sim_hrv, "RestingECG": 0
    }
    
    dummy_pipeline = DigitalTwinPipeline(patient_id=1, age=50, gender="Male", sustained_minutes=10)
    abnormal_reasons = dummy_pipeline.check_abnormality(sim_measurement)
    sim_risk_score = dummy_pipeline.calculate_risk_score(abnormal_reasons)
    sim_state = dummy_pipeline.determine_state(sim_risk_score, sustained_alert=False)
    
    st.markdown("---")
    st.markdown("### 🤖 Simulated Risk Output")
    
    if sim_state == "STABLE":
        st.markdown(f'<div class="alert-stable">✅ Predicted State: {sim_state} (Risk Score: {sim_risk_score})</div>', unsafe_allow_html=True)
    elif sim_state in ["WATCH", "HIGH RISK"]:
        st.markdown(f'<div class="alert-warning">⚠️ Predicted State: {sim_state} (Risk Score: {sim_risk_score})</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-critical">🚨 Predicted State: {sim_state} (Risk Score: {sim_risk_score})</div>', unsafe_allow_html=True)
        
    if abnormal_reasons:
        flags = "\n".join([f"- {r}" for r in abnormal_reasons])
        st.error(f"**Clinical Flags Triggered:**\n{flags}", icon="⚕️")
    
    if dummy_pipeline.ml_model is not None:
        import shap
        features = ["SystolicBP", "DiastolicBP", "RestingHR", "RespRate", "BodyTemp_C", "SpO2", "HRV"]
        row_df = pd.DataFrame([{f: sim_measurement[f] for f in features}])
        
        scaler = dummy_pipeline.ml_model.named_steps['scaler']
        iso_forest = dummy_pipeline.ml_model.named_steps['anomaly_detector']
        scaled_row = scaler.transform(row_df)
        
        explainer = shap.TreeExplainer(iso_forest)
        shap_values = explainer.shap_values(scaled_row)
        
        st.markdown("---")
        st.markdown("### 📊 ML Model Feature Importance (SHAP)")
        st.markdown("This chart breaks down the Isolation Forest's reasoning. **Red bars** push the patient towards anomaly (deterioration), while **Blue bars** push towards normal (stable).")
        
        shap_vals = shap_values[0]
        colors = ['#EF4444' if x < 0 else '#3B82F6' for x in shap_vals] # Negative SHAP means anomaly for IsolationForest
        
        fig_shap = go.Figure(go.Bar(
            x=shap_vals,
            y=features,
            orientation='h',
            marker_color=colors,
            text=[f"{v:.2f}" for v in shap_vals],
            textposition='auto'
        ))
        
        fig_shap.update_layout(
            title="SHAP Values: Impact on Anomaly Score",
            xaxis_title="Impact on Prediction",
            yaxis_title="Vital Sign",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_shap, width="stretch")
