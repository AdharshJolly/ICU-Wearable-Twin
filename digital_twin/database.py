import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Setup SQLite Database in the root directory
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icu_telemetry.db')
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    hr = Column(Float)
    rr = Column(Float)
    temp = Column(Float)
    spo2 = Column(Float)
    sbp = Column(Float, nullable=True)
    dbp = Column(Float, nullable=True)
    
    risk_state = Column(String)
    abnormal_reasons = Column(String) # JSON stringified
    llm_summary = Column(String)
    intervention = Column(String, nullable=True)

class TwinSnapshot(Base):
    __tablename__ = "twin_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Physiology
    hr = Column(Float)
    rr = Column(Float)
    spo2 = Column(Float)
    sbp = Column(Float)
    dbp = Column(Float)
    temp = Column(Float)
    
    # Model Outputs
    risk_probability = Column(Float)
    state = Column(String)
    confidence = Column(String)
    
    # Meta (JSON stringified)
    top_factors = Column(String) 
    baseline = Column(String)
    model_version = Column(String, default="ensemble-fallback-v1.0")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
