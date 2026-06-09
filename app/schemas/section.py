from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.errors import invalid_payload_message

# It si embedded in case response and is used to define the shape of the data that the AI will return for each legal section it identifies.
class LegalSection(BaseModel):
    ipc_section: str = Field(description="The applicable Indian Penal Code (IPC) section, e.g., 'Section 378'")
    bns_equivalent: str = Field(description="The equivalent section in the Bharatiya Nyaya Sanhita (BNS), e.g., 'Section 303(2)'")
    offense: str = Field(description="The name of the crime, e.g., 'Theft'")
    explanation: str = Field(description="A brief, precise legal explanation of why this section applies to the provided facts.")

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


class ChargeRead(BaseModel):
    id: UUID
    ipc_section: str
    bns_equivalent: str # We map bns_section to this so the frontend is happy
    explanation: str    # We map reason to this
    is_approved: bool | None = None