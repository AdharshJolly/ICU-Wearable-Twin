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
        
        # Add slight biological noise
        import random
        noise_hr = random.gauss(0, 2)
        noise_rr = random.gauss(0, 1)
        noise_temp = random.gauss(0, 0.1)

        # Gradual deterioration
        if level == 1:
            reading["RestingHR"] += 15 + noise_hr
            reading["RespRate"] += 3 + noise_rr
            reading["BodyTemp_C"] += 0.5 + noise_temp

        elif level == 2:
            reading["RestingHR"] += 30 + noise_hr
            reading["RespRate"] += 7 + noise_rr
            reading["BodyTemp_C"] += 1.0 + noise_temp

        elif level == 3:
            reading["RestingHR"] += 45 + noise_hr
            reading["RespRate"] += 12 + noise_rr
            reading["BodyTemp_C"] += 1.5 + noise_temp

        return reading

    # --------------------------------------------------------
    # RECOVERY STATE
    # --------------------------------------------------------

    def recovery_reading(self, level):

        reading = self.stable_reading()
        
        # Add slight biological noise
        import random
        noise_hr = random.gauss(0, 2)
        noise_rr = random.gauss(0, 1)
        noise_temp = random.gauss(0, 0.1)

        # Gradual recovery from deterioration
        if level == 1:
            reading["RestingHR"] += 30 + noise_hr
            reading["RespRate"] += 7 + noise_rr
            reading["BodyTemp_C"] += 1.0 + noise_temp

        elif level == 2:
            reading["RestingHR"] += 15 + noise_hr
            reading["RespRate"] += 3 + noise_rr
            reading["BodyTemp_C"] += 0.5 + noise_temp

        elif level == 3:
            # Almost completely recovered, just noise
            reading["RestingHR"] += noise_hr
            reading["RespRate"] += noise_rr
            reading["BodyTemp_C"] += noise_temp

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