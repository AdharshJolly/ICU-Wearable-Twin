import pandas as pd
import numpy as np
import torch
from app.services.model_manager import model_manager

def engineer_xgb_features(hr_data, rr_data, spo2_data, sys_data, dia_data, baseline):
    df_vitals = {
        'hr': hr_data,
        'rr': rr_data,
        'spo2': spo2_data,
        'sbp': sys_data,
        'dbp': dia_data
    }
    feats = []
    feature_names = []
    for key, vals in df_vitals.items():
        arr = np.array(vals, dtype=float)
        b = baseline.get(key, arr[0])
        mean_val = float(arr.mean())
        max_val = float(arr.max())
        feats.extend([
            mean_val, float(arr.min()), max_val,
            float(arr.std()) if len(arr) > 1 else 0.0,
            b,
            mean_val - b,
            max_val - b,
            float(arr[-1] - arr[0]) if len(arr) > 1 else 0.0
        ])
        feature_names.extend([
            f"{key}_mean", f"{key}_min", f"{key}_max", f"{key}_std", 
            f"{key}_baseline", f"{key}_delta_mean", f"{key}_delta_max", f"{key}_slope"
        ])
    return pd.DataFrame([feats], columns=feature_names), feature_names

def calculate_risk_forecast(hr_data, rr_data, spo2_data, sys_data, dia_data, baseline=None):
    if baseline is None:
        baseline = {
            'hr': hr_data[0] if hr_data else 75,
            'rr': rr_data[0] if rr_data else 16,
            'spo2': spo2_data[0] if spo2_data else 98,
            'sbp': sys_data[0] if sys_data else 120,
            'dbp': dia_data[0] if dia_data else 80
        }
        
    if not model_manager.predictive_model or not model_manager.shap_explainer:
        return {"error": "Predictive model not loaded."}
        
    X, feature_names = engineer_xgb_features(hr_data, rr_data, spo2_data, sys_data, dia_data, baseline)
    
    if model_manager.icu_scaler is not None:
        X_scaled = model_manager.icu_scaler.transform(X)
    else:
        X_scaled = X.values
        
    xgb_prob = float(model_manager.predictive_model.predict_proba(X_scaled)[0, 1]) * 100.0
    
    lstm_prob = xgb_prob
    if model_manager.lstm_model is not None and model_manager.lstm_scaler is not None and len(hr_data) >= 10:
        seq_raw = []
        for i in range(-10, 0):
            seq_raw.append([hr_data[i], rr_data[i], spo2_data[i], sys_data[i], dia_data[i]])
            
        seq_scaled = model_manager.lstm_scaler.transform(np.array(seq_raw))
        x_tensor = torch.tensor([seq_scaled], dtype=torch.float32)
        with torch.no_grad():
            lstm_prob = float(model_manager.lstm_model(x_tensor).item()) * 100.0
    
    # Priority 9: Stacking Meta-Learner for Ensemble Weights
    if model_manager.ensemble_meta_model is not None:
        # Scale to 0-1 for the meta-learner input
        x_meta = np.array([[xgb_prob / 100.0, lstm_prob / 100.0]])
        # Get stacked probability
        ensembled_prob = float(model_manager.ensemble_meta_model.predict_proba(x_meta)[0, 1]) * 100.0
        # Compute disagreement for UI alerts
        disagreement = abs(lstm_prob - xgb_prob) / 100.0
    else:
        # Fallback to hardcoded if meta-learner is missing
        ensembled_prob = (lstm_prob * 0.6) + (xgb_prob * 0.4)
        disagreement = abs(lstm_prob - xgb_prob) / 100.0
    if disagreement > 0.3:
        confidence = "LOW"
        alert_msg = "High model disagreement detected. Manual review recommended."
    elif disagreement > 0.15:
        confidence = "MODERATE"
        alert_msg = "Moderate model variance."
    else:
        confidence = "HIGH"
        alert_msg = "Models are in strong agreement."
        
    try:
        shap_values = model_manager.shap_explainer.shap_values(X_scaled)[0]
        contributions = sorted(zip(feature_names, shap_values), key=lambda x: abs(x[1]), reverse=True)
        top_factors = []
        for feat, val in contributions[:3]:
            impact = "increased" if val > 0 else "decreased"
            feat_val = round(X[feat].iloc[0], 2)
            top_factors.append({
                "feature": feat,
                "value": feat_val,
                "shap_impact": round(float(val), 3),
                "description": f"{feat} ({round(feat_val, 1)}) {impact} risk"
            })
    except Exception:
        top_factors = []
        
    return {
        "risk_probability": round(ensembled_prob, 1),
        "xgboost_prob": round(xgb_prob, 1),
        "lstm_prob": round(lstm_prob, 1),
        "confidence": confidence,
        "uncertainty_alert": alert_msg,
        "disagreement_score": round(disagreement * 100, 1),
        "top_factors": top_factors
    }
