from uuid import UUID, uuid4 # Universal Unique Identifier. It generates a random 36-character string
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
import uuid 

# Helper function to get strict UTC time, but format it so PostgreSQL accepts it
def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BaseModel(SQLModel):
    # Automatically generates a unique UUID for every new row
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    # Automatically sets the time when created
    created_at: datetime = Field(
        default_factory=get_utc_now,
        nullable=False
    )

    # Automatically updates this timestamp whenever the row is modified
    updated_at: datetime = Field(
        default_factory=get_utc_now,
        nullable=False,
        sa_column_kwargs={
            "onupdate": get_utc_now
        }
    )
    
    # --- SOFT DELETE FIELDS ---
    is_deleted: bool = Field(default=False, index=True)

    deleted_at: datetime | None = Field(
        default=None,
        nullable=True
    )