import os
import sys
import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add digital_twin to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'digital_twin'))
from digital_twin.deterioration_simulator import DeteriorationSimulator
from digital_twin.pipeline import DigitalTwinPipeline
from digital_twin.llm_agent import ClinicalLLMAgent
from digital_twin.database import SessionLocal, TelemetryLog
from digital_twin.counterfactual_engine import CounterfactualEngine
import json
import asyncio
from datetime import datetime

from pydantic import BaseModel
from digital_twin.multi_agent import MultiAgentBoard

app = FastAPI()

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate counterfactual engine at startup
counterfactual_engine = CounterfactualEngine()

app = FastAPI()

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Board
multi_agent_board = MultiAgentBoard()

@app.post("/api/patients/{patient_id}/consult")
async def run_clinical_consult(patient_id: str):
    db = SessionLocal()
    try:
        # Fetch patient history from DB
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(10).all()
        history_data = [
            {"hr": log.hr, "spo2": log.spo2, "rr": log.rr, "temp": log.temp, "time": log.timestamp.strftime('%H:%M:%S')}
            for log in reversed(logs)
        ]
        
        # Fetch patient demographics
        dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
        patient_data = {}
        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            patient_row = df[df['Patient_ID'].astype(str) == str(patient_id)]
            if not patient_row.empty:
                p = patient_row.iloc[0].to_dict()
                patient_data = {
                    "id": str(p["Patient_ID"]),
                    "age": int(p["Age"]),
                    "gender": str(p["Gender"]),
                    "physician": "Dr. Sarah Chen"
                }

        result = await multi_agent_board.run_consult(patient_data, history_data)
        return result
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────
# COUNTERFACTUAL ENDPOINT
# POST /api/patients/{id}/counterfactual
# Body: { "current_vitals": {...}, "state": "DETERIORATING",
#         "scenarios": ["none", "beta_blockers", "o2_and_fluids"] }
# ──────────────────────────────────────────────────────────────
class CounterfactualRequest(BaseModel):
    current_vitals: dict
    state: str = "STABLE"
    scenarios: list = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]
    n_steps: int = 30

@app.post("/api/patients/{patient_id}/counterfactual")
async def run_counterfactual(patient_id: str, req: CounterfactualRequest):
    """
    Returns projected risk trajectories for each intervention scenario.
    This is the Digital Twin counterfactual engine.
    """
    result = await asyncio.to_thread(
        counterfactual_engine.simulate,
        req.current_vitals,
        req.state,
        req.n_steps,
        req.scenarios,
    )
    result["patient_id"] = patient_id
    result["current_state"] = req.state
    return result


# ──────────────────────────────────────────────────────────────
# MODEL METRICS ENDPOINT  (for the Evidence Panel in the UI)
# GET /api/model/metrics
# ──────────────────────────────────────────────────────────────
@app.get("/api/model/metrics")
def get_model_metrics():
    """Returns the Phase 1 cross-validation metrics for the UI evidence panel."""
    metrics_path = os.path.join(os.path.dirname(__file__), "digital_twin", "model_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            return json.load(f)
    return {"error": "Metrics not found. Run train_phase1_correct_ml.py first."}

import joblib
import torch
import torch.nn as nn

class EarlyWarningLSTM(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=32, num_layers=2, dropout=0.3, output_dim=1):
        super(EarlyWarningLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])

# Load Predictive ML Models
predictive_model_path = os.path.join(os.path.dirname(__file__), "digital_twin", "predictive_icu_model.pkl")
shap_explainer_path = os.path.join(os.path.dirname(__file__), "digital_twin", "shap_explainer.pkl")
lstm_path = os.path.join(os.path.dirname(__file__), "digital_twin", "lstm_early_warning.pth")
scaler_path = os.path.join(os.path.dirname(__file__), "digital_twin", "icu_scaler.pkl")

predictive_model = None
shap_explainer = None
lstm_model = None
icu_scaler = None

if os.path.exists(predictive_model_path):
    predictive_model = joblib.load(predictive_model_path)
    shap_explainer = joblib.load(shap_explainer_path)

if os.path.exists(scaler_path):
    icu_scaler = joblib.load(scaler_path)

try:
    if os.path.exists(lstm_path):
        lstm_model = EarlyWarningLSTM()
        lstm_model.load_state_dict(torch.load(lstm_path, map_location=torch.device('cpu'), weights_only=True))
        lstm_model.eval()
except Exception as e:
    print(f"LSTM load warning: {e}")

