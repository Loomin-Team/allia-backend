from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.enums.answer_type_enum import AnswerTypeEnum
from app.enums.message_tone_enum import MessageToneEnum

class MessageRequest(BaseModel):
    user_id: int
    entry: str
    tone: MessageToneEnum
    answer_type: AnswerTypeEnum

    class Config:
        orm_mode = True 
        
class MessageDemoRequest(BaseModel):
    entry: str
    tone: MessageToneEnum
    answer_type: AnswerTypeEnum

    class Config:
        orm_mode = True 
        
class MessageTurnRequest(BaseModel):
    user_id: int
    entry: str
    tone: MessageToneEnum
    answer_type: AnswerTypeEnum
    chat_id: str

    class Config:
        orm_mode = True 
        
class MessageResponse(BaseModel):
    id: int
    chat_id: str
    answer: str
    entry: str
    answer_type: AnswerTypeEnum
    created_at: datetime

    class Config:
        orm_mode = True 