import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class ClinicalLLMAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            print("SUCCESS: Gemini LLM Initialized (google-genai)")
        else:
            self.enabled = False
            print("ERROR: Gemini API Key not found")
            
        self.last_state = None
        self.last_reasons = set()
        self.last_summary = "Initializing LLM baseline assessment..."
        
    async def generate_summary(self, risk_state, reasons, metrics):
        if not self.enabled:
            return "Gemini API key missing. LLM disabled."
            
        reasons_set = set(reasons)
        
        # Only call the LLM if the patient's state or anomalies have actually changed
        if self.last_state == risk_state and self.last_reasons == reasons_set:
            return self.last_summary
            
        self.last_state = risk_state
        self.last_reasons = reasons_set
        self.last_summary = "Generating clinical note via Gemini..." # temporary loading text
        
        prompt = f"""
        You are an advanced ICU AI assistant.
        Analyze these real-time vitals and generate a professional, highly concise 1-2 sentence clinical nursing note.
        
        State: {risk_state}
        Heart Rate: {metrics.get('hr', 0):.0f} BPM
        SpO2: {metrics.get('spo2', 0):.0f} %
        Resp Rate: {metrics.get('rr', 0):.0f} RPM
        Temp: {metrics.get('temp', 0):.1f} C
        Anomalies: {', '.join(reasons) if reasons else 'None'}
        
        Keep it purely clinical, direct, and under 30 words. No markdown. If STABLE, just say routine monitoring.
        """
        
        try:
            # Use the new unified google-genai aio client and the latest flash model
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            self.last_summary = response.text.strip()
            return self.last_summary
        except Exception as e:
            print(f"Gemini API Error: {e}")
            self.last_summary = f"[{risk_state}] System evaluating... (LLM fallback)"
            return self.last_summary