@app.get("/api/patients/{patient_id}/risk-forecast")
async def get_risk_forecast(patient_id: str):
    if predictive_model is None or shap_explainer is None:
        return {"error": "Predictive model not loaded."}
        
    db = SessionLocal()
    try:
        # Fetch last 4 hours (simulated as 16 logs for simplicity)
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(16).all()
        if len(logs) < 2:
            return {"error": "Not enough historical data for predictive forecasting."}
            
        logs.reverse()
        hr_data = [log.hr for log in logs if log.hr is not None]
        spo2_data = [log.spo2 for log in logs if log.spo2 is not None]
        rr_data = [log.rr for log in logs if log.rr is not None]
        temp_data = [log.temp for log in logs if log.temp is not None]
        
        # We don't have BP in logs, so mock it for now based on HR
        sys_data = [120 + (hr - 75)*0.5 for hr in hr_data]
        dia_data = [80 + (hr - 75)*0.3 for hr in hr_data]
        
        # Engineer features for XGBoost
        features = {
            'HR_mean': float(sum(hr_data)/len(hr_data)),
            'HR_max': float(max(hr_data)),
            'HR_trend': float(hr_data[-1] - hr_data[0]),
            'SpO2_mean': float(sum(spo2_data)/len(spo2_data)),
            'SpO2_min': float(min(spo2_data)),
            'SpO2_trend': float(spo2_data[-1] - spo2_data[0]),
            'RR_mean': float(sum(rr_data)/len(rr_data)),
            'RR_max': float(max(rr_data)),
            'RR_trend': float(rr_data[-1] - rr_data[0]),
            'SysBP_mean': float(sum(sys_data)/len(sys_data)),
            'SysBP_min': float(min(sys_data)),
            'SysBP_trend': float(sys_data[-1] - sys_data[0]),
            'Age': 65
        }
        
        # Predict
        import pandas as pd
        X = pd.DataFrame([features])
        # XGBoost Prediction
        prob = float(predictive_model.predict_proba(X)[0, 1])
        
        # PyTorch LSTM Deep Learning Prediction
        lstm_prob = prob # default fallback
        if lstm_model is not None and icu_scaler is not None and len(hr_data) >= 10:
            seq_raw = []
            for i in range(-10, 0):
                seq_raw.append([hr_data[i], rr_data[i], spo2_data[i], sys_data[i], dia_data[i]])
            
            # Use real MIMIC-IV StandardScaler
            import numpy as np
            seq_scaled = icu_scaler.transform(np.array(seq_raw))
            
            x_tensor = torch.tensor([seq_scaled], dtype=torch.float32)
            with torch.no_grad():
                lstm_prob = float(lstm_model(x_tensor).item())
        
        # Ensembled Risk Score (60% LSTM, 40% XGBoost)
        ensembled_prob = (lstm_prob * 0.6) + (prob * 0.4)
        
        # SHAP Explanation (Using XGBoost features as proxy for interpretability)
        shap_values = shap_explainer.shap_values(X)[0]
        
        # Format Top 3 Contributors
        feature_names = list(features.keys())
        contributions = sorted(zip(feature_names, shap_values), key=lambda x: abs(x[1]), reverse=True)
        
        top_factors = []
        for feat, val in contributions[:3]:
            impact = "increased" if val > 0 else "decreased"
            top_factors.append({
                "feature": feat,
                "value": round(features[feat], 2),
                "shap_impact": round(float(val), 3),
                "description": f"{feat} ({round(features[feat], 1)}) {impact} risk"
            })
            
        return {
            "risk_probability": round(ensembled_prob * 100, 1),
            "xgboost_prob": round(prob * 100, 1),
            "lstm_prob": round(lstm_prob * 100, 1),
            "top_factors": top_factors
        }
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.get("/api/patients")
def get_patients():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
        patients = df[['Patient_ID', 'Age', 'Gender']].head(8).to_dict(orient="records")
        return {"patients": patients}
    return {"patients": []}

@app.get("/api/patients/{patient_id}")
def get_patient_info(patient_id: str):
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
        patient_row = df[df['Patient_ID'].astype(str) == str(patient_id)]
        if not patient_row.empty:
            p = patient_row.iloc[0].to_dict()
            return {
                "id": str(p["Patient_ID"]),
                "age": int(p["Age"]),
                "gender": str(p["Gender"]),
                "physician": "Dr. Sarah Chen"
            }
    return {"error": "Patient not found"}

