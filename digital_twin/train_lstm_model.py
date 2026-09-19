import os
import glob
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import joblib

# ---------------------------------------------------------
# 1. MIMIC-IV Data Processing
# ---------------------------------------------------------
print("Loading MIMIC-IV Demo Dataset...")
dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset", "mimic_demo", "mimic-iv-clinical-database-demo-2.2", "icu")

chartevents_path = os.path.join(dataset_dir, "chartevents.csv.gz")
if not os.path.exists(chartevents_path):
    print("MIMIC-IV Demo dataset not found yet. The download might still be in progress.")
    print("Using a synthetic fallback dataset for LSTM architectural test...")
    # Synthetic fallback to test architecture while waiting
    dummy_data = []
    for subject_id in range(100):
        for seq in range(20):
            dummy_data.append({
                'subject_id': subject_id,
                'charttime': seq,
                'valuenum': np.random.normal(75, 10),
                'itemid': 220045 # HR
            })
    df_chart = pd.DataFrame(dummy_data)
else:
    df_chart = pd.read_csv(chartevents_path, usecols=['subject_id', 'itemid', 'charttime', 'valuenum'])
    df_chart = df_chart.dropna(subset=['valuenum'])

print(f"Loaded {len(df_chart)} clinical events.")

# Extremely simplified preprocessing: Focus on Heart Rate (220045) and SpO2 (220277)
hr_data = df_chart[df_chart['itemid'] == 220045].rename(columns={'valuenum': 'hr'})
spo2_data = df_chart[df_chart['itemid'] == 220277].rename(columns={'valuenum': 'spo2'})

# For the sake of the demo, we group by subject and create artificial sequences
sequences = []
labels = []
seq_length = 10 # 10 timesteps

for subject_id, group in df_chart.groupby('subject_id'):
    # Extract values sequentially (ignoring strict timestamps for demo brevity)
    vals = group['valuenum'].values
    if len(vals) < seq_length:
        continue
    
    # Slide window
    for i in range(len(vals) - seq_length - 1):
        seq = vals[i:i+seq_length]
        # Normalize roughly
        seq = (seq - 70) / 30.0 
        sequences.append([[x, x*0.9] for x in seq]) # Fake 2-feature vector (HR, SpO2 proxy)
        
        # Label: Does the next value jump significantly? (Anomaly proxy)
        next_val = vals[i+seq_length]
        is_anomaly = 1.0 if abs(next_val - vals[i+seq_length-1]) > 15 else 0.0
        labels.append(is_anomaly)

X = torch.tensor(sequences, dtype=torch.float32)
y = torch.tensor(labels, dtype=torch.float32).unsqueeze(1)

print(f"Created {len(X)} sequential windows of shape {X.shape}")

# ---------------------------------------------------------
# 2. PyTorch LSTM Architecture
# ---------------------------------------------------------
class EarlyWarningLSTM(nn.Module):
    def __init__(self, input_dim=2, hidden_dim=32, num_layers=2, output_dim=1):
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
# 4. Save the Architecture
# ---------------------------------------------------------
model_path = os.path.join(os.path.dirname(__file__), "lstm_early_warning.pth")
torch.save(model.state_dict(), model_path)
print(f"LSTM Model saved to {model_path}")
print("Deep Learning Phase Complete!")
