import datetime
from time import timezone
import traceback
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update

from app import crud
from app.errors import user_not_found_exc, case_not_found_exc, server_error_exc
from app.schemas.case import CaseRequest, CaseSummaryApproveRequest, CaseResponse
from app.schemas.section import ChargesActionRequest, NewChargeRequest
from app.models.legal_case import LegalCase
from app.models.legal_section import LegalSection
from app.models.precedent import PrecedentCase
from app.services.legal_service import LegalAnalysisService
from app.services.kanoon_service import KanoonService

async def get_user_cases_controller(user_id: UUID, search: str | None, skip: int, limit: int, db: AsyncSession):
    try:
        # LOGIC STEP 1: Verify the user actually exists
        user = await crud.user.get(db, id=user_id)  # TODO: will be authorised by the authentication Decorator
        if not user:
            raise user_not_found_exc()

        # LOGIC STEP 2: Fetch the paginated cases
        cases = await crud.legal_case.get_multi_by_user(
            db=db, user_id=user_id, skip=skip, limit=limit, search=search
        )
        return cases
    except Exception as e:
        print("🚨 FETCH ERROR 🚨")
        traceback.print_exc()
        raise server_error_exc(e)





async def create_draft_case_controller(request: CaseRequest, db: AsyncSession, legal_service: LegalAnalysisService):
    try:
        # 1. Verify user
        user = await crud.user.get(db, id=request.user_id)
        if not user:
            raise user_not_found_exc()

        # 2. Call Groq ONLY for the summary and title
        print("🚀 Calling Groq for Draft Summary...")
        draft_result = await legal_service.draft_summary(case_description=request.case_description)

        # 3. Save as "pending_review"
        db_case = LegalCase(
             # Generate a new UUID for the case
            user_id=request.user_id,
            title=draft_result.title,
            raw_description=request.case_description,
            llm_summary=draft_result.summary,
            status="pending_review"
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


async def approve_summary_and_extract_controller(case_id: UUID, request: CaseSummaryApproveRequest, db: AsyncSession, legal_service: LegalAnalysisService):
    try:
        # 1. Fetch case
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 2. Save the lawyer's approved summary
        db_case.lawyer_approved_summary = request.lawyer_approved_summary
        
        # 3. Call Groq to extract charges
        print("🚀 Calling Groq for IPC Extraction...")
        charges = await legal_service.extract_charges(approved_summary=request.lawyer_approved_summary)

        # 4. Save DRAFT charges to DB
        if charges:
            for charge in charges:
                db_section = LegalSection(
                    case_id=db_case.id,
                    ipc_section=charge.ipc_section,
                    bns_section=charge.bns_equivalent,
                    reason=charge.explanation,
                    source="LLM"
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


async def add_manual_charge_controller(case_id: UUID, request: NewChargeRequest, db: AsyncSession):
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
            is_approved=True, # It's manual, so it starts approved
            has_lawyer_verified=True
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
                "is_approved": new_charge.is_approved
            }
        }
    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        raise server_error_exc(e)


async def finalize_charges_status_controller(case_id: UUID, request: ChargesActionRequest, db: AsyncSession):
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
                "is_approved": charge.is_approved
            } 
            for charge in final_db_charges
        ]

        return {
            "message": "Charges successfully locked and verified by lawyer.",
            "applicable_charges": clean_charges
        }
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN CHARGE FINALIZATION 🚨")
        traceback.print_exc()
        raise server_error_exc(e)


async def fetch_and_store_precedents_controller(case_id: UUID, db: AsyncSession, kanoon_service: KanoonService):
    try:
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 1. Gather ONLY the charges that are actively set to true in the database
        query = select(LegalSection).where(
            LegalSection.case_id == case_id,
            LegalSection.is_approved == True
        )
        result = await db.execute(query)
        approved_db_charges = result.scalars().all()
        
        # ==========================================
        # 🚨 NEW: THE GUARDRAIL
        # ==========================================
        if not approved_db_charges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action denied: The lawyer must approve at least one IPC section before fetching precedents."
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

            print(f"🚀 Calling Kanoon API for compound logic criteria: {search_query}...")
            kanoon_results = await kanoon_service.fetch_precedents(search_query=search_query)

            # Clear out existing relational rows to prevent duplicates if recalculated
            await db.execute(delete(PrecedentCase).where(PrecedentCase.case_id == case_id))

            # 3. Save each incoming record item into a separate database row
            for item in kanoon_results:
               # Use DOT NOTATION here instead of brackets!
                kanoon_url = f"https://indiankanoon.org/doc/{item.doc_id}/"
                
                new_precedent = PrecedentCase(
                    case_id=db_case.id,
                    title=item.title,        # <--- Changed from item["title"]
                    doc_id=item.doc_id,
                    doc_url=kanoon_url,
                    ai_score=None # Ready for custom re-ranking models
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
                "is_approved": charge.is_approved
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
                "ai_score": p.ai_score
            }
            for p in precedents
        ]

        return CaseResponse(
            case_summary=db_case.lawyer_approved_summary,
            applicable_charges=clean_charges,
            precedent_cases=clean_precedents
        )
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PRECEDENT RETRIEVAL 🚨")
        traceback.print_exc()
        raise server_error_exc(e)


