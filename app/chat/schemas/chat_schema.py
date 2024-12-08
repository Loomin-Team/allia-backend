from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.enums.answer_type_enum import AnswerTypeEnum

class ChatRequest(BaseModel):
    sender_id: int
    entry: str
    answer_type: AnswerTypeEnum

    class Config:
        orm_mode = True 
        
        
class ChatResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    entry: str
    answer: str
    answer_type: AnswerTypeEnum
    created_at: datetime

    class Config:
        orm_mode = True 