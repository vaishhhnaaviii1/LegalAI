import traceback
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.models.precedent import PrecedentCase


async def get_case_precedents_controller(case_id: UUID, db: AsyncSession):
    try:
        # 1. Verify the parent case actually exists
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 2. Fetch all precedents linked to this case ID
        query = select(PrecedentCase).where(PrecedentCase.case_id == case_id)
        result = await db.execute(query)
        precedents = result.scalars().all()

        # 3. Return the list (FastAPI & Pydantic automatically format them using PrecedentRead)
        return precedents
    except HTTPException:
        raise
    except Exception as e:
        print("🚨 CRITICAL ERROR FETCHING PRECEDENTS 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
