
# ============================================================
# PATIENT DIGITAL TWIN
# STATE MODEL
# ============================================================

class PatientDigitalTwin:

    def __init__(self, patient_id, age, gender):

        self.patient_id = patient_id
        self.age = age
        self.gender = gender

        # Current physiological state
        self.current_state = "STABLE"

        # Current risk score
        self.current_risk_score = 0

        # Previous state
        self.previous_state = "STABLE"

        # History of states
        self.state_history = []

        # History of risk scores
        self.risk_history = []


    # --------------------------------------------------------
    # Update Digital Twin
    # --------------------------------------------------------

    def update(self, assessment):

        self.previous_state = self.current_state

        self.current_state = assessment["state"]

        self.current_risk_score = assessment["risk_score"]


        # Store history
        self.state_history.append(
            self.current_state
        )

        self.risk_history.append(
            self.current_risk_score
        )


        # Determine whether state changed
        state_changed = (
            self.previous_state
            != self.current_state
        )


        return {
            "patient_id": self.patient_id,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "risk_score": self.current_risk_score,
            "state_changed": state_changed,
            "reasons": assessment["reasons"]
        }


    # --------------------------------------------------------
    # Display Current Digital Twin
    # --------------------------------------------------------

    def display(self):

        print("\n======================================")
        print("PATIENT DIGITAL TWIN")
        print("======================================")

        print("Patient ID :", self.patient_id)
        print("Age        :", self.age)
        print("Gender     :", self.gender)

        print("\nCurrent State :", self.current_state)
        print("Risk Score    :", self.current_risk_score)

        print("\nState History:")

        for i, state in enumerate(
            self.state_history,
            start=1
        ):

            print(
                f"Measurement {i}: {state}"
            )

        print("\nRisk History:")

        for i, score in enumerate(
            self.risk_history,
            start=1
        ):

            print(
                f"Measurement {i}: {score}"
            )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from rule_engine import assess_patient


    # Create Digital Twin
    twin = PatientDigitalTwin(
        patient_id="P001",
        age=52,
        gender="Male"
    )


    # --------------------------------------------------------
    # Measurement 1
    # --------------------------------------------------------

    result = assess_patient(

        systolic_bp=120,
        diastolic_bp=80,
        heart_rate=72,
        resp_rate=16,
        temperature=36.8,
        spo2=98,
        resting_ecg=0,
        hrv=55
    )

    update_result = twin.update(result)

    print("\nMeasurement 1")
    print(update_result)


    # --------------------------------------------------------
    # Measurement 2
    # --------------------------------------------------------

    result = assess_patient(

        systolic_bp=105,
        diastolic_bp=70,
        heart_rate=105,
        resp_rate=23,
        temperature=38.2,
        spo2=93,
        resting_ecg=1,
        hrv=25
    )

    update_result = twin.update(result)

    print("\nMeasurement 2")
    print(update_result)


    # --------------------------------------------------------
    # Measurement 3
    # --------------------------------------------------------

    result = assess_patient(

        systolic_bp=88,
        diastolic_bp=60,
        heart_rate=125,
        resp_rate=31,
        temperature=39.2,
        spo2=88,
        resting_ecg=2,
        hrv=15
    )

    update_result = twin.update(result)

    print("\nMeasurement 3")
    print(update_result)


    # Display Digital Twin
    twin.display()
