import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from pydantic import BaseModel
from sqlalchemy import or_
from app.crud.base import CRUDBase
from app.models.legal_case import LegalCase
from app.models.schemas import CaseRequest 

# 2. Add a quick placeholder for updates so the Generic base class is happy
class CaseUpdate(BaseModel):
    pass

# 3. FIXED: Plug CaseRequest and CaseUpdate into the CRUDBase
class CRUDLegalCase(CRUDBase[LegalCase, CaseRequest, CaseUpdate]):
    async def get_multi_by_user(
        self, 
        db: AsyncSession, 
        *,   #*: Enforces keyword-only arguments.
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 100,
        search: str | None = None #If the React frontend doesn't send a search word, it just fetches all cases normally.
    ) -> List[LegalCase]:
        
        
        # 1. Start with the base query (Find this user's cases)
        query = select(self.model).where(self.model.user_id == user_id)
        
        # 2. If the user typed something into the search bar, apply the filter
        if search:
            # The % signs act as wildcards. "%theft%" means "find 'theft' anywhere in the text"
            search_term = f"%{search}%"
            query = query.where(
                # or_: This tells the database to look in multiple columns simultaneously.
                # "i" stands for case-insensitive.
                or_(
                    self.model.title.ilike(search_term),
                    self.model.raw_description.ilike(search_term)
                )
            )
            
        # 3. Add the relationships and pagination, then execute
        # selectinload forces the database to fetch all the linked IPC charges at the exact same time it fetches the case.
        query = query.options(selectinload(self.model.sections)).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

legal_case = CRUDLegalCase(LegalCase)