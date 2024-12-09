import requests
import json
import datetime

from app.chat.schemas.message_schema import MessageRequest, MessageTurnRequest
from app.utils.vectara import VectaraClient
from app.utils.groq import GroqClient
from app.utils.webscrapping.google_scraper import GoogleNewsWebScraper
from app.utils.webscrapping.bing_scraper import BingNewsWebScraper
from app.models.chat import Chat
from app.models.message import Message

class ChatService:
    @staticmethod
    def create_chat(message_request: MessageRequest, db: requests.Session, is_demo: bool = False):
        """
        Creates a chat or a demo chat depending on the `is_demo` flag.

        Args:
            message_request (MessageRequest): The message request object.
            db (Session): The database session.
            is_demo (bool): Indicates if this is a demo request.

        Returns:
            dict or Chat: The created chat or a dictionary with the chat demo details.
        """

        
        vectara_client = VectaraClient()

        # Create a corpus
        corpus_description = "Demo corpus for user interaction" if is_demo else "Documents with important information for the prompt."
        corpus_key = vectara_client.create_corpus(description=corpus_description)

        # Use Groq for query generation
        groq_client = GroqClient()
        query_data = groq_client.generate_news_query(user_description=message_request.entry)
        query_content = query_data["query"]
        query_language = query_data["language"]

        # Use web scraping
        google_scraper = GoogleNewsWebScraper()
        concatenated_google = google_scraper.get_news(query=query_content, language=query_language, max_results=5)

        bing_scraper = BingNewsWebScraper()
        concatenated_bing = bing_scraper.get_news(query=query_content, language=query_language, max_results=5)

        # Index documents into the corpus
        vectara_client.index_document(concatenated_google, query_language, corpus_key)
        vectara_client.index_document(concatenated_bing, query_language, corpus_key)

        
        # Payload preparation
        payload = {
            "query": message_request.entry,
            "search": {
                "corpora": [
                    {
                        "corpus_key": corpus_key,
                        "lexical_interpolation": 0.025,
                        "semantics": "default"
                    }
                ],
                "offset": 0,
                "limit": 10,
                "context_configuration": {
                    "characters_before": 30,
                    "characters_after": 30,
                    "sentences_before": 3,
                    "sentences_after": 3,
                    "start_tag": "<em>",
                    "end_tag": "</em>"
                },
                "reranker": {
                    "type": "customer_reranker",
                    "reranker_name": "Rerank_Multilingual_v1",
                    "limit": 1,
                    "cutoff": 0
                }
            },
            "generation": {
                "generation_preset_name": "vectara-summary-ext-v1.2.0",
                "max_used_search_results": 5,
                "prompt_template": f"""
                [
                {{"role": "system", "content": "You are a helpful assistant. You will create a response based on the user's query and the tone provided."}},
                {{"role": "user", "content": "{message_request.entry}, with a {message_request.tone.value} tone."}},
                {{"role": "assistant", "content": "Generate a response with the specified tone: {message_request.tone.value}"}}
                ]
                """,
                "max_response_characters": 250,
                "response_language": "auto",
                "model_parameters": {
                    "max_tokens": 500,
                    "temperature": 0,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                },
                "citations": {
                    "style": "none",
                    "url_pattern": "https://vectara.com/documents/{doc.id}",
                    "text_pattern": "{doc.title}"
                },
                "enable_factual_consistency_score": True
            },
            "chat": {
                "store": True
            },
            "save_history": True,
            "stream_response": False
        }

        
        response = requests.post(f"{vectara_client.BASE_URL}/chats", headers=vectara_client._get_headers(), data=payload)
        response.raise_for_status()
        response_data = response.json()
            
        answer = response_data.get('answer', "No answer available")
        chat_id = response_data.get('chat_id', "No chat id available")
        turn_id = response_data.get('turn_id', "No turn id available")

        formatted_response = {
            "id": turn_id,
            "chat_id": chat_id,
            "answer": answer,
            "created_at": datetime.now(),
            "entry": message_request.entry,
            "tone": message_request.tone.value,
            "answer_type": message_request.answer_type.value
        }

        # If it's a demo, create a demo response
        if is_demo:
            return formatted_response
        try:
            new_chat = Chat(
                id = chat_id,
                corpus_key = corpus_key,
                title = query_content,
                created_at = datetime.now()
            )
            
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)
            
            new_message = Message(
                id = turn_id,
                user_id = message_request.user_id,
                chat_id = chat_id,
                entry = message_request.entry,
                answer = answer,
                tone = message_request.tone,
                answer_type = message_request.answer_type,
                created_at = datetime.now()
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            return new_message
        except Exception as e:
            raise Exception(f"Failed to create chat: {e}")

    @staticmethod
    def create_reply(turn_request: MessageTurnRequest, db: requests.Session):
        vectara_client = VectaraClient()
        groq_client = GroqClient()

        # Get the corpus key from the chat ID
        chat = db.query(Chat).filter(Chat.id == turn_request.chat_id).first()
        if not chat:
            raise ValueError("Chat not found.")
        corpus_key = chat.corpus_key

        # Generate query using Groq
        query_data = groq_client.generate_query(user_description=turn_request.entry)
        query_content = query_data["query"]
        query_language = query_data["language"]

        reply_payload = json.dumps({
            "query": turn_request.entry,
            "search": {
                "corpora": [
                {
                    "corpus_key": corpus_key,
                    "lexical_interpolation": 0.025,
                    "semantics": "default"
                }
                ],
                "offset": 0,
                "limit": 10,
                "context_configuration": {
                "characters_before": 30,
                "characters_after": 30,
                "sentences_before": 3,
                "sentences_after": 3,
                "start_tag": "<em>",
                "end_tag": "</em>"
                },
                "reranker": {
                "type": "customer_reranker",
                "reranker_name": "Rerank_Multilingual_v1",
                "limit": 1,
                "cutoff": 0
                }
            },
            "generation": {
                "generation_preset_name": "vectara-summary-ext-v1.2.0",
                "max_used_search_results": 5,
                "prompt_template": f"""
                [
                {{"role": "system", "content": "You are a helpful assistant. You will create a response based on the user's query and the tone provided."}},
                {{"role": "user", "content": "{turn_request.entry}, with a {turn_request.tone.value} tone."}},
                {{"role": "assistant", "content": "Generate a response with the specified tone: {turn_request.tone.value}"}}
                ]
                """,
                "max_response_characters": 300,
                "response_language": "auto",
                "model_parameters": {
                "max_tokens": 500,
                "temperature": 0,
                "frequency_penalty": 0,
                "presence_penalty": 0
                },
                "citations": {
                "style": "none",
                "url_pattern": "https://vectara.com/documents/{doc.id}",
                "text_pattern": "{doc.title}"
                },
                "enable_factual_consistency_score": True
            },
            "chat": {
                "store": True
            },
            "save_history": True,
            "stream_response": False
        })
            
         # Send the reply to Vectara and get the response
        vectara_response = vectara_client.create_reply_turn(turn_request.chat_id, reply_payload)

        # Extract information from Vectara response
        turn_id = vectara_response.get("turn_id")
        answer = vectara_response.get("answer", "No answer available")

        # Save the reply in the database
        reply_message = Message(
            id=turn_id,
            user_id=turn_request.user_id,
            chat_id=turn_request.chat_id,
            entry=turn_request.entry,
            answer=answer,
            tone=turn_request.tone,
            created_at=datetime.now()
        )
        db.add(reply_message)
        db.commit()
        db.refresh(reply_message)

        return reply_message
   
    @staticmethod
    def get_chats_by_user_id(user_id: int, db: requests.Session):
        try: 
            chats = db.query(Chat).join(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).all()
            return chats
        except Exception as e:
            print(f"Error getting chats by user ID: {e}")
            return []
        
    @staticmethod
    def get_messages_by_chat_id(chat_id: str, db: requests.Session):
        try:
            messages = db.query(Message).filter(Message.chat_id == chat_id).all()
            return messages
        except Exception as e:
            print(f"Error getting messages by chat ID: {e}")
            return []