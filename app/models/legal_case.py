import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel



# Prevent Circular Imports! This allows us to reference the User and LegalSection models without importing them at the top level, which would cause a circular import error.
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.legal_section import LegalSection

class LegalCase(BaseModel, table=True):
    # Foreign Key now points to a UUID
    user_id: uuid.UUID = Field(foreign_key="user.id")
    
    title: str
    raw_description: str
    
    # JSON field for the LLM output
    # llm_summary: Optional[dict] = Field(default={}, sa_column=Column(JSONB))
    llm_summary: str | None = None
    lawyer_approved_summary: str| None=None
    
    # Status: completed, inprogress, pending
    status: str = Field(default="pending") 
    
    # Soft delete flag
    # is_deleted: bool = Field(default=False)

    # Relationships
    user: "User" = Relationship(back_populates="cases")
    sections: List["LegalSection"] = Relationship(back_populates="legal_case")
    # It lets you write simple code like case.user.name to instantly fetch linked data, 
    # saving you from writing massive, complex SQL queries to combine tables.


    # In database design, tables constantly talk to each other.
    #  Your User file needs to import LegalCase to list a user's cases,
    #  and your LegalCase file needs to import User to know who the owner is.
    #  If they both import each other at the exact same time, Python gets confused, 
    # creates an infinite loop, and crashes. This is called a Circular Import.