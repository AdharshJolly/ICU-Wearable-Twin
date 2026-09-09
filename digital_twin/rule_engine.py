# ============================================================
# PATIENT DIGITAL TWIN
# EXPERT RULE-BASED DETERIORATION ENGINE
# ============================================================


# ------------------------------------------------------------
# Respiratory Rules
# ------------------------------------------------------------

def respiratory_rules(spo2, resp_rate):

    score = 0
    reasons = []

    # SpO2 assessment
    if spo2 < 90:
        score += 3
        reasons.append("Severely low SpO2")

    elif spo2 < 94:
        score += 2
        reasons.append("Low SpO2")

    elif spo2 < 96:
        score += 1
        reasons.append("Mildly reduced SpO2")


    # Respiratory rate assessment
    if resp_rate >= 30:
        score += 3
        reasons.append("Very high respiratory rate")

    elif resp_rate >= 22:
        score += 2
        reasons.append("High respiratory rate")

    elif resp_rate > 20:
        score += 1
        reasons.append("Elevated respiratory rate")


    return score, reasons


# ------------------------------------------------------------
# Cardiovascular Rules
# ------------------------------------------------------------

def cardiovascular_rules(
    systolic_bp,
    diastolic_bp,
    heart_rate,
    resting_ecg,
    hrv
):

    score = 0
    reasons = []


    # Blood pressure
    if systolic_bp < 90:
        score += 3
        reasons.append("Low systolic blood pressure")

    elif systolic_bp < 100:
        score += 2
        reasons.append("Reduced systolic blood pressure")


    # Heart rate
    if heart_rate >= 120:
        score += 3
        reasons.append("Very high heart rate")

    elif heart_rate >= 100:
        score += 2
        reasons.append("High heart rate")

    elif heart_rate > 90:
        score += 1
        reasons.append("Elevated heart rate")


    # ECG
    if resting_ecg != 0:
        score += 2
        reasons.append("Abnormal resting ECG")


    # HRV
    if hrv < 20:
        score += 2
        reasons.append("Very low HRV")

    elif hrv < 30:
        score += 1
        reasons.append("Reduced HRV")


    return score, reasons


# ------------------------------------------------------------
# Temperature / Systemic Rules
# ------------------------------------------------------------

def systemic_rules(
    temperature,
    heart_rate,
    resp_rate
):

    score = 0
    reasons = []


    # Temperature
    if temperature >= 39:
        score += 3
        reasons.append("High body temperature")

    elif temperature >= 38:
        score += 2
        reasons.append("Elevated body temperature")

    elif temperature < 35:
        score += 3
        reasons.append("Low body temperature")


    # Combination: temperature + HR
    if temperature >= 38 and heart_rate >= 100:
        score += 1
        reasons.append(
            "Elevated temperature with high heart rate"
        )


    # Combination: temperature + RR
    if temperature >= 38 and resp_rate >= 22:
        score += 1
        reasons.append(
            "Elevated temperature with high respiratory rate"
        )


    return score, reasons


# ------------------------------------------------------------
# Overall Deterioration Assessment
# ------------------------------------------------------------

def assess_patient(
    systolic_bp,
    diastolic_bp,
    heart_rate,
    resp_rate,
    temperature,
    spo2,
    resting_ecg,
    hrv
):

    respiratory_score, respiratory_reasons = respiratory_rules(
        spo2,
        resp_rate
    )

    cardiovascular_score, cardiovascular_reasons = (
        cardiovascular_rules(
            systolic_bp,
            diastolic_bp,
            heart_rate,
            resting_ecg,
            hrv
        )
    )

    systemic_score, systemic_reasons = systemic_rules(
        temperature,
        heart_rate,
        resp_rate
    )


    # --------------------------------------------------------
    # Total Risk Score
    # --------------------------------------------------------

    total_score = (
        respiratory_score
        + cardiovascular_score
        + systemic_score
    )


    # --------------------------------------------------------
    # Determine Patient State
    # --------------------------------------------------------

    if total_score >= 9:

        state = "CRITICAL"

    elif total_score >= 6:

        state = "HIGH RISK"

    elif total_score >= 3:

        state = "WATCH"

    else:

        state = "STABLE"


    # --------------------------------------------------------
    # Combine Explanations
    # --------------------------------------------------------

    reasons = (
        respiratory_reasons
        + cardiovascular_reasons
        + systemic_reasons
    )


    return {
        "risk_score": total_score,
        "state": state,
        "reasons": reasons,
        "respiratory_score": respiratory_score,
        "cardiovascular_score": cardiovascular_score,
        "systemic_score": systemic_score
    }


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

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

    print("\n======================================")
    print("PATIENT DIGITAL TWIN")
    print("EXPERT RULE ENGINE")
    print("======================================")

    print("Risk Score :", result["risk_score"])
    print("Patient State :", result["state"])

    print("\nReasons:")

    if result["reasons"]:

        for reason in result["reasons"]:
            print("-", reason)

    else:

        print("- No significant abnormalities detected")

    print("\nSystem Scores:")
    print(
        "Respiratory   :",
        result["respiratory_score"]
    )

    print(
        "Cardiovascular:",
        result["cardiovascular_score"]
    )

    print(
        "Systemic      :",
        result["systemic_score"]
    )