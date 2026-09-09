# ============================================================
# DIGITAL TWIN - INTEGRATED MONITORING PIPELINE
# ============================================================

from datetime import datetime, timedelta
import pandas as pd


class DigitalTwinPipeline:

    def __init__(self, patient_id, age, gender, sustained_minutes=10):

        self.patient_id = patient_id
        self.age = age
        self.gender = gender

        self.sustained_minutes = sustained_minutes

        # Current Digital Twin state
        self.current_state = "STABLE"
        self.current_risk_score = 0

        # Abnormal episode tracking
        self.abnormal_start_time = None
        self.alert_generated = False

        # History
        self.trajectory = []
        
        # Load ML Model
        import os
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), "anomaly_pipeline.pkl")
        if os.path.exists(model_path):
            self.ml_model = joblib.load(model_path)
        else:
            self.ml_model = None

    # --------------------------------------------------------
    # CHECK LITERATURE-SUPPORTED ABNORMAL CONDITIONS
    # --------------------------------------------------------

    def check_abnormality(self, measurement):

        abnormal_reasons = []

        # Heart rate (Refined: Tachycardia / Bradycardia)
        if measurement["RestingHR"] > 110:
            abnormal_reasons.append("RestingHR > 110 bpm (Tachycardia)")
        elif measurement["RestingHR"] < 40:
            abnormal_reasons.append("RestingHR < 40 bpm (Bradycardia)")

        # Respiratory rate (Refined: Tachypnea / Bradypnea)
        if measurement["RespRate"] > 22:
            abnormal_reasons.append("RespRate > 22 breaths/min (Tachypnea)")
        elif measurement["RespRate"] < 8:
            abnormal_reasons.append("RespRate < 8 breaths/min (Bradypnea)")

        # Temperature (Refined: Fever / Hypothermia)
        if measurement["BodyTemp_C"] > 38.0:
            abnormal_reasons.append("BodyTemp > 38.0 C (Fever)")
        elif measurement["BodyTemp_C"] < 36.0:
            abnormal_reasons.append("BodyTemp < 36.0 C (Hypothermia)")

        # SpO2 (Refined: Hypoxia)
        if measurement["SpO2"] < 92:
            abnormal_reasons.append("SpO2 < 92% (Hypoxia)")

        # Blood Pressure (Refined: Hypertension / Hypotension)
        if measurement["SystolicBP"] > 160:
            abnormal_reasons.append("SystolicBP > 160 (Hypertension)")
        elif measurement["SystolicBP"] < 90:
            abnormal_reasons.append("SystolicBP < 90 (Hypotension)")

        # ML Model Anomaly Detection
        if self.ml_model is not None:
            import pandas as pd
            features = [
                "SystolicBP", "DiastolicBP", "RestingHR", 
                "RespRate", "BodyTemp_C", "SpO2", "HRV"
            ]
            # Create a single-row dataframe for prediction
            row = pd.DataFrame([{f: measurement[f] for f in features}])
            prediction = self.ml_model.predict(row)[0]
            
            if prediction == -1:
                abnormal_reasons.append("ML Anomaly Detected")

        return abnormal_reasons

    # --------------------------------------------------------
    # CALCULATE PROJECT RISK SCORE
    # --------------------------------------------------------

    def calculate_risk_score(self, abnormal_reasons):

        number_of_abnormalities = len(abnormal_reasons)

        if number_of_abnormalities == 0:
            return 0

        elif number_of_abnormalities == 1:
            return 1

        elif number_of_abnormalities == 2:
            return 2

        else:
            return 3

    # --------------------------------------------------------
    # DETERMINE DIGITAL TWIN STATE
    # --------------------------------------------------------

    def determine_state(self, risk_score, sustained_alert):

        if sustained_alert:
            return "CRITICAL"

        if risk_score == 3:
            return "HIGH RISK"

        if risk_score == 2:
            return "WATCH"

        if risk_score == 1:
            return "WATCH"

        return "STABLE"

    # --------------------------------------------------------
    # PROCESS ONE MEASUREMENT
    # --------------------------------------------------------

    def process_measurement(self, measurement, timestamp):

        abnormal_reasons = self.check_abnormality(measurement)

        risk_score = self.calculate_risk_score(
            abnormal_reasons
        )

        sustained_alert = False

        # ----------------------------------------------------
        # NO ABNORMALITY
        # ----------------------------------------------------

        if len(abnormal_reasons) == 0:

            self.abnormal_start_time = None
            self.alert_generated = False

        # ----------------------------------------------------
        # ABNORMALITY STARTED
        # ----------------------------------------------------

        else:

            if self.abnormal_start_time is None:

                self.abnormal_start_time = timestamp
                self.alert_generated = False

            # Calculate duration
            duration = (
                timestamp - self.abnormal_start_time
            ).total_seconds() / 60

            # Sustained abnormality
            if duration >= self.sustained_minutes:

                sustained_alert = True

                if not self.alert_generated:

                    self.alert_generated = True

        # ----------------------------------------------------
        # UPDATE DIGITAL TWIN
        # ----------------------------------------------------

        previous_state = self.current_state

        self.current_risk_score = risk_score

        self.current_state = self.determine_state(
            risk_score,
            sustained_alert
        )

        # ----------------------------------------------------
        # ALERT MESSAGE
        # ----------------------------------------------------

        if sustained_alert:

            alert = "CRITICAL ALERT - SUSTAINED ABNORMALITY"

        elif len(abnormal_reasons) > 0:

            alert = "WARNING - ABNORMAL VITAL SIGN"

        else:

            alert = "NO ALERT"

        # ----------------------------------------------------
        # STORE TRAJECTORY
        # ----------------------------------------------------

        record = {

            "Patient_ID": self.patient_id,

            "Timestamp": timestamp,

            "Age": self.age,

            "Gender": self.gender,

            "SystolicBP": measurement["SystolicBP"],

            "DiastolicBP": measurement["DiastolicBP"],

            "RestingHR": measurement["RestingHR"],

            "RespRate": measurement["RespRate"],

            "BodyTemp_C": measurement["BodyTemp_C"],

            "SpO2": measurement["SpO2"],

            "RestingECG": measurement["RestingECG"],

            "HRV": measurement["HRV"],

            "Risk_Score": risk_score,

            "Previous_State": previous_state,

            "Current_State": self.current_state,

            "Abnormality_Duration_Min": (
                0
                if self.abnormal_start_time is None
                else round(
                    (
                        timestamp -
                        self.abnormal_start_time
                    ).total_seconds() / 60,
                    2
                )
            ),

            "Alert": alert,

            "Reasons": "; ".join(abnormal_reasons)
        }

        self.trajectory.append(record)

        return record

    # --------------------------------------------------------
    # GET COMPLETE RISK TRAJECTORY
    # --------------------------------------------------------

    def get_trajectory(self):

        return pd.DataFrame(self.trajectory)