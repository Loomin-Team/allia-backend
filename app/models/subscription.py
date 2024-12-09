from typing import TYPE_CHECKING
from app.enums.subscription_plan_enum import SusbscriptionPlanEnum
from sqlalchemy import Column, ForeignKey, Integer, Float, Enum, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.config.db import Base

if TYPE_CHECKING:
    from app.models.user import User

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    subscription_plan: Mapped[SusbscriptionPlanEnum] = mapped_column(Enum(SusbscriptionPlanEnum), nullable=False)
    payment_date: Mapped[str] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
