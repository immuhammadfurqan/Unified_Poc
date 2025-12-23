from pydantic import BaseModel

class BoardCreate(BaseModel):
    name: str

class CardCreate(BaseModel):
    list_id: str
    name: str
    desc: str = ""

