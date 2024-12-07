from fastapi import APIRouter

from app.subscription.routes.subscription_router import subscriptions
from app.auth.routes.auth_routes import auth

from app.users.routes.user_routes import users
from app.profiles.routes.profiles_routes import profiles

from app.config.routes import prefix
routes = APIRouter()


routes.include_router(auth, prefix= prefix, tags=["Auth"])
routes.include_router(users, prefix=prefix, tags=["Users"])
routes.include_router(profiles, prefix= prefix, tags=["Profiles"])
routes.include_router(subscriptions,  prefix= prefix, tags=["Subscriptions"])