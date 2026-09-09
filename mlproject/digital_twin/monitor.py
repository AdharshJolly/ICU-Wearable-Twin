# ============================================================
# PATIENT DIGITAL TWIN
# SUSTAINED ABNORMALITY MONITOR
# ============================================================

from datetime import datetime, timedelta

from rule_engine import assess_patient
from state_model import PatientDigitalTwin


class ContinuousMonitor:

    def __init__(self, patient_twin):

        self.twin = patient_twin

        # Stores incoming measurements
        self.measurements = []

        # Stores generated timestamps
        self.timestamps = []

        # Stores rule-engine results
        self.assessments = []

        # Stores alerts
        self.alerts = []


    # --------------------------------------------------------
    # Add a new physiological measurement
    # --------------------------------------------------------

    def process_measurement(
        self,
        measurement,
        timestamp
    ):

        # Run expert rule engine
        assessment = assess_patient(

            systolic_bp=measurement["SystolicBP"],
            diastolic_bp=measurement["DiastolicBP"],
            heart_rate=measurement["RestingHR"],
            resp_rate=measurement["RespRate"],
            temperature=measurement["BodyTemp_C"],
            spo2=measurement["SpO2"],
            resting_ecg=measurement["RestingECG"],
            hrv=measurement["HRV"]
        )


        # Update Digital Twin
        twin_result = self.twin.update(
            assessment
        )


        # Store data
        self.measurements.append(
            measurement
        )

        self.timestamps.append(
            timestamp
        )

        self.assessments.append(
            assessment
        )


        # ----------------------------------------------------
        # Alert generation
        # ----------------------------------------------------

        if assessment["state"] in [
            "HIGH RISK",
            "CRITICAL"
        ]:

            alert = {
                "timestamp": timestamp,
                "patient_id": self.twin.patient_id,
                "state": assessment["state"],
                "risk_score": assessment["risk_score"],
                "reasons": assessment["reasons"]
            }

            self.alerts.append(alert)


        return twin_result


    # --------------------------------------------------------
    # Display monitoring history
    # --------------------------------------------------------

    def display_history(self):

        print("\n==========================================")
        print("CONTINUOUS DIGITAL TWIN MONITORING")
        print("==========================================")

        for i in range(len(self.measurements)):

            print("\n------------------------------------------")

            print(
                "Time:",
                self.timestamps[i]
            )

            print(
                "Risk:",
                self.assessments[i]["risk_score"]
            )

            print(
                "State:",
                self.assessments[i]["state"]
            )


            if self.assessments[i]["reasons"]:

                print("Reasons:")

                for reason in self.assessments[i]["reasons"]:

                    print(" -", reason)

            else:

                print("Reasons: None")


    # --------------------------------------------------------
    # Display alerts
    # --------------------------------------------------------

    def display_alerts(self):

        print("\n==========================================")
        print("ALERT HISTORY")
        print("==========================================")


        if not self.alerts:

            print("No alerts generated.")

            return


        for alert in self.alerts:

            print("\nALERT")

            print(
                "Time:",
                alert["timestamp"]
            )

            print(
                "Patient:",
                alert["patient_id"]
            )

            print(
                "State:",
                alert["state"]
            )

            print(
                "Risk Score:",
                alert["risk_score"]
            )

            print("Reasons:")

            for reason in alert["reasons"]:

                print(" -", reason)


# ============================================================
# SIMULATED WEARABLE STREAM
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Create patient Digital Twin
    # --------------------------------------------------------

    twin = PatientDigitalTwin(

        patient_id="P001",

        age=52,

        gender="Male"
    )


    # --------------------------------------------------------
    # Create continuous monitor
    # --------------------------------------------------------

    monitor = ContinuousMonitor(twin)


    # --------------------------------------------------------
    # Simulated measurements
    #
    # Each record represents a new wearable observation.
    # --------------------------------------------------------

    simulated_data = [

        {
            "SystolicBP": 120,
            "DiastolicBP": 80,
            "RestingHR": 72,
            "RespRate": 16,
            "BodyTemp_C": 36.8,
            "SpO2": 98,
            "RestingECG": 0,
            "HRV": 55
        },

        {
            "SystolicBP": 118,
            "DiastolicBP": 78,
            "RestingHR": 75,
            "RespRate": 17,
            "BodyTemp_C": 36.9,
            "SpO2": 97,
            "RestingECG": 0,
            "HRV": 52
        },

        {
            "SystolicBP": 110,
            "DiastolicBP": 72,
            "RestingHR": 95,
            "RespRate": 21,
            "BodyTemp_C": 37.5,
            "SpO2": 95,
            "RestingECG": 0,
            "HRV": 38
        },

        {
            "SystolicBP": 105,
            "DiastolicBP": 70,
            "RestingHR": 105,
            "RespRate": 23,
            "BodyTemp_C": 38.2,
            "SpO2": 93,
            "RestingECG": 1,
            "HRV": 25
        },

        {
            "SystolicBP": 100,
            "DiastolicBP": 68,
            "RestingHR": 110,
            "RespRate": 24,
            "BodyTemp_C": 38.4,
            "SpO2": 92,
            "RestingECG": 1,
            "HRV": 22
        },

        {
            "SystolicBP": 88,
            "DiastolicBP": 60,
            "RestingHR": 125,
            "RespRate": 31,
            "BodyTemp_C": 39.2,
            "SpO2": 88,
            "RestingECG": 2,
            "HRV": 15
        }
    ]


    # --------------------------------------------------------
    # Start simulated monitoring
    # --------------------------------------------------------

    start_time = datetime.now()


    for i, measurement in enumerate(
        simulated_data
    ):

        timestamp = (
            start_time
            + timedelta(minutes=i * 2)
        )


        result = monitor.process_measurement(

            measurement,

            timestamp
        )


        print("\n==========================================")
        print(
            "MEASUREMENT",
            i + 1
        )
        print("==========================================")

        print(
            "Timestamp:",
            timestamp
        )

        print(
            "Risk Score:",
            result["risk_score"]
        )

        print(
            "State:",
            result["current_state"]
        )


    # --------------------------------------------------------
    # Display complete history
    # --------------------------------------------------------

    monitor.display_history()


    # --------------------------------------------------------
    # Display alerts
    # --------------------------------------------------------

    monitor.display_alerts()


    # --------------------------------------------------------
    # Display final Digital Twin
    # --------------------------------------------------------

    twin.display()