import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDBase
from app.models.legal_section import LegalSection
from app.models.schemas import LegalSectionCreate, LegalSectionUpdate # Ensure these exist

class CRUDLegalSection(CRUDBase[LegalSection, LegalSectionCreate, LegalSectionUpdate]):
    async def get_by_case(self, db: AsyncSession, *, case_id: uuid.UUID) -> List[LegalSection]:
        statement = select(LegalSection).where(LegalSection.case_id == case_id)
        result = await db.execute(statement)
        return result.scalars().all()

legal_section = CRUDLegalSection(LegalSection)