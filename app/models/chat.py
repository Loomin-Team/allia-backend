from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.config.db import Base

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(String(255), primary_key=True, index=True)
    corpus_key = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False) 
    created_at = Column(DateTime, nullable=False)

    message = relationship('Message', back_populates='messages')