from datetime import datetime
import os
import requests
import json

from sqlalchemy import null

from app.chat.models.chat_model import Chat
from app.chat.models.corpus_model import Corpus
from app.chat.schemas.chat_schema import ChatRequest
from app.profiles.services.profiles_services import ProfileService

class ChatService:
    @staticmethod
    def create_chat(entry: str, corpus_key: str):
        pass

    @staticmethod
    def create_reply(entry: str, chat_id: str, db: requests.Session):
        # TODO: To be implemented
        pass

    @staticmethod
    def get_chat_history(chat_id: str, db: requests.Session):
        # TODO: To be implemented
        pass