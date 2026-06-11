from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.precedent import PrecedentRead
from app.controllers import get_case_precedents_controller

router = APIRouter()


@router.get(
    "/{case_id}/precedents",
    response_model=list[PrecedentRead],
    status_code=status.HTTP_200_OK,
    summary="Get all saved legal precedents for a specific case",
)
async def get_case_precedents(
    case_id: UUID, db: AsyncSession = Depends(get_db_session)
):
    return await get_case_precedents_controller(case_id, db)
