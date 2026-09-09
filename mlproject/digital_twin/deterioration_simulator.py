# ============================================================
# CONTROLLED PATIENT DETERIORATION & RECOVERY SIMULATOR
# ============================================================

class DeteriorationSimulator:

    def __init__(self, patient):

        self.patient = patient

    # --------------------------------------------------------
    # STABLE STATE
    # --------------------------------------------------------

    def stable_reading(self):

        return {
            "SystolicBP": self.patient["SystolicBP"],
            "DiastolicBP": self.patient["DiastolicBP"],
            "RestingHR": self.patient["RestingHR"],
            "RespRate": self.patient["RespRate"],
            "BodyTemp_C": self.patient["BodyTemp_C"],
            "SpO2": self.patient["SpO2"],
            "RestingECG": self.patient["RestingECG"],
            "HRV": self.patient["HRV"]
        }

    # --------------------------------------------------------
    # DETERIORATION STATE
    # --------------------------------------------------------

    def deterioration_reading(self, level):

        reading = self.stable_reading()

        # Gradual deterioration
        if level == 1:

            reading["RestingHR"] += 15
            reading["RespRate"] += 3
            reading["BodyTemp_C"] += 0.5

        elif level == 2:

            reading["RestingHR"] += 30
            reading["RespRate"] += 7
            reading["BodyTemp_C"] += 1.0

        elif level == 3:

            reading["RestingHR"] += 45
            reading["RespRate"] += 12
            reading["BodyTemp_C"] += 1.5

        return reading

    # --------------------------------------------------------
    # RECOVERY STATE
    # --------------------------------------------------------

    def recovery_reading(self, level):

        reading = self.stable_reading()

        # Gradual recovery from deterioration
        if level == 1:

            reading["RestingHR"] += 30
            reading["RespRate"] += 7
            reading["BodyTemp_C"] += 1.0

        elif level == 2:

            reading["RestingHR"] += 15
            reading["RespRate"] += 3
            reading["BodyTemp_C"] += 0.5

        elif level == 3:

            # Almost completely recovered
            pass

        return reading

    # --------------------------------------------------------
    # GENERATE COMPLETE SCENARIO
    # --------------------------------------------------------

    def generate_scenario(self):

        readings = []

        # ----------------------------------------------------
        # PHASE 1: STABLE
        # ----------------------------------------------------

        for _ in range(3):

            readings.append(
                self.stable_reading()
            )

        # ----------------------------------------------------
        # PHASE 2: EARLY DETERIORATION
        # ----------------------------------------------------

        readings.append(
            self.deterioration_reading(1)
        )

        # ----------------------------------------------------
        # PHASE 3: HIGHER DETERIORATION
        # ----------------------------------------------------

        readings.append(
            self.deterioration_reading(2)
        )

        # ----------------------------------------------------
        # PHASE 4: SEVERE / SUSTAINED ABNORMALITY
        # ----------------------------------------------------

        readings.append(
            self.deterioration_reading(3)
        )

        readings.append(
            self.deterioration_reading(3)
        )

        readings.append(
            self.deterioration_reading(3)
        )

        # ----------------------------------------------------
        # PHASE 5: RECOVERY
        # ----------------------------------------------------

        readings.append(
            self.recovery_reading(1)
        )

        readings.append(
            self.recovery_reading(2)
        )

        readings.append(
            self.recovery_reading(3)
        )

        return readings