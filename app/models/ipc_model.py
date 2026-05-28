from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship




class IPCSection(SQLModel, table=True):
    __tablename__ = "ipc_sections"

    id: Optional[int] = Field(default=None, primary_key=True)

    section_number: str
    title: str
    description: str
    case_id: Optional[int] = Field(default=None, foreign_key="cases.id")
    cases: List["Case"] = Relationship(
        back_populates="ipc_sections",
    )