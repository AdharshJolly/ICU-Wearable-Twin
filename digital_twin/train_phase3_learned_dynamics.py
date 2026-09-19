import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

# The interventions we support
INTERVENTIONS = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]

# 1. Generate Training Data
# For a proof-of-concept Learned Dynamics Model, we will generate a robust dataset 
# of state transitions based on physiological rules. In a full production system, 
# this would be causal inference data extracted from MIMIC-IV inputevents.
def generate_transition_data(num_samples=20000):
    X = []
    y = []
    
    for _ in range(num_samples):
        # Random initial state
        hr = np.random.uniform(50, 150)
        rr = np.random.uniform(10, 35)
        spo2 = np.random.uniform(80, 100)
        sbp = np.random.uniform(80, 180)
        dbp = np.random.uniform(50, 120)
        
        # Pick random intervention
        action_idx = np.random.randint(0, len(INTERVENTIONS))
        action = INTERVENTIONS[action_idx]
        
        # One-hot encode action
        action_vec = [1.0 if i == action_idx else 0.0 for i in range(len(INTERVENTIONS))]
        
        # Current state vector
        current_state = [hr, rr, spo2, sbp, dbp]
        
        # Simulate next state (Delta)
        d_hr, d_rr, d_spo2, d_sbp, d_dbp = 0, 0, 0, 0, 0
        
        # Natural drift (Deterioration)
        if hr > 100: d_hr += np.random.uniform(0.1, 0.5)
        if spo2 < 94: d_spo2 -= np.random.uniform(0.1, 0.3)
        
        # Intervention Effects (The Physics to Learn)
        if action == "administer_o2":
            d_spo2 += np.random.uniform(0.5, 1.5)
            d_rr -= np.random.uniform(0.2, 0.6)
        elif action == "beta_blockers":
            d_hr -= np.random.uniform(1.0, 3.0)
            d_sbp -= np.random.uniform(0.5, 2.0)
            d_dbp -= np.random.uniform(0.2, 1.0)
        elif action == "o2_and_fluids":
            d_spo2 += np.random.uniform(0.5, 1.2)
            d_sbp += np.random.uniform(1.0, 3.0)
            d_hr -= np.random.uniform(0.5, 1.5)
            
        # Add slight noise
        d_hr += np.random.normal(0, 0.5)
        d_rr += np.random.normal(0, 0.2)
        d_spo2 += np.random.normal(0, 0.2)
        d_sbp += np.random.normal(0, 0.5)
        d_dbp += np.random.normal(0, 0.5)
        
        delta = [d_hr, d_rr, d_spo2, d_sbp, d_dbp]
        
        X.append(current_state + action_vec)
        y.append(delta)
        
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

print("Generating synthetic physiological transition dataset...")
X_data, y_data = generate_transition_data(50000)

# 2. Scale the input data
scaler_X = StandardScaler()
X_scaled = scaler_X.fit_transform(X_data)
# We don't scale Y because we want the network to output absolute delta values directly.

# 3. Create PyTorch Datasets
tensor_X = torch.tensor(X_scaled)
tensor_y = torch.tensor(y_data)
dataset = TensorDataset(tensor_X, tensor_y)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

# 4. Define the Dynamics Neural Network
class DynamicsNN(nn.Module):
    def __init__(self, input_dim=9, hidden_dim=64, output_dim=5):
        super().__init__()
        # Input = 5 vitals + 4 one-hot encoded interventions
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
    def forward(self, x):
        return self.net(x)

model = DynamicsNN()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 5. Train the Model
print("Training Learned Dynamics Model...")
epochs = 20
for epoch in range(epochs):
    epoch_loss = 0.0
    for batch_X, batch_y in loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    if (epoch + 1) % 5 == 0:
        print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(loader):.4f}")

# 6. Save Artifacts
OUT_DIR = os.path.dirname(__file__)
model_path = os.path.join(OUT_DIR, "learned_dynamics_model.pth")
scaler_path = os.path.join(OUT_DIR, "dynamics_scaler.pkl")

torch.save({'state_dict': model.state_dict()}, model_path)
joblib.dump(scaler_X, scaler_path)

print(f"Saved Dynamics Model to: {model_path}")
print(f"Saved Dynamics Scaler to: {scaler_path}")
