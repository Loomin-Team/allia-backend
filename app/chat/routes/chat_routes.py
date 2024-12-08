from fastapi import APIRouter, Depends
from requests import Session

from app.chat.services.chat_services import ChatService
from app.config.db import get_db

chats = APIRouter()
tag = "Chat"
endpoint = "/chats"

@chats.post("/chats/{entry}")
def create_chat(entry: str, db: Session = Depends(get_db)):
    corpus_key = ChatService.create_corpus(db)
    ChatService.index_document("Technology is the application of scientific knowledge for practical purposes, especially in industry.", "us", corpus_key)
    return ChatService.create_chat(entry, corpus_key)
