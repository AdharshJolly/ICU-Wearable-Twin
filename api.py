import os
import sys
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add digital_twin to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'digital_twin'))
from digital_twin.deterioration_simulator import DeteriorationSimulator
from digital_twin.pipeline import DigitalTwinPipeline
from digital_twin.llm_agent import ClinicalLLMAgent
from digital_twin.database import SessionLocal, TelemetryLog
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
                    "risk_state": risk_state,
                    "reasons": reasons
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
