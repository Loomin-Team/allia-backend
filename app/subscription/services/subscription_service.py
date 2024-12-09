from datetime import datetime
from sqlite3 import IntegrityError
from app.models.subscription import Subscription
from app.subscription.schemas.subscription_schema import SubscriptionRequest, SubscriptionResponse
from sqlalchemy.orm import Session

class SubscriptionService:
    @staticmethod
    def add_subscription(subscription: SubscriptionRequest, db: Session):
        #user = db.query(User).filter(User.id == user_id).first()
        #if not user:
        #    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no existe.")

        new_subscription = Subscription(
            user_id=subscription.user_id,
            price=subscription.price,
            subscription_plan=subscription.subscription_plan,
            payment_date=datetime.now()
        )

        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        
        return new_subscription
    
    @staticmethod
    def get_subscription_by_user_id(user_id: int, db: Session):
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        return subscription