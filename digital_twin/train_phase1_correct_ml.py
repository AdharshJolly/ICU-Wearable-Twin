"""

=======================
Implements the full methodological fix stack:






"""

import os, sys, warnings, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    roc_auc_score, average_precision_score, classification_report,
    roc_curve, precision_recall_curve, brier_score_loss, auc,
    f1_score, recall_score, precision_score
)
import joblib
warnings.filterwarnings('ignore')

BASE = os.path.join(os.path.dirname(__file__), "..", "dataset",
                    "mimic_demo", "mimic-iv-clinical-database-demo-2.2")
OUT  = os.path.dirname(__file__)

# ============================================================
# STEP 1 — Build real outcome labels from MIMIC-IV
# ============================================================
print("=" * 62)
print("STEP 1  Build real outcome labels from MIMIC-IV")
print("=" * 62)

stays = pd.read_csv(os.path.join(BASE, "icu", "icustays.csv.gz"))
pts   = pd.read_csv(os.path.join(BASE, "hosp", "patients.csv.gz"))
stays = stays.merge(pts[['subject_id','dod']], on='subject_id', how='left')

stays['intime']  = pd.to_datetime(stays['intime'])
stays['outtime'] = pd.to_datetime(stays['outtime'])
stays['dod']     = pd.to_datetime(stays['dod'])

days_to_death = (stays['dod'] - stays['outtime']).dt.days
stays['died_within_30d'] = stays['dod'].notna() & (days_to_death.fillna(999) < 30)
stays['prolonged_los']   = stays['los'] > 5                  # clinically severe
stays['label']           = (stays['died_within_30d'] | stays['prolonged_los']).astype(int)

print(f"  Total ICU stays : {len(stays)}")
print(f"  Unique patients : {stays['subject_id'].nunique()}")
print(f"  Deterioration   : {stays['label'].sum()} / {len(stays)} ({stays['label'].mean()*100:.1f}%)")

# ============================================================
# STEP 2 — Build temporal features from chartevents
# ============================================================
print("\n" + "=" * 62)
print("STEP 2  Extract and engineer temporal features from MIMIC-IV")
print("=" * 62)

# Vital sign item IDs
VITALS = {
    220045: 'hr',
    220210: 'rr',
    220277: 'spo2',
    220179: 'sbp',
    220180: 'dbp',
}

charts = pd.read_csv(
    os.path.join(BASE, "icu", "chartevents.csv.gz"),
    usecols=['subject_id', 'stay_id', 'itemid', 'charttime', 'valuenum']
)
charts = charts[charts['itemid'].isin(VITALS)].dropna(subset=['valuenum'])
charts['name'] = charts['itemid'].map(VITALS)
charts['charttime'] = pd.to_datetime(charts['charttime'])

print(f"  Loaded {len(charts):,} vital sign observations")

# For each ICU stay, extract observations in the FIRST 4 HOURS (observation window)
# and use the outcome label from stays table.
# This directly implements the temporal prediction task:
#   "Given first 4h of vitals, predict deterioration during the stay"

feature_rows = []
group_ids    = []   # for GroupKFold — each unique patient is a group

