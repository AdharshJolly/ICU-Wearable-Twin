def apply_pharmacokinetics(vitals: dict, active_medications: dict) -> dict:
    """
    Applies deterministic physiological effects based on active medications.
    This serves as the single source of truth for both live twin ingest and counterfactual simulation.
    """
    v = dict(vitals)
    
    if "Beta Blockers" in active_medications:
        intensity = active_medications["Beta Blockers"] / 100.0
        v["hr"] = max(40, v["hr"] - (15 * intensity))
        v["sbp"] = max(80, v["sbp"] - (20 * intensity))
        v["dbp"] = max(50, v["dbp"] - (10 * intensity))
        
    if "IV Fluids" in active_medications:
        intensity = active_medications["IV Fluids"] / 100.0
        v["sbp"] = min(180, v["sbp"] + (25 * intensity))
        v["dbp"] = min(110, v["dbp"] + (15 * intensity))
        v["hr"] = max(50, v["hr"] - (5 * intensity))
        
    if "Supplemental O2" in active_medications:
        intensity = active_medications["Supplemental O2"] / 100.0
        v["spo2"] = min(100, v["spo2"] + (8 * intensity))
        
    return v

def decay_medications(active_medications: dict) -> dict:
    decay_rates = {
        "Beta Blockers": 5,
        "IV Fluids": 8,
        "Supplemental O2": 10
    }
    new_meds = dict(active_medications)
    expired = []
    for med, level in new_meds.items():
        rate = decay_rates.get(med, 5)
        new_meds[med] = max(0, level - rate)
        if new_meds[med] == 0:
            expired.append(med)
    for med in expired:
        del new_meds[med]
    return new_meds
