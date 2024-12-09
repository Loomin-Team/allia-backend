from sqlalchemy import Column, DateTime, Enum, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.config.db import Base
from app.enums.answer_type_enum import AnswerTypeEnum


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ForeignKey to the 'users' table
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)  # ForeignKey to the 'chats' table
    entry = Column(Text, nullable=False)  # Changed to Text for large text compatibility
    answer_type = Column(Enum(AnswerTypeEnum), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship('User', back_populates='messages')  
    chat = relationship('Chat', back_populates='messages')  
