import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.schemas.case import CaseSummaryApproveRequest
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection
from app.services.legal_service import LegalAnalysisService


async def approve_summary_and_extract_controller(
    case_id: UUID,
    request: CaseSummaryApproveRequest,
    db: AsyncSession,
    legal_service: LegalAnalysisService,
):
    try:
        # 1. Fetch case
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 2. Save the lawyer's approved summary
        db_case.lawyer_approved_summary = request.lawyer_approved_summary

        # 3. Call Groq to extract charges
        print("🚀 Calling Groq for IPC Extraction...")
        charges = await legal_service.extract_charges(
            approved_summary=request.lawyer_approved_summary
        )

        # 4. Save DRAFT charges to DB
        if charges:
            for charge in charges:
                db_section = LegalSection(
                    case_id=db_case.id,
                    ipc_section=charge.ipc_section,
                    bns_section=charge.bns_equivalent,
                    reason=charge.explanation,
                    source="LLM",
                )
                db.add(db_section)

        # 5. Update status so the frontend knows it's waiting on charge approval
        db_case.status = "pending_charge_review"
        await db.commit()

        return {"message": "Charges extracted successfully", "draft_charges": charges}
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PHASE 2 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
