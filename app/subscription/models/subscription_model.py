import json
from wsgiref import validate
from pydantic import parse_obj_as
from app.enums.subscription_plan_enum import SusbscriptionPlanEnum
from sqlalchemy import JSON, Enum, Column, ForeignKey, Integer, Nullable, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.config.db import Base

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float, nullable=False)
    subscription_plan = Column(Enum(SusbscriptionPlanEnum), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False)
    #user_id = Column(Integer, ForeignKey('users.id'), nullable=False, default=None)
    
    #user = relationship("User", back_populates="users")