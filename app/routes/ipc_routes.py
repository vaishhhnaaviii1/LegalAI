from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.ipc_model import IPCSection

router = APIRouter(
    prefix="/ipc",
    tags=["IPC"]
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