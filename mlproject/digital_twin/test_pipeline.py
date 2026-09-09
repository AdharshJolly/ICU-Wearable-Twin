# ============================================================
# TEST DIGITAL TWIN PIPELINE
# ============================================================

from datetime import datetime, timedelta

from pipeline import DigitalTwinPipeline


# ------------------------------------------------------------
# CREATE DIGITAL TWIN
# ------------------------------------------------------------

twin = DigitalTwinPipeline(
    patient_id="P001",
    age=52,
    gender="Male",
    sustained_minutes=10
)


# ------------------------------------------------------------
# SIMULATED WEARABLE DATA
# ------------------------------------------------------------

measurements = [

    {
        "SystolicBP": 120,
        "DiastolicBP": 80,
        "RestingHR": 82,
        "RespRate": 18,
        "BodyTemp_C": 36.8,
        "SpO2": 98,
        "RestingECG": 0,
        "HRV": 55
    },

    {
        "SystolicBP": 121,
        "DiastolicBP": 81,
        "RestingHR": 90,
        "RespRate": 19,
        "BodyTemp_C": 37.0,
        "SpO2": 98,
        "RestingECG": 0,
        "HRV": 52
    },

    {
        "SystolicBP": 125,
        "DiastolicBP": 82,
        "RestingHR": 135,
        "RespRate": 27,
        "BodyTemp_C": 38.2,
        "SpO2": 96,
        "RestingECG": 1,
        "HRV": 40
    },

    {
        "SystolicBP": 126,
        "DiastolicBP": 83,
        "RestingHR": 138,
        "RespRate": 28,
        "BodyTemp_C": 38.3,
        "SpO2": 95,
        "RestingECG": 1,
        "HRV": 38
    },

    {
        "SystolicBP": 128,
        "DiastolicBP": 84,
        "RestingHR": 140,
        "RespRate": 29,
        "BodyTemp_C": 38.4,
        "SpO2": 94,
        "RestingECG": 1,
        "HRV": 36
    },

    {
        "SystolicBP": 130,
        "DiastolicBP": 85,
        "RestingHR": 142,
        "RespRate": 30,
        "BodyTemp_C": 38.5,
        "SpO2": 93,
        "RestingECG": 2,
        "HRV": 34
    },

    {
        "SystolicBP": 132,
        "DiastolicBP": 86,
        "RestingHR": 145,
        "RespRate": 31,
        "BodyTemp_C": 38.6,
        "SpO2": 92,
        "RestingECG": 2,
        "HRV": 31
    },

    {
        "SystolicBP": 135,
        "DiastolicBP": 88,
        "RestingHR": 148,
        "RespRate": 32,
        "BodyTemp_C": 38.7,
        "SpO2": 91,
        "RestingECG": 2,
        "HRV": 28
    }
]


# ------------------------------------------------------------
# START TIME
# ------------------------------------------------------------

start_time = datetime.now()


# ------------------------------------------------------------
# PROCESS EACH READING
# ------------------------------------------------------------

for i, measurement in enumerate(measurements):

    timestamp = start_time + timedelta(
        minutes=i * 2
    )

    result = twin.process_measurement(
        measurement,
        timestamp
    )

    print("\n========================================")
    print("PATIENT ID :", result["Patient_ID"])
    print("TIME       :", result["Timestamp"])
    print("RISK SCORE :", result["Risk_Score"])
    print("STATE      :", result["Current_State"])
    print("DURATION   :", result["Abnormality_Duration_Min"])
    print("ALERT      :", result["Alert"])
    print("REASONS    :", result["Reasons"])


# ------------------------------------------------------------
# DISPLAY COMPLETE TRAJECTORY
# ------------------------------------------------------------

trajectory = twin.get_trajectory()

print("\n\n========================================")
print("COMPLETE PATIENT RISK TRAJECTORY")
print("========================================")

print(
    trajectory[
        [
            "Timestamp",
            "RestingHR",
            "RespRate",
            "BodyTemp_C",
            "Risk_Score",
            "Current_State",
            "Alert"
        ]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# SAVE TRAJECTORY
# ------------------------------------------------------------

trajectory.to_csv(
    "risk_trajectory.csv",
    index=False
)

print("\nRisk trajectory saved as:")
print("risk_trajectory.csv")