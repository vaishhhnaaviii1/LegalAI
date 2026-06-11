from typing import List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import BaseModel

# This prevents Circular Imports!
if TYPE_CHECKING:
    from app.models.legal_case import LegalCase


class User(BaseModel, table=True):
    name: str
    email: str = Field(unique=True, index=True)
    phone_no: str | None = None
    password_hash: str
    is_active: bool = Field(default=True)

    # Relationship: A user can have many Legal Cases
    cases: List["LegalCase"] = Relationship(back_populates="user")