@app.get("/api/patients/{patient_id}/history")
def get_patient_history(patient_id: str, limit: int = 100):
    db = SessionLocal()
    try:
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(limit).all()
        # Reverse to get chronological order
        logs.reverse()
        return {
            "history": [
                {
                    "time": log.timestamp.strftime("%H:%M:%S"),
                    "hr": log.hr,
                    "rr": log.rr,
                    "temp": log.temp,
                    "spo2": log.spo2,
                    "risk_state": log.risk_state,
                    "abnormal_reasons": json.loads(log.abnormal_reasons) if log.abnormal_reasons else [],
                    "llm_summary": log.llm_summary,
                    "intervention": log.intervention
                }
                for log in logs
            ]
        }
    finally:
        db.close()

@app.websocket("/ws/simulate/{patient_id}")
async def websocket_simulate(websocket: WebSocket, patient_id: str):
    await websocket.accept()
    
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset", "Heart Disease Dataset .csv")
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
    else:
        df = pd.DataFrame() # Fallback
        
    # Find patient by ID
    patient_row = df[df['Patient_ID'].astype(str) == str(patient_id)]
    
    if patient_row.empty:
        await websocket.close(code=1008)
        return
        
    patient_data = patient_row.iloc[0].to_dict()
    
    simulator = DeteriorationSimulator(patient_data)
    pipeline = DigitalTwinPipeline(
        patient_id=patient_data["Patient_ID"],
        age=patient_data["Age"],
        gender=patient_data["Gender"],
        sustained_minutes=3 
    )
    llm_agent = ClinicalLLMAgent()
    
    # Task to listen for incoming interventions
    async def listen_for_interventions():
        try:
            while True:
                data = await websocket.receive_text()
                command = json.loads(data)
                if "action" in command:
                    action_name = command["action"]
                    print(f"Applying intervention: {action_name}", flush=True)
                    simulator.apply_intervention(action_name)
                    
                    # Log Intervention to DB
                    db = SessionLocal()
                    try:
                        log_entry = TelemetryLog(
                            patient_id=str(patient_id),
                            intervention=action_name,
                            risk_state="INTERVENTION",
                            abnormal_reasons="[]"
                        )
                        db.add(log_entry)
                        db.commit()
                    except Exception as e:
                        pass
                    finally:
                        db.close()
        except WebSocketDisconnect:
            pass

    listen_task = asyncio.create_task(listen_for_interventions())
    
    try:
        print("Generating scenario...", flush=True)
        readings = simulator.generate_scenario()
        print(f"Generated {len(readings)} readings.", flush=True)
        
        while True:
            for i, base_reading in enumerate(readings):
                # Apply any active interventions dynamically
                reading = simulator._apply_modifiers(base_reading.copy())
                
                print(f"Processing reading {i}...", flush=True)
                current_time = datetime.now()
                state_dict = pipeline.process_measurement(reading, current_time)
                
                risk_state = state_dict.get("State", "STABLE")
                reasons = state_dict.get("Abnormal_Reasons", [])
                
                print(f"Processed. State: {risk_state}", flush=True)
                
                payload = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "hr": float(reading.get("RestingHR", 75) + (i % 2)),
                    "rr": float(reading.get("RespRate", 16) + (i % 2)),
                    "temp": float(reading.get("BodyTemp_C", 36.8)),
                    "spo2": float(reading.get("SpO2", 98) - (i % 2)),
                    "sbp": float(reading.get("SystolicBP", 120)),
                    "dbp": float(reading.get("DiastolicBP", 80)),
                    "risk_state": risk_state,
                    "reasons": reasons,
                    "active_medications": reading.get("active_medications", {})
                }
                
                # Generate LLM Summary asynchronously
                payload["llm_summary"] = await llm_agent.generate_summary(risk_state, reasons, payload)
                
                # Save to database
                db = SessionLocal()
                try:
                    log_entry = TelemetryLog(
                        patient_id=str(patient_id),
                        hr=payload["hr"],
                        rr=payload["rr"],
                        temp=payload["temp"],
                        spo2=payload["spo2"],
                        risk_state=risk_state,
                        abnormal_reasons=json.dumps(reasons),
                        llm_summary=payload["llm_summary"]
                    )
                    db.add(log_entry)
                    db.commit()
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()
                
                print("Sending payload via websocket...", flush=True)
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(1) 
                
    except WebSocketDisconnect:
        print(f"Client disconnected for patient {patient_id}", flush=True)
    except Exception as e:
        import traceback
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        await websocket.close()
    finally:
        listen_task.cancel()
