"""
PRIORITY 7 — GRU vs LSTM Temporal Model Comparison
====================================================
Uses the same patient-level GroupKFold methodology from Phase 1.
Scaler fitted on training fold ONLY.
Labels come from real MIMIC-IV outcomes.
Compares: LSTM vs GRU vs BiLSTM

Both models are evaluated with identical hyperparameters for a fair comparison.
The winner is saved as the production temporal model.
"""

import os, sys, warnings, random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
import joblib

warnings.filterwarnings('ignore')
torch.manual_seed(42)
np.random.seed(42)

BASE = os.path.join(os.path.dirname(__file__), "..", "dataset",
                    "mimic_demo", "mimic-iv-clinical-database-demo-2.2")
OUT  = os.path.dirname(__file__)

# ============================================================
# STEP 1 — Load MIMIC data + build real sequences
# ============================================================
print("=" * 60)
print("STEP 1  Loading MIMIC-IV sequences with real outcome labels")
print("=" * 60)

stays = pd.read_csv(os.path.join(BASE, "icu", "icustays.csv.gz"))
pts   = pd.read_csv(os.path.join(BASE, "hosp", "patients.csv.gz"))
stays = stays.merge(pts[['subject_id','dod']], on='subject_id', how='left')
stays['intime']  = pd.to_datetime(stays['intime'])
stays['outtime'] = pd.to_datetime(stays['outtime'])
stays['dod']     = pd.to_datetime(stays['dod'])

days_to_death = (stays['dod'] - stays['outtime']).dt.days
stays['label'] = (
    (stays['dod'].notna() & (days_to_death.fillna(999) < 30)) |
    (stays['los'] > 5)
).astype(int)

VITALS = {220045: 'hr', 220210: 'rr', 220277: 'spo2', 220179: 'sbp', 220180: 'dbp'}
charts = pd.read_csv(
    os.path.join(BASE, "icu", "chartevents.csv.gz"),
    usecols=['subject_id','stay_id','itemid','charttime','valuenum']
)
charts = charts[charts['itemid'].isin(VITALS)].dropna(subset=['valuenum'])
charts['name'] = charts['itemid'].map(VITALS)
charts['charttime'] = pd.to_datetime(charts['charttime'])

SEQ_LEN = 10   # 10 consecutive observations per sequence
VITAL_NAMES = ['hr', 'rr', 'spo2', 'sbp', 'dbp']

sequences, labels, groups = [], [], []

for _, stay in stays.iterrows():
    sid    = stay['stay_id']
    subj   = stay['subject_id']
    label  = stay['label']
    intime = stay['intime']
    window_end = intime + pd.Timedelta(hours=6)

    stay_charts = charts[
        (charts['stay_id'] == sid) &
        (charts['charttime'] >= intime) &
        (charts['charttime'] <= window_end)
    ].sort_values('charttime')

    # Build per-vital pivot
    pivot = stay_charts.pivot_table(index='charttime', columns='name',
                                     values='valuenum').reset_index()
    pivot = pivot[VITAL_NAMES].ffill().bfill().dropna() if all(v in pivot.columns for v in VITAL_NAMES) else pd.DataFrame()

    if len(pivot) < SEQ_LEN:
        continue

    # Extract all possible overlapping windows
    for i in range(len(pivot) - SEQ_LEN + 1):
        seq = pivot.iloc[i:i+SEQ_LEN][VITAL_NAMES].values
        sequences.append(seq)
        labels.append(float(label))
        groups.append(subj)

X_raw = np.array(sequences, dtype=np.float32)   # (N, SEQ_LEN, 5)
y_all = np.array(labels, dtype=np.float32)
groups_all = np.array(groups)

print(f"  Total sequences : {len(X_raw)}")
print(f"  Unique patients : {len(set(groups_all))}")
print(f"  Positive rate   : {y_all.mean()*100:.1f}%")

# ============================================================
# STEP 2 — Model Definitions
# ============================================================
print("\n" + "=" * 60)
print("STEP 2  Defining LSTM, GRU and BiLSTM architectures")
print("=" * 60)

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.75, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        bce = F.binary_cross_entropy(inputs, targets, reduction='none')
        pt  = torch.exp(-bce)
        at  = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        return (at * (1 - pt) ** self.gamma * bce).mean()


