import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import BaseModel

class PrecedentCase(BaseModel, table=True):
    # 1. The Foreign Key linking it to the parent case
    case_id: uuid.UUID = Field(foreign_key="legalcase.id", index=True)
    
    # 2. Indian Kanoon Data
    title: str = Field(description="The official title of the legal precedent")
    doc_id: str = Field(description="The unique Kanoon document ID")  #TODO: Make it url for frontend
    doc_url: str = Field(description="The direct Indian Kanoon URL for the frontend") # <--- NEW
    
    
    # 4. The SQLAlchemy Relationship back to the parent
    parent_case: Optional["LegalCase"] = Relationship(back_populates="precedents")

if TYPE_CHECKING:
    # import for type checking / linters to recognize the model
    from app.models.legal_case import LegalCase

    ai_score: float | None = Field(
        default=None,
        description="The AI-generated relevance score for this precedent"
    )

