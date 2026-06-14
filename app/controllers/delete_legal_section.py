import traceback
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.errors import server_error_exc
from app.models.legal_section import LegalSection


async def delete_legal_section_controller(
    section_id: UUID,
    db: AsyncSession,
):
    try:
        # Fetch section which is not already deleted
        query = select(LegalSection).where(
            LegalSection.id == section_id,
            LegalSection.is_deleted == False,
        )

        result = await db.execute(query)
        db_section = result.scalar_one_or_none()

        if not db_section:
            raise HTTPException(
                status_code=404,
                detail="Legal section not found",
            )

        # Soft delete
        db_section.is_deleted = True

        # Optional: if you maintain deleted_at
        # db_section.deleted_at = get_utc_now()

        await db.commit()

        return {
            "message": "Legal section deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()

        print("🚨 CRITICAL ERROR DURING LEGAL SECTION DELETION 🚨")
        traceback.print_exc()

        raise server_error_exc(e)