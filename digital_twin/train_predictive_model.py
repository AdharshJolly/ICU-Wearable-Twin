import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib
import os
import shap

print("Generating synthetic temporal ICU dataset...")
np.random.seed(42)

n_patients = 5000
features_list = []
labels = []

for i in range(n_patients):
    is_crashing = np.random.rand() < 0.2 # 20% of patients crash
    
    # Base vitals
    base_hr = np.random.normal(75, 10)
    base_spo2 = np.random.normal(98, 1)
    base_rr = np.random.normal(16, 2)
    base_sys = np.random.normal(120, 15)
    
    # Trends over a 4-hour window (sampled every 15 mins = 16 steps)
    steps = 16
    if is_crashing:
        # HR rises, SpO2 drops, RR rises, BP drops
        hr_trend = np.linspace(base_hr, base_hr + np.random.uniform(20, 50), steps) + np.random.normal(0, 2, steps)
        spo2_trend = np.linspace(base_spo2, base_spo2 - np.random.uniform(5, 12), steps) + np.random.normal(0, 1, steps)
        rr_trend = np.linspace(base_rr, base_rr + np.random.uniform(5, 15), steps) + np.random.normal(0, 1, steps)
        sys_trend = np.linspace(base_sys, base_sys - np.random.uniform(15, 40), steps) + np.random.normal(0, 3, steps)
    else:
        # Stable
        hr_trend = base_hr + np.random.normal(0, 3, steps)
        spo2_trend = base_spo2 + np.random.normal(0, 1, steps)
        rr_trend = base_rr + np.random.normal(0, 1, steps)
        sys_trend = base_sys + np.random.normal(0, 5, steps)
        
    # Feature Engineering for the model
    features = {
        'HR_mean': np.mean(hr_trend),
        'HR_max': np.max(hr_trend),
        'HR_trend': hr_trend[-1] - hr_trend[0],
        'SpO2_mean': np.mean(spo2_trend),
        'SpO2_min': np.min(spo2_trend),
        'SpO2_trend': spo2_trend[-1] - spo2_trend[0],
        'RR_mean': np.mean(rr_trend),
        'RR_max': np.max(rr_trend),
        'RR_trend': rr_trend[-1] - rr_trend[0],
        'SysBP_mean': np.mean(sys_trend),
        'SysBP_min': np.min(sys_trend),
        'SysBP_trend': sys_trend[-1] - sys_trend[0],
        'Age': np.random.randint(40, 90)
    }
    
    features_list.append(features)
    labels.append(1 if is_crashing else 0)

df = pd.DataFrame(features_list)
y = np.array(labels)

X_train, X_test, y_train, y_test = train_test_split(df, y, test_size=0.2, random_state=42)

print("Training XGBoost Predictive Model...")
model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.05,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]

print("\n--- Model Evaluation ---")
print(f"ROC-AUC Score: {roc_auc_score(y_test, probs):.4f}")
print(classification_report(y_test, preds))

# Save the model
model_path = os.path.join(os.path.dirname(__file__), "predictive_icu_model.pkl")
joblib.dump(model, model_path)
print(f"Model saved to {model_path}")

# Generate SHAP baseline explainer and save it
print("Initializing SHAP Explainer...")
explainer = shap.TreeExplainer(model)
explainer_path = os.path.join(os.path.dirname(__file__), "shap_explainer.pkl")
joblib.dump(explainer, explainer_path)
print(f"SHAP Explainer saved to {explainer_path}")

print("ML Pipeline Phase 1 Complete!")
