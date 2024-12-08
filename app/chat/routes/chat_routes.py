from fastapi import APIRouter, Depends
from requests import Session

from app.chat.services.chat_services import ChatService
from app.config.db import get_db

chats = APIRouter()
tag = "Chat"
endpoint = "/chats"

@chats.post("/chats")
def create_chat(db: Session = Depends(get_db)):
    corpus_key = ChatService.create_corpus(db)
    return ChatService.index_document("Hello, world!", corpus_key, db)
