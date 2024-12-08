from fastapi import APIRouter

from app.subscription.routes.subscription_router import subscriptions
from app.auth.routes.auth_routes import auth
from app.news.routes.webscraping_routes import news
from app.chat.routes.chat_routes import chats

from app.config.routes import prefix
routes = APIRouter()

# Include all the routes
routes.include_router(subscriptions,  prefix= prefix, tags=["Subscriptions"])
routes.include_router(auth, prefix= prefix, tags=["Auth"])
routes.include_router(news, prefix= prefix, tags=["News"])
routes.include_router(chats, prefix= prefix, tags=["Chats"])