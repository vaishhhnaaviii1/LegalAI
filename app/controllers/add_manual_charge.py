import traceback
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.errors import case_not_found_exc, server_error_exc
from app.schemas.section import NewChargeRequest
from app.models.legal_section import LegalSection


async def add_manual_charge_controller(
    case_id: UUID, request: NewChargeRequest, db: AsyncSession
):
    try:
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # Create the brand new manual charge
        new_charge = LegalSection(
            case_id=case_id,
            ipc_section=request.ipc_section,
            bns_section=request.bns_section,
            reason=request.reason,
            source="LAWYER_MANUAL",
            is_approved=True,  # It's manual, so it starts approved
            has_lawyer_verified=True,
        )

        db.add(new_charge)
        await db.commit()
        await db.refresh(new_charge)

        return {
            "message": "Charge added successfully",
            "charge": {
                "id": new_charge.id,
                "ipc_section": new_charge.ipc_section,
                "bns_equivalent": new_charge.bns_section,
                "explanation": new_charge.reason,
                "is_approved": new_charge.is_approved,
            },
        }
    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        raise server_error_exc(e)
