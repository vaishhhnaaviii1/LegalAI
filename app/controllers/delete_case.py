import traceback
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.errors import case_not_found_exc, server_error_exc
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection


async def delete_case_controller(case_id: UUID, db: AsyncSession):
    try:
        # 1. Fetch the case (Ensuring it isn't already deleted)
        query = select(LegalCase).where(
            LegalCase.id == case_id, LegalCase.is_deleted == False
        )
        result = await db.execute(query)
        db_case = result.scalar_one_or_none()

        if not db_case:
            raise case_not_found_exc()

        # 2. Soft delete the parent case
        db_case.is_deleted = True

        # 3. CASCADE: Soft delete all associated IPC sections efficiently
        # This bulk update is faster and ignores the NULL/False trap
        await db.execute(
            update(LegalSection)
            .where(LegalSection.case_id == case_id)
            .values(is_deleted=True)
        )

        # 4. Commit the changes
        await db.commit()

        return {"message": "Case and associated data successfully deleted."}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR DURING CASE DELETION 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
