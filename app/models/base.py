import uuid  #Universal Unique Identifier. It generates a random 36-character string
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class BaseModel(SQLModel):
    # Automatically generates a unique UUID for every new row
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    # default_factory=uuid.uuid4:Every single time a new row is inserted, run this function fresh to generate a completely random, unique ID
    # Automatically sets the time when created
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # lambda: A function,executes fresh the exact split-second the row is saved to insert the current time in UTC.
    # Automatically updates this timestamp whenever the row is modified
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc)
        },
        nullable=False
    )
#sa_column_kwargs: sa: SQLAlchemy Column Keyword Arguments.
# Take these key-value pairs and pass them directly down to the underlying SQLAlchemy Column constructor exactly as they are written. Do not alter them."
    is_deleted: bool =Field(
        default=False,
        nullable=False
     )