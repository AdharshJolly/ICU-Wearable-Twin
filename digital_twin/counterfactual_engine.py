"\"\"
COUNTERFACTUAL ENGINE
=====================
Given the patient's current vital signs and simulator state,
projects MULTIPLE future trajectories - one per intervention
scenario.

Crucially, this uses the EXACT SAME physiological model as the 
live twin (app.services.pharmacokinetics) to ensure strict
consistency between what-if projections and live interventions.
"\"\"

import copy
import numpy as np

# We import the exact same physiological functions used by the live digital twin
from app.services.pharmacokinetics import apply_pharmacokinetics, decay_medications

INTERVENTIONS = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]
INTERVENTION_META = {
    "none":           {"label": "No Intervention", "color": "#ef4444"},
    "administer_o2":  {"label": "Supplemental O2", "color": "#06b6d4"},
    "beta_blockers":  {"label": "Beta Blocker",    "color": "#a855f7"},
    "o2_and_fluids":  {"label": "O2 + IV Fluids",  "color": "#f59e0b"},
}

class CounterfactualEngine:

    def __init__(self):
        from app.services.risk_service import calculate_risk_forecast
        self.calculate_risk_forecast = calculate_risk_forecast

    def simulate(
        self,
        current_vitals: dict,
        current_state: str,
        n_steps: int = 30,
        scenarios: list[str] | None = None,
    ) -> dict:
        if scenarios is None:
            scenarios = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]

        result = {"steps": list(range(n_steps + 1)), "trajectories": {}}

        # Define baseline for risk calculation
        baseline = {
            'hr': 75, 'rr': 16, 'spo2': 98, 'sbp': 120, 'dbp': 80
        }

        for scenario_key in scenarios:
            if scenario_key not in INTERVENTION_META:
                continue

            meta = INTERVENTION_META[scenario_key]
            
            # Keep rolling history for risk calculation
            history = {
                'hr': [current_vitals['hr']],
                'rr': [current_vitals['rr']],
                'spo2': [current_vitals['spo2']],
                'sbp': [current_vitals['sbp']],
                'dbp': [current_vitals['dbp']]
            }
            
            # Initial Risk
            f = self.calculate_risk_forecast(
                history['hr'], history['rr'], history['spo2'], history['sbp'], history['dbp'], baseline
            )
            risk_over_time = [f.get("risk_probability", 50.0)]
            
            prev = dict(current_vitals)
            
            # Set up active medications for this scenario
            active_medications = {}
            if scenario_key == "beta_blockers":
                active_medications["Beta Blockers"] = 100
            elif scenario_key == "administer_o2":
                active_medications["Supplemental O2"] = 100
            elif scenario_key == "o2_and_fluids":
                active_medications["Supplemental O2"] = 100
                active_medications["IV Fluids"] = 100

            for step in range(n_steps):
                # Apply decay
                active_medications = decay_medications(active_medications)
                
                # Natural Deterioration drift
                drift = 0.5 if current_state in ("DETERIORATING", "CRITICAL", "HIGH_RISK") else 0
                
                nxt = {
                    'hr':   np.clip(prev['hr']   + (drift if step < 10 else 0), 30, 200),
                    'rr':   np.clip(prev['rr'], 4, 50),
                    'spo2': np.clip(prev['spo2'] - (drift*0.2 if step < 10 else 0), 70, 100),
                    'sbp':  np.clip(prev['sbp'], 60, 200),
                    'dbp':  np.clip(prev['dbp'], 30, 130),
                    'temp': prev.get('temp', 36.8)
                }
                
                # Apply strictly unified pharmacological rules
                nxt = apply_pharmacokinetics(nxt, active_medications)

                for k in history:
                    history[k].append(nxt[k])
                    if len(history[k]) > 16:
                        history[k].pop(0)

                f = self.calculate_risk_forecast(
                    history['hr'], history['rr'], history['spo2'], history['sbp'], history['dbp'], baseline
                )
                risk_over_time.append(f.get("risk_probability", 50.0))
                
                prev = nxt

            result["trajectories"][scenario_key] = {
                "label": meta["label"],
                "color": meta["color"],
                "risk":  risk_over_time,
            }

        return result
