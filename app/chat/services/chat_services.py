import requests

from app.chat.schemas.chat_schema import ChatRequest
from app.utils.vectara import VectaraClient

class ChatService:
    @staticmethod
    def create_chat(chat_request: ChatRequest, db: requests.Session):
        try:
            vectara_client = VectaraClient()
            chat = vectara_client.create_chat(chat_request, db)
            return chat
        except Exception as e:
            return {"status": "error", "message": "Failed to create chat", "details": str(e)}


    @staticmethod
    def create_reply(entry: str, chat_id: str, db: requests.Session):
        # TODO: To be implemented
        pass

    @staticmethod
    def get_chat_history(chat_id: str, db: requests.Session):
        # TODO: To be implemented
        pass