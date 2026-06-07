from pydantic import BaseModel
from typing import List


class IPCPrediction(BaseModel):
    section_code: str
    title: str
    punishment: str
    reason: str


class IPCResponse(BaseModel):
    sections: List[IPCPrediction]