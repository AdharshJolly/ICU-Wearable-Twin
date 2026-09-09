# ============================================================
# PATIENT DIGITAL TWIN - DATA PREPROCESSING
# ============================================================

import pandas as pd

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer


# ------------------------------------------------------------
# 1. Load Dataset
# ------------------------------------------------------------

df = pd.read_csv(
    r"C:\Users\abelw\Documents\College\Project\mlproject\dataset\Heart Disease Dataset .csv"
)

print("\n========== FIRST 5 RECORDS ==========")
print(df.head())


# ------------------------------------------------------------
# 2. Dataset Information
# ------------------------------------------------------------

print("\n========== DATASET INFORMATION ==========")
df.info()

print("\n========== DATASET SHAPE ==========")
print("Rows    :", df.shape[0])
print("Columns :", df.shape[1])


# ------------------------------------------------------------
# 3. Select Only Project Variables
# ------------------------------------------------------------

required_columns = [
    "Patient_ID",
    "Age",
    "Gender",
    "SystolicBP",
    "DiastolicBP",
    "RestingHR",
    "RespRate",
    "BodyTemp_C",
    "SpO2",
    "RestingECG",
    "HRV"
]

df = df[required_columns].copy()

print("\n========== PROJECT DATASET ==========")
print(df.head())

print("\nColumns being used:")
print(df.columns.tolist())


# ------------------------------------------------------------
# 4. Check Duplicate Records
# ------------------------------------------------------------

print("\n========== DUPLICATES ==========")

duplicate_count = df.duplicated().sum()

print("Duplicate records:", duplicate_count)

df = df.drop_duplicates()

print("Shape after removing duplicates:", df.shape)


# ------------------------------------------------------------
# 5. Check Missing Values
# ------------------------------------------------------------

print("\n========== MISSING VALUES ==========")

print(df.isnull().sum())


# ------------------------------------------------------------
# 6. Separate Patient ID
# ------------------------------------------------------------

# Patient_ID is only an identifier.
# It is NOT used as an ML feature.

patient_ids = df["Patient_ID"].copy()

df = df.drop(columns=["Patient_ID"])


# ------------------------------------------------------------
# 7. Encode Gender
# ------------------------------------------------------------

gender_encoder = LabelEncoder()

df["Gender"] = gender_encoder.fit_transform(
    df["Gender"].astype(str)
)

print("\n========== GENDER ENCODING ==========")

for value, encoded_value in zip(
    gender_encoder.classes_,
    gender_encoder.transform(gender_encoder.classes_)
):
    print(value, "->", encoded_value)


# ------------------------------------------------------------
# 8. Define Numerical Columns
# ------------------------------------------------------------

# RestingECG is NOT included because it is already
# encoded as 0, 1, 2.

numerical_columns = [
    "Age",
    "SystolicBP",
    "DiastolicBP",
    "RestingHR",
    "RespRate",
    "BodyTemp_C",
    "SpO2",
    "HRV"
]


# ------------------------------------------------------------
# 9. Convert Numerical Columns
# ------------------------------------------------------------

for column in numerical_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# RestingECG is already numerical
df["RestingECG"] = pd.to_numeric(
    df["RestingECG"],
    errors="coerce"
)


# ------------------------------------------------------------
# 10. Handle Missing Numerical Values
# ------------------------------------------------------------

imputer = SimpleImputer(strategy="median")

df[numerical_columns] = imputer.fit_transform(
    df[numerical_columns]
)


# Handle missing RestingECG values
df["RestingECG"] = df["RestingECG"].fillna(
    df["RestingECG"].mode()[0]
)


# ------------------------------------------------------------
# 11. Check RestingECG Values
# ------------------------------------------------------------

print("\n========== RESTING ECG VALUES ==========")

print(
    sorted(
        df["RestingECG"].unique()
    )
)


# ------------------------------------------------------------
# 12. Check Vital Sign Ranges
# ------------------------------------------------------------

print("\n========== VITAL SIGN RANGES ==========")

for column in numerical_columns:

    print(
        f"{column}: "
        f"{df[column].min()} - {df[column].max()}"
    )


# ------------------------------------------------------------
# 13. Feature Scaling
# ------------------------------------------------------------

scaler = StandardScaler()

df[numerical_columns] = scaler.fit_transform(
    df[numerical_columns]
)


# ------------------------------------------------------------
# 14. Final Dataset
# ------------------------------------------------------------

print("\n========== PREPROCESSED DATA ==========")

print(df.head())


print("\n========== FINAL SHAPE ==========")

print(df.shape)


print("\n========== FINAL DATA TYPES ==========")

print(df.dtypes)


print("\n========== FINAL MISSING VALUES ==========")

print(df.isnull().sum())


# ------------------------------------------------------------
# 15. Save Preprocessed Dataset
# ------------------------------------------------------------

df.to_csv(
    r"C:\Users\abelw\Documents\College\Project\mlproject\dataset\preprocessed_patient_data.csv",
    index=False
)

print("\nPreprocessed dataset saved successfully.")
