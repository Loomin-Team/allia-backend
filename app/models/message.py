from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.config.db import Base
from app.enums.answer_type_enum import AnswerTypeEnum
from app.enums.message_tone_enum import MessageToneEnum

class Message(Base):
    __tablename__ = 'messages'
    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ForeignKey to the 'users' table
    chat_id = Column(String(255), ForeignKey('chats.id'), nullable=False)  # ForeignKey to the 'chats' table
    entry = Column(Text, nullable=False)  
    answer = Column(Text, nullable=False)  
    tone = Column(Enum(MessageToneEnum), nullable=False)
    answer_type = Column(Enum(AnswerTypeEnum), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='users')  
    chat = relationship('Chat', back_populates='chats')  