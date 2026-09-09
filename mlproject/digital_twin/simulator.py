# ============================================================
# PATIENT DATA SIMULATOR
# Software-only replacement for wearable sensors
# ============================================================

import pandas as pd
import random


class PatientDataSimulator:

    def __init__(self, csv_file):

        self.csv_file = csv_file

        self.data = pd.read_csv(csv_file)

        self.required_columns = [
            "Patient_ID",
            "Age",
            "Gender",
            "SystolicBP",
            "DiastolicBP",
            "RestingHR",
            "RespRate",
            "BodyTemp_C",
            "SpO2",
            "RestingECG",
            "HRV"
        ]

        # Check required columns
        missing_columns = [
            column
            for column in self.required_columns
            if column not in self.data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing columns: {missing_columns}"
            )

    # --------------------------------------------------------
    # GET PATIENT
    # --------------------------------------------------------

    def get_patient(self, patient_id):

        patient = self.data[
            self.data["Patient_ID"] == patient_id
        ]

        if patient.empty:
            raise ValueError(
                f"Patient {patient_id} not found."
            )

        return patient.iloc[0]

    # --------------------------------------------------------
    # CREATE ONE MEASUREMENT
    # --------------------------------------------------------

    def create_measurement(self, patient):

        measurement = {

            "SystolicBP": float(
                patient["SystolicBP"]
            ),

            "DiastolicBP": float(
                patient["DiastolicBP"]
            ),

            "RestingHR": float(
                patient["RestingHR"]
            ),

            "RespRate": float(
                patient["RespRate"]
            ),

            "BodyTemp_C": float(
                patient["BodyTemp_C"]
            ),

            "SpO2": float(
                patient["SpO2"]
            ),

            "RestingECG": float(
                patient["RestingECG"]
            ),

            "HRV": float(
                patient["HRV"]
            )
        }

        return measurement

    # --------------------------------------------------------
    # SIMULATE SENSOR NOISE
    # --------------------------------------------------------

    def add_sensor_variation(
        self,
        measurement,
        variation=True
    ):

        if not variation:
            return measurement

        measurement["SystolicBP"] += random.uniform(
            -2, 2
        )

        measurement["DiastolicBP"] += random.uniform(
            -2, 2
        )

        measurement["RestingHR"] += random.uniform(
            -2, 2
        )

        measurement["RespRate"] += random.uniform(
            -1, 1
        )

        measurement["BodyTemp_C"] += random.uniform(
            -0.1, 0.1
        )

        measurement["SpO2"] += random.uniform(
            -0.5, 0.5
        )

        measurement["HRV"] += random.uniform(
            -2, 2
        )

        return measurement

    # --------------------------------------------------------
    # GENERATE CONTINUOUS STREAM
    # --------------------------------------------------------

    def generate_stream(
        self,
        patient_id,
        number_of_readings=10,
        variation=True
    ):

        patient = self.get_patient(patient_id)

        stream = []

        for _ in range(number_of_readings):

            measurement = self.create_measurement(
                patient
            )

            measurement = self.add_sensor_variation(
                measurement,
                variation
            )

            stream.append(measurement)

        return stream