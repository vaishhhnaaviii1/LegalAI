import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import server_error_exc
from app.services.legal_service import LegalAnalysisService

async def regenerate_summary_controller(
    case_id: UUID,
    new_description: str,
    db: AsyncSession,
    legal_service: LegalAnalysisService
):
    try:
        # 1. Fetch the existing case
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            return None # The router will catch this and throw a 404

        # 2. Call Groq ONLY for the updated summary and title
        print(f"🚀 Calling Groq to Regenerate Summary for Case {case_id}...")
        draft_result = await legal_service.draft_summary(
            case_description=new_description
        )

        # 3. Overwrite the existing data on the same row
        db_case.raw_description = new_description
        db_case.title = draft_result.title
        db_case.llm_summary = draft_result.summary
        db_case.status = "pending_review" # Ensure status resets properly

        await db.commit()
        await db.refresh(db_case)

        return db_case
        
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN REGENERATE PHASE 🚨")
        traceback.print_exc()
        raise server_error_exc(e)