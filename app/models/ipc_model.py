from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from app.models.case_model import Case
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.case_model import Case


class IPCSection(SQLModel, table=True):
    __tablename__ = "ipc_sections"

    id: Optional[int] = Field(default=None, primary_key=True)

    section_number: str
    title: str
    punishment: str

    case_id: Optional[int] = Field(
        default=None,
        foreign_key="cases.id"
    )

    case: Optional["Case"] = Relationship(
        back_populates="ipc_sections"
    )