import requests

from app.chat.schemas.chat_schema import ChatResponse
from app.chat.schemas.message_schema import MessageDemoRequest, MessageRequest, MessageResponse, MessageTurnRequest
from app.utils.vectara import VectaraClient

from app.models.message import Message

class ChatService:
    
    @staticmethod
    def create_chat(message_request: MessageRequest, db: requests.Session):
        vectara_client = VectaraClient()
        chat = vectara_client.create_chat(message_request, db)
        return chat
    
    @staticmethod
    def create_chat_demo(message_request: MessageDemoRequest):
        vectara_client = VectaraClient()
        chat = vectara_client.create_chat_demo(message_request)
        return chat

    @staticmethod
    def create_reply(turn_request: MessageTurnRequest, db: requests.Session):
        vectara_client = VectaraClient()
        reply = vectara_client.create_index_reply(turn_request, db)
        return reply

   
    @staticmethod
    def get_chats_by_user_id(user_id: int, db: requests.Session):
        vectara_client = VectaraClient()
        chats = vectara_client.get_chats_by_user_id(user_id, db)
        return chats
        
    @staticmethod
    def get_messages_by_chat_id(chat_id: str, db: requests.Session):
        vectara_client = VectaraClient()
        messages = vectara_client.get_messages_by_chat_id(chat_id, db)
        return messages
    