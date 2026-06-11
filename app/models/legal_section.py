from uuid import UUID
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.legal_case import LegalCase

class LegalSection(BaseModel, table=True):
    # Foreign Key pointing to the Case UUID
    case_id: UUID = Field(foreign_key="legalcase.id")
    
    ipc_section: str
    bns_section: str
    reason: str
    
    # 1/0 Bool/Null as requested
    is_approved: bool| None=Field(default=None) 
    
    # Source: Lawyer or LLM
    source: str = Field(default="LLM") 
    has_lawyer_verified: bool = Field(default=False)

    # Relationship linking back to the Case
    legal_case: "LegalCase" = Relationship(back_populates="sections")