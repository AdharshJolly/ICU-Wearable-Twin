import sys
import os
import json
import asyncio
import pandas as pd
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

# Import digital_twin tools
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from digital_twin.database import SessionLocal, TelemetryLog
from digital_twin.multi_agent import MultiAgentBoard
from digital_twin.counterfactual_engine import CounterfactualEngine
from digital_twin.llm_agent import ClinicalLLMAgent
from digital_twin.deterioration_simulator import DeteriorationSimulator
from app.services.risk_service import calculate_risk_forecast
from app.schemas.schemas import CounterfactualRequest

api_router = APIRouter()
multi_agent_board = MultiAgentBoard()
counterfactual_engine = CounterfactualEngine()
llm_agent = ClinicalLLMAgent()

@api_router.get("/")
def read_root():
    return {"status": "API is running"}

@api_router.get("/api/patients")
def get_patients():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "Heart Disease Dataset .csv")
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
        patients = df[['Patient_ID', 'Age', 'Gender']].head(8).to_dict(orient="records")
        return {"patients": patients}
    return {"patients": []}

@api_router.get("/api/patients/{patient_id}")
def get_patient(patient_id: str):
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "Heart Disease Dataset .csv")
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

@api_router.get("/api/patients/{patient_id}/history")
def get_patient_history(patient_id: str):
    db = SessionLocal()
    try:
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(100).all()
        history = [
            {
                "time": log.timestamp.isoformat(),
                "hr": log.hr,
                "rr": log.rr,
                "spo2": log.spo2,
                "temp": log.temp
            } for log in logs
        ]
        history.reverse()
        return {"patient_id": patient_id, "history": history}
    finally:
        db.close()

@api_router.get("/api/patients/{patient_id}/risk-forecast")
async def get_risk_forecast_api(patient_id: str):
    db = SessionLocal()
    try:
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(16).all()
        if len(logs) < 2:
            return {"error": "Not enough historical data for predictive forecasting."}
            
        logs.reverse()
        hr_data = [log.hr for log in logs if log.hr is not None]
        spo2_data = [log.spo2 for log in logs if log.spo2 is not None]
        rr_data = [log.rr for log in logs if log.rr is not None]
        temp_data = [log.temp for log in logs if log.temp is not None]
        
        # Mock BP based on HR
        sys_data = [120 + (hr - 75)*0.5 for hr in hr_data]
        dia_data = [80 + (hr - 75)*0.3 for hr in hr_data]
        
        return calculate_risk_forecast(hr_data, rr_data, spo2_data, sys_data, dia_data)
    finally:
        db.close()

@api_router.post("/api/patients/{patient_id}/consult")
async def run_clinical_consult(patient_id: str):
    db = SessionLocal()
    try:
        logs = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).limit(10).all()
        history_data = [
            {"hr": log.hr, "spo2": log.spo2, "rr": log.rr, "temp": log.temp, "time": log.timestamp.strftime('%H:%M:%S')}
            for log in reversed(logs)
        ]
        
        patient_data = {"id": patient_id, "age": 65, "gender": "Unknown", "physician": "Dr. Sarah Chen"}
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "Heart Disease Dataset .csv")
        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            patient_row = df[df['Patient_ID'].astype(str) == str(patient_id)]
            if not patient_row.empty:
                p = patient_row.iloc[0].to_dict()
                patient_data["age"] = int(p["Age"])
                patient_data["gender"] = str(p["Gender"])

        result = await multi_agent_board.run_consult(patient_data, history_data)
        return result
    finally:
        db.close()

@api_router.post("/api/patients/{patient_id}/counterfactual")
async def run_counterfactual(patient_id: str, req: CounterfactualRequest):
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

@api_router.get("/api/model/metrics")
def get_model_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "..", "digital_twin", "model_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            return json.load(f)
    return {"error": "Metrics not found. Run train_phase1_correct_ml.py first."}

@api_router.websocket("/ws/simulate/{patient_id}")
async def websocket_simulate(websocket: WebSocket, patient_id: str):
    await websocket.accept()
    
    patient_data = {
        "SystolicBP": 120, "DiastolicBP": 80,
        "RestingHR": 75, "RespRate": 16,
        "BodyTemp_C": 36.8, "SpO2": 98,
        "RestingECG": 0, "HRV": 50
    }
    
    simulator = DeteriorationSimulator(patient_data)
    scenario_ticks = simulator.generate_scenario()
    
    risk_state = "STABLE"
    reasons = []
    
    try:
        for i, reading in enumerate(scenario_ticks):
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                data = json.loads(msg)
                if "action" in data:
                    simulator.apply_intervention(data["action"])
            except asyncio.TimeoutError:
                pass
            
            # Use active state mapping
            if i < 60:
                risk_state = "STABLE"
                reasons = ["Normal Vitals"]
            elif i < 90:
                risk_state = "ELEVATED"
                reasons = ["Mild Tachycardia", "Slight Tachypnea"]
            elif i < 120:
                risk_state = "HIGH_RISK"
                reasons = ["Tachycardia", "Hypoxia", "Fever"]
            else:
                risk_state = "CRITICAL"
                reasons = ["Severe Tachycardia", "Severe Hypoxia", "Hypotension"]
                
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
            
            payload["llm_summary"] = await llm_agent.generate_summary(risk_state, reasons, payload)
            
            db = SessionLocal()
            try:
                log = TelemetryLog(
                    patient_id=patient_id,
                    hr=payload["hr"], rr=payload["rr"],
                    spo2=payload["spo2"], temp=payload["temp"],
                    risk_state=risk_state, llm_summary=payload["llm_summary"]
                )
                db.add(log)
                db.commit()
            except Exception as e:
                print(f"DB Error: {e}")
            finally:
                db.close()
                
            await websocket.send_json(payload)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        pass
