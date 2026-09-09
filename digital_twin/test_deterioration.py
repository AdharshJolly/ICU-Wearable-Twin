# ============================================================
# TEST CONTROLLED DETERIORATION SIMULATOR
# ============================================================

import pandas as pd

from deterioration_simulator import DeteriorationSimulator


import os

# ------------------------------------------------------------
# LOAD DATASET
# ------------------------------------------------------------

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(base_dir, "dataset", "Heart Disease Dataset .csv")

df = pd.read_csv(dataset_path)


# ------------------------------------------------------------
# SELECT FIRST PATIENT
# ------------------------------------------------------------

patient = df.iloc[0]

print("\n========================================")
print("CONTROLLED DETERIORATION SIMULATION")
print("========================================")

print("Patient ID:", patient["Patient_ID"])


# ------------------------------------------------------------
# CREATE SIMULATOR
# ------------------------------------------------------------

simulator = DeteriorationSimulator(patient)


# ------------------------------------------------------------
# GENERATE SCENARIO
# ------------------------------------------------------------

readings = simulator.generate_scenario()


# ------------------------------------------------------------
# DISPLAY READINGS
# ------------------------------------------------------------

for i, reading in enumerate(readings, start=1):

    print("\n----------------------------------------")
    print("Reading:", i)

    print(
        "Systolic BP :", round(reading["SystolicBP"], 2)
    )

    print(
        "Diastolic BP:", round(reading["DiastolicBP"], 2)
    )

    print(
        "Heart Rate  :", round(reading["RestingHR"], 2)
    )

    print(
        "Resp Rate   :", round(reading["RespRate"], 2)
    )

    print(
        "Temperature :", round(reading["BodyTemp_C"], 2)
    )

    print(
        "SpO2        :", round(reading["SpO2"], 2)
    )

    print(
        "Resting ECG :", reading["RestingECG"]
    )

    print(
        "HRV         :", round(reading["HRV"], 2)
    )