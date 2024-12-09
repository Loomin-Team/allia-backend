from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(255), nullable=False)
   # username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(155), unique=True, index=True, nullable=False)
    profile_picture = Column(String(255), default="")
    password = Column(String(255), nullable=False)
    registered = Column(Boolean, default=False)

    messages = relationship('Message', back_populates='user')
    subscriptions = relationship('Subscription', back_populates='user')