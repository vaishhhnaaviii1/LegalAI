import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.schemas.section import ChargesActionRequest
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection


async def finalize_charges_status_controller(
    case_id: UUID, request: ChargesActionRequest, db: AsyncSession
):
    try:
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 1. Fetch ALL existing draft charges for this case
        query = select(LegalSection).where(LegalSection.case_id == case_id)
        result = await db.execute(query)
        existing_charges = result.scalars().all()

        # Optimize lookups for tracking lists
        approved_ids = set(request.approved_id or [])
        rejected_dict = {item.id: item.reason for item in (request.rejected_data or [])}

        final_db_charges = []

        # 2. Synchronize lawyer's explicit actions with the database state
        for charge in existing_charges:
            if charge.id in approved_ids:
                # SCENARIO A: Lawyer Ticked (Approved)
                charge.is_approved = True
                charge.has_lawyer_verified = True

            elif charge.id in rejected_dict:
                # SCENARIO B: Lawyer Crossed (Rejected & Reason Provided)
                charge.is_approved = False
                charge.has_lawyer_verified = True
                charge.reason = rejected_dict[charge.id]

            else:
                # SCENARIO C: Cleanup (Orphan handling)
                if charge.source == "LLM":
                    charge.is_approved = False
                    charge.has_lawyer_verified = True
                elif charge.source == "LAWYER_MANUAL":
                    # Keep manual additions safely intact
                    pass

            db.add(charge)
            final_db_charges.append(charge)

        # Update transitional status before Kanoon handling
        db_case.status = "pending_precedents"
        await db.commit()

        # Return the verified list layout back to the UI
        clean_charges = [
            {
                "id": charge.id,
                "ipc_section": charge.ipc_section,
                "bns_equivalent": charge.bns_section,
                "offense": "Refer to IPC",
                "explanation": charge.reason,
                "is_approved": charge.is_approved,
            }
            for charge in final_db_charges
        ]

        return {
            "message": "Charges successfully locked and verified by lawyer.",
            "applicable_charges": clean_charges,
        }
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN CHARGE FINALIZATION 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
