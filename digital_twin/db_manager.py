import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_name="digital_twin.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_name)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                age INTEGER,
                gender TEXT
            )
        ''')
        
        # Create Trajectory / Vitals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trajectory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                timestamp TEXT,
                resting_hr REAL,
                resp_rate REAL,
                body_temp REAL,
                spo2 REAL,
                systolic_bp REAL,
                diastolic_bp REAL,
                hrv REAL,
                risk_score INTEGER,
                current_state TEXT,
                alert TEXT,
                reasons TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_patient(self, patient_id, age, gender):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO patients (patient_id, age, gender)
            VALUES (?, ?, ?)
        ''', (str(patient_id), age, gender))
        conn.commit()
        conn.close()

    def log_trajectory(self, record):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trajectory (
                patient_id, timestamp, resting_hr, resp_rate, body_temp, 
                spo2, systolic_bp, diastolic_bp, hrv, risk_score, 
                current_state, alert, reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(record["Patient_ID"]),
            str(record["Timestamp"]),
            record["RestingHR"],
            record["RespRate"],
            record["BodyTemp_C"],
            record["SpO2"],
            record["SystolicBP"],
            record["DiastolicBP"],
            record["HRV"],
            record["Risk_Score"],
            record["Current_State"],
            record["Alert"],
            record["Reasons"]
        ))
        conn.commit()
        conn.close()

# Provide a global instance for ease of use
db = DatabaseManager()