for _, stay in stays.iterrows():
    sid      = stay['stay_id']
    subj     = stay['subject_id']
    label    = stay['label']
    intime   = stay['intime']
    window_end = intime + pd.Timedelta(hours=4)

    stay_charts = charts[
        (charts['stay_id'] == sid) &
        (charts['charttime'] >= intime) &
        (charts['charttime'] <= window_end)
    ]

    if stay_charts.empty:
        continue

    feats = {'stay_id': sid, 'subject_id': subj, 'label': label}
    for vital_name in VITALS.values():
        v_sorted = stay_charts.loc[stay_charts['name'] == vital_name].sort_values('charttime')
        if len(v_sorted) == 0:
            feats = None
            break
            
        v = v_sorted['valuenum']
        
        baseline = v.iloc[:3].mean() if len(v) >= 3 else v.iloc[0]
        
        feats[f'{vital_name}_mean'] = v.mean()
        feats[f'{vital_name}_min']  = v.min()
        feats[f'{vital_name}_max']  = v.max()
        feats[f'{vital_name}_std']  = v.std() if len(v) > 1 else 0.0
        
        # New Personalized Delta features
        feats[f'{vital_name}_baseline'] = baseline
        feats[f'{vital_name}_delta_mean'] = v.mean() - baseline
        feats[f'{vital_name}_delta_max'] = v.max() - baseline
        
        if len(v_sorted) > 1:
            dt_hours = (v_sorted['charttime'].iloc[-1] - v_sorted['charttime'].iloc[0]).total_seconds() / 3600
            feats[f'{vital_name}_slope'] = (v_sorted['valuenum'].iloc[-1] - v_sorted['valuenum'].iloc[0]) / max(dt_hours, 0.01)
        else:
            feats[f'{vital_name}_slope'] = 0.0

    if feats is None:
        continue

    feature_rows.append(feats)
    group_ids.append(subj)

df = pd.DataFrame(feature_rows).dropna()
groups = np.array([g for g, row in zip(group_ids, feature_rows) if not any(pd.isna(v) for v in row.values())])

# Align
valid_idx = df.index
groups = np.array(group_ids)[: len(df)]

print(f"  Usable ICU stays after feature extraction : {len(df)}")
print(f"  Unique patients in usable set             : {df['subject_id'].nunique()}")
print(f"  Label distribution: 0={( df['label']==0).sum()}  1={(df['label']==1).sum()}")

FEATURE_COLS = [c for c in df.columns if c not in ('stay_id','subject_id','label')]
X_all = df[FEATURE_COLS].values
y_all = df['label'].values
groups_all = df['subject_id'].values   # patient-level groups for GroupKFold

# ============================================================
# STEP 3 — Patient-level GroupKFold evaluation
# (same patient NEVER appears in both train and test)
# ============================================================
print("\n" + "=" * 62)
print("STEP 3  Patient-level 5-fold GroupKFold evaluation")
print("=" * 62)
print("  NOTE: The scaler will be fit only on the training fold")
print("        to prevent ANY information from leaking into test.")

N_SPLITS = 5
gkf = GroupKFold(n_splits=N_SPLITS)

results = {
    'logistic_regression': [],
    'xgboost': [],
}

fold_scalers = []   # save the per-fold scalers

for fold, (train_idx, test_idx) in enumerate(gkf.split(X_all, y_all, groups=groups_all)):
    X_train_raw, X_test_raw = X_all[train_idx], X_all[test_idx]
    y_train, y_test         = y_all[train_idx],  y_all[test_idx]

    # --- 
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)   # fit + transform on train
    X_test  = scaler.transform(X_test_raw)         # transform only on test

    fold_scalers.append(scaler)

    # --- 
    lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    lr.fit(X_train, y_train)
    lr_probs = lr.predict_proba(X_test)[:, 1]

    # --- XGBoost ---
    xgb_model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / max((y_train == 1).sum(), 1),  # handle imbalance natively
        eval_metric='logloss', random_state=42, verbosity=0
    )
    xgb_model.fit(X_train, y_train)
    xgb_probs = xgb_model.predict_proba(X_test)[:, 1]

    for name, probs in [('logistic_regression', lr_probs), ('xgboost', xgb_probs)]:
        if len(np.unique(y_test)) < 2:
            continue  # skip fold if only one class in test (can happen with small dataset)
        preds = (probs >= 0.5).astype(int)
        results[name].append({
            'fold': fold + 1,
            'auroc':       roc_auc_score(y_test, probs),
            'auprc':       average_precision_score(y_test, probs),
            'sensitivity': recall_score(y_test, preds, zero_division=0),
            'specificity': recall_score(1 - y_test, 1 - preds, zero_division=0),
            'f1':          f1_score(y_test, preds, zero_division=0),
            'brier':       brier_score_loss(y_test, probs),
        })

    print(f"  Fold {fold+1}: train={len(train_idx)} test={len(test_idx)} "
          f"| LR AUROC={results['logistic_regression'][-1]['auroc']:.3f} "
          f"| XGB AUROC={results['xgboost'][-1]['auroc']:.3f}")

