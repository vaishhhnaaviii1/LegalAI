from sqlmodel import Session, select

from app.models.ipc_model import IPCSection


def create_ipc_controller(
    ipc: IPCSection,
    session: Session
):

    session.add(ipc)
    session.commit()
    session.refresh(ipc)

    return ipc


def get_ipc_sections_controller(
    session: Session
):

    statement = select(IPCSection)

    return session.exec(statement).all()


def get_single_ipc_controller(
    ipc_id: int,
    session: Session
):

    return session.get(IPCSection, ipc_id)


def delete_ipc_controller(
    ipc_id: int,
    session: Session
):

    ipc = session.get(IPCSection, ipc_id)

    if ipc:

        session.delete(ipc)
        session.commit()

    return ipc