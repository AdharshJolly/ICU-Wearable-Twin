import json
from datetime import datetime
from app.services.risk_service import calculate_risk_forecast
from digital_twin.database import SessionLocal, TelemetryLog, TwinSnapshot

class PatientDigitalTwin:
    def __init__(self, patient_id: str, baseline: dict):
        self.patient_id = patient_id
        self.baseline = baseline
        self.history = {
            'hr': [], 'rr': [], 'spo2': [], 'sbp': [], 'dbp': []
        }
        self.current_state = "STABLE"
        self.consecutive_state_ticks = 0
        self.last_risk = 0.0

    def ingest(self, vitals: dict, active_medications: dict = None):
        """
        Ingest a new set of vitals, update memory, calculate risk, 
        and run the state machine.
        vitals must contain: hr, rr, spo2, sbp, dbp, temp
        """
        # Update rolling memory
        for k in ['hr', 'rr', 'spo2', 'sbp', 'dbp']:
            self.history[k].append(vitals[k])
            if len(self.history[k]) > 16:
                self.history[k].pop(0)

        # 1. Risk Forecasting (Only if we have enough history)
        forecast = None
        if len(self.history['hr']) >= 2:
            forecast = calculate_risk_forecast(
                self.history['hr'], self.history['rr'], 
                self.history['spo2'], self.history['sbp'], 
                self.history['dbp'], baseline=self.baseline
            )

        # 2. Dynamic State Machine with Hysteresis (Priority 14)
        reasons = ["Vitals within normal limits"]
        confidence = "HIGH"
        risk_prob = self.last_risk

        if forecast and "error" not in forecast:
            risk_prob = forecast["risk_probability"]
            self.last_risk = risk_prob
            confidence = forecast.get("confidence", "HIGH")
            
            # Determine target state
            if risk_prob < 30:
                target_state = "STABLE"
            elif risk_prob < 50:
                target_state = "WATCH"
            elif risk_prob < 70:
                target_state = "ELEVATED"
            elif risk_prob < 85:
                target_state = "HIGH_RISK"
            else:
                target_state = "CRITICAL"
            
            # Hysteresis logic
            if target_state == self.current_state:
                self.consecutive_state_ticks += 1
            else:
                self.consecutive_state_ticks = 0
                
            # Wait for 3 consecutive ticks in the new state to prevent flickering
            if self.consecutive_state_ticks >= 2: 
                self.current_state = target_state
                
            # Extract SHAP factors as reasons
            if risk_prob >= 30 and forecast.get("top_factors"):
                reasons = [f["description"] for f in forecast["top_factors"][:2]]

        # 3. Create TwinSnapshot
        snapshot = {
            "patient_id": self.patient_id,
            "timestamp": datetime.now(),
            "hr": vitals.get('hr'),
            "rr": vitals.get('rr'),
            "spo2": vitals.get('spo2'),
            "sbp": vitals.get('sbp'),
            "dbp": vitals.get('dbp'),
            "temp": vitals.get('temp'),
            "risk_probability": risk_prob,
            "state": self.current_state,
            "confidence": confidence,
            "top_factors": forecast.get("top_factors", []) if forecast else [],
            "reasons": reasons,
            "active_medications": active_medications or {}
        }
        
        # 4. Save to DB
        self._persist(snapshot, vitals)
        
        return snapshot
        
    def _persist(self, snapshot: dict, vitals: dict):
        db = SessionLocal()
        try:
            # Save raw telemetry
            log = TelemetryLog(
                patient_id=self.patient_id,
                hr=vitals['hr'], rr=vitals['rr'],
                spo2=vitals['spo2'], temp=vitals['temp'],
                sbp=vitals['sbp'], dbp=vitals['dbp'],
                risk_state=snapshot['state']
            )
            db.add(log)
            
            # Save Twin Snapshot
            twin_snap = TwinSnapshot(
                patient_id=self.patient_id,
                hr=vitals['hr'], rr=vitals['rr'],
                spo2=vitals['spo2'], temp=vitals['temp'],
                sbp=vitals['sbp'], dbp=vitals['dbp'],
                risk_probability=snapshot['risk_probability'],
                state=snapshot['state'],
                confidence=snapshot['confidence'],
                top_factors=json.dumps(snapshot['top_factors']),
                baseline=json.dumps(self.baseline)
            )
            db.add(twin_snap)
            db.commit()
        except Exception as e:
            print(f"Twin DB Error: {e}")
        finally:
            db.close()


class DigitalTwinService:
    def __init__(self):
        self.active_twins = {}

    def get_or_create_twin(self, patient_id: str, initial_vitals: dict) -> PatientDigitalTwin:
        if patient_id not in self.active_twins:
            # The initial_vitals become the patient's baseline
            baseline = {
                'hr': initial_vitals.get('hr', 75),
                'rr': initial_vitals.get('rr', 16),
                'spo2': initial_vitals.get('spo2', 98),
                'sbp': initial_vitals.get('sbp', 120),
                'dbp': initial_vitals.get('dbp', 80)
            }
            self.active_twins[patient_id] = PatientDigitalTwin(patient_id, baseline)
        return self.active_twins[patient_id]

digital_twin_service = DigitalTwinService()
