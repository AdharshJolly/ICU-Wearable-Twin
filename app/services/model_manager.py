import os
import joblib
import torch
import torch.nn as nn

class TemporalModel(nn.Module):
    def __init__(self, arch='lstm', input_dim=5, hidden_dim=64, num_layers=2, dropout=0.3):
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

class ModelManager:
    def __init__(self):
        self.predictive_model = None
        self.shap_explainer = None
        self.lstm_model = None
        self.icu_scaler = None
        self.lstm_scaler = None

        self._load_models()

    def _load_models(self):
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "digital_twin")
        
        try:
            self.predictive_model = joblib.load(os.path.join(base_dir, "predictive_icu_model.pkl"))
        except Exception as e:
            print(f"XGBoost load error: {e}")

        try:
            self.shap_explainer = joblib.load(os.path.join(base_dir, "shap_explainer.pkl"))
        except Exception as e:
            print(f"SHAP load error: {e}")

        try:
            scaler_path = os.path.join(base_dir, "icu_scaler.pkl")
            if os.path.exists(scaler_path):
                self.icu_scaler = joblib.load(scaler_path)
        except Exception as e:
            print(f"Scaler load error: {e}")

        try:
            lstm_scaler_path = os.path.join(base_dir, "lstm_scaler.pkl")
            if os.path.exists(lstm_scaler_path):
                self.lstm_scaler = joblib.load(lstm_scaler_path)
        except Exception as e:
            print(f"LSTM Scaler load error: {e}")

        try:
            lstm_path = os.path.join(base_dir, "lstm_early_warning.pth")
            if os.path.exists(lstm_path):
                checkpoint = torch.load(lstm_path, map_location=torch.device('cpu'), weights_only=True)
                if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                    self.lstm_model = TemporalModel(
                        arch=checkpoint.get('arch', 'lstm'),
                        hidden_dim=checkpoint.get('hidden_dim', 64),
                        num_layers=checkpoint.get('num_layers', 2),
                        dropout=checkpoint.get('dropout', 0.3)
                    )
                    self.lstm_model.load_state_dict(checkpoint['state_dict'])
                else:
                    self.lstm_model = TemporalModel(arch='lstm', input_dim=5, hidden_dim=32, num_layers=2, dropout=0.3)
                    self.lstm_model.load_state_dict(checkpoint)
                self.lstm_model.eval()
        except Exception as e:
            print(f"LSTM load warning: {e}")

model_manager = ModelManager()
