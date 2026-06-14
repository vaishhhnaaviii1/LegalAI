from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.controllers.delete_legal_section import (
    delete_legal_section_controller,
)

router = APIRouter()


@router.delete(
    "/legal-sections/{section_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft delete a legal section",
)
async def delete_legal_section(
    section_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    return await delete_legal_section_controller(
        section_id,
        db,
    )