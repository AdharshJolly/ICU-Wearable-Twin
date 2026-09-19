from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import sys

# Add digital_twin to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'digital_twin'))
from deterioration_simulator import DeteriorationSimulator
from pipeline import DigitalTwinPipeline

app = FastAPI(title="ICU Digital Twin API")

# Enable CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with Next.js app URL (e.g., http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load baseline data
dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
if os.path.exists(dataset_path):
    df = pd.read_csv(dataset_path)
else:
    df = pd.DataFrame() # Fallback

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.get("/api/patients")
def get_patients():
    if df.empty:
        return []
    # Return basic patient list
    patients = df[['Patient_ID', 'Age', 'Gender']].head(10).to_dict(orient="records")
    return patients

@app.get("/api/simulate/{patient_index}")
def simulate_patient(patient_index: int):
    if df.empty or patient_index >= len(df):
        return {"error": "Patient not found"}
        
    patient_data = df.iloc[patient_index]
    
    # Initialize simulator and pipeline
    simulator = DeteriorationSimulator(patient_data)
    # Generate 1 step instead of full scenario for live stream API
    # In a real app, you would maintain state for this simulator across API calls
    
    # This is a mock response to give the frontend something to render
    return {
        "patient_id": patient_data["Patient_ID"],
        "hr": patient_data.get("Heart Rate", 75),
        "rr": patient_data.get("Respiratory Rate", 16),
        "temp": patient_data.get("Body Temperature", 36.8),
        "spo2": patient_data.get("SpO2", 98),
        "risk_state": "STABLE"
    }

# Run with: uvicorn api:app --reload
