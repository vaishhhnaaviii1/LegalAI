from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    full_name: str
    email: str = Field(unique=True, index=True)
    phone_number: str

    cases: List["Case"] = Relationship(back_populates="user")