# ============================================================
# DIGITAL TWIN - RISK TRAJECTORY VISUALIZATION
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. LOAD TRAJECTORY
# ============================================================

df = pd.read_csv("risk_trajectory.csv")

df["Timestamp"] = pd.to_datetime(df["Timestamp"])


# ============================================================
# 2. CREATE READING NUMBER
# ============================================================

df["Reading"] = range(1, len(df) + 1)


# ============================================================
# 3. DISPLAY BASIC INFORMATION
# ============================================================

print("\n============================================")
print("       DIGITAL TWIN TRAJECTORY")
print("============================================")

print("\nPatient ID:", df["Patient_ID"].iloc[0])

print("Number of readings:", len(df))

print("\nState progression:")

for _, row in df.iterrows():

    print(
        f"Reading {row['Reading']}: "
        f"{row['Current_State']}"
    )


# ============================================================
# 4. HEART RATE
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    df["Reading"],
    df["RestingHR"],
    marker="o"
)

plt.axhline(
    131,
    linestyle="--",
    label="HR threshold = 131 bpm"
)

plt.title("Heart Rate Trajectory")

plt.xlabel("Reading")

plt.ylabel("Heart Rate (bpm)")

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# 5. RESPIRATORY RATE
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    df["Reading"],
    df["RespRate"],
    marker="o"
)

plt.axhline(
    25,
    linestyle="--",
    label="RR threshold = 25 breaths/min"
)

plt.title("Respiratory Rate Trajectory")

plt.xlabel("Reading")

plt.ylabel("Respiratory Rate")

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# 6. BODY TEMPERATURE
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    df["Reading"],
    df["BodyTemp_C"],
    marker="o"
)

plt.axhline(
    38.1,
    linestyle="--",
    label="Temperature threshold = 38.1 C"
)

plt.title("Body Temperature Trajectory")

plt.xlabel("Reading")

plt.ylabel("Temperature (C)")

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# 7. RISK SCORE
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    df["Reading"],
    df["Risk_Score"],
    marker="o"
)

plt.title("Digital Twin Risk Score Trajectory")

plt.xlabel("Reading")

plt.ylabel("Risk Score")

plt.yticks([0, 1, 2, 3])

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# 8. SAVE SUMMARY
# ============================================================

summary = df[
    [
        "Patient_ID",
        "Reading",
        "Timestamp",
        "Risk_Score",
        "Previous_State",
        "Current_State",
        "Abnormality_Duration_Min",
        "Alert",
        "Reasons"
    ]
]

summary.to_csv(
    "risk_trajectory_summary.csv",
    index=False
)


print("\n============================================")
print("Visualization completed.")
print("============================================")

print(
    "\nSaved:",
    "risk_trajectory_summary.csv"
)