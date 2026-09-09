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

# ---------------------------------------------------------
# TABS SETUP
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🔴 Live Monitor", "🔬 What-If Simulator"])

with tab1:
    if st.sidebar.button("▶️ Start Simulation", type="primary"):
        
        simulator = DeteriorationSimulator(patient_data)
        readings = simulator.generate_scenario()
        
        pipeline = DigitalTwinPipeline(
            patient_id=patient_data["Patient_ID"],
            age=patient_data["Age"],
            gender=patient_data["Gender"],
            sustained_minutes=10
        )
        
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
        start_time = pd.Timestamp.now()
        
        for i, measurement in enumerate(readings):
            current_sim_time = start_time + pd.Timedelta(minutes=i*2)
            
            result = pipeline.process_measurement(measurement, current_sim_time)
            trajectory_data.append(result)
            df_traj = pd.DataFrame(trajectory_data)
            
            hr_metric.metric("Heart Rate (bpm)", f"{measurement['RestingHR']:.1f}")
            rr_metric.metric("Resp Rate", f"{measurement['RespRate']:.1f}")
            temp_metric.metric("Temperature (°C)", f"{measurement['BodyTemp_C']:.1f}")
            spo2_metric.metric("SpO2 (%)", f"{measurement['SpO2']:.1f}")
            
            state = result["Current_State"]
            if state == "STABLE":
                status_alert.success(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
            elif state in ["WATCH", "HIGH RISK"]:
                status_alert.warning(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
            else:
                status_alert.error(f"**State: {state}** | Risk Score: {result['Risk_Score']} | {result['Alert']}")
                
            if result["Reasons"]:
                reasons_box.error(f"⚠️ **Explainability (Why?):** {result['Reasons']}")
            else:
                reasons_box.empty()
                
            if len(df_traj) > 0:
                chart_data = df_traj[['Timestamp', 'RestingHR', 'RespRate']].set_index('Timestamp')
                chart_spot.line_chart(chart_data)
                
            time.sleep(1.2)
            
        st.success("Simulation Complete!")
        st.balloons()
    else:
        st.info("👈 Click **Start Simulation** in the sidebar to watch the Digital Twin in action.")

with tab2:
    st.header("What-If Interventional Simulator")
    st.markdown("Adjust the patient's current vitals to simulate how clinical interventions (e.g., oxygen therapy, medication) affect the Digital Twin's predicted risk state.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        sim_hr = st.slider("Heart Rate (bpm)", 30, 200, int(patient_data["RestingHR"]))
        sim_rr = st.slider("Respiratory Rate", 5, 50, int(patient_data["RespRate"]))
        sim_temp = st.slider("Body Temperature (°C)", 35.0, 41.0, float(patient_data["BodyTemp_C"]))
        
    with col_b:
        sim_spo2 = st.slider("SpO2 (%)", 70, 100, int(patient_data["SpO2"]))
        sim_sysbp = st.slider("Systolic BP", 70, 200, int(patient_data["SystolicBP"]))
        sim_diabp = st.slider("Diastolic BP", 40, 130, int(patient_data["DiastolicBP"]))
        sim_hrv = st.slider("HRV", 0, 150, int(patient_data["HRV"]))
        
    # Re-run pipeline for this single reading
    sim_measurement = {
        "RestingHR": sim_hr,
        "RespRate": sim_rr,
        "BodyTemp_C": sim_temp,
        "SpO2": sim_spo2,
        "SystolicBP": sim_sysbp,
        "DiastolicBP": sim_diabp,
        "HRV": sim_hrv,
        "RestingECG": 0
    }
    
    # We create a dummy pipeline just to check the rules
    dummy_pipeline = DigitalTwinPipeline(patient_id=1, age=50, gender="Male", sustained_minutes=10)
    abnormal_reasons = dummy_pipeline.check_abnormality(sim_measurement)
    sim_risk_score = dummy_pipeline.calculate_risk_score(abnormal_reasons)
    sim_state = dummy_pipeline.determine_state(sim_risk_score, sustained_alert=False)
    
    st.markdown("### Simulated Risk Output")
    
    if sim_state == "STABLE":
        st.success(f"**Predicted State:** {sim_state} (Risk Score: {sim_risk_score})")
    elif sim_state in ["WATCH", "HIGH RISK"]:
        st.warning(f"**Predicted State:** {sim_state} (Risk Score: {sim_risk_score})")
    else:
        st.error(f"**Predicted State:** {sim_state} (Risk Score: {sim_risk_score})")
        
    if abnormal_reasons:
        st.error(f"**Flags:** {'; '.join(abnormal_reasons)}")
    
    # SHAP Explainability for ML Model
    if dummy_pipeline.ml_model is not None:
        import shap
        import matplotlib.pyplot as plt
        
        features = ["SystolicBP", "DiastolicBP", "RestingHR", "RespRate", "BodyTemp_C", "SpO2", "HRV"]
        row_df = pd.DataFrame([{f: sim_measurement[f] for f in features}])
        
        # Extract components from pipeline
        scaler = dummy_pipeline.ml_model.named_steps['scaler']
        iso_forest = dummy_pipeline.ml_model.named_steps['anomaly_detector']
        
        scaled_row = scaler.transform(row_df)
        
        # Isolation forest SHAP
        explainer = shap.TreeExplainer(iso_forest)
        shap_values = explainer.shap_values(scaled_row)
        
        st.markdown("### ML Model Feature Importance (SHAP)")
        st.markdown("Shows how much each vital sign contributed to the Isolation Forest anomaly score.")
        
        # Simple bar plot of SHAP values
        fig, ax = plt.subplots(figsize=(8, 4))
        shap_vals = shap_values[0]
        ax.barh(features, shap_vals, color=['red' if x < 0 else 'blue' for x in shap_vals])
        ax.set_xlabel("SHAP Value (Impact on Anomaly Score)")
        st.pyplot(fig)
