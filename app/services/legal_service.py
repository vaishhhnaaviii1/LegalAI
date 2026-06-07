import logging
import json
from groq import AsyncGroq
from app.core.config import settings
from app.models.schemas import CaseResponse,DraftResponse, LegalSection
from app.decorators import with_api_retry

logger = logging.getLogger(__name__)

class LegalAnalysisService:
    def __init__(self):
        #establishing a secure connection to Groq using your secret API key from the .env file.
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model_id = "llama-3.3-70b-versatile"
        
        # for converting caseResponse in JSON.
        schema_instructions = CaseResponse.model_json_schema()
        
  
    @with_api_retry
    async def draft_summary(self, case_description: str) -> DraftResponse:
        """PHASE 1: Reads the raw input and generates a clean title and summary."""
        
        prompt = f"""
        You are an expert legal assistant. Read the following incident description.
        1. Create a short, professional title for the case along with the names of parties involved if mentioned in the description.
        2. Write a clear, objective, one-sentence summary of the facts.
        
        Return ONLY valid JSON in this exact format:
        {{
            "title": "...",
            "summary": "..."
        }}
        
        Incident: {case_description}
        """
        
        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", # Or whichever Groq model you are using
            response_format={"type": "json_object"}
        )
        
        result_dict = json.loads(response.choices[0].message.content)
        return DraftResponse(**result_dict)

    @with_api_retry
    async def extract_charges(self, approved_summary: str) -> list[LegalSection]:
        """PHASE 2: Takes the HUMAN-VERIFIED summary and extracts penal charges."""
        
        prompt = f"""
        You are an expert Indian criminal lawyer. Based on the verified facts below, 
        identify the applicable Indian Penal Code (IPC) and Bharatiya Nyaya Sanhita (BNS) sections.
        
        Return ONLY valid JSON in this exact format, with a list of "charges":
        {{
            "charges": [
                {{
                    "ipc_section": "Section 378",
                    "bns_equivalent": "Section 303(2)",
                    "offense": "Theft",
                    "explanation": "Brief reason..."
                }}
            ]
        }}
        
        Verified Facts: {approved_summary}
        """
        
        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            response_format={"type": "json_object"}
        )
        
        result_dict = json.loads(response.choices[0].message.content)
        
        # Convert the raw dictionaries into your nice Pydantic models
        return [LegalSection(**charge) for charge in result_dict.get("charges", [])]
    
    