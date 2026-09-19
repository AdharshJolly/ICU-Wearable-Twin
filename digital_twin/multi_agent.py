import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from digital_twin.rag_engine import RAGEngine

load_dotenv()

class MultiAgentBoard:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            self.rag = RAGEngine()
        else:
            self.enabled = False
            self.rag = None

    async def get_cardiologist_opinion(self, patient_data, history_text, rag_context=""):
        prompt = f"""You are an elite virtual Cardiologist in the ICU.
Review the following patient data and vital history.
Focus STRICTLY on cardiovascular indicators (Heart Rate, ECG rhythms, Perfusion).
Ignore respiratory issues unless they directly cause cardiac compromise.

Patient Data: {patient_data}
Recent History: {history_text}

CLINICAL GUIDELINES (RAG Context):
{rag_context}

Provide a concise, 2-3 sentence expert opinion on the cardiac status and your primary recommendation based on the clinical guidelines."""
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text

    async def get_pulmonologist_opinion(self, patient_data, history_text, rag_context=""):
        prompt = f"""You are an elite virtual Pulmonologist in the ICU.
Review the following patient data and vital history.
Focus STRICTLY on respiratory indicators (SpO2, Respiratory Rate, Oxygenation, Airway).
Ignore cardiac issues unless they directly cause respiratory failure.

Patient Data: {patient_data}
Recent History: {history_text}

CLINICAL GUIDELINES (RAG Context):
{rag_context}

Provide a concise, 2-3 sentence expert opinion on the pulmonary status and your primary recommendation based on the clinical guidelines."""
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text

    async def get_chief_resident_synthesis(self, patient_data, cardio_opinion, pulmo_opinion, rag_context=""):
        prompt = f"""You are the ICU Chief Resident. You must synthesize the opinions of your specialists into a final, unified treatment plan.

Patient Data: {patient_data}

Cardiologist Opinion:
"{cardio_opinion}"

Pulmonologist Opinion:
"{pulmo_opinion}"

CLINICAL GUIDELINES (RAG Context):
{rag_context}

Provide a concise, authoritative synthesis."""

        from pydantic import BaseModel
        
        class Synthesis(BaseModel):
            summary: str
            primary_diagnosis: str
            recommended_interventions: list[str]
            critical_alerts: list[str]

        response = await self.client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Synthesis,
            ),
        )
        import json
        return json.loads(response.text)

    async def run_consult(self, patient_data, history_data):
        if not self.enabled:
            return {"error": "Gemini API key missing. Multi-agent disabled."}

        # Format history for prompt
        history_text = "\n".join([f"T-{i}: HR {h['hr']}, SpO2 {h['spo2']}, RR {h['rr']}, Temp {h['temp']}" for i, h in enumerate(history_data[:10])])

        # RAG Retrieval
        rag_context = ""
        sources = []
        if self.rag and self.rag.enabled:
            # Query FAISS with the most recent vitals to find relevant guidelines
            recent_vitals = history_data[0] if history_data else {}
            query = f"Patient vitals: Heart Rate {recent_vitals.get('hr', 'N/A')}, SpO2 {recent_vitals.get('spo2', 'N/A')}, Respiratory Rate {recent_vitals.get('rr', 'N/A')}."
            chunks, sources = self.rag.retrieve(query, top_k=2)
            if chunks:
                rag_context = "\n\n---\n\n".join(chunks)

        # Run specialists concurrently
        cardio_task = asyncio.create_task(self.get_cardiologist_opinion(patient_data, history_text, rag_context))
        pulmo_task = asyncio.create_task(self.get_pulmonologist_opinion(patient_data, history_text, rag_context))
        
        cardio_opinion, pulmo_opinion = await asyncio.gather(cardio_task, pulmo_task)

        # Run synthesizer
        final_plan = await self.get_chief_resident_synthesis(patient_data, cardio_opinion, pulmo_opinion, rag_context)

        return {
            "cardiologist": cardio_opinion,
            "pulmonologist": pulmo_opinion,
            "chief_resident": final_plan,
            "citations": list(set(sources)) # Unique sources
        }
