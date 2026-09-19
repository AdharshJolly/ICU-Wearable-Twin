import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os

print("Testing MIMIC-IV Pivot & Scaler Logic...")
dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset", "mimic_demo", "mimic-iv-clinical-database-demo-2.2", "icu")
chartevents_path = os.path.join(dataset_dir, "chartevents.csv.gz")

df = pd.read_csv(chartevents_path, usecols=['subject_id', 'charttime', 'itemid', 'valuenum'])
df = df.dropna(subset=['valuenum'])

vital_ids = [220045, 220210, 220277, 220179, 220180]
df = df[df['itemid'].isin(vital_ids)]

print(f"Filtered to {len(df)} core vital events.")

pivot_df = df.pivot_table(index=['subject_id', 'charttime'], columns='itemid', values='valuenum').reset_index()
print(f"Pivoted into {len(pivot_df)} unique timestamp rows.")

pivot_df = pivot_df.groupby('subject_id').ffill().bfill()
pivot_df = pivot_df.dropna()

print(f"After ffill/bfill and dropna: {len(pivot_df)} complete rows.")

X_raw = pivot_df[vital_ids].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

print("Scaler Means:", scaler.mean_)
print("Scaler Variance:", scaler.var_)

joblib.dump(scaler, os.path.join(os.path.dirname(__file__), "icu_scaler.pkl"))
print("Saved icu_scaler.pkl")
