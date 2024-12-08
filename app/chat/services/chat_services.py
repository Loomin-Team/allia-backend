import os
import requests
import json

from sqlalchemy import null

from app.chat.models.corpus_model import Corpus

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