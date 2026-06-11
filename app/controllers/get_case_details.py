import traceback
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.models.legal_section import LegalSection
from app.models.precedent import PrecedentCase


async def get_case_details_controller(case_id: UUID, db: AsyncSession):
    try:
        # 1. Fetch the main case
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 2. Fetch all associated charges (sections)
        query_sec = select(LegalSection).where(LegalSection.case_id == case_id)
        sections_result = await db.execute(query_sec)
        sections = sections_result.scalars().all()

        # 3. Fetch all associated precedent cases
        query_prec = select(PrecedentCase).where(PrecedentCase.case_id == case_id)
        prec_result = await db.execute(query_prec)
        precedents = prec_result.scalars().all()

        # 4. Stitch them all together into a dictionary that perfectly matches CaseDetailRead
        return {
            "id": db_case.id,
            "title": db_case.title,
            "raw_description": db_case.raw_description,
            "llm_summary": db_case.llm_summary,
            "lawyer_approved_summary": db_case.lawyer_approved_summary,
            "status": db_case.status,
            "applicable_charges": [
                {
                    "id": sec.id,
                    "ipc_section": sec.ipc_section,
                    "bns_equivalent": sec.bns_section,
                    "explanation": sec.reason,
                    "is_approved": sec.is_approved,
                }
                for sec in sections
            ],
            "precedent_cases": [
                {
                    "id": p.id,
                    "title": p.title,
                    "doc_id": p.doc_id,
                    "doc_url": p.doc_url,
                    "ai_score": p.ai_score,
                }
                for p in precedents
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        print("🚨 ERROR FETCHING CASE DETAILS 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
