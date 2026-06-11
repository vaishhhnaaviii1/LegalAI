import logging
import json
from groq import AsyncGroq
from app.core.config import settings
from app.schemas.case import CaseResponse, DraftResponse
from app.schemas.section import LegalSection
from app.decorators import with_api_retry

# 🚨 NEW: Import your prompt functions
from app.prompts.legal_analysis import (
    get_draft_summary_prompt,
    get_charge_extraction_prompt,
)

logger = logging.getLogger(__name__)


class LegalAnalysisService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model_id = "llama-3.3-70b-versatile"
        schema_instructions = CaseResponse.model_json_schema()

    @with_api_retry
    async def draft_summary(self, case_description: str) -> DraftResponse:
        """PHASE 1: Reads the raw input and generates a clean title and summary."""

        # 🚨 NEW: Generate the prompt using the imported function
        prompt = get_draft_summary_prompt(case_description)

        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_id,
            response_format={"type": "json_object"},
        )

        result_dict = json.loads(response.choices[0].message.content)
        return DraftResponse(**result_dict)

    @with_api_retry
    async def extract_charges(self, approved_summary: str) -> list[LegalSection]:
        """PHASE 2: Takes the HUMAN-VERIFIED summary and extracts penal charges."""

        # 🚨 NEW: Generate the prompt using the imported function
        prompt = get_charge_extraction_prompt(approved_summary)

        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_id,
            response_format={"type": "json_object"},
        )

        result_dict = json.loads(response.choices[0].message.content)
        return [LegalSection(**charge) for charge in result_dict.get("charges", [])]
