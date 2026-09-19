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

MODEL_DIR = os.path.dirname(__file__)

# Intervention physics: delta applied per timestep, with decay
INTERVENTION_EFFECTS = {
    "none": {
        "label": "No Intervention",
        "color": "#ef4444",
        "hr_delta": 0.0,
        "spo2_delta": 0.0,
        "rr_delta": 0.0,
        "sbp_delta": 0.0,
        "dbp_delta": 0.0,
        "decay": 1.0,          # no decay needed
    },
    "administer_o2": {
        "label": "Supplemental O2",
        "color": "#06b6d4",
        "hr_delta": -3.0,
        "spo2_delta": +5.0,
        "rr_delta": -2.5,
        "sbp_delta": +2.0,
        "dbp_delta": +1.0,
        "decay": 0.88,          # fast dissipation
    },
    "beta_blockers": {
        "label": "Beta Blocker (Metoprolol)",
        "color": "#a855f7",
        "hr_delta": -22.0,
        "spo2_delta": +1.0,
        "rr_delta": -1.0,
        "sbp_delta": -12.0,
        "dbp_delta": -8.0,
        "decay": 0.97,          # slow wash-out
    },
    "fluids": {
        "label": "IV Fluids (Saline 30ml/kg)",
        "color": "#22c55e",
        "hr_delta": -10.0,
        "spo2_delta": +1.5,
        "rr_delta": -0.5,
        "sbp_delta": +15.0,
        "dbp_delta": +8.0,
        "decay": 0.99,
    },
    "o2_and_fluids": {
        "label": "O2 + IV Fluids (Bundle)",
        "color": "#f59e0b",
        "hr_delta": -12.0,
        "spo2_delta": +6.0,
        "rr_delta": -3.0,
        "sbp_delta": +14.0,
        "dbp_delta": +7.0,
        "decay": 0.93,
    },
}

# Feature engineering matches Phase 1 training exactly
def _engineer_features(vitals_history: list[dict]) -> np.ndarray:
    """
    Takes a list of vital-sign dicts (each tick), 
    returns the 25-feature vector the XGBoost model expects.
    """
    df = {
        'hr':  [v.get('hr',  75) for v in vitals_history],
        'rr':  [v.get('rr',  16) for v in vitals_history],
        'spo2':[v.get('spo2',98) for v in vitals_history],
        'sbp': [v.get('sbp',120) for v in vitals_history],
        'dbp': [v.get('dbp', 80) for v in vitals_history],
    }

    feats = []
    for key, vals in df.items():
        arr = np.array(vals, dtype=float)
        feats.extend([
            arr.mean(), arr.min(), arr.max(),
            arr.std() if len(arr) > 1 else 0.0,
            float(arr[-1] - arr[0]) if len(arr) > 1 else 0.0,  # slope proxy
        ])
    return np.array(feats).reshape(1, -1)


class CounterfactualEngine:

    def __init__(self):
        model_path   = os.path.join(MODEL_DIR, "predictive_icu_model.pkl")
        scaler_path  = os.path.join(MODEL_DIR, "icu_scaler.pkl")

        self.model  = joblib.load(model_path)  if os.path.exists(model_path)  else None
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        self.enabled = self.model is not None

    def _predict_risk(self, vitals_window: list[dict]) -> float:
        """Predict a risk probability from a window of vitals."""
        if not self.enabled:
            return 0.5
        try:
            X = _engineer_features(vitals_window)
            if self.scaler:
                # Scaler was trained on 25 features (5 vitals × 5 stats)
                # Our feature vector length must match
                if X.shape[1] == self.scaler.n_features_in_:
                    X = self.scaler.transform(X)
            return float(self.model.predict_proba(X)[0, 1])
        except Exception:
            return 0.5

    def simulate(
        self,
        current_vitals: dict,
        current_state: str,
        n_steps: int = 30,
        scenarios: list[str] | None = None,
    ) -> dict:
        """
        Projects n_steps into the future for each scenario.

        current_vitals: dict with keys hr, rr, spo2, sbp, dbp
        current_state:  'STABLE' | 'DETERIORATING' | 'CRITICAL' etc.
        n_steps:        number of future ticks (each ~2 seconds in the sim)
        scenarios:      list of intervention keys to simulate

        Returns:
        {
          "steps": [0, 1, ... n_steps],
          "trajectories": {
            "none":           { "label": ..., "color": ..., "risk": [...] },
            "beta_blockers":  { ... },
            ...
          }
        }
        """
        if scenarios is None:
            scenarios = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]

        # Determine the underlying physiological drift direction
        is_deteriorating = current_state in ("DETERIORATING", "CRITICAL", "HIGH_RISK")
        drift = {
            'hr':   +0.8  if is_deteriorating else -0.1,
            'rr':   +0.4  if is_deteriorating else -0.05,
            'spo2': -0.3  if is_deteriorating else +0.05,
            'sbp':  -0.6  if is_deteriorating else +0.1,
            'dbp':  -0.4  if is_deteriorating else +0.05,
        }

        result = {"steps": list(range(n_steps + 1)), "trajectories": {}}

        for scenario_key in scenarios:
            if scenario_key not in INTERVENTION_EFFECTS:
                continue

            fx = INTERVENTION_EFFECTS[scenario_key]
            vitals_window = [dict(current_vitals)]

            # Carry the intervention effect, decaying each step
            effect_remaining = {
                'hr':   fx['hr_delta'],
                'spo2': fx['spo2_delta'],
                'rr':   fx['rr_delta'],
                'sbp':  fx['sbp_delta'],
                'dbp':  fx['dbp_delta'],
            }
            decay = fx['decay']

            risk_over_time = [self._predict_risk(vitals_window)]
            prev = dict(current_vitals)

            for _ in range(n_steps):
                noise = lambda s=1.5: random.gauss(0, s)
                nxt = {
                    'hr':   np.clip(prev['hr']   + drift['hr']   + effect_remaining['hr']   + noise(1.5), 30, 200),
                    'rr':   np.clip(prev['rr']   + drift['rr']   + effect_remaining['rr']   + noise(0.5), 4,  50),
                    'spo2': np.clip(prev['spo2'] + drift['spo2'] + effect_remaining['spo2'] + noise(0.3), 70, 100),
                    'sbp':  np.clip(prev['sbp']  + drift['sbp']  + effect_remaining['sbp']  + noise(2.0), 60, 200),
                    'dbp':  np.clip(prev['dbp']  + drift['dbp']  + effect_remaining['dbp']  + noise(1.5), 30, 130),
                }
                vitals_window.append(nxt)
                if len(vitals_window) > 16:
                    vitals_window.pop(0)

                risk_over_time.append(self._predict_risk(vitals_window))

                # Decay the intervention effect
                for k in effect_remaining:
                    effect_remaining[k] *= decay

                prev = nxt

            result["trajectories"][scenario_key] = {
                "label": fx["label"],
                "color": fx["color"],
                "risk":  [round(r * 100, 1) for r in risk_over_time],
            }

        return result
