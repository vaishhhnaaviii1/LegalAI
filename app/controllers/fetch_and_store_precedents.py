import traceback
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.models.legal_section import LegalSection
from app.models.precedent import PrecedentCase
from app.schemas.case import CaseResponse
from app.services.kanoon_service import KanoonService
from app.services.similarity_service import compute_similarity_percentage
from app.services.llm_similarity_service import llm_similarity_score

async def fetch_and_store_precedents_controller(
    case_id: UUID,
    db: AsyncSession,
    kanoon_service: KanoonService,
):
    try:
        # ==========================================
        # Fetch Case
        # ==========================================
        db_case = await crud.legal_case.get(db, id=case_id)

        if not db_case:  
            raise case_not_found_exc()

        # ==========================================
        # Fetch Approved Sections
        # ==========================================
        query = select(LegalSection).where(
            LegalSection.case_id == case_id,
            LegalSection.is_approved == True,
        )

        result = await db.execute(query)
        approved_db_charges = result.scalars().all()

        if not approved_db_charges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action denied: The lawyer must approve at least one IPC section before fetching precedents.",
            )

        approved_sections = [
            charge.ipc_section
            for charge in approved_db_charges
        ]

        precedents = []

        # ==========================================
        # Search Indian Kanoon
        # ==========================================
        if approved_sections:

            top_sections = approved_sections[:3]

            combined_sections = " AND ".join(
                [f'"{sec}"' for sec in top_sections]
            )

            search_query = f'({combined_sections}) AND "IPC"'

            print(f"🚀 Kanoon Search Query : {search_query}")

            kanoon_results = await kanoon_service.fetch_precedents(
                search_query=search_query
            )

            # Remove old precedents
            await db.execute(
                delete(PrecedentCase).where(
                    PrecedentCase.case_id == case_id
                )
            )

            # ==========================================
            # Save Each Precedent
            # ==========================================
            for item in kanoon_results:

                kanoon_url = (
                    f"https://indiankanoon.org/doc/{item.doc_id}/"
                )

                precedent_text_chunk = (
                    getattr(item, "snippet", "")
                    or item.title
                )

                # ==========================================
                # STEP 1 : Embedding Score
                # ==========================================
                embedding_score = compute_similarity_percentage(
                    current_case_text=db_case.raw_description,
                    precedent_case_text=precedent_text_chunk,
                )

                print(f"Embedding Score : {embedding_score}")

                # ==========================================
                # STEP 2 : Final AI Score
                # ==========================================
                if 30 <= embedding_score <= 70:

                    final_score = embedding_score

                else:

                    llm_score = await llm_similarity_score(
                        current_case=db_case.raw_description,
                        precedent_case=precedent_text_chunk,
                    )

                    final_score = int(
                        (embedding_score + llm_score) / 2
                    )

                print(f"Final AI Score : {final_score}")

                # ==========================================
                # Save Precedent
                # ==========================================
                new_precedent = PrecedentCase(
                    case_id=db_case.id,
                    title=item.title,
                    doc_id=item.doc_id,
                    doc_url=kanoon_url,
                    ai_score=final_score,
                )

                db.add(new_precedent)
                precedents.append(new_precedent)

        # ==========================================
        # Complete Case
        # ==========================================
        db_case.status = "completed"

        await db.commit()

        # ==========================================
        # Response Charges
        # ==========================================
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

        # ==========================================
        # Response Precedents
        # ==========================================
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

        # Highest AI score first
        clean_precedents.sort(
            key=lambda x: x["ai_score"],
            reverse=True,
        )

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