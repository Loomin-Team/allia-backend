from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.config.db import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.subscription import Subscription

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fullname: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(155), unique=True, index=True, nullable=False)
    profile_picture: Mapped[str] = mapped_column(String(255), default="")
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    registered: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user")
