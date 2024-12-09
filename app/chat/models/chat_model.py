import json
from wsgiref import validate
from pydantic import parse_obj_as
from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.config.db import Base
from app.enums.answer_type_enum import AnswerTypeEnum

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, index=True)
    corpus_key = Column(Integer, nullable=False)
    sender_id = Column(Integer, nullable=False)
    chat_id = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False)
    entry = Column(String(255), nullable=False)
    answer = Column(String(255), nullable=False)
    answer_type = Column(Enum(AnswerTypeEnum), nullable=False)
    created_at = DateTime()