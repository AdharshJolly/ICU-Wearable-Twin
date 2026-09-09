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

    # --------------------------------------------------------
    # CHECK LITERATURE-SUPPORTED ABNORMAL CONDITIONS
    # --------------------------------------------------------

    def check_abnormality(self, measurement):

        abnormal_reasons = []

        # Heart rate
        if measurement["RestingHR"] > 131:
            abnormal_reasons.append(
                "RestingHR > 131 bpm"
            )

        # Respiratory rate
        if measurement["RespRate"] > 25:
            abnormal_reasons.append(
                "RespRate > 25 breaths/min"
            )

        # Temperature
        if measurement["BodyTemp_C"] >= 38.1:
            abnormal_reasons.append(
                "BodyTemp >= 38.1 C"
            )

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