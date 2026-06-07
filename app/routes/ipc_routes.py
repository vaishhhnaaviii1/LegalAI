from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.ipc_model import IPCSection
from app.serializers.review_serializer import IPCReviewRequest

router = APIRouter(
    prefix="/ipc",
    tags=["IPC Review"]
)


@router.post("/")
def create_ipc(
    ipc: IPCSection,
    session: Session = Depends(get_session)
):

    session.add(ipc)
    session.commit()
    session.refresh(ipc)

    return ipc


@router.get("/")
def get_ipc_sections(
    session: Session = Depends(get_session)
):

    statement = select(IPCSection)

    return session.exec(statement).all()


@router.get("/{ipc_id}")
def get_single_ipc(
    ipc_id: int,
    session: Session = Depends(get_session)
):

    ipc = session.get(IPCSection, ipc_id)

    if not ipc:
        raise HTTPException(
            status_code=404,
            detail="IPC section not found"
        )

    return ipc

@router.get("/case/{case_id}")
def get_case_ipcs(
    case_id: int,
    session: Session = Depends(get_session)
):

    statement = select(IPCSection).where(
        IPCSection.case_id == case_id
    )

    sections = session.exec(statement).all()

    return sections

@router.delete("/{ipc_id}")
def delete_ipc(
    ipc_id: int,
    session: Session = Depends(get_session)
):

    ipc = session.get(IPCSection, ipc_id)

    if not ipc:
        raise HTTPException(
            status_code=404,
            detail="IPC section not found"
        )

    session.delete(ipc)
    session.commit()

    return {
        "message": "IPC section deleted"
    }

@router.patch("/{ipc_id}/review")
def review_ipc(
    ipc_id: int,
    review: IPCReviewRequest,
    session: Session = Depends(get_session)
):

    ipc = session.get(
        IPCSection,
        ipc_id
    )

    if not ipc:
        raise HTTPException(
            status_code=404,
            detail="IPC section not found"
        )

    if review.decision not in [
        "approved",
        "rejected"
    ]:
        raise HTTPException(
            status_code=400,
            detail="decision must be approved or rejected"
        )

    ipc.lawyer_decision = review.decision

    session.add(ipc)
    session.commit()
    session.refresh(ipc)

    return {
        "message": "Review saved",
        "ipc_id": ipc.id,
        "decision": ipc.lawyer_decision
    }