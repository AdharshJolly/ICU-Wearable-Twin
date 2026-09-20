# ICU Patient Digital Twin & Clinical Decision Support System

## Overview
This project implements a sophisticated **Patient Digital Twin** and **Hybrid Clinical Decision Support System (CDSS)** designed for continuous Intensive Care Unit (ICU) monitoring. It bridges the gap between continuous telemetry streaming, predictive Machine Learning, large language model (LLM) clinical reasoning, and interactive physiological simulation.

By maintaining a continuous computational representation of the patient, the system predicts deterioration trajectories before they occur and allows clinicians to simulate "what-if" pharmacological interventions with real-time feedback.

---

## System Architecture

The digital twin processes high-frequency patient telemetry through a multi-tier architecture:

1. **Patient Telemetry Stream:** High-frequency ingestion of vitals (HR, SpO2, RR, SBP, DBP, Temp).
2. **Patient Digital Twin Core:** Maintains stateful physiological tracking, baseline deviations, memory, and hysteresis to prevent alert flickering.
3. **Ensemble Meta-Learner:** A stacking model combining calibrated XGBoost and sequence-based Deep Learning (LSTM/GRU) trained on real clinical outcomes.
4. **Clinical LLM Agent (RAG-Enabled):** A Generative AI "Chief Resident" agent that analyzes anomalies against rigorous medical protocols (AHA ACLS, Surviving Sepsis, ARDSNet) to output structured clinical notes and intervention recommendations.
5. **Counterfactual Simulation Engine:** A trained Neural Network dynamics model that predicts next-state physiological responses to pharmacological interventions (e.g., Beta Blockers, IV Fluids, Supplemental O2).
6. **Next.js Real-time Dashboard:** A clinical monitoring interface featuring live ICU waveforms, explainability panels, pharmacokinetics tracking, and board-consult interfaces.

---

## Core Capabilities

### 1. The Patient Digital Twin
Unlike simple monitoring software that only displays the latest reading, the **PatientDigitalTwin** acts as a stateful object. It tracks the patient's biological baseline upon admission and calculates live deviations (deltas). It orchestrates rolling memory banks for time-series models and manages the natural drift of the patient's health.

### 2. Predictive Ensemble Meta-Learner
The system utilizes a hybrid modeling approach for early warning detection:
- **XGBoost:** Analyzes static baselines and immediate point-in-time anomalies.
- **BiLSTM / GRU:** Captures temporal deterioration patterns across a sliding window of historical telemetry.
- **Logistic Regression Meta-Learner:** Calibrates the outputs of the underlying models to produce a strictly bounded, clinically accurate probability score for clinical deterioration.

### 3. Pharmacokinetic Counterfactual Engine
Clinicians can use the UI to simulate interventions. The **Learned Dynamics NN** projects the patient's future physiological trajectory under different clinical scenarios. When a medication (e.g., a Beta Blocker) is administered in the live stream, the Twin inherently models the biological half-life and decay, suppressing specific symptoms while tracking the underlying disease drift.

### 4. AI Explainability & RAG Consults
The "Board Consult" feature triggers a clinical reasoning pipeline. The system retrieves relevant medical protocols via a local Knowledge Base (RAG) and passes the patient's digital twin snapshot to a structured LLM Agent. The agent returns a strictly formatted JSON response detailing the primary diagnosis, actionable interventions, and explicit citations to medical literature, minimizing hallucination risk.

### 5. Persistent Electronic Health Records
A robust SQLAlchemy backend provides a persistent EHR layer. Every generated vital sign, risk state transition, and clinical summary is permanently logged to the system database for retrospective audit trails and long-term analysis.

---

## Repository Structure

- pp/: FastAPI backend, WebSocket endpoints, and core Digital Twin services.
- dashboard/: Next.js frontend with TailwindCSS, Recharts, and SmoothieChart for real-time waveform visualization.
- digital_twin/: Machine Learning models, Counterfactual Neural Networks, LLM Agents, and training pipelines.
- knowledge_base/: Markdown-formatted clinical guidelines driving the RAG architecture.
