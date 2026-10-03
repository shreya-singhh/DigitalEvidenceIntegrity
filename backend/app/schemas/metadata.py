from pydantic import BaseModel

class MetadataBase(BaseModel):
    data: str
