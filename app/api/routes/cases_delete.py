from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.controllers import delete_case_controller

router = APIRouter()


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft delete a legal case and its associated charges",
)
async def delete_case(case_id: UUID, db: AsyncSession = Depends(get_db_session)):
    return await delete_case_controller(case_id, db)
