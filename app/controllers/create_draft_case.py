import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import user_not_found_exc, server_error_exc
from app.schemas.case import CaseRequest
from app.models.legal_case import LegalCase
from app.services.legal_service import LegalAnalysisService


async def create_draft_case_controller(
    request: CaseRequest, db: AsyncSession, legal_service: LegalAnalysisService
):
    try:
        # 1. Verify user
        user = await crud.user.get(db, id=request.user_id)
        if not user:
            raise user_not_found_exc()

        # 2. Call Groq ONLY for the summary and title
        print("🚀 Calling Groq for Draft Summary...")
        draft_result = await legal_service.draft_summary(
            case_description=request.case_description
        )

        # 3. Save as "pending_review"
        db_case = LegalCase(
            # Generate a new UUID for the case
            user_id=request.user_id,
            title=draft_result.title,
            raw_description=request.case_description,
            llm_summary=draft_result.summary,
            status="pending_review",
        )

        db.add(db_case)
        await db.commit()
        await db.refresh(db_case)

        return db_case
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PHASE 1 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
