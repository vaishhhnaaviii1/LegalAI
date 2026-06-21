from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_legal_service
from app.schemas.case import CaseRead, CaseRegenerateRequest
from app.services.legal_service import LegalAnalysisService

# Import the controller
from app.controllers.regenerate_summary_controller import regenerate_summary_controller

router = APIRouter()

@router.put(
    "/{case_id}/regenerate",
    response_model=CaseRead,
    status_code=status.HTTP_200_OK,
    summary="Regenerate an existing case summary based on an updated description",
)
# 👇 CHANGED: Renamed this function so it doesn't collide with the controller name
async def regenerate_case_summary_endpoint(
    case_id: UUID,
    request: CaseRegenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    legal_service: LegalAnalysisService = Depends(get_legal_service),
):
    # 👇 CHANGED: Passing request.case_description instead of the whole request object
    result = await regenerate_summary_controller(
        case_id=case_id, 
        new_description=request.description, 
        db=db, 
        legal_service=legal_service
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found"
        )
        
    return result