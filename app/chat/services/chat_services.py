import requests

from app.chat.schemas.chat_schema import ChatRequest
from app.utils.vectara import VectaraClient

class ChatService:
    
    @staticmethod
    def create_chat(chat_request: ChatRequest, db: requests.Session):
        vectara_client = VectaraClient()
        chat = vectara_client.create_chat(chat_request, db)
        return chat

    @staticmethod
    def create_reply(entry: str, chat_id: str, db: requests.Session):
        # TODO: To be implemented
        pass

    @staticmethod
    def get_chat_history(chat_id: str, db: requests.Session):
        vectara_client = VectaraClient()
        chat_history = vectara_client.get_chat_by_id(chat_id, db)
        return chat_history
        
    @staticmethod
    def get_chat_by_user_id(user_id: int, db: requests.Session):
        vectara_client = VectaraClient()
        chat_history = vectara_client.get_chat_by_user_id(user_id, db)
        return chat_history
        