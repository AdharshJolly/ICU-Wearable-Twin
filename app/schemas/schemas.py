from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PatientInfo(BaseModel):
    id: str
    age: int
    gender: str
    physician: str

class Vitals(BaseModel):
    hr: float
    rr: float
    spo2: float
    sbp: float
    dbp: float
    temp: float

class CounterfactualRequest(BaseModel):
    current_vitals: dict
    state: str = "STABLE"
    scenarios: list = ["none", "administer_o2", "beta_blockers", "o2_and_fluids"]
    n_steps: int = 30
