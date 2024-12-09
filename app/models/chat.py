from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.config.db import Base

if TYPE_CHECKING:
    from app.models.message import Message

class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    corpus_key: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)

    # Relationship
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")
