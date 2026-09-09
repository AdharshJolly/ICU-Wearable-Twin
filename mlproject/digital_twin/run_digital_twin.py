# ============================================================
# PATIENT DIGITAL TWIN
# INTEGRATED SIMULATION + MONITORING
# ============================================================

import pandas as pd
from datetime import datetime, timedelta

from deterioration_simulator import DeteriorationSimulator
from pipeline import DigitalTwinPipeline


# ============================================================
# 1. DATASET PATH
# ============================================================

dataset_path = (
    r"C:\Users\abelw\Documents\College"
    r"\Project\mlproject\dataset"
    r"\Heart Disease Dataset .csv"
)


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("\n==============================================")
print("          PATIENT DIGITAL TWIN")
print("==============================================")

df = pd.read_csv(dataset_path)

print("\nDataset loaded successfully.")
print("Total patients:", len(df))


# ============================================================
# 3. SELECT PATIENT
# ============================================================

patient = df.iloc[0]

patient_id = patient["Patient_ID"]
age = patient["Age"]
gender = patient["Gender"]


print("\n----------------------------------------------")
print("PATIENT INFORMATION")
print("----------------------------------------------")

print("Patient ID :", patient_id)
print("Age        :", age)
print("Gender     :", gender)


# ============================================================
# 4. CREATE DETERIORATION SIMULATOR
# ============================================================

simulator = DeteriorationSimulator(patient)


# ============================================================
# 5. GENERATE SIMULATED VITAL STREAM
# ============================================================

readings = simulator.generate_scenario()

print("\n----------------------------------------------")
print("SIMULATION")
print("----------------------------------------------")

print(
    "Generated readings:",
    len(readings)
)

print(
    "Reading interval : 2 minutes"
)


# ============================================================
# 6. CREATE DIGITAL TWIN
# ============================================================

digital_twin = DigitalTwinPipeline(
    patient_id=patient_id,
    age=age,
    gender=gender,
    sustained_minutes=10
)


# ============================================================
# 7. START SIMULATED TIME
# ============================================================

start_time = datetime.now()


# ============================================================
# 8. PROCESS EACH READING
# ============================================================

print("\n==============================================")
print("          DIGITAL TWIN MONITOR")
print("==============================================")


for i, measurement in enumerate(readings):

    # Each simulated reading occurs every 2 minutes
    timestamp = start_time + timedelta(
        minutes=i * 2
    )

    result = digital_twin.process_measurement(
        measurement,
        timestamp
    )

    print("\n----------------------------------------------")
    print(
        f"READING {i + 1}/{len(readings)}"
    )
    print("----------------------------------------------")

    print(
        "Time             :",
        timestamp.strftime("%H:%M:%S")
    )

    print(
        "Heart Rate       :",
        round(measurement["RestingHR"], 2),
        "bpm"
    )

    print(
        "Respiratory Rate :",
        round(measurement["RespRate"], 2),
        "breaths/min"
    )

    print(
        "Temperature      :",
        round(measurement["BodyTemp_C"], 2),
        "C"
    )

    print(
        "SpO2             :",
        round(measurement["SpO2"], 2),
        "%"
    )

    print(
        "Systolic BP      :",
        round(measurement["SystolicBP"], 2)
    )

    print(
        "Diastolic BP     :",
        round(measurement["DiastolicBP"], 2)
    )

    print(
        "Resting ECG      :",
        measurement["RestingECG"]
    )

    print(
        "HRV              :",
        round(measurement["HRV"], 2)
    )

    print(
        "Risk Score       :",
        result["Risk_Score"]
    )

    print(
        "Previous State   :",
        result["Previous_State"]
    )

    print(
        "Current State    :",
        result["Current_State"]
    )

    print(
        "Abnormal Duration:",
        result["Abnormality_Duration_Min"],
        "minutes"
    )

    print(
        "Alert            :",
        result["Alert"]
    )

    if result["Reasons"]:

        print(
            "Reason           :",
            result["Reasons"]
        )


# ============================================================
# 9. GET FINAL RISK TRAJECTORY
# ============================================================

trajectory = digital_twin.get_trajectory()


# ============================================================
# 10. DISPLAY RISK TRAJECTORY
# ============================================================

print("\n\n==============================================")
print("             RISK TRAJECTORY")
print("==============================================")

print()

print(
    trajectory[
        [
            "Timestamp",
            "RestingHR",
            "RespRate",
            "BodyTemp_C",
            "Risk_Score",
            "Previous_State",
            "Current_State",
            "Abnormality_Duration_Min",
            "Alert"
        ]
    ].to_string(index=False)
)


# ============================================================
# 11. SAVE COMPLETE TRAJECTORY
# ============================================================

output_file = "risk_trajectory.csv"

trajectory.to_csv(
    output_file,
    index=False
)


# ============================================================
# 12. FINAL SUMMARY
# ============================================================

print("\n==============================================")
print("             FINAL SUMMARY")
print("==============================================")

print(
    "Patient ID       :",
    patient_id
)

print(
    "Total readings   :",
    len(trajectory)
)

print(
    "Final risk score :",
    trajectory.iloc[-1]["Risk_Score"]
)

print(
    "Final state      :",
    trajectory.iloc[-1]["Current_State"]
)

print(
    "Final alert      :",
    trajectory.iloc[-1]["Alert"]
)

print(
    "\nRisk trajectory saved to:",
    output_file
)

print("\n==============================================")
print("        DIGITAL TWIN EXECUTION COMPLETE")
print("==============================================")