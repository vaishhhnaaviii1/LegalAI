from uuid import UUID
from datetime import datetime
# BaseModel is a pre-built engine provided by a Python library called Pydantic. It does all the heavy, boring work of inspecting and verifying data
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.section import LegalSection
from app.schemas.precedent import PrecedentRead
from app.schemas.section import ChargeRead

# Whenever data comes into your app (from the user) or goes out of your app (from the AI or Kanoon),
#  this file stops it, measures it, and makes sure it fits the exact shapes defined here.

# ==========================================
# Input schema classes
# ==========================================
# It is for accepting data from user
class CaseRequest(BaseModel):
    # NEW: This forces Pydantic to trim spaces before checking min_length
    model_config = {"str_strip_whitespace": True}
    case_description: str = Field(
        ...,
        min_length=10,
        description="The facts of the legal incident to be analyzed.",
        max_length=5000,
    )
    user_id: UUID = Field(description="The UUID of the user creating this case.")


# This schema is for when a lawyer approves a case and submits their final summary.
class CaseSummaryApproveRequest(BaseModel):
    lawyer_approved_summary: str = Field(
        ...,
        min_length=10,
        description="The final, human-verified summary of the case facts.",
    )

#This schema is strictly for Database Operations.
# It acts as a bridge between the API route and the CRUD class.
# It ensures that the data passed to the database is in the correct format.
class LegalCaseCreate(BaseModel):
    title: str = "Untitled Case"
    raw_description: str
    user_id: UUID
    status: str = "pending"


class LegalCaseUpdate(BaseModel):
    title: str | None = None
    raw_description: str | None = None
    status: str | None = None
    lawyer_approved_summary: str | None = None
    is_deleted: bool | None = None



# ==========================================
# Input schema classes
# ==========================================

# Update your existing CaseResponse to include the new list
class CaseResponse(BaseModel):
    case_summary: str = Field(
        description="A concise one-sentence legal summary of the incident."
    )
    applicable_charges: list[LegalSection] = Field(
        description="Comprehensive list of all applicable penal charges."
    )
    # NEW: We make this optional so the AI doesn't try to generate it.
    # We will populate it manually from the Kanoon API.
    precedent_cases: list[PrecedentRead] | None = None



# NEW: The schema for reading a case from the database
# 1. THE DASHBOARD VIEW (List API)
class CaseListRead(BaseModel):
    id: UUID
    title: str
    status: str
    updated_at: datetime  # This represents "Last Modified"

    model_config = ConfigDict(from_attributes=True)


# 2. THE WORKSPACE VIEW (Detail API)
class CaseDetailRead(BaseModel):
    id: UUID
    title: str
    raw_description: str  # Original Summary/Facts
    llm_summary: str | None = None
    lawyer_approved_summary: str | None = None  # New Summary
    status: str
    applicable_charges: list[ChargeRead] = []  # IPC/BNS sections + Approved status
    precedent_cases: list[PrecedentRead] = []  # Kanoon cases

    model_config = ConfigDict(from_attributes=True)


class CaseRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    raw_description: str
    llm_summary: str | None = None
    lawyer_approved_summary: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # This tells Pydantic to happily read database rows!


# (Also, if you haven't already, ensure you have a simple DraftResponse to hold the AI's first output)
class DraftResponse(BaseModel):
    title: str
    summary: str
