from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.enums.answer_type_enum import AnswerTypeEnum
        
class ChatResponse(BaseModel):
    chat_id: str
    title: str
    created_at: datetime

    class Config:
        orm_mode = True 