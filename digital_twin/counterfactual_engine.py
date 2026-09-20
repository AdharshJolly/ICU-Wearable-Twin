"""
COUNTERFACTUAL ENGINE
=====================
Given the patient's current vital signs and simulator state,
projects MULTIPLE future trajectories — one per intervention
scenario — so the UI can show:

  Risk without intervention:   ─────────────────→ 91%
  Risk with Beta Blocker:      ──────╲──────────→ 58%
  Risk with O2 + Fluids:       ────────╲─────────→ 43%

This makes "Digital Twin" academically defensible:
the system isn't just monitoring, it's simulating
counterfactual clinical outcomes.
"""

import copy
import random
import numpy as np
import joblib
import os
import torch
import torch.nn as nn

MODEL_DIR = os.path.dirname(__file__)

# 1. Define the Neural Network Architecture for the Learned Dynamics
class DynamicsNN(nn.Module):
    def __init__(self, input_dim=9, hidden_dim=64, output_dim=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    def forward(self, x):
        return self.net(x)

INTERVENTIONS = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]
INTERVENTION_META = {
    "none":           {"label": "No Intervention", "color": "#ef4444"},
    "administer_o2":  {"label": "Supplemental O2", "color": "#06b6d4"},
    "beta_blockers":  {"label": "Beta Blocker",    "color": "#a855f7"},
    "o2_and_fluids":  {"label": "O2 + IV Fluids",  "color": "#f59e0b"},
}

class CounterfactualEngine:

    def __init__(self):
        # We will use the centralized risk service for risk predictions
        from app.services.risk_service import calculate_risk_forecast
        self.calculate_risk_forecast = calculate_risk_forecast
        
        # Load the newly trained Learned Dynamics Model
        model_path  = os.path.join(MODEL_DIR, "learned_dynamics_model.pth")
        scaler_path = os.path.join(MODEL_DIR, "dynamics_scaler.pkl")
        
        try:
            self.dynamics_model = DynamicsNN()
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
            self.dynamics_model.load_state_dict(checkpoint['state_dict'])
            self.dynamics_model.eval()
            self.dynamics_scaler = joblib.load(scaler_path)
            self.enabled = True
        except Exception as e:
            print(f"Learned Dynamics load error: {e}")
            self.enabled = False

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
            
            # One-hot encode the intervention
            action_idx = INTERVENTIONS.index(scenario_key) if scenario_key in INTERVENTIONS else 0
            action_vec = [1.0 if i == action_idx else 0.0 for i in range(len(INTERVENTIONS))]

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

            for step in range(n_steps):
                if self.enabled:
                    
                    current_state_vec = [prev['hr'], prev['rr'], prev['spo2'], prev['sbp'], prev['dbp']]
                    x_input = np.array([current_state_vec + action_vec], dtype=np.float32)
                    x_scaled = self.dynamics_scaler.transform(x_input)
                    x_tensor = torch.tensor(x_scaled)
                    
                    with torch.no_grad():
                        delta = self.dynamics_model(x_tensor).numpy()[0]
                    
                    # Next state = Current state + Model's predicted Delta + Natural Deterioration drift
                    drift = 0.5 if current_state in ("DETERIORATING", "CRITICAL", "HIGH_RISK") else 0
                    
                    nxt = {
                        'hr':   np.clip(prev['hr']   + delta[0] + (drift if step < 10 else 0), 30, 200),
                        'rr':   np.clip(prev['rr']   + delta[1], 4, 50),
                        'spo2': np.clip(prev['spo2'] + delta[2] - (drift*0.2 if step < 10 else 0), 70, 100),
                        'sbp':  np.clip(prev['sbp']  + delta[3], 60, 200),
                        'dbp':  np.clip(prev['dbp']  + delta[4], 30, 130),
                    }
                else:
                    nxt = dict(prev)

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
