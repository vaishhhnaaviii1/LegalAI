from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.section import NewChargeRequest
from app.controllers import add_manual_charge_controller

router = APIRouter()


@router.post(
    "/{case_id}/charges",
    status_code=status.HTTP_201_CREATED,
    summary="Add a new manual charge to a case",
)
async def add_manual_charge(
    case_id: UUID, request: NewChargeRequest, db: AsyncSession = Depends(get_db_session)
):
    return await add_manual_charge_controller(case_id, request, db)
