from pydantic import BaseModel

class ReportBase(BaseModel):
    summary: str