# ============================================================
# STEP 4 — Report all metrics properly
# ============================================================
print("\n" + "=" * 62)
print("STEP 4  Final metrics (mean +/- std across folds)")
print("=" * 62)

metric_keys = ['auroc','auprc','sensitivity','specificity','f1','brier']
all_metrics = {}

for model_name, fold_results in results.items():
    all_metrics[model_name] = {}
    print(f"\n  Model: {model_name.upper()}")
    for k in metric_keys:
        vals = [r[k] for r in fold_results]
        mean, std = np.mean(vals), np.std(vals)
        all_metrics[model_name][k] = {'mean': round(mean, 4), 'std': round(std, 4)}
        print(f"    {k:15s}: {mean:.4f} +/- {std:.4f}")

# ============================================================
# STEP 5 — Train final models on ALL data, generate diagnostic plots
# ============================================================
print("\n" + "=" * 62)
print("STEP 5  Training final models on full dataset + diagnostic plots")
print("=" * 62)

# Use the last fold scaler as production scaler (fitted on its training fold)
# Better: refit on 80% of data using a fixed split for production model
train_n = int(0.8 * len(X_all))
# Patient-level split: get patients sorted, use first 80% as train
unique_patients = df['subject_id'].unique()
np.random.seed(42)
np.random.shuffle(unique_patients)
train_patients = set(unique_patients[:int(0.8 * len(unique_patients))])
test_patients  = set(unique_patients[int(0.8 * len(unique_patients)):])

train_mask = df['subject_id'].isin(train_patients).values
test_mask  = df['subject_id'].isin(test_patients).values

X_tr, y_tr = X_all[train_mask], y_all[train_mask]
X_te, y_te = X_all[test_mask],  y_all[test_mask]

# Fit scaler on train ONLY
final_scaler = StandardScaler()
X_tr_s = final_scaler.fit_transform(X_tr)
X_te_s  = final_scaler.transform(X_te)

# Save production scaler
joblib.dump(final_scaler, os.path.join(OUT, "icu_scaler.pkl"))
print("  Saved icu_scaler.pkl (fitted on training patients only)")

# Final LR
final_lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
final_lr.fit(X_tr_s, y_tr)
lr_test_probs = final_lr.predict_proba(X_te_s)[:, 1]

# Final XGBoost
final_xgb = xgb.XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=(y_tr==0).sum() / max((y_tr==1).sum(), 1),
    eval_metric='logloss', random_state=42, verbosity=0
)
final_xgb.fit(X_tr_s, y_tr)
xgb_test_probs = final_xgb.predict_proba(X_te_s)[:, 1]

# Save models
joblib.dump(final_xgb, os.path.join(OUT, "predictive_icu_model.pkl"))
import shap
explainer = shap.TreeExplainer(final_xgb)
joblib.dump(explainer, os.path.join(OUT, "shap_explainer.pkl"))
print("  Saved XGBoost + SHAP explainer")

# ============================================================
# STEP 6 — Generate all diagnostic plots
# ============================================================
print("\n" + "=" * 62)
print("STEP 6  Generating diagnostic plots")
print("=" * 62)

