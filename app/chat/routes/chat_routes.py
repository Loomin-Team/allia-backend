from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.chat.services.chat_services import ChatService
from app.config.db import get_db

chats = APIRouter()
tag = "Chat"
endpoint = "/chats"


class ChatRequest(BaseModel):
    entry: str


@chats.post("/", summary="Create a new chat", tags=[tag])
def create_chat(chat_request: ChatRequest, db: Session = Depends(get_db)):
    """
    Create a new chat with the provided entry.
    """
    try:
        corpus_key = ChatService.create_corpus(db)
        ChatService.index_document(chat_request.entry, "us", corpus_key)
        chat = ChatService.create_chat(chat_request.entry, corpus_key)
        return {"success": True, "chat": chat}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chats.post("/{chat_id}/reply", summary="Post a reply to an existing chat", tags=[tag])
def create_reply(chat_id: str, chat_request: ChatRequest, db: Session = Depends(get_db)):
    """
    Post a reply to an existing chat with the given `chat_id`.
    """
    try:
        reply = ChatService.create_reply(chat_request.entry, chat_id, db)
        return {"success": True, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chats.get("/{chat_id}/history", summary="Get chat history", tags=[tag])
def get_chat_history(chat_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the chat history for the given `chat_id`.
    """
    try:
        history = ChatService.get_chat_history(chat_id, db)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
