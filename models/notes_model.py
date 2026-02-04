from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NoteModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    project_name: str
    created_by_user_email: str
    created_date: str
    notes: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "project_name": "Teen Theory Platform",
                "created_by_user_email": "user@example.com",
                "created_date": "2026-02-04 14:30:00",
                "notes": "This is a sample note for the project."
            }
        }


class NoteUpdateModel(BaseModel):
    project_name: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Updated Project Name",
                "notes": "Updated note content."
            }
        }
