from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.section import ChargesActionRequest
from app.controllers import finalize_charges_status_controller

router = APIRouter()


@router.put(
    "/{case_id}/finalize-charges",
    status_code=status.HTTP_200_OK,
    summary="Phase 3A: Save lawyer-approved and rejected charges state to database",
)
async def finalize_charges_status(
    case_id: UUID,
    request: ChargesActionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    return await finalize_charges_status_controller(case_id, request, db)
