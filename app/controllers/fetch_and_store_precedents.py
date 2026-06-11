import traceback
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.schemas.case import CaseResponse
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection
from app.models.precedent import PrecedentCase
from app.services.kanoon_service import KanoonService


async def fetch_and_store_precedents_controller(
    case_id: UUID, db: AsyncSession, kanoon_service: KanoonService
):
    try:
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 1. Gather ONLY the charges that are actively set to true in the database
        query = select(LegalSection).where(
            LegalSection.case_id == case_id, LegalSection.is_approved == True
        )
        result = await db.execute(query)
        approved_db_charges = result.scalars().all()

        # ==========================================
        # 🚨 NEW: THE GUARDRAIL
        # ==========================================
        if not approved_db_charges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action denied: The lawyer must approve at least one IPC section before fetching precedents.",
            )
        # ==========================================

        precedents = []
        approved_sections = [charge.ipc_section for charge in approved_db_charges]

        # 2. Execute external search if approved sections exist
        if approved_sections:
            # Look at top 3 primary overlapping segments to avoid matching to zero records
            top_sections = approved_sections[:3]
            combined_sections = " AND ".join([f'"{sec}"' for sec in top_sections])
            search_query = f'({combined_sections}) AND "IPC"'

            print(
                f"🚀 Calling Kanoon API for compound logic criteria: {search_query}..."
            )
            kanoon_results = await kanoon_service.fetch_precedents(
                search_query=search_query
            )

            # Clear out existing relational rows to prevent duplicates if recalculated
            await db.execute(
                delete(PrecedentCase).where(PrecedentCase.case_id == case_id)
            )

            # 3. Save each incoming record item into a separate database row
            for item in kanoon_results:
                # Use DOT NOTATION here instead of brackets!
                kanoon_url = f"https://indiankanoon.org/doc/{item.doc_id}/"

                new_precedent = PrecedentCase(
                    case_id=db_case.id,
                    title=item.title,  # <--- Changed from item["title"]
                    doc_id=item.doc_id,
                    doc_url=kanoon_url,
                    ai_score=None,  # Ready for custom re-ranking models
                )
                db.add(new_precedent)
                precedents.append(new_precedent)

        # 4. Finalize the state machine step completely
        db_case.status = "completed"
        await db.commit()

        # 5. Format clean response payloads safely avoiding Pydantic V2 engine panic
        clean_charges = [
            {
                "id": charge.id,
                "ipc_section": charge.ipc_section,
                "bns_equivalent": charge.bns_section,
                "offense": "Refer to IPC",
                "explanation": charge.reason,
                "is_approved": charge.is_approved,
            }
            for charge in approved_db_charges
        ]

        # NEW: Clean the precedent database objects into pure dictionaries
        clean_precedents = [
            {
                "id": p.id,
                "title": p.title,
                "doc_id": p.doc_id,
                "doc_url": p.doc_url,
                "ai_score": p.ai_score,
            }
            for p in precedents
        ]

        return CaseResponse(
            case_summary=db_case.lawyer_approved_summary,
            applicable_charges=clean_charges,
            precedent_cases=clean_precedents,
        )
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PRECEDENT RETRIEVAL 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
