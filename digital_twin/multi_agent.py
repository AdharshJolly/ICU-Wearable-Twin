import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

class MultiAgentBoard:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
        else:
            self.enabled = False

    async def get_cardiologist_opinion(self, patient_data, history_text):
        prompt = f"""You are an elite virtual Cardiologist in the ICU.
Review the following patient data and vital history.
Focus STRICTLY on cardiovascular indicators (Heart Rate, ECG rhythms, Perfusion).
Ignore respiratory issues unless they directly cause cardiac compromise.

Patient Data: {patient_data}
Recent History: {history_text}

Provide a concise, 2-3 sentence expert opinion on the cardiac status and your primary recommendation."""
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text

    async def get_pulmonologist_opinion(self, patient_data, history_text):
        prompt = f"""You are an elite virtual Pulmonologist in the ICU.
Review the following patient data and vital history.
Focus STRICTLY on respiratory indicators (SpO2, Respiratory Rate, Oxygenation, Airway).
Ignore cardiac issues unless they directly cause respiratory failure.

Patient Data: {patient_data}
Recent History: {history_text}

Provide a concise, 2-3 sentence expert opinion on the pulmonary status and your primary recommendation."""
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text

    async def get_chief_resident_synthesis(self, patient_data, cardio_opinion, pulmo_opinion):
        prompt = f"""You are the ICU Chief Resident. You must synthesize the opinions of your specialists into a final, unified treatment plan.

Patient Data: {patient_data}

Cardiologist Opinion:
"{cardio_opinion}"

Pulmonologist Opinion:
"{pulmo_opinion}"

Provide a final, authoritative 3-point action plan resolving any conflicts between the specialists."""
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text

    async def run_consult(self, patient_data, history_data):
        if not self.enabled:
            return {"error": "Gemini API key missing. Multi-agent disabled."}

        # Format history for prompt
        history_text = "\n".join([f"T-{i}: HR {h['hr']}, SpO2 {h['spo2']}, RR {h['rr']}, Temp {h['temp']}" for i, h in enumerate(history_data[:10])])

        # Run specialists concurrently
        cardio_task = asyncio.create_task(self.get_cardiologist_opinion(patient_data, history_text))
        pulmo_task = asyncio.create_task(self.get_pulmonologist_opinion(patient_data, history_text))
        
        cardio_opinion, pulmo_opinion = await asyncio.gather(cardio_task, pulmo_task)

        # Run synthesizer
        final_plan = await self.get_chief_resident_synthesis(patient_data, cardio_opinion, pulmo_opinion)

        return {
            "cardiologist": cardio_opinion,
            "pulmonologist": pulmo_opinion,
            "chief_resident": final_plan
        }
