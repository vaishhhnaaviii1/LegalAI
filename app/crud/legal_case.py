import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDBase
from app.models.legal_case import LegalCase
from app.models.schemas import LegalCaseCreate, LegalCaseUpdate # Ensure these exist

class CRUDLegalCase(CRUDBase[LegalCase, LegalCaseCreate, LegalCaseUpdate]):
    async def get_multi_by_owner(
        self, db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[LegalCase]:
        # Only fetch cases that aren't marked as deleted!
        statement = select(LegalCase).where(
            LegalCase.user_id == user_id, 
            LegalCase.is_deleted == False
        ).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

legal_case = CRUDLegalCase(LegalCase)
