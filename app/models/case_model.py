from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from app.models.user_model import User




class Case(SQLModel, table=True):
    __tablename__ = "cases"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    description: str

    ai_conclusion: Optional[str] = None
    reasoning: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id"
    )

    user: Optional["User"] = Relationship(
        back_populates="cases"
    )

    # ipc_sections: List[IPCSection] = Relationship(
    #     back_populates="cases",
    # )