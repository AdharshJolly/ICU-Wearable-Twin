import os
import json
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

MODEL_DIR = os.path.dirname(__file__)

def train_meta_learner():
    print("Training Phase 4: Meta-Learner (Ensemble Stacking)...")
    
    # In a full production pipeline, we would load the Out-Of-Fold (OOF) 
    # predictions from the Phase 1 (XGB) and Phase 2 (LSTM) cross-validation.
    # For this architecture demo, we simulate a validation set of model probabilities
    # where the LSTM is slightly more performant on temporal patterns.
    
    np.random.seed(42)
    n_samples = 2000
    
    # True labels (1 = deterioration, 0 = stable)
    y_val = np.random.binomial(1, 0.15, n_samples)
    
    # Simulate XGB probabilities (AUROC ~ 0.75)
    xgb_probs = np.clip(y_val * np.random.beta(5, 2, n_samples) + 
                        (1 - y_val) * np.random.beta(2, 5, n_samples), 0, 1)
                        
    # Simulate LSTM probabilities (AUROC ~ 0.80)
    lstm_probs = np.clip(y_val * np.random.beta(6, 2, n_samples) + 
                         (1 - y_val) * np.random.beta(2, 6, n_samples), 0, 1)
                         
    X_val = np.column_stack((xgb_probs, lstm_probs))
    
    # Test baselines
    print(f"XGBoost-only AUROC:  {roc_auc_score(y_val, xgb_probs):.3f}")
    print(f"LSTM-only AUROC:     {roc_auc_score(y_val, lstm_probs):.3f}")
    
    naive_ensemble = (xgb_probs * 0.5) + (lstm_probs * 0.5)
    print(f"50/50 Naive AUROC:   {roc_auc_score(y_val, naive_ensemble):.3f}")
    
    # Train Logistic Meta-Learner
    meta_model = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs')
    meta_model.fit(X_val, y_val)
    
    stacked_probs = meta_model.predict_proba(X_val)[:, 1]
    stacked_auroc = roc_auc_score(y_val, stacked_probs)
    stacked_brier = brier_score_loss(y_val, stacked_probs)
    print(f"Stacked Meta AUROC:  {stacked_auroc:.3f}")
    
    # Extract Weights
    coefs = meta_model.coef_[0]
    total = np.sum(coefs)
    xgb_weight = coefs[0] / total
    lstm_weight = coefs[1] / total
    
    print(f"\nLearned Ensemble Weights:")
    print(f"XGBoost Weight: {xgb_weight:.2%}")
    print(f"LSTM Weight:    {lstm_weight:.2%}")
    
    # Save Model Artifacts
    meta_path = os.path.join(MODEL_DIR, "ensemble_meta.pkl")
    metadata_path = os.path.join(MODEL_DIR, "ensemble_metadata.json")
    
    joblib.dump(meta_model, meta_path)
    
    metadata = {
        "model_version": "ensemble_v3_stacked",
        "trained_at": "2026-09-20",
        "xgb_weight": float(xgb_weight),
        "lstm_weight": float(lstm_weight),
        "calibration_brier_score": float(stacked_brier),
        "meta_model_type": "LogisticRegression"
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\nSaved Meta-Learner to {meta_path}")
    print(f"Saved Metadata to {metadata_path}")

if __name__ == "__main__":
    train_meta_learner()
