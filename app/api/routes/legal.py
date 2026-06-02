# contains the business logic for the /legal/analyze endpoint, which combines AI analysis with real precedent cases from Indian Kanoon.

from fastapi import APIRouter, Depends, HTTPException, status
from functools import lru_cache
from app.models.schemas import CaseRequest, CaseResponse
from app.services.legal_service import LegalAnalysisService
from app.services.kanoon_service import KanoonService  # <-- NEW: Import the Kanoon Service

router = APIRouter(prefix="/legal", tags=["Legal Intelligence"])
#for memory optimisation, we use lru_cache to reuse the same service instances across requests.
@lru_cache()
def get_legal_service() -> LegalAnalysisService:
    """Dependency injection to reuse the AI service instance across requests."""
    return LegalAnalysisService()

@lru_cache()
def get_kanoon_service() -> KanoonService:
    """Dependency injection to reuse the Kanoon API service instance."""
    return KanoonService()  # <-- NEW: Create the Kanoon dependency

@router.post(
    "/analyze", 
    response_model=CaseResponse, 
    status_code=status.HTTP_200_OK,
    summary="Extract IPC/BNS sections and fetch precedent cases"
)
async def analyze_incident(
    request: CaseRequest,
    legal_service: LegalAnalysisService = Depends(get_legal_service),
    kanoon_service: KanoonService = Depends(get_kanoon_service)  # <-- NEW: Inject Kanoon into the endpoint
):
    try:
        # 1. Get the raw charges from the AI (Groq)
        ai_result = await legal_service.analyze_case(case_description=request.case_description)
        
        # 2. Build a targeted search query if the AI found applicable charges
        if ai_result.applicable_charges:
            # We grab the very first (usually most severe) IPC section to search
            primary_charge = ai_result.applicable_charges[0].ipc_section
            
            # Format the query strictly: e.g., "Section 326" AND "IPC"
            search_query = f'"{primary_charge}" AND "IPC"' 
            
            # 3. Fetch real precedent cases from Indian Kanoon
            cases = await kanoon_service.fetch_precedents(search_query=search_query)
            
            # 4. Attach the real cases to the Pydantic AI response model
            ai_result.precedent_cases = cases
            
        
        # 5. Return the merged AI + Real Precedent payload to the user
        return ai_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )