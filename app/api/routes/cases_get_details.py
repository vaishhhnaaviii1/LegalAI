from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.case import CaseDetailRead
from app.controllers import get_case_details_controller

router = APIRouter()


@router.get(
    "/{case_id}",
    response_model=CaseDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Fetch full case details including sections and precedents",
)
async def get_case_details(case_id: UUID, db: AsyncSession = Depends(get_db_session)):
    return await get_case_details_controller(case_id, db)
