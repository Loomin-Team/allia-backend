from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.config.db import Base
from app.enums.answer_type_enum import AnswerTypeEnum
from app.enums.message_tone_enum import MessageToneEnum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chat import Chat

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)  
    entry: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[MessageToneEnum] = mapped_column(Enum(MessageToneEnum), nullable=False)
    answer_type: Mapped[AnswerTypeEnum] = mapped_column(Enum(AnswerTypeEnum), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
