from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.enums.subscription_plan_enum import SusbscriptionPlanEnum

class SubscriptionRequest(BaseModel):
    user_id: int
    price: float
    subscription_plan: SusbscriptionPlanEnum

    class Config:
        orm_mode = True 
        
        
class SubscriptionResponse(BaseModel):
    id: int
    price: float
    subscription_plan: SusbscriptionPlanEnum
    payment_date: datetime
    user_id: int

    class Config:
        orm_mode = True 