async def get_case_precedents_controller(case_id: UUID, db: AsyncSession):
    try:
        # 1. Verify the parent case actually exists
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 2. Fetch all precedents linked to this case ID
        query = select(PrecedentCase).where(PrecedentCase.case_id == case_id)
        result = await db.execute(query)
        precedents = result.scalars().all()

        # 3. Return the list (FastAPI & Pydantic automatically format them using PrecedentRead)
        return precedents
    except HTTPException:
        raise
    except Exception as e:
        print("🚨 CRITICAL ERROR FETCHING PRECEDENTS 🚨")
        traceback.print_exc()
        raise server_error_exc(e)

async def delete_case_controller(case_id: UUID, db: AsyncSession):
    try:
        # 1. Fetch the case (Ensuring it isn't already deleted)
        query = select(LegalCase).where(
            LegalCase.id == case_id, 
            LegalCase.is_deleted == False
        )
        result = await db.execute(query)
        db_case = result.scalar_one_or_none()

        if not db_case:
            raise case_not_found_exc() 
        
        

        # 2. Soft delete the parent case
        db_case.is_deleted = True
        
        # 3. CASCADE: Soft delete all associated IPC sections efficiently
        # This bulk update is faster and ignores the NULL/False trap
        await db.execute(
            update(LegalSection)
            .where(LegalSection.case_id == case_id)
            .values(
                is_deleted=True
            )
        )

        # 4. Commit the changes
        await db.commit()

        return {"message": "Case and associated data successfully deleted."}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR DURING CASE DELETION 🚨")
        traceback.print_exc()
        raise server_error_exc(e)




async def fetch_and_store_precedents_controller(case_id: UUID, db: AsyncSession, kanoon_service: KanoonService):
    try:
        db_case = await crud.legal_case.get(db, id=case_id)
        if not db_case:
            raise case_not_found_exc()

        # 1. Gather ONLY the charges that are actively set to true in the database
        query = select(LegalSection).where(
            LegalSection.case_id == case_id,
            LegalSection.is_approved == True
        )
        result = await db.execute(query)
        approved_db_charges = result.scalars().all()
        
        # ==========================================
        # 🚨 NEW: THE GUARDRAIL
        # ==========================================
        if not approved_db_charges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action denied: The lawyer must approve at least one IPC section before fetching precedents."
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

            print(f"🚀 Calling Kanoon API for compound logic criteria: {search_query}...")
            kanoon_results = await kanoon_service.fetch_precedents(search_query=search_query)

            # Clear out existing relational rows to prevent duplicates if recalculated
            await db.execute(delete(PrecedentCase).where(PrecedentCase.case_id == case_id))

            # 3. Save each incoming record item into a separate database row
            for item in kanoon_results:
               # Use DOT NOTATION here instead of brackets!
                kanoon_url = f"https://indiankanoon.org/doc/{item.doc_id}/"
                
                new_precedent = PrecedentCase(
                    case_id=db_case.id,
                    title=item.title,        # <--- Changed from item["title"]
                    doc_id=item.doc_id,
                    doc_url=kanoon_url,
                    ai_score=None # Ready for custom re-ranking models
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
                "is_approved": charge.is_approved
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
                "ai_score": p.ai_score
            }
            for p in precedents
        ]

        return CaseResponse(
            case_summary=db_case.lawyer_approved_summary,
            applicable_charges=clean_charges,
            precedent_cases=clean_precedents
        )
    except Exception as e:
        await db.rollback()
        print("🚨 CRITICAL ERROR IN PRECEDENT RETRIEVAL 🚨")
        traceback.print_exc()
        raise server_error_exc(e)

    
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
                    "is_approved": sec.is_approved
                } for sec in sections
            ],
            "precedent_cases": [
                {
                    "id": p.id,
                    "title": p.title,
                    "doc_id": p.doc_id,
                    "doc_url": p.doc_url,
                    "ai_score": p.ai_score
                } for p in precedents
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print("🚨 ERROR FETCHING CASE DETAILS 🚨")
        traceback.print_exc()
        raise server_error_exc(e)
