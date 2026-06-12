import logging
import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.schemas.case import CaseSummaryApproveRequest
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection
from app.services.legal_service import LegalAnalysisService

# Set up production logger
logger = logging.getLogger(__name__)

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

        # 3. Call AI to extract charges
        logger.info("Calling Groq for IPC Extraction...", extra={"case_id": str(case_id)})
        ai_charges = await legal_service.extract_charges(
            approved_summary=request.lawyer_approved_summary
        )

        # 4. Save DRAFT charges to DB AND capture them in a list
        saved_db_charges = []
        if ai_charges:
            for charge in ai_charges:
                db_section = LegalSection(
                    case_id=db_case.id,
                    ipc_section=charge.ipc_section,
                    bns_section=charge.bns_equivalent,
                    reason=charge.explanation,
                    source="LLM",
                )
                db.add(db_section)
                saved_db_charges.append(db_section) # <-- CHANGE 1: Capture the DB objects

        # 5. Update status and commit
        db_case.status = "pending_charge_review"
        await db.commit()
        
        # 6. CRITICAL ASYNC STEP: Refresh objects to safely fetch the new IDs
        for db_section in saved_db_charges:
            await db.refresh(db_section) # <-- CHANGE 2: Fetch the generated UUIDs into memory

        # 7. Return the DB models, NOT the raw ai_charges
        return {
            "message": "Charges extracted successfully", 
            "draft_charges": saved_db_charges # <-- CHANGE 3: Return the captured list
        }
        
    except Exception as e:
        await db.rollback()
        logger.error("CRITICAL ERROR IN PHASE 2", exc_info=True, extra={"case_id": str(case_id)})
        raise server_error_exc(e)