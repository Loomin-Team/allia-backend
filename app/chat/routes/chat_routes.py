from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.chat.schemas.message_schema import MessageDemoRequest, MessageRequest, MessageTurnRequest
from app.chat.services.chat_services import ChatService
from app.config.db import get_db

chats = APIRouter()
tag = "Chats"
endpoint = "/chats"

@chats.post("/chats", summary="Create a new chat", tags=[tag])
def create_chat(message_request: MessageRequest, db: Session = Depends(get_db)):
    """
    Create a new chat with the provided entry.
    """
    try:
        chat = ChatService.create_chat(message_request, db)
        return {"success": True, "chat": chat}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@chats.post("/chats/demo", summary="Create a new chat demo", tags=[tag])
def create_chat(message_request: MessageDemoRequest):
    """
    Create a new chat demo with the provided entry.
    """
    try:
        chat = ChatService.create_chat_demo(message_request)
        return {"success": True, "chat": chat}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chats.post("/reply", summary="Post a reply to an existing chat", tags=[tag])
def create_reply(turn_request: MessageTurnRequest, db: Session = Depends(get_db)):
    """
    Post a reply to an existing chat.
    """
    try:
        reply = ChatService.create_reply(turn_request, db)
        return {"success": True, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@chats.get("/{user_id}", summary="Get chats by user id", tags=[tag])
def get_chats_by_user_id(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve chats for the given `user_id`.
    """
    try:
        chats = ChatService.get_chats_by_user_id(user_id, db)
        if not chats:
            raise HTTPException(status_code=404, detail="No chats found for this user")

        return {"success": True, "chats": chats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chats.get("/messages/{chat_id}", summary="Get messages by chat id", tags=[tag])
def get_messages_by_chat_id(chat_id: str, db: Session = Depends(get_db)):
    """
    Retrieve messages for the given `chat_id`.
    """
    try:
        messages = ChatService.get_messages_by_chat_id(chat_id, db)
        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for this chat")

        return {"success": True, "messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
