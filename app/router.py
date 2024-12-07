from fastapi import APIRouter

from app.subscription.routes.subscription_router import subscriptions
from app.auth.routes.auth_router import auth

from app.config.routes import prefix
routes = APIRouter()

# Include all the routes
routes.include_router(subscriptions,  prefix= prefix, tags=["Subscriptions"])
routes.include_router(auth, prefix= prefix, tags=["Auth"])