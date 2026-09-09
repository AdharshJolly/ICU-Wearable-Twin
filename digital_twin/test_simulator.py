# ============================================================
# TEST PATIENT DATA SIMULATOR
# ============================================================

from simulator import PatientDataSimulator


import os

# ------------------------------------------------------------
# DATASET LOCATION
# ------------------------------------------------------------

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(base_dir, "dataset", "Heart Disease Dataset .csv")


# ------------------------------------------------------------
# CREATE SIMULATOR
# ------------------------------------------------------------

simulator = PatientDataSimulator(
    dataset_path
)


# ------------------------------------------------------------
# SELECT PATIENT
# ------------------------------------------------------------

patient_id = simulator.data.iloc[0]["Patient_ID"]


print("\n========================================")
print("PATIENT DATA SIMULATOR")
print("========================================")

print("Selected Patient:", patient_id)


# ------------------------------------------------------------
# GENERATE SENSOR STREAM
# ------------------------------------------------------------

stream = simulator.generate_stream(
    patient_id=patient_id,
    number_of_readings=10,
    variation=True
)


# ------------------------------------------------------------
# DISPLAY STREAM
# ------------------------------------------------------------

for i, measurement in enumerate(stream, start=1):

    print("\n----------------------------------------")
    print("Reading:", i)

    for key, value in measurement.items():

        print(
            f"{key:15}: {value:.2f}"
        )