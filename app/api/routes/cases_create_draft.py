from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_legal_service
from app.schemas.case import CaseRead, CaseRequest
from app.services.legal_service import LegalAnalysisService
from app.controllers import create_draft_case_controller

router = APIRouter()


@router.post(
    "/",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Phase 1: Draft case summary (Pending Review)",
)
async def create_draft_case(
    request: CaseRequest,
    db: AsyncSession = Depends(get_db_session),
    legal_service: LegalAnalysisService = Depends(get_legal_service),
):
    return await create_draft_case_controller(request, db, legal_service)
