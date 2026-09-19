# ============================================================
# CONTROLLED PATIENT DETERIORATION & RECOVERY SIMULATOR
# ============================================================

class DeteriorationSimulator:

    def __init__(self, patient):

        self.patient = patient
        
        # Track active interventions applied by the user
        self.interventions = {
            "hr_modifier": 0.0,
            "spo2_modifier": 0.0,
            "rr_modifier": 0.0,
        }
        self.active_medications = {} # { drug_name: { "concentration": 100.0, "half_life": 0.95 } }

    def apply_intervention(self, action):
        """Called via WebSocket from the frontend"""
        if action == "administer_o2":
            self.interventions["spo2_modifier"] += 4.0
            self.interventions["rr_modifier"] -= 3.0
            # Oxygen dissipates extremely quickly in the blood (Short half-life)
            self.active_medications["Supplemental O2"] = {"concentration": 100.0, "decay_rate": 0.85}
        elif action == "beta_blockers":
            self.interventions["hr_modifier"] -= 25.0
            # Metoprolol has a moderate half-life
            self.active_medications["Beta Blocker (Metoprolol)"] = {"concentration": 100.0, "decay_rate": 0.97}
        elif action == "fluids":
            self.interventions["hr_modifier"] -= 10.0
            # IV fluids slowly absorb into tissue
            self.active_medications["IV Fluids (Saline)"] = {"concentration": 100.0, "decay_rate": 0.99}
            
    def _apply_modifiers(self, reading):
        """Apply active interventions and naturally decay them over time"""
        reading["RestingHR"] += self.interventions["hr_modifier"]
        reading["SpO2"] += self.interventions["spo2_modifier"]
        reading["RespRate"] += self.interventions["rr_modifier"]
        
        # Decay interventions relative to their drugs
        self.interventions["hr_modifier"] *= 0.96
        self.interventions["spo2_modifier"] *= 0.90
        self.interventions["rr_modifier"] *= 0.90
        
        # Explicit Pharmacokinetic Exponential Decay tracking
        meds_to_remove = []
        ui_medications = {}
        for med, data in self.active_medications.items():
            # Exponential decay calculation: C(t) = C(t-1) * decay_rate
            data["concentration"] *= data["decay_rate"]
            ui_medications[med] = round(data["concentration"], 1)
            
            if data["concentration"] < 1.0:
                meds_to_remove.append(med)
                
        for med in meds_to_remove:
            del self.active_medications[med]
            
        reading["active_medications"] = ui_medications
        
        # Clamp SpO2 to realistic max
        if reading["SpO2"] > 100:
            reading["SpO2"] = 100.0
            
        return reading

    # --------------------------------------------------------
    # STABLE STATE
    # --------------------------------------------------------

    def stable_reading(self):

        reading = {
            "SystolicBP": self.patient["SystolicBP"],
            "DiastolicBP": self.patient["DiastolicBP"],
            "RestingHR": self.patient["RestingHR"],
            "RespRate": self.patient["RespRate"],
            "BodyTemp_C": self.patient["BodyTemp_C"],
            "SpO2": self.patient["SpO2"],
            "RestingECG": self.patient["RestingECG"],
            "HRV": self.patient["HRV"]
        }
        return self._apply_modifiers(reading)

    # --------------------------------------------------------
    # DETERIORATION STATE
    # --------------------------------------------------------

    def deterioration_reading(self, level):

        # Get base stable reading (without modifiers yet)
        reading = {
            "SystolicBP": self.patient["SystolicBP"],
            "DiastolicBP": self.patient["DiastolicBP"],
            "RestingHR": self.patient["RestingHR"],
            "RespRate": self.patient["RespRate"],
            "BodyTemp_C": self.patient["BodyTemp_C"],
            "SpO2": self.patient["SpO2"],
            "RestingECG": self.patient["RestingECG"],
            "HRV": self.patient["HRV"]
        }
        
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

        return self._apply_modifiers(reading)

    # --------------------------------------------------------
    # RECOVERY STATE
    # --------------------------------------------------------

    def recovery_reading(self, level):

        # Get base stable reading
        reading = {
            "SystolicBP": self.patient["SystolicBP"],
            "DiastolicBP": self.patient["DiastolicBP"],
            "RestingHR": self.patient["RestingHR"],
            "RespRate": self.patient["RespRate"],
            "BodyTemp_C": self.patient["BodyTemp_C"],
            "SpO2": self.patient["SpO2"],
            "RestingECG": self.patient["RestingECG"],
            "HRV": self.patient["HRV"]
        }
        
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
            reading["RestingHR"] += 0 + noise_hr
            reading["RespRate"] += 0 + noise_rr
            reading["BodyTemp_C"] += 0 + noise_temp

        return self._apply_modifiers(reading)

    # --------------------------------------------------------
    # GENERATE COMPLETE SCENARIO
    # --------------------------------------------------------

    def generate_scenario(self):
        readings = []

        # ----------------------------------------------------
        # PHASE 1: STABLE (60 seconds)
        # ----------------------------------------------------
        for _ in range(60):
            readings.append(self.stable_reading())

        # ----------------------------------------------------
        # PHASE 2: EARLY DETERIORATION (30 seconds)
        # ----------------------------------------------------
        for _ in range(30):
            readings.append(self.deterioration_reading(1))

        # ----------------------------------------------------
        # PHASE 3: HIGHER DETERIORATION (30 seconds)
        # ----------------------------------------------------
        for _ in range(30):
            readings.append(self.deterioration_reading(2))

        # ----------------------------------------------------
        # PHASE 4: SEVERE / CRITICAL (30 seconds)
        # ----------------------------------------------------
        for _ in range(30):
            readings.append(self.deterioration_reading(3))
            
        return readings