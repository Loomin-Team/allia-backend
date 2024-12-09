import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from app.subscription.schemas.subscription_schema import SubscriptionRequest, SubscriptionResponse
from app.subscription.services.subscription_service import SubscriptionService
from sqlalchemy.orm import Session
from app.config.db import get_db


subscriptions = APIRouter()
tag = "Subsription"
endpoint = "/subscriptions"

@subscriptions.get("/subscriptions/user/{user_id}", response_model=SubscriptionResponse)
def get_subscription_by_user_id(user_id: int, db: Session = Depends(get_db)):
    try:
        return SubscriptionService.get_subscription_by_user_id(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@subscriptions.post("/subscriptions", response_model=SubscriptionResponse)
def add_subscription(subscription_data: SubscriptionRequest, db: Session = Depends(get_db)):
    return SubscriptionService.add_subscription(subscription_data, db)