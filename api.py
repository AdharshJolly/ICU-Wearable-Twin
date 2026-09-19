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

# Load Models
predictive_model = None
try:
    predictive_model = joblib.load(os.path.join(os.path.dirname(__file__), "digital_twin", "predictive_icu_model.pkl"))
except Exception as e:
    print(f"XGBoost load error: {e}")

shap_explainer = None
try:
    shap_explainer = joblib.load(os.path.join(os.path.dirname(__file__), "digital_twin", "shap_explainer.pkl"))
except Exception as e:
    print(f"SHAP load error: {e}")

icu_scaler = None
try:
    # Use the scaler from Phase 1 for XGBoost features
    scaler_path = os.path.join(os.path.dirname(__file__), "digital_twin", "icu_scaler.pkl")
    if os.path.exists(scaler_path):
        icu_scaler = joblib.load(scaler_path)
except Exception as e:
    print(f"Scaler load error: {e}")

lstm_scaler = None
try:
    # Use the scaler from Phase 2 for LSTM sequence features
    scaler_path = os.path.join(os.path.dirname(__file__), "digital_twin", "lstm_scaler.pkl")
    if os.path.exists(scaler_path):
        lstm_scaler = joblib.load(scaler_path)
except Exception as e:
    pass

# Early Warning LSTM Model (Phase 2 Temporal Model)
class TemporalModel(nn.Module):
    def __init__(self, arch='lstm', input_dim=5, hidden_dim=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.arch = arch
        bidirectional = (arch == 'bilstm')
        rnn_cls = nn.GRU if arch == 'gru' else nn.LSTM
        self.rnn = rnn_cls(
            input_dim, hidden_dim, num_layers,
            batch_first=True, dropout=dropout,
            bidirectional=bidirectional
        )
        fc_in = hidden_dim * 2 if bidirectional else hidden_dim
        self.fc = nn.Sequential(
            nn.Linear(fc_in, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        out, _ = self.rnn(x)
        return self.fc(out[:, -1, :])

lstm_model = None
try:
    lstm_path = os.path.join(os.path.dirname(__file__), "digital_twin", "lstm_early_warning.pth")
    if os.path.exists(lstm_path):
        checkpoint = torch.load(lstm_path)
        if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            lstm_model = TemporalModel(
                arch=checkpoint.get('arch', 'lstm'),
                hidden_dim=checkpoint.get('hidden_dim', 64),
                num_layers=checkpoint.get('num_layers', 2),
                dropout=checkpoint.get('dropout', 0.3)
            )
            lstm_model.load_state_dict(checkpoint['state_dict'])
        else:
            lstm_model = TemporalModel(arch='lstm', input_dim=5, hidden_dim=32, num_layers=2, dropout=0.3)
            lstm_model.load_state_dict(checkpoint)
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
        
        # Engineer features for XGBoost (Matches Phase 1: 5 vitals x 5 stats = 25 features)
        import numpy as np
        df_vitals = {
            'hr': hr_data,
            'rr': rr_data,
            'spo2': spo2_data,
            'sbp': sys_data,
            'dbp': dia_data
        }
        
        feats = []
        feature_names = []
        for key, vals in df_vitals.items():
            arr = np.array(vals, dtype=float)
            feats.extend([
                float(arr.mean()), float(arr.min()), float(arr.max()),
                float(arr.std()) if len(arr) > 1 else 0.0,
                float(arr[-1] - arr[0]) if len(arr) > 1 else 0.0
            ])
            feature_names.extend([
                f"{key}_mean", f"{key}_min", f"{key}_max", f"{key}_std", f"{key}_slope"
            ])
        
        # Predict
        import pandas as pd
        X = pd.DataFrame([feats], columns=feature_names)
        
        # Scale for XGBoost (if the scaler was used in Phase 1 for XGBoost)
        # Wait, in Phase 1, XGBoost WAS trained on scaled features!
        if icu_scaler is not None:
            X_scaled = icu_scaler.transform(X)
        else:
            X_scaled = X.values
            
        prob = float(predictive_model.predict_proba(X_scaled)[0, 1])
        
        # PyTorch LSTM Deep Learning Prediction
        lstm_prob = prob # default fallback
        if lstm_model is not None and lstm_scaler is not None and len(hr_data) >= 10:
            seq_raw = []
            for i in range(-10, 0):
                seq_raw.append([hr_data[i], rr_data[i], spo2_data[i], sys_data[i], dia_data[i]])
            
            # Use real MIMIC-IV StandardScaler for LSTM
            import numpy as np
            seq_scaled = lstm_scaler.transform(np.array(seq_raw))
            
            x_tensor = torch.tensor([seq_scaled], dtype=torch.float32)
            with torch.no_grad():
                lstm_prob = float(lstm_model(x_tensor).item())
        
        # Ensembled Risk Score (60% LSTM, 40% XGBoost)
        ensembled_prob = (lstm_prob * 0.6) + (prob * 0.4)
        
        # Priority 8: Uncertainty & Model Disagreement
        disagreement = abs(lstm_prob - prob)
        if disagreement > 0.3:
            confidence = "LOW"
            alert_msg = "High model disagreement detected. Manual review recommended."
        elif disagreement > 0.15:
            confidence = "MODERATE"
            alert_msg = "Moderate model variance."
        else:
            confidence = "HIGH"
            alert_msg = "Models are in strong agreement."
        
        # SHAP Explanation (Using XGBoost features as proxy for interpretability)
        try:
            shap_values = shap_explainer.shap_values(X_scaled)[0]
            contributions = sorted(zip(feature_names, shap_values), key=lambda x: abs(x[1]), reverse=True)
            
            top_factors = []
            for feat, val in contributions[:3]:
                impact = "increased" if val > 0 else "decreased"
                feat_val = round(X[feat].iloc[0], 2)
                top_factors.append({
                    "feature": feat,
                    "value": feat_val,
                    "shap_impact": round(float(val), 3),
                    "description": f"{feat} ({round(feat_val, 1)}) {impact} risk"
                })
        except Exception:
            top_factors = []
            
        return {
            "risk_probability": round(ensembled_prob * 100, 1),
            "xgboost_prob": round(prob * 100, 1),
            "lstm_prob": round(lstm_prob * 100, 1),
            "confidence": confidence,
            "uncertainty_alert": alert_msg,
            "disagreement_score": round(disagreement * 100, 1),
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
