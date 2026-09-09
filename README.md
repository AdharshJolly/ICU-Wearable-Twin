# An Explainable Machine Learning-Based Patient Digital Twin for Early Detection of Patient Deterioration

## 📌 Project Overview
This project implements a **Hybrid Clinical Decision Support System (CDSS)** and **Patient Digital Twin** designed to monitor real-time (or simulated) patient vital signs. It is built to bridge the gap between continuous wearable biomarker tracking, predictive Machine Learning, and explainable medical reasoning.

*Note: As per the updated project scope, physical wearable hardware (ESP32, MAX30102, etc.) is simulated using a software-driven data stream.*

---

## 🏗️ System Architecture & Workflow

The digital twin processes patient data through a comprehensive, multi-layer architecture:

1. **Patient Vital Signs** (Simulated stream or Historical Data)
2. **Data Preprocessing**
3. **Unsupervised ML Model** (Isolation Forest)
4. **Clinical Rule Engine** (SIRS / NEWS standards)
5. **Digital Twin Patient State** (Risk scoring & sustained abnormalities)
6. **SQLite Database** (Permanent EHR logging)
7. **Web Dashboard** (Real-time monitoring, Alerts, SHAP Explainability, & What-If Simulation)

---

## 🧩 Module Breakdown (For Project Report)

### 1. Patient Data Input & Simulator (`digital_twin/deterioration_simulator.py`)
Instead of physical hardware, the system uses a controlled software simulator. It takes a baseline patient from the dataset and injects **biological noise** (using Gaussian randomness) while safely transitioning the patient through stable, deteriorating, and recovery states to test the system's responsiveness.

### 2. Data Preprocessing & EDA (`data_preprocessing/`, `analysis/`)
Handles missing values, scaling, and feature engineering. Standardized pipelines ensure that raw sensor data is correctly normalized before entering the ML model.

### 3. Machine Learning Model (`digital_twin/train_ml_model.py`)
- **Algorithm Used:** `IsolationForest` (Unsupervised Anomaly Detection).
- **Why?** Our historical dataset contains baseline measurements without explicit "Deterioration = True/False" labels. Instead of forcing a supervised model, we use an Isolation Forest to learn the high-dimensional mathematical boundaries of "Normal" patient vitals. 
- When a patient's vitals deviate from this learned normal distribution, the model flags it as an anomaly.

### 4. Explainable Rule Engine (`digital_twin/pipeline.py`)
The system doesn't rely solely on the "black-box" ML model. It integrates hardcoded clinical thresholds:
- **Tachycardia / Bradycardia:** HR > 110 or < 40
- **Tachypnea / Bradypnea:** RR > 22 or < 8
- **Fever / Hypothermia:** Temp > 38.0°C or < 36.0°C
- **Hypoxia:** SpO2 < 92%
- **Hypertension / Hypotension:** Systolic BP > 160 or < 90

**Sustained Abnormality Window:** To prevent alert fatigue, the engine tracks how long a condition persists before escalating the patient from `HIGH RISK` to `CRITICAL`.

### 5. Database Integration (`digital_twin/db_manager.py`)
Uses **SQLite** to provide a persistent Electronic Health Record (EHR) logging layer. Every generated vital sign and risk state is permanently logged to `digital_twin.db` for retrospective analysis.

### 6. Web Dashboard & UI (`dashboard.py`)
Built using **Streamlit** and **Plotly**, serving two main functions:
1. **Live ICU Monitor:** Continuously streams the simulated patient, updates delta metrics, logs clinical flags, and plots the vitals trajectory in real-time.
2. **What-If Interventional Simulator:** Allows a clinician to manually adjust vital sliders to instantly see the predicted risk score.

### 7. Explainability & SHAP (Inside the Dashboard)
In the What-If Simulator, the system generates a **SHAP (SHapley Additive exPlanations)** plot. This breaks down the Isolation Forest's internal logic, showing exactly which vital signs pushed the patient into an anomalous state (Red) and which kept them stable (Blue).

---

## 🚀 How to Run the System

### 1. Install Requirements
Ensure you have the necessary Python libraries installed:
```bash
pip install pandas scikit-learn streamlit plotly shap
```

### 2. Train the Machine Learning Model
Before running the dashboard, generate the model pipeline file (`anomaly_pipeline.pkl`):
```bash
python digital_twin/train_ml_model.py
```

### 3. Launch the Live Dashboard
Start the interactive Streamlit server:
```bash
streamlit run dashboard.py
```
*The dashboard will automatically open in your default web browser.*

### 4. Generate Evaluation Plots (Optional)
To generate static 2D Scatter and Time-Series plots for your final report:
```bash
python analysis/ml_evaluation_plots.py
```

---

## 💡 Key Contributions to highlight in the Report
Your literature review identified a major gap: **the lack of an explainable rule engine connected to continuous predictive modeling**. 
This project solves that exact gap by creating a **Hybrid CDSS** where Unsupervised Anomaly Detection (Isolation Forest) works *alongside* strict clinical rules, all wrapped in a visually interpretable "Digital Twin" dashboard that provides SHAP explainability.
