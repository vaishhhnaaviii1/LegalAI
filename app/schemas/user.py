from pydantic import BaseModel, Field

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