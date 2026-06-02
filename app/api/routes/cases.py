# coordinates database (crud),  AI (LegalAnalysisService), and  external web scraper (KanoonService).

import traceback
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException,Query,status
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache

from app.db.database import get_session
from app import crud
from app.models.schemas import CaseRequest, CaseResponse, CaseRead
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

# create and analyse
@router.post(
    "", # FIXED: This prevents the /cases/cases double URL
    response_model=CaseResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Save a case to the database and run full legal analysis"
)
async def create_and_analyze_case(
    request: CaseRequest,
    db: AsyncSession = Depends(get_session),
    legal_service: LegalAnalysisService = Depends(get_legal_service),
    kanoon_service: KanoonService = Depends(get_kanoon_service)
):
    try:
        # LOGIC STEP 1: Verify the user exists in the database
        user = await crud.user.get(db, id=request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # LOGIC STEP 2: Save the "Pending" Case
        db_case = LegalCase(
            user_id=request.user_id,
            title=request.title,
            raw_description=request.case_description,
            status="pending"
        )
        db.add(db_case)
        await db.commit()
        await db.refresh(db_case)

        # LOGIC STEP 3: Run the AI Analysis
        ai_result = await legal_service.analyze_case(case_description=request.case_description)

        # LOGIC STEP 4: Update the database with the AI's summary
        db_case.llm_summary = ai_result.case_summary
        db_case.status = "completed"
        db.add(db_case)

        # LOGIC STEP 5: Save charges and fetch Kanoon precedents
        if ai_result.applicable_charges:
            for charge in ai_result.applicable_charges:
                db_section = LegalSection(
                    case_id=db_case.id,
                    ipc_section=charge.ipc_section,
                    bns_section=charge.bns_equivalent,
                    reason=charge.explanation,
                    source="LLM"
                )
                db.add(db_section)
                
            # Now that we have the charges, we build the query and call Kanoon
            primary_charge = ai_result.applicable_charges[0].ipc_section
            search_query = f'"{primary_charge}" AND "IPC"' 
            cases = await kanoon_service.fetch_precedents(search_query=search_query)
            ai_result.precedent_cases = cases
            
        # Commit all the new sections and case updates at once
        await db.commit()
        
        return ai_result

    except Exception as e:
        # If anything fails, rollback the database to prevent corrupted data
        await db.rollback()
        # --- NEW: Force the terminal to print the exact error and line number ---
        print("🚨 CRITICAL ERROR 🚨")
        traceback.print_exc()
        # Adding 'str(e)' helps you see the exact Python error in Swagger!
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server Error: {str(e)}"
        )
    

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