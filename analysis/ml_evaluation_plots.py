import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

def generate_plots():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trajectory_file = os.path.join(base_dir, "digital_twin", "risk_trajectory.csv")
    dataset_file = os.path.join(base_dir, "dataset", "Heart Disease Dataset .csv")
    
    if not os.path.exists(trajectory_file):
        print("Trajectory file not found! Run digital_twin/run_digital_twin.py first.")
        return
        
    df_traj = pd.read_csv(trajectory_file)
    
    # Identify anomalies based on Reasons containing "ML Anomaly Detected"
    # Note: handle NaN in Reasons
    df_traj['Is_Anomaly'] = df_traj['Reasons'].fillna('').str.contains("ML Anomaly Detected")
    
    # ---------------------------------------------------------
    # PLOT 1: Time Series of Heart Rate & Resp Rate with Anomalies
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Convert timestamp to relative minutes for easier plotting
    df_traj['Time_Min'] = np.arange(len(df_traj)) * 2  # Assuming 2 min intervals
    
    # Plot Heart Rate
    ax1.plot(df_traj['Time_Min'], df_traj['RestingHR'], color='blue', label='Heart Rate', alpha=0.6)
    
    # Highlight anomalies
    anomalies = df_traj[df_traj['Is_Anomaly']]
    ax1.scatter(anomalies['Time_Min'], anomalies['RestingHR'], color='red', label='ML Anomaly Detected', zorder=5)
    
    # Add clinical thresholds
    ax1.axhline(110, color='orange', linestyle='--', label='Tachycardia Threshold (>110)')
    ax1.set_title('Patient Deterioration over Time: Heart Rate')
    ax1.set_ylabel('Heart Rate (bpm)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot Respiratory Rate
    ax2.plot(df_traj['Time_Min'], df_traj['RespRate'], color='green', label='Respiratory Rate', alpha=0.6)
    ax2.scatter(anomalies['Time_Min'], anomalies['RespRate'], color='red', label='ML Anomaly Detected', zorder=5)
    ax2.axhline(22, color='orange', linestyle='--', label='Tachypnea Threshold (>22)')
    
    ax2.set_title('Patient Deterioration over Time: Respiratory Rate')
    ax2.set_ylabel('Resp Rate (breaths/min)')
    ax2.set_xlabel('Time (Minutes)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    time_series_path = os.path.join(os.path.dirname(__file__), "ml_timeseries_plot.png")
    plt.savefig(time_series_path)
    print(f"Time series plot saved to {time_series_path}")
    
    # ---------------------------------------------------------
    # PLOT 2: 2D Feature Space (Heart Rate vs Resp Rate)
    # ---------------------------------------------------------
    plt.figure(figsize=(9, 7))
    
    # Load a sample of normal dataset to show the "baseline distribution"
    df_baseline = pd.read_csv(dataset_file).sample(2000, random_state=42)
    
    # Plot baseline (Normal points)
    plt.scatter(df_baseline['RestingHR'], df_baseline['RespRate'], color='lightgrey', alpha=0.5, label='Normal Baseline Data (Training)')
    
    # Plot simulated trajectory
    normals = df_traj[~df_traj['Is_Anomaly']]
    plt.scatter(normals['RestingHR'], normals['RespRate'], color='blue', label='Digital Twin (Normal)', edgecolor='k', s=80)
    plt.scatter(anomalies['RestingHR'], anomalies['RespRate'], color='red', label='Digital Twin (ML Anomaly)', edgecolor='k', s=100, marker='X')
    
    # Draw clinical rule boundaries (Top right quadrant is rule-based abnormal)
    plt.axvline(110, color='orange', linestyle='--', alpha=0.7)
    plt.axhline(22, color='orange', linestyle='--', alpha=0.7)
    
    # Annotate regions
    plt.text(115, 23, "Violates Clinical Rules", color='orange', fontsize=12)
    
    plt.title('Isolation Forest Anomaly Detection in 2D Feature Space')
    plt.xlabel('Resting Heart Rate (bpm)')
    plt.ylabel('Respiratory Rate (breaths/min)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    scatter_path = os.path.join(os.path.dirname(__file__), "ml_scatter_plot.png")
    plt.savefig(scatter_path)
    print(f"Scatter plot saved to {scatter_path}")
    
    plt.close('all')

if __name__ == "__main__":
    generate_plots()
