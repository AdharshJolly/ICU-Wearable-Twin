import pandas as pd
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

def train_and_save_model():
    print("Loading raw dataset to fit scaler and model...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "dataset", "Heart Disease Dataset .csv")
    
    df = pd.read_csv(input_path)
    
    features = [
        "SystolicBP",
        "DiastolicBP",
        "RestingHR",
        "RespRate",
        "BodyTemp_C",
        "SpO2",
        "HRV"
    ]
    
    # Handle missing values simply for the baseline
    df[features] = df[features].fillna(df[features].median())
    X = df[features]
    
    print("Creating ML Pipeline (Scaler + Isolation Forest)...")
    # The pipeline will scale incoming raw data and then predict
    # Contamination defines the proportion of outliers in the data
    ml_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('anomaly_detector', IsolationForest(n_estimators=100, contamination=0.05, random_state=42))
    ])
    
    ml_pipeline.fit(X)
    
    output_path = os.path.join(os.path.dirname(__file__), "anomaly_pipeline.pkl")
    joblib.dump(ml_pipeline, output_path)
    
    print(f"ML Pipeline saved successfully to {output_path}")

if __name__ == "__main__":
    train_and_save_model()
