import os
import glob
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import joblib

import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------
# 1. MIMIC-IV Data Processing (5 Core Features)
# ---------------------------------------------------------
print("Loading MIMIC-IV Demo Dataset...")
dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset", "mimic_demo", "mimic-iv-clinical-database-demo-2.2", "icu")

chartevents_path = os.path.join(dataset_dir, "chartevents.csv.gz")
if not os.path.exists(chartevents_path):
    print("MIMIC-IV Demo dataset not found yet.")
    exit(1)
else:
    df_chart = pd.read_csv(chartevents_path, usecols=['subject_id', 'itemid', 'charttime', 'valuenum'])
    df_chart = df_chart.dropna(subset=['valuenum'])

# Focus on Heart Rate, Resp Rate, SpO2, SysBP, DiaBP
vital_ids = [220045, 220210, 220277, 220179, 220180]
df_chart = df_chart[df_chart['itemid'].isin(vital_ids)]

print(f"Loaded {len(df_chart)} clinical events. Pivoting data...")

pivot_df = df_chart.pivot_table(index=['subject_id', 'charttime'], columns='itemid', values='valuenum').reset_index()
pivot_df[vital_ids] = pivot_df.groupby('subject_id')[vital_ids].ffill().bfill()
pivot_df = pivot_df.dropna()

print(f"Created {len(pivot_df)} complete timestamp rows across 5 features.")

X_raw = pivot_df[vital_ids].values
scaler = StandardScaler()
X_scaled_all = scaler.fit_transform(X_raw)

joblib.dump(scaler, os.path.join(os.path.dirname(__file__), "icu_scaler.pkl"))
print("Saved icu_scaler.pkl")

# Attach scaled features back to dataframe for sequence generation
pivot_df['scaled_f1'] = X_scaled_all[:, 0]
pivot_df['scaled_f2'] = X_scaled_all[:, 1]
pivot_df['scaled_f3'] = X_scaled_all[:, 2]
pivot_df['scaled_f4'] = X_scaled_all[:, 3]
pivot_df['scaled_f5'] = X_scaled_all[:, 4]

sequences = []
labels = []
seq_length = 10 

for subject_id, group in pivot_df.groupby('subject_id'):
    vals = group[['scaled_f1', 'scaled_f2', 'scaled_f3', 'scaled_f4', 'scaled_f5']].values
    hr_raw = group[220045].values
    sysbp_raw = group[220179].values
    
    if len(vals) < seq_length:
        continue
    
    for i in range(len(vals) - seq_length - 1):
        seq = vals[i:i+seq_length]
        sequences.append(seq.tolist()) 
        
        # Anomaly Label: If HR spikes by 15+ OR SysBP crashes by 15+ in the NEXT timestep
        next_hr = hr_raw[i+seq_length]
        current_hr = hr_raw[i+seq_length-1]
        next_bp = sysbp_raw[i+seq_length]
        current_bp = sysbp_raw[i+seq_length-1]
        
        is_anomaly = 1.0 if (next_hr - current_hr > 15) or (current_bp - next_bp > 15) else 0.0
        labels.append(is_anomaly)

X = torch.tensor(sequences, dtype=torch.float32)
y = torch.tensor(labels, dtype=torch.float32).unsqueeze(1)

print(f"Created {len(X)} sequential windows of shape {X.shape}")

# ---------------------------------------------------------
# 2. PyTorch LSTM Architecture
# ---------------------------------------------------------
class EarlyWarningLSTM(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=32, num_layers=2, output_dim=1):
        super(EarlyWarningLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM Layer
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        
        # Fully connected layer
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

model = EarlyWarningLSTM()
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.005)

# ---------------------------------------------------------
# 3. Training Loop
# ---------------------------------------------------------
print("Training LSTM Network...")
epochs = 5
batch_size = 64

dataset = torch.utils.data.TensorDataset(X, y)
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

model.train()
for epoch in range(epochs):
    epoch_loss = 0
    for batch_X, batch_y in loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    print(f"Epoch [{epoch+1}/{epochs}], Loss: {epoch_loss/len(loader):.4f}")

# ---------------------------------------------------------
# 4. Generate AUROC Plot
# ---------------------------------------------------------
print("Generating AUROC diagnostics...")
model.eval()
with torch.no_grad():
    y_pred = model(X).numpy().flatten()
    y_true = y.numpy().flatten()

fpr, tpr, _ = roc_curve(y_true, y_pred)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'LSTM ROC curve (area = {roc_auc:.3f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic - Deep Learning Ensemble')
plt.legend(loc="lower right")
plot_path = os.path.join(os.path.dirname(__file__), "lstm_roc_curve.png")
plt.savefig(plot_path)
print(f"Saved AUROC plot to {plot_path}")

# ---------------------------------------------------------
# 5. Save the Architecture
# ---------------------------------------------------------
model_path = os.path.join(os.path.dirname(__file__), "lstm_early_warning.pth")
torch.save(model.state_dict(), model_path)
print(f"LSTM Model saved to {model_path}")
print("Deep Learning Phase Complete!")
