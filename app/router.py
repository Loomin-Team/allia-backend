from fastapi import APIRouter

from app.subscription.routes.subscription_router import subscriptions

from app.config.routes import prefix
routes = APIRouter()

# Include all the routes
routes.include_router(subscriptions,  prefix= prefix, tags=["Subscriptions"])