if len(np.unique(y_te)) > 1:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('#0f172a')
    for ax in axes:
        ax.set_facecolor('#1e293b')
        ax.tick_params(colors='#94a3b8')
        ax.xaxis.label.set_color('#94a3b8')
        ax.yaxis.label.set_color('#94a3b8')
        ax.title.set_color('#e2e8f0')
        for spine in ax.spines.values():
            spine.set_edgecolor('#334155')

    # --- Plot 1: ROC Curves ---
    ax = axes[0]
    for name, probs, color in [
        ('Logistic Regression (baseline)', lr_test_probs, '#64748b'),
        ('XGBoost + GroupKFold',           xgb_test_probs, '#3b82f6'),
    ]:
        fpr, tpr, _ = roc_curve(y_te, probs)
        score = roc_auc_score(y_te, probs)
        ax.plot(fpr, tpr, lw=2.5, color=color, label=f'{name} (AUROC={score:.3f})')
        ax.fill_between(fpr, tpr, alpha=0.07, color=color)
    ax.plot([0,1],[0,1], '--', color='#475569', lw=1.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve — Patient-level GroupKFold\n(MIMIC-IV Real Outcomes)')
    ax.legend(fontsize=9, facecolor='#0f172a', labelcolor='#e2e8f0')

    # --- Plot 2: Precision-Recall Curves (AUPRC - more informative for imbalanced data) ---
    ax = axes[1]
    for name, probs, color in [
        ('Logistic Regression', lr_test_probs, '#64748b'),
        ('XGBoost',             xgb_test_probs, '#3b82f6'),
    ]:
        prec, rec, _ = precision_recall_curve(y_te, probs)
        score = average_precision_score(y_te, probs)
        ax.plot(rec, prec, lw=2.5, color=color, label=f'{name} (AUPRC={score:.3f})')
        ax.fill_between(rec, prec, alpha=0.07, color=color)
    baseline_rate = y_te.mean()
    ax.axhline(baseline_rate, color='#475569', lw=1.5, linestyle='--',
               label=f'Random (rate={baseline_rate:.2f})')
    ax.set_xlabel('Recall (Sensitivity)')
    ax.set_ylabel('Precision (PPV)')
    ax.set_title('Precision-Recall Curve\n(Critical for imbalanced deterioration data)')
    ax.legend(fontsize=9, facecolor='#0f172a', labelcolor='#e2e8f0')

    # --- Plot 3: Calibration Plot ---
    ax = axes[2]
    for name, probs, color in [
        ('Logistic Regression', lr_test_probs, '#64748b'),
        ('XGBoost',             xgb_test_probs, '#3b82f6'),
    ]:
        try:
            prob_true, prob_pred = calibration_curve(y_te, probs, n_bins=5)
            brier = brier_score_loss(y_te, probs)
            ax.plot(prob_pred, prob_true, 'o-', lw=2, color=color,
                    label=f'{name} (Brier={brier:.3f})')
        except Exception:
            pass
    ax.plot([0,1],[0,1], '--', color='#475569', lw=1.5, label='Perfect calibration')
    ax.set_xlabel('Mean Predicted Probability')
    ax.set_ylabel('Fraction of Positives (True Rate)')
    ax.set_title('Calibration Plot\n(Do probabilities reflect real risk?)')
    ax.legend(fontsize=9, facecolor='#0f172a', labelcolor='#e2e8f0')

    plt.suptitle('ICU Early Warning System — 
                 color='#e2e8f0', fontsize=13, y=1.02)
    plt.tight_layout()
    plot_path = os.path.join(OUT, "phase1_evaluation.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight', facecolor='#0f172a')
    print(f"  Saved diagnostic plots to {plot_path}")
else:
    print("  WARNING: Test set has only one class - plots skipped. Dataset too small for this split.")

# ============================================================
# STEP 7 — Save metrics report as JSON (for frontend/API use)
# ============================================================
print("\n" + "=" * 62)
print("STEP 7  Saving metrics report")
print("=" * 62)

report = {
    'methodology': {
        'splitting': 'Patient-level GroupKFold (n_folds=5)',
        'scaler': 'StandardScaler fitted on training fold ONLY',
        'label': 'Composite: died_within_30d OR LOS > 5 days',
        'data_source': 'MIMIC-IV Clinical Database Demo 2.2',
        'n_stays': len(df),
        'n_patients': int(df['subject_id'].nunique()),
        'label_rate': round(float(df['label'].mean()) * 100, 1),
    },
    'cross_val_results': all_metrics,
}

report_path = os.path.join(OUT, "model_metrics.json")
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)
print(f"  Saved model_metrics.json")

print("\n[DONE] 
print("  Eliminated: synthetic labels, test-set tuning, scaler leakage")
print("  Added: patient-level splits, real outcomes, baseline model, AUROC+AUPRC+calibration+Brier")
