# Whenever data comes into your app (from the user) or goes out of your app (from the AI or Kanoon),
#  this file stops it, measures it, and makes sure it fits the exact shapes defined here.
import uuid
from uuid import UUID
# BaseModel is a pre-built engine provided by a Python library called Pydantic. It does all the heavy, boring work of inspecting and verifying data
from pydantic import BaseModel, Field, model_validator
from app.errors import invalid_payload_message
from datetime import datetime
from pydantic import BaseModel

# NEW: This forces Pydantic to trim spaces before checking min_length
model_config = {
        "str_strip_whitespace": True
    }

# It is for accepting data from user
class CaseRequest(BaseModel):
    case_description: str = Field(
        ..., 
        min_length=10, 
        description="The facts of the legal incident to be analyzed.",
        max_length=5000
    )
    user_id: UUID = Field(
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

# 1. New schema for reading a Precedent
class PrecedentRead(BaseModel):
    id: uuid.UUID
    title: str
    doc_id: str
    doc_url: str             # <--- Now the frontend can just slap this into an <a href> tag!
    ai_score: float | None = None
    
# Update your existing CaseResponse to include the new list
class CaseResponse(BaseModel):
    case_summary: str = Field(description="A concise one-sentence legal summary of the incident.")
    applicable_charges: list[LegalSection] = Field(description="Comprehensive list of all applicable penal charges.")
    # NEW: We make this optional so the AI doesn't try to generate it. 
    # We will populate it manually from the Kanoon API.
    precedent_cases: list[PrecedentRead] | None = None

# This schema is strictly for Database Operations. 
# It acts as a bridge between the API route and the CRUD class.
# It ensures that the data passed to the database is in the correct format.
class LegalCaseCreate(BaseModel):
    title: str = "Untitled Case"
    raw_description: str
    user_id: UUID
    status: str = "pending"



# ==========================================
# USER SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    name: str
    email: str # Optionally use EmailStr if you have pydantic[email] installed
    phone_no: str | None = None
    password: str = Field(min_length=6)

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone_no: str | None = None
    is_active: bool | None = None

# ==========================================
# LEGAL CASE SCHEMAS (For CRUD ops)
# ==========================================

class LegalCaseUpdate(BaseModel):
    title: str | None = None
    raw_description: str | None = None
    status: str | None = None
    lawyer_approved_summary: str | None = None
    is_deleted: bool | None = None

# ==========================================
# LEGAL SECTION SCHEMAS (For CRUD ops)
# ==========================================
class LegalSectionCreate(BaseModel):
    case_id: UUID
    ipc_section: str
    bns_section: str
    reason: str
    source: str = "LLM"

class LegalSectionUpdate(BaseModel):
    is_approved: bool | None = None
    has_lawyer_verified: bool | None = None


 

# ... (keep your existing CaseRequest, CaseResponse, etc.)

# NEW: The schema for reading a case from the database
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

# This schema is for when a lawyer approves a case and submits their final summary.
class CaseSummaryApproveRequest(BaseModel):
        lawyer_approved_summary: str = Field(
        ..., 
        min_length=10,
        description="The final, human-verified summary of the case facts."
    )

 # (Also, if you haven't already, ensure you have a simple DraftResponse to hold the AI's first output)
class DraftResponse(BaseModel):
        title: str
        summary: str


# Used in Phase 3 to represent a single charge the lawyer approved/added
class ChargeItem(BaseModel):
    ipc_section: str
    bns_section: str
    reason: str
    is_approved: bool

# 1. The new format for the Tick/Cross UI
class ChargeUpdateItem(BaseModel):
    # Existing AI charges will have an ID. New charges added by the lawyer won't!
    id: UUID | None = None 
    ipc_section: str
    bns_section: str
    reason: str
    is_approved: bool # True if Ticked, False if Crossed

class rejectedChargeItem(BaseModel):
    id: UUID
    reason: str

# 2. The payload the frontend sends when they click "Finalize"
class ChargesActionRequest(BaseModel):
    approved_id: list[UUID] | None = Field(
        None,
        description="List of IDs for charges that the lawyer approved (Ticked)."
    )
    rejected_data: list[rejectedChargeItem] | None = Field(
        None,
        description="List of objects containing IDs and reasons for charges that the lawyer rejected (Crossed)."
    )

    @model_validator(mode='after') 
    def validate_at_least_one_present(self):
        """
        Validates that at least one of 'approved_id' or 'rejected_data' 
        is provided and is not an empty list.
        """
        # Evaluates to False if they are None or empty lists ([])
        has_approved = bool(self.approved_id)
        has_rejected = bool(self.rejected_data)

        if not has_approved and not has_rejected:
            raise ValueError(invalid_payload_message())
        
        return self
    # final_charges: list[ChargeUpdateItem]


class NewChargeRequest(BaseModel):
    ipc_section: str
    bns_section: str
    reason: str

# Authorisation 
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    name: str
    email: str