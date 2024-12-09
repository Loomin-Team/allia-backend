from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.config.db import Base

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True, index=True)
    corpus_key = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)  # Specify maximum length (e.g., 255)
    created_at = Column(DateTime, nullable=False)

    messages = relationship('Message', back_populates='chat')