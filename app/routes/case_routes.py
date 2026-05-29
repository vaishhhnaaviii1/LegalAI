from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime
import requests

from app.db.database import get_session
from app.models.case_model import Case, CaseCreate
from app.models.ipc_model import IPCSection
from app.core.config import settings

router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


# =========================================
# CREATE CASE
# =========================================

@router.post("/")
def create_case(
    case: CaseCreate,
    session: Session = Depends(get_session)
):

    # ---------------------------------
    # CREATE MAIN CASE
    # ---------------------------------

    new_case = Case(
        title=case.title,
        description=case.description,
        ai_conclusion="This appears to be robbery and assault.",
        reasoning="""
The accused used force while stealing
and threatened nearby people.
        """,
        created_at=datetime.utcnow()
    )

    session.add(new_case)
    session.commit()
    session.refresh(new_case)

    # ---------------------------------
    # IPC SECTIONS
    # ---------------------------------

    ipc_sections_data = [
        {
            "section": "392",
            "title": "Robbery",
            "description": "Punishment for robbery",
            "punishment": "Up to 10 years imprisonment and fine"
        },
        {
            "section": "506",
            "title": "Criminal Intimidation",
            "description": "Threatening another person",
            "punishment": "Up to 2 years imprisonment"
        }
    ]

    saved_ipcs = []

    for ipc in ipc_sections_data:

        ipc_obj = IPCSection(
            section_number=ipc["section"],
            title=ipc["title"],
            description=ipc["description"],
            punishment=ipc["punishment"],
            case_id=new_case.id
        )

        session.add(ipc_obj)

        saved_ipcs.append({
            "section": ipc["section"],
            "title": ipc["title"],
            "description": ipc["description"],
            "punishment": ipc["punishment"]
        })

    session.commit()

    # ---------------------------------
    # INDIAN KANOON API
    # ---------------------------------

    related_cases = []

    try:

        headers = {
            "Authorization": f"Token {settings.INDIAN_KANOON_API_KEY}"
        }

        query = "IPC 392 robbery"

        response = requests.post(
            "https://api.indiankanoon.org/search/",
            headers=headers,
            data={
                "formInput": query
            }
        )

        kanoon_data = response.json()

        docs = kanoon_data.get("docs", [])

        for doc in docs[:5]:

            related_cases.append({

                "title": doc.get("title"),

                "court": doc.get("docsource"),

                "date": doc.get("publishdate"),

                "citation": doc.get("citation"),

                "headline": doc.get("headline"),

                "link": f"https://indiankanoon.org/doc/{doc.get('tid')}/"

            })

    except Exception as e:

        print("Indian Kanoon Error:", e)

    # ---------------------------------
    # FINAL RESPONSE
    # ---------------------------------

    return {

        "case_summary": {

            "id": new_case.id,

            "title": new_case.title,

            "description": new_case.description,

            "ai_conclusion": new_case.ai_conclusion,

            "reasoning": new_case.reasoning,

            "created_at": new_case.created_at
        },

        "ipc_sections": saved_ipcs,

        "related_cases": related_cases
    }


# =========================================
# GET ALL CASES
# =========================================

@router.get("/")
def get_cases(
    session: Session = Depends(get_session)
):

    statement = select(Case)

    cases = session.exec(statement).all()

    return cases


# =========================================
# UPDATE CASE
# =========================================

@router.patch("/{case_id}")
def update_case(
    case_id: int,
    updated_case: CaseCreate,
    session: Session = Depends(get_session)
):

    existing_case = session.get(Case, case_id)

    if not existing_case:
        return {
            "message": "Case not found"
        }

    if updated_case.title:
        existing_case.title = updated_case.title

    if updated_case.description:
        existing_case.description = updated_case.description

    if updated_case.ai_conclusion:
        existing_case.ai_conclusion = updated_case.ai_conclusion

    if updated_case.reasoning:
        existing_case.reasoning = updated_case.reasoning

    session.add(existing_case)

    session.commit()

    session.refresh(existing_case)

    return {
        "message": "Case updated successfully",
        "data": existing_case
    }


# =========================================
# DELETE CASE
# =========================================

@router.delete("/{case_id}")
def delete_case(
    case_id: int,
    session: Session = Depends(get_session)
):

    existing_case = session.get(Case, case_id)

    if not existing_case:
        return {
            "message": "Case not found"
        }

    session.delete(existing_case)

    session.commit()

    return {
        "message": f"Case {case_id} deleted successfully"
    }


# =========================================
# BATCH CREATE
# =========================================

@router.post("/batch")
def create_cases_batch(
    cases: List[CaseCreate],
    session: Session = Depends(get_session)
):

    created_cases = []

    for case in cases:

        new_case = Case(
            title=case.title,
            description=case.description,
            ai_conclusion=case.ai_conclusion,
            reasoning=case.reasoning
        )

        session.add(new_case)

        created_cases.append(new_case)

    session.commit()

    return {
        "message": "Batch cases created",
        "count": len(created_cases)
    }


# =========================================
# REPLACE CASE
# =========================================

@router.put("/{case_id}")
def replace_case(
    case_id: int,
    updated_case: CaseCreate,
    session: Session = Depends(get_session)
):

    existing_case = session.get(Case, case_id)

    if not existing_case:
        return {
            "message": "Case not found"
        }

    existing_case.title = updated_case.title
    existing_case.description = updated_case.description
    existing_case.ai_conclusion = updated_case.ai_conclusion
    existing_case.reasoning = updated_case.reasoning

    session.add(existing_case)

    session.commit()

    session.refresh(existing_case)

    return {
        "message": f"Case {case_id} replaced successfully",
        "data": existing_case
    }

