# coordinates database (crud),  AI (LegalAnalysisService), and  external web scraper (KanoonService).

import traceback  #for tracing error 
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException,Query,status
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache
from app.db.database import get_session
from app import crud
from app.models.schemas import CaseRequest, CaseResponse, CaseRead, CaseApproveRequest
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection
from app.services.legal_service import LegalAnalysisService
from app.services.kanoon_service import KanoonService

# FIXED: Prefix handles the "/cases" part, so the route below just needs ""
# This groups all the routes in this file under the /cases URL
router = APIRouter(prefix="/cases", tags=["Legal Cases"])

# --- DEPENDENCIES ---
@lru_cache()
def get_legal_service() -> LegalAnalysisService:
    """Dependency injection to reuse the AI service instance across requests."""
    return LegalAnalysisService()

@lru_cache()
def get_kanoon_service() -> KanoonService:
    """Dependency injection to reuse the Kanoon API service instance."""
    return KanoonService()

@router.get(
    "", 
    response_model=List[CaseRead], # Returns a LIST of your Pydantic schemas
    status_code=status.HTTP_200_OK,
    summary="Fetch all cases for a specific user"
)
async def get_user_cases(
    user_id: uuid.UUID, # Requires the client to pass the user ID in the URL
    # NEW: Add the search query parameter. Default is None if they aren't searching.
    search: str | None = Query(None, description="Search by case title or description"),
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(100, ge=1, le=100, description="How many records to return"),
    db: AsyncSession = Depends(get_session)
):
    try:
        # LOGIC STEP 1: Verify the user actually exists
        user = await crud.user.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # LOGIC STEP 2: Fetch the paginated cases
        cases = await crud.legal_case.get_multi_by_user(
            db=db, user_id=user_id, skip=skip, limit=limit, search=search
        )

        # FASTAPI MAGIC: Because you set response_model=List[CaseResponse], 
        # FastAPI will automatically format the raw database objects into secure JSON!
        return cases

    except Exception as e:
        print("🚨 FETCH ERROR 🚨")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: {str(e)}"
        )
    



# ==========================================
# PHASE 1: INTAKE & DRAFT SUMMARY
# ==========================================
@router.post(
    "", 
    response_model=CaseRead, # Returns the saved DB object
    status_code=status.HTTP_201_CREATED,
    summary="Phase 1: Draft case summary (Pending Review)"
)
async def create_draft_case(
    request: CaseRequest,
    db: AsyncSession = Depends(get_session),
    legal_service: LegalAnalysisService = Depends(get_legal_service)
):
    try:
        # 1. Verify user
        user = await crud.user.get(db, id=request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Call Groq ONLY for the summary and title
        print("🚀 Calling Groq for Draft Summary...")
        draft_result = await legal_service.draft_summary(case_description=request.case_description)

        # 3. Save as "pending_review"
        db_case = LegalCase(
            user_id=request.user_id,
            title=draft_result.title,
            raw_description=request.case_description,
            llm_summary=draft_result.summary,
            status="pending_review"
        )
        db.add(db_case)
        await db.commit()
        await db.refresh(db_case)

        return db_case

    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PHASE 1 🚨")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: {str(e)}"
        )

# ==========================================
# PHASE 2: APPROVAL & LEGAL ANALYSIS
# ==========================================
@router.patch(
    "/{case_id}/analyze", 
    response_model=CaseResponse, # Returns the full analysis payload
    status_code=status.HTTP_200_OK,
    summary="Phase 2: Approve summary, extract charges, fetch Kanoon"
)
async def analyze_approved_case(
    case_id: uuid.UUID,
    request: CaseApproveRequest, # The payload containing the lawyer's edits
    db: AsyncSession = Depends(get_session),
    legal_service: LegalAnalysisService = Depends(get_legal_service),
    kanoon_service: KanoonService = Depends(get_kanoon_service)
):
    try:
        # 1. Fetch the pending case
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 2. Save the lawyer's approved summary
        db_case.lawyer_approved_summary = request.lawyer_approved_summary
        
        # 3. Call Groq to extract charges based on the VERIFIED summary
        print("🚀 Calling Groq for IPC Extraction...")
        charges = await legal_service.extract_charges(approved_summary=request.lawyer_approved_summary)

        # 4. Save charges to DB and fetch Precedents
        precedents = []
        if charges:
            for charge in charges:
                db_section = LegalSection(
                    case_id=db_case.id,
                    ipc_section=charge.ipc_section,
                    bns_section=charge.bns_equivalent,
                    reason=charge.explanation,
                    source="LLM"
                )
                db.add(db_section)
                
            # Call Kanoon using the first identified charge
            primary_charge = charges[0].ipc_section
            search_query = f'"{primary_charge}" AND "IPC"' 
            print("🚀 Calling Kanoon API...")
            precedents = await kanoon_service.fetch_precedents(search_query=search_query)

        # 5. Mark as completed and save everything
        db_case.status = "completed"
        await db.commit()

        # 6. Format the final output to match CaseResponse
        return CaseResponse(
            case_summary=request.lawyer_approved_summary,
            applicable_charges=charges,
            precedent_cases=precedents
        )

    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PHASE 2 🚨")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: {str(e)}"
        )