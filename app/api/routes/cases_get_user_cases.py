from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.case import CaseRead
from app.controllers import get_user_cases_controller

router = APIRouter()


@router.get(
    "/",
    response_model=List[CaseRead],
    status_code=status.HTTP_200_OK,
    summary="Fetch all cases for a specific user",
)
async def get_user_cases(
    user_id: UUID,
    search: str | None = Query(None, description="Search by case title or description"),
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(100, ge=1, le=100, description="How many records to return"),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_user_cases_controller(user_id, search, skip, limit, db)
