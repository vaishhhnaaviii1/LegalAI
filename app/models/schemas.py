# Whenever data comes into your app (from the user) or goes out of your app (from the AI or Kanoon),
#  this file stops it, measures it, and makes sure it fits the exact shapes defined here.

import uuid
from typing import Optional
# BaseModel is a pre-built engine provided by a Python library called Pydantic. It does all the heavy, boring work of inspecting and verifying data
from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import BaseModel

# It is for accepting data from user
class CaseRequest(BaseModel):
    title: str = Field(
        default="Untitled Case", 
        description="The title of the legal case. Defaults to 'Untitled Case'."
    )
    case_description: str = Field(
        ..., 
        min_length=10, 
        description="The facts of the legal incident to be analyzed."
    )
    user_id: uuid.UUID = Field(
        description="The UUID of the user creating this case."
    )
# It si embedded in case response and is used to define the shape of the data that the AI will return for each legal section it identifies.
class LegalSection(BaseModel):
    ipc_section: str = Field(description="The applicable Indian Penal Code (IPC) section, e.g., 'Section 378'")
    bns_equivalent: str = Field(description="The equivalent section in the Bharatiya Nyaya Sanhita (BNS), e.g., 'Section 303(2)'")
    offense: str = Field(description="The name of the crime, e.g., 'Theft'")
    explanation: str = Field(description="A brief, precise legal explanation of why this section applies to the provided facts.")

# This is the new schema for the precedent cases we will fetch from Kanoon. Each case has a title, a unique document ID, a brief snippet, and a URL to the full case on Indian Kanoon.
class ReferenceCase(BaseModel):
    title: str = Field(description="The title of the court case.")
    doc_id: str = Field(description="The Indian Kanoon document ID.")
    snippet: str = Field(description="A brief text snippet from the judgment.")
    url: str = Field(description="The full URL to the Indian Kanoon document.")

# Update your existing CaseResponse to include the new list
class CaseResponse(BaseModel):
    case_summary: str = Field(description="A concise one-sentence legal summary of the incident.")
    applicable_charges: list[LegalSection] = Field(description="Comprehensive list of all applicable penal charges.")
    # NEW: We make this optional so the AI doesn't try to generate it. 
    # We will populate it manually from the Kanoon API.
    precedent_cases: list[ReferenceCase] | None = None

# This schema is strictly for Database Operations. 
# It acts as a bridge between the API route and the CRUD class.
# It ensures that the data passed to the database is in the correct format.
class LegalCaseCreate(BaseModel):
    title: str = "Untitled Case"
    raw_description: str
    user_id: uuid.UUID
    status: str = "pending"



# ==========================================
# USER SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    name: str
    email: str # Optionally use EmailStr if you have pydantic[email] installed
    phone_no: Optional[str] = None
    password: str = Field(min_length=6)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_no: Optional[str] = None
    is_active: Optional[bool] = None

# ==========================================
# LEGAL CASE SCHEMAS (For CRUD ops)
# ==========================================

class LegalCaseUpdate(BaseModel):
    title: Optional[str] = None
    raw_description: Optional[str] = None
    status: Optional[str] = None
    lawyer_approved_summary: Optional[str] = None
    is_deleted: Optional[bool] = None

# ==========================================
# LEGAL SECTION SCHEMAS (For CRUD ops)
# ==========================================
class LegalSectionCreate(BaseModel):
    case_id: uuid.UUID
    ipc_section: str
    bns_section: str
    reason: str
    source: str = "LLM"

class LegalSectionUpdate(BaseModel):
    is_approved: Optional[bool] = None
    has_lawyer_verified: Optional[bool] = None


 

# ... (keep your existing CaseRequest, CaseResponse, etc.)

# NEW: The schema for reading a case from the database
class CaseRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    raw_description: str
    llm_summary: str | None = None
    lawyer_approved_summary: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # This tells Pydantic to happily read database rows!