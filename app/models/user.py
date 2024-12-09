from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, mapped_column
from app.config.db import Base

class User(Base):
    __tablename__ = 'users'

    id = mapped_column(Integer, primary_key=True, index=True)
    fullname = Column(String(255), nullable=False)
    email = Column(String(155), unique=True, index=True, nullable=False)
    profile_picture = Column(String(255), default="")
    password = Column(String(255), nullable=False)
    registered = Column(Boolean, default=False)

    messages = relationship('Message', back_populates='messages')
    subscriptions = relationship('Subscription', back_populates='subsriptions')
