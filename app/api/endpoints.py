import sys
import os
import json
import asyncio
import pandas as pd
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

# Import digital_twin tools
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from digital_twin.database import SessionLocal, TelemetryLog, TwinSnapshot
from digital_twin.multi_agent import MultiAgentBoard
from digital_twin.counterfactual_engine import CounterfactualEngine
from digital_twin.llm_agent import ClinicalLLMAgent
from digital_twin.deterioration_simulator import DeteriorationSimulator
from app.services.risk_service import calculate_risk_forecast
from app.schemas.schemas import CounterfactualRequest
from app.services.digital_twin_service import digital_twin_service

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
                "temp": log.temp,
                "sbp": log.sbp,
                "dbp": log.dbp
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
        
        # Priority 19: Use real BP from database instead of fake generation
        sys_data = [log.sbp if log.sbp else 120 for log in logs]
        dia_data = [log.dbp if log.dbp else 80 for log in logs]
        
        # Priority 4: Personalized Baselines (using earliest available log)
        baseline = {
            'hr': hr_data[0] if hr_data else 75,
            'rr': rr_data[0] if rr_data else 16,
            'spo2': spo2_data[0] if spo2_data else 98,
            'sbp': sys_data[0] if sys_data else 120,
            'dbp': dia_data[0] if dia_data else 80
        }
        
        return calculate_risk_forecast(hr_data, rr_data, spo2_data, sys_data, dia_data, baseline=baseline)
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
    
    # Priority 1, 2, 17: Build a real Digital Twin Service!
    initial_vitals = {
        'hr': patient_data['RestingHR'],
        'rr': patient_data['RespRate'],
        'spo2': patient_data['SpO2'],
        'sbp': patient_data['SystolicBP'],
        'dbp': patient_data['DiastolicBP']
    }
    twin = digital_twin_service.get_or_create_twin(patient_id, initial_vitals)
    
    try:
        for i, reading in enumerate(scenario_ticks):
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                data = json.loads(msg)
                if "action" in data:
                    simulator.apply_intervention(data["action"])
            except asyncio.TimeoutError:
                pass
            
            # Extract current vitals
            vitals = {
                'hr': float(reading.get("RestingHR", 75) + (i % 2)),
                'rr': float(reading.get("RespRate", 16) + (i % 2)),
                'temp': float(reading.get("BodyTemp_C", 36.8)),
                'spo2': float(reading.get("SpO2", 98) - (i % 2)),
                'sbp': float(reading.get("SystolicBP", 120)),
                'dbp': float(reading.get("DiastolicBP", 80))
            }
            
            # The Twin orchestrates risk forecasting, memory, hysteresis, and persistence
            snapshot = twin.ingest(vitals, active_medications=reading.get("active_medications", {}))
            
            # Prepare payload for frontend
            payload = {
                "time": snapshot["timestamp"].strftime("%H:%M:%S"),
                "hr": snapshot["hr"],
                "rr": snapshot["rr"],
                "temp": snapshot["temp"],
                "spo2": snapshot["spo2"],
                "sbp": snapshot["sbp"],
                "dbp": snapshot["dbp"],
                "risk_state": snapshot["state"],
                "reasons": snapshot["reasons"],
                "active_medications": snapshot["active_medications"]
            }
            
            # Fire LLM in background
            payload["llm_summary"] = await llm_agent.generate_summary(snapshot["state"], snapshot["reasons"], payload)
            
            # Update the latest log with LLM summary (as it wasn't saved in ingest)
            db = SessionLocal()
            try:
                latest_log = db.query(TelemetryLog).filter(TelemetryLog.patient_id == patient_id).order_by(TelemetryLog.timestamp.desc()).first()
                if latest_log:
                    latest_log.llm_summary = payload["llm_summary"]
                    db.commit()
            except Exception as e:
                pass
            finally:
                db.close()
                
            await websocket.send_json(payload)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        pass
