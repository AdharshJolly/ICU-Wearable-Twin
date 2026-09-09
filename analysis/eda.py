# ============================================================
# PATIENT DIGITAL TWIN - EXPLORATORY DATA ANALYSIS
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    # ------------------------------------------------------------
    # 1. Load Dataset
    # ------------------------------------------------------------
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "dataset", "Heart Disease Dataset .csv")

    df = pd.read_csv(input_path)


    # ------------------------------------------------------------
    # 2. Select Only Project Variables
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


    # ------------------------------------------------------------
    # 3. Display First 5 Records
    # ------------------------------------------------------------

    print("\n========== FIRST 5 RECORDS ==========")
    print(df.head())


    # ------------------------------------------------------------
    # 4. Dataset Shape
    # ------------------------------------------------------------

    print("\n========== DATASET SHAPE ==========")
    print("Number of rows    :", df.shape[0])
    print("Number of columns :", df.shape[1])


    # ------------------------------------------------------------
    # 5. Dataset Information
    # ------------------------------------------------------------

    print("\n========== DATASET INFORMATION ==========")
    df.info()


    # ------------------------------------------------------------
    # 6. Missing Values
    # ------------------------------------------------------------

    print("\n========== MISSING VALUES ==========")

    missing_values = df.isnull().sum()

    print(missing_values)


    # ------------------------------------------------------------
    # 7. Duplicate Records
    # ------------------------------------------------------------

    print("\n========== DUPLICATE RECORDS ==========")

    print(
        "Number of duplicate records:",
        df.duplicated().sum()
    )


    # ------------------------------------------------------------
    # 8. Statistical Summary
    # ------------------------------------------------------------

    print("\n========== STATISTICAL SUMMARY ==========")

    print(
        df.describe()
    )


    # ------------------------------------------------------------
    # 9. Unique Values
    # ------------------------------------------------------------

    print("\n========== UNIQUE VALUES ==========")

    for column in [
        "Gender",
        "RestingECG"
    ]:

        print("\n", column)
        print(df[column].value_counts())


    # ------------------------------------------------------------
    # 10. Numerical Columns
    # ------------------------------------------------------------

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
    # 11. Display Min, Max, Mean
    # ------------------------------------------------------------

    print("\n========== VITAL SIGN STATISTICS ==========")

    for column in numerical_columns:

        print("\n", column)

        print("Minimum :", df[column].min())
        print("Maximum :", df[column].max())
        print("Mean    :", df[column].mean())
        print("Median  :", df[column].median())


    # ------------------------------------------------------------
    # 12. Gender Distribution
    # ------------------------------------------------------------

    print("\n========== GENDER DISTRIBUTION ==========")

    print(
        df["Gender"].value_counts()
    )

    plt.figure(figsize=(6, 5))

    df["Gender"].value_counts().plot(
        kind="bar"
    )

    plt.title("Gender Distribution")
    plt.xlabel("Gender")
    plt.ylabel("Number of Patients")
    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 13. Resting ECG Distribution
    # ------------------------------------------------------------

    print("\n========== RESTING ECG DISTRIBUTION ==========")

    print(
        df["RestingECG"].value_counts()
    )

    plt.figure(figsize=(6, 5))

    df["RestingECG"].value_counts().sort_index().plot(
        kind="bar"
    )

    plt.title("Resting ECG Distribution")
    plt.xlabel("Resting ECG")
    plt.ylabel("Number of Patients")
    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 14. Distribution of Vital Signs
    # ------------------------------------------------------------

    for column in numerical_columns:

        plt.figure(figsize=(7, 5))

        plt.hist(
            df[column].dropna(),
            bins=20
        )

        plt.title(f"Distribution of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")

        plt.tight_layout()
        plt.show()


    # ------------------------------------------------------------
    # 15. Boxplots for Vital Signs
    # ------------------------------------------------------------

    for column in numerical_columns:

        plt.figure(figsize=(7, 4))

        plt.boxplot(
            df[column].dropna(),
            vert=False
        )

        plt.title(f"Boxplot of {column}")
        plt.xlabel(column)

        plt.tight_layout()
        plt.show()


    # ------------------------------------------------------------
    # 16. Correlation Matrix
    # ------------------------------------------------------------

    correlation_columns = numerical_columns + [
        "RestingECG"
    ]

    correlation_matrix = df[
        correlation_columns
    ].corr()

    print("\n========== CORRELATION MATRIX ==========")

    print(
        correlation_matrix
    )


    # ------------------------------------------------------------
    # 17. Correlation Heatmap
    # ------------------------------------------------------------

    plt.figure(figsize=(10, 8))

    plt.imshow(
        correlation_matrix,
        interpolation="nearest"
    )

    plt.colorbar()

    plt.xticks(
        range(len(correlation_matrix.columns)),
        correlation_matrix.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(correlation_matrix.columns)),
        correlation_matrix.columns
    )

    plt.title("Correlation Matrix of Patient Variables")

    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 18. Scatter Plot - Heart Rate vs SpO2
    # ------------------------------------------------------------

    plt.figure(figsize=(7, 5))

    plt.scatter(
        df["RestingHR"],
        df["SpO2"]
    )

    plt.title("Resting Heart Rate vs SpO2")
    plt.xlabel("Resting Heart Rate")
    plt.ylabel("SpO2")

    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 19. Scatter Plot - Respiratory Rate vs SpO2
    # ------------------------------------------------------------

    plt.figure(figsize=(7, 5))

    plt.scatter(
        df["RespRate"],
        df["SpO2"]
    )

    plt.title("Respiratory Rate vs SpO2")
    plt.xlabel("Respiratory Rate")
    plt.ylabel("SpO2")

    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 20. Scatter Plot - HR vs HRV
    # ------------------------------------------------------------

    plt.figure(figsize=(7, 5))

    plt.scatter(
        df["RestingHR"],
        df["HRV"]
    )

    plt.title("Resting Heart Rate vs HRV")
    plt.xlabel("Resting Heart Rate")
    plt.ylabel("HRV")

    plt.tight_layout()
    plt.show()


    # ------------------------------------------------------------
    # 21. Final EDA Summary
    # ------------------------------------------------------------

    print("\n================================================")
    print("EDA COMPLETED")
    print("================================================")

    print("Total patients/records:", len(df))

    print(
        "Missing values:",
        df.isnull().sum().sum()
    )

    print(
        "Duplicate records:",
        df.duplicated().sum()
    )

    print(
        "Average Heart Rate:",
        df["RestingHR"].mean()
    )

    print(
        "Average SpO2:",
        df["SpO2"].mean()
    )

    print(
        "Average Respiratory Rate:",
        df["RespRate"].mean()
    )

    print(
        "Average Temperature:",
        df["BodyTemp_C"].mean()
    )

    print(
        "Average Systolic BP:",
        df["SystolicBP"].mean()
    )

    print(
        "Average Diastolic BP:",
        df["DiastolicBP"].mean()
    )

    print(
        "Average HRV:",
        df["HRV"].mean()
    )

if __name__ == "__main__":
    main()