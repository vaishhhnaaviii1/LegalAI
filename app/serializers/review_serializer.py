from pydantic import BaseModel


class IPCReviewRequest(BaseModel):
    decision: str