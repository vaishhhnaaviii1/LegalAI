import uuid
from pydantic import BaseModel, Field

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