class TemporalModel(nn.Module):
    """Unified wrapper — switches between LSTM, GRU, BiLSTM via arch param."""

    def __init__(self, arch='lstm', input_dim=5, hidden_dim=64,
                 num_layers=2, dropout=0.3):
        super().__init__()
        self.arch = arch
        bidirectional = (arch == 'bilstm')
        rnn_cls = nn.GRU if arch == 'gru' else nn.LSTM
        self.rnn = rnn_cls(
            input_dim, hidden_dim, num_layers,
            batch_first=True, dropout=dropout,
            bidirectional=bidirectional
        )
        fc_in = hidden_dim * 2 if bidirectional else hidden_dim
        self.fc = nn.Sequential(
            nn.Linear(fc_in, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        out, _ = self.rnn(x)
        return self.fc(out[:, -1, :])


def train_one_fold(X_tr, y_tr, X_te, y_te, arch='lstm', epochs=15):
    """Trains a single model on one fold, returns test AUROC and AUPRC."""
    # Balance via minority oversampling on tensors
    pos_idx = np.where(y_tr == 1)[0]
    neg_idx = np.where(y_tr == 0)[0]
    factor  = len(neg_idx) // max(len(pos_idx), 1)
    balanced_idx = np.concatenate([neg_idx, np.tile(pos_idx, factor)])
    np.random.shuffle(balanced_idx)

    Xb = torch.tensor(X_tr[balanced_idx], dtype=torch.float32)
    yb = torch.tensor(y_tr[balanced_idx],  dtype=torch.float32).unsqueeze(1)

    loader  = DataLoader(TensorDataset(Xb, yb), batch_size=64, shuffle=True)
    model   = TemporalModel(arch=arch)
    opt     = torch.optim.Adam(model.parameters(), lr=5e-4, weight_decay=1e-4)
    sched   = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    crit    = FocalLoss(alpha=0.75, gamma=2.0)

    model.train()
    for _ in range(epochs):
        for bx, by in loader:
            opt.zero_grad()
            crit(model(bx), by).backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        sched.step()

    model.eval()
    with torch.no_grad():
        X_te_t = torch.tensor(X_te, dtype=torch.float32)
        probs   = model(X_te_t).numpy().flatten()

    te = y_te
    if len(np.unique(te)) < 2:
        return None, None, model

    return (
        roc_auc_score(te, probs),
        average_precision_score(te, probs),
        model
    )


# ============================================================
# STEP 3 — Patient-level GroupKFold comparison
# ============================================================
print("\n" + "=" * 60)
print("STEP 3  5-fold GroupKFold comparison: LSTM vs GRU vs BiLSTM")
print("=" * 60)

N_SPLITS = 5
gkf = GroupKFold(n_splits=N_SPLITS)
ARCHS = ['lstm', 'gru', 'bilstm']

cv_results = {a: {'auroc': [], 'auprc': []} for a in ARCHS}

for fold, (train_idx, test_idx) in enumerate(gkf.split(X_raw, y_all, groups=groups_all)):
    X_tr_raw, X_te_raw = X_raw[train_idx], X_raw[test_idx]
    y_tr, y_te = y_all[train_idx], y_all[test_idx]

    # ── Scaler fitted on train ONLY ───────────────────────────
    sc = StandardScaler()
    n, t, f = X_tr_raw.shape
    X_tr = sc.fit_transform(X_tr_raw.reshape(-1, f)).reshape(n, t, f)
    nt = X_te_raw.shape[0]
    X_te = sc.transform(X_te_raw.reshape(-1, f)).reshape(nt, t, f)

    print(f"\n  Fold {fold+1}: train={len(train_idx)}  test={len(test_idx)}")
    for arch in ARCHS:
        auroc, auprc, _ = train_one_fold(X_tr, y_tr, X_te, y_te, arch=arch)
        if auroc is not None:
            cv_results[arch]['auroc'].append(auroc)
            cv_results[arch]['auprc'].append(auprc)
            print(f"    {arch.upper():<8} AUROC={auroc:.3f}  AUPRC={auprc:.3f}")

# ============================================================
# STEP 4 — Report + pick winner
# ============================================================
print("\n" + "=" * 60)
print("STEP 4  Results summary")
print("=" * 60)

summary = {}
for arch in ARCHS:
    auc_vals  = cv_results[arch]['auroc']
    aprc_vals = cv_results[arch]['auprc']
    if not auc_vals:
        continue
    mean_auc  = np.mean(auc_vals)
    std_auc   = np.std(auc_vals)
    mean_aprc = np.mean(aprc_vals)
    summary[arch] = {'auroc_mean': mean_auc, 'auroc_std': std_auc, 'auprc_mean': mean_aprc}
    print(f"  {arch.upper():<8}: AUROC {mean_auc:.4f} +/- {std_auc:.4f}  "
          f"| AUPRC {mean_aprc:.4f}")

best_arch = max(summary, key=lambda a: summary[a]['auroc_mean'])
print(f"\n  Winner: {best_arch.upper()} (AUROC={summary[best_arch]['auroc_mean']:.4f})")

# ============================================================
# STEP 5 — Train final winner on all data, save it
# ============================================================
print("\n" + "=" * 60)
print(f"STEP 5  Training final {best_arch.upper()} on all data")
print("=" * 60)

# Patient-level train/test split for final model
unique_patients = list(set(groups_all))
random.shuffle(unique_patients)
split = int(0.8 * len(unique_patients))
train_pts = set(unique_patients[:split])

tr_mask = np.array([g in train_pts for g in groups_all])
te_mask = ~tr_mask

X_tr_r, y_tr_f = X_raw[tr_mask], y_all[tr_mask]
X_te_r, y_te_f = X_raw[te_mask], y_all[te_mask]

n, t, f = X_tr_r.shape
final_sc = StandardScaler()
X_tr_s = final_sc.fit_transform(X_tr_r.reshape(-1, f)).reshape(n, t, f)

nt = X_te_r.shape[0]
X_te_s = final_sc.transform(X_te_r.reshape(-1, f)).reshape(nt, t, f)

# Save scaler (overrides the XGBoost scaler for live LSTM inference)
joblib.dump(final_sc, os.path.join(OUT, "lstm_scaler.pkl"))

_, _, final_model = train_one_fold(X_tr_s, y_tr_f, X_te_s, y_te_f,
                                    arch=best_arch, epochs=25)

model_path = os.path.join(OUT, "lstm_early_warning.pth")
torch.save({
    'state_dict': final_model.state_dict(),
    'arch': best_arch,
    'hidden_dim': 64,
    'num_layers': 2,
    'dropout': 0.3,
}, model_path)
print(f"  Saved {best_arch.upper()} model to {model_path}")

# Update model_metrics.json with temporal results
import json
metrics_path = os.path.join(OUT, "model_metrics.json")
if os.path.exists(metrics_path):
    with open(metrics_path) as fp:
        metrics = json.load(fp)
else:
    metrics = {}

metrics['temporal_comparison'] = {
    arch: {
        'auroc_mean': round(summary[arch]['auroc_mean'], 4),
        'auroc_std':  round(summary[arch]['auroc_std'],  4),
        'auprc_mean': round(summary[arch]['auprc_mean'], 4),
    }
    for arch in summary
}
metrics['best_temporal_model'] = best_arch

with open(metrics_path, 'w') as fp:
    json.dump(metrics, fp, indent=2)
print("  Updated model_metrics.json with temporal comparison")

# ============================================================
# STEP 6 — Comparison bar chart
# ============================================================
print("\n" + "=" * 60)
print("STEP 6  Generating architecture comparison chart")
print("=" * 60)

archs_present = list(summary.keys())
auroc_means = [summary[a]['auroc_mean'] for a in archs_present]
auroc_stds  = [summary[a]['auroc_std']  for a in archs_present]
auprc_means = [summary[a]['auprc_mean'] for a in archs_present]

x = np.arange(len(archs_present))
w = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#0f172a')
ax.set_facecolor('#1e293b')

bars1 = ax.bar(x - w/2, auroc_means, w, yerr=auroc_stds, capsize=5,
               color='#3b82f6', label='AUROC', error_kw={'color': '#94a3b8'})
bars2 = ax.bar(x + w/2, auprc_means, w,
               color='#a855f7', label='AUPRC')

ax.axhline(0.5, color='#ef4444', linestyle='--', lw=1.5, label='Random baseline')
ax.set_xticks(x)
ax.set_xticklabels([a.upper() for a in archs_present], color='#e2e8f0', fontsize=13)
ax.set_ylabel('Score', color='#94a3b8')
ax.set_title('Temporal Model Comparison — Patient-level GroupKFold\nLSTM vs GRU vs BiLSTM (Real MIMIC-IV outcomes)',
             color='#e2e8f0', fontsize=12)
ax.legend(facecolor='#0f172a', labelcolor='#e2e8f0')
ax.tick_params(colors='#94a3b8')
for spine in ax.spines.values():
    spine.set_edgecolor('#334155')
ax.set_ylim(0, 1.05)
ax.yaxis.label.set_color('#94a3b8')

plt.tight_layout()
chart_path = os.path.join(OUT, "temporal_model_comparison.png")
plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='#0f172a')
print(f"  Saved chart to {chart_path}")

print("\n[DONE] Priority 7 complete.")
print(f"  Best temporal model: {best_arch.upper()}")
print(f"  Model saved + metrics updated.")
