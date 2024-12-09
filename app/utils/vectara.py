from datetime import datetime
import os
import json
import string
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.chat.schemas.message_schema import MessageDemoRequest, MessageRequest, MessageTurnRequest
from app.models.chat import Chat
from app.models.message import Message
from app.profiles.services.profiles_services import ProfileService  
import random

from app.utils.groq import GroqClient
from app.utils.webscrapping.bing_scraper import BingNewsWebScraper
from app.utils.webscrapping.google_scraper import GoogleNewsWebScraper

load_dotenv()


class VectaraClient:
    """
    A client for interacting with the Vectara API, including creating corpora,
    indexing documents, and managing chats.
    """

    BASE_URL = "https://api.vectara.io/v2"
    API_KEY = os.getenv("VECTARA_API_KEY")

    def __init__(self):
        if not self.API_KEY:
            raise ValueError("VECTARA_API_KEY is not set in the environment.")

    def _get_headers(self):
        """
        Helper method to generate headers for API requests.
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.API_KEY
        }

    def create_corpus(self) -> str:
        """
        Creates a new corpus in Vectara and stores it in the database.

        Args:
            db (Session): The database session.

        Returns:
            str: The corpus key of the newly created corpus.

        Raises:
            Exception: If the API call fails or the corpus key is not returned.
        """

        corpus_key = ''.join(random.choices(string.ascii_letters + string.digits + "_=-", k=32))

        payload = json.dumps({
            "key": corpus_key,
            "name": corpus_key,
            "description": "Documents with important information for the prompt.",
            "queries_are_answers": False,
            "documents_are_questions": False,
            "encoder_id": "enc_0",
            "filter_attributes": [
                {
                    "name": "Title",
                    "level": "document",
                    "description": "The title of the document.",
                    "indexed": True,
                    "type": "text"
                }
            ],
            "custom_dimensions": []
        })

        try:
            response = requests.post(f"{self.BASE_URL}/corpora", headers=self._get_headers(), data=payload)
            response.raise_for_status()
            response_data = response.json()
            corpus_key = response_data.get("key")
            if not corpus_key:
                raise Exception("Corpus key not returned by API.")
            return corpus_key
        except Exception as e:
            raise Exception(f"Failed to create corpus: {e}")

    def index_document(self, text: str, lang: str, corpus_key: str) -> dict:
        """
        Indexes a document in the specified corpus.

        Args:
            text (str): The text of the document to index.
            lang (str): The language of the document.
            corpus_key (str): The key of the corpus.

        Returns:
            dict: A status dictionary indicating success or error.
        """
        payload = json.dumps({
            "id": "my-doc-id",
            "type": "core",
            "metadata": {
                "title": "A Nice Document",
                "lang": lang
            },
            "document_parts": [
                {
                    "text": text,
                    "metadata": {
                        "nice_rank": 9000
                    },
                    "context": "string",
                    "custom_dimensions": {}
                }
            ]
        })

        try:
            response = requests.post(f"{self.BASE_URL}/corpora/{corpus_key}/documents",
                                     headers=self._get_headers(), data=payload)
            response.raise_for_status()
            return {"status": "success", "message": "Document indexed successfully"}
        except Exception as e:
            return {"status": "error", "message": "Failed to index document", "details": str(e)}

    def create_new_turn(self, message: MessageRequest, title: str, corpus_key: str, db: Session) -> Chat:
        """
        Creates a new chat with the specified query and corpus.

        Args:
            entry (str): The query for the chat.
            corpus_key (str): The key of the corpus.

        Returns:
            dict: A status dictionary indicating success or error.
        """
        payload = json.dumps({
            "query": message.entry,
            "search": {
                "corpora": [
                {
                    "custom_dimensions": {},
                    "metadata_filter": None,
                    "lexical_interpolation": 0.025,
                    "semantics": "default",
                    "corpus_key": corpus_key
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
                {{"role": "user", "content": "{message.entry}, with a {message.tone.value} tone."}},
                {{"role": "assistant", "content": "Generate a response with the specified tone: {message.tone.value}"}}
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
        })

        try:
            response = requests.post(f"{self.BASE_URL}/chats", headers=self._get_headers(), data=payload)
            response.raise_for_status()
            response_data = response.json()  

            answer = response_data.get('answer', "No answer available")
            chat_id = response_data.get('chat_id', "No chat id available")
            turn_id = response_data.get('turn_id', "No turn id available")
                
            new_chat = Chat(
                id = chat_id,
                corpus_key = corpus_key,
                title = title,
                created_at = datetime.now()
            )
            
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)
            
            new_message = Message(
                id = turn_id,
                user_id = message.user_id,
                chat_id = chat_id,
                entry = message.entry,
                answer = answer,
                tone = message.tone,
                answer_type = message.answer_type,
                created_at = datetime.now()
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            return new_message
        
        except Exception as e:
            return {"status": "error", "message": "Failed to create chat", "details": str(e)}
        
    
    def create_chat(self, message_request: MessageRequest, db: Session):
        
        # Create corpus
        corpus_key = self.create_corpus()
        
        # Use Groq
        groq_client = GroqClient()
        query_data = groq_client.generate_news_query(user_description=message_request.entry)
        query_content = query_data["query"] 
        query_language = query_data["language"]
        
        # Use Webscrapping
        google_scraper = GoogleNewsWebScraper()
        concatenatedGoogle = google_scraper.get_news(query=query_content, language=query_language, max_results=5)
        
        bing_scraper = BingNewsWebScraper()
        concatenatedBing = bing_scraper.get_news(query=query_content, language=query_language, max_results=5)
        
        # Use Vectara
        self.index_document(concatenatedBing, query_language, corpus_key)
        self.index_document(concatenatedGoogle, query_language, corpus_key)
        message = self.create_new_turn(message_request, query_content, corpus_key, db)
        return message
    
    def create_reply(self, message: MessageTurnRequest, corpus_key: str, db: Session):
        
        payload = json.dumps({
            "query": message.entry,
            "search": {
                "corpora": [
                {
                    "custom_dimensions": {},
                    "metadata_filter": None,
                    "lexical_interpolation": 0.025,
                    "semantics": "default",
                    "corpus_key": corpus_key
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
                {{"role": "user", "content": "{message.entry}, with a {message.tone.value} tone."}},
                {{"role": "assistant", "content": "Generate a response with the specified tone: {message.tone.value}"}}
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
            
        try:
            response = requests.post(f"{self.BASE_URL}/chats/{message.chat_id}/turns", headers=self._get_headers(), data=payload)
            response.raise_for_status()
            response_data = response.json()
            answer = response_data.get('answer', "No answer available")
            turn_id = response_data.get('turn_id', "No turn id available")
            
            new_message = Message(
                id = turn_id,
                user_id = message.user_id,
                chat_id = message.chat_id,
                entry = message.entry,
                tone = message.tone,
                answer = answer,
                answer_type = message.answer_type,
                created_at = datetime.now()
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            return new_message
            
        except Exception as e:
            return {"status": "error", "message": "Failed to create reply", "details": str(e)}

    def get_corpus_key_by_chat_id(self, chat_id: str, db: Session):
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            return chat.corpus_key
        
        except Exception as e:
            return {"status": "error", "message": "Failed to get corpus key", "details": str(e)}

    def create_index_reply(self, message_request: MessageTurnRequest, db: Session):
        try:
        
            corpus_key = self.get_corpus_key_by_chat_id(message_request.chat_id, db)
            
            # Use Groq
            groq_client = GroqClient()
            query_data = groq_client.generate_news_query(user_description=message_request.entry)
            query_content = query_data["query"] 
            query_language = query_data["language"]
            
            # Use Webscrapping
            google_scraper = GoogleNewsWebScraper()
            concatenatedGoogle = google_scraper.get_news(query=query_content, language=query_language, max_results=5)
            
            bing_scraper = BingNewsWebScraper()
            concatenatedBing = bing_scraper.get_news(query=query_content, language=query_language, max_results=5)
            
            # Use Vectara
            self.index_document(concatenatedBing, query_language, corpus_key)
            self.index_document(concatenatedGoogle, query_language, corpus_key)
            
            turn = self.create_reply(message_request, corpus_key, db)
            return turn
        
        except Exception as e:
            return {"status": "error", "message": "Failed to create reply", "details": str(e)}
        
    def get_chats_by_user_id(self, user_id: int, db: Session):
        try:
            chats = db.query(Chat).join(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).all()
            return chats
        except Exception as e:
            raise Exception(f"Error al obtener los chats para el usuario {user_id}: {str(e)}")    
      

    def get_messages_by_chat_id(self, chat_id: str, db: Session):
        try:
            messages = db.query(Message).filter(Message.chat_id == chat_id).all()
            return messages
        except Exception as e:
            raise Exception(f"Error al obtener los mensajes para el chat {chat_id}: {str(e)}")
            
            
    def create_new_turn_demo(self, message: MessageDemoRequest, corpus_key: str) -> dict:
        """
        Creates a new chat demo with the specified MessageDemoRequest and corpus.

        Args:
            message (MessageDemoRequest): The message request object.
            corpus_key (str): The key of the corpus.

        Returns:
            dict: A status dictionary indicating success or error.
        """
        payload = json.dumps({
            "query": message.entry,
            "search": {
                "corpora": [
                {
                    "custom_dimensions": {},
                    "metadata_filter": None,
                    "lexical_interpolation": 0.025,
                    "semantics": "default",
                    "corpus_key": corpus_key
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
                {{"role": "user", "content": "{message.entry}, with a {message.tone.value} tone."}},
                {{"role": "assistant", "content": "Generate a response with the specified tone: {message.tone.value}"}}
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
        })

        try:
            response = requests.post(f"{self.BASE_URL}/chats", headers=self._get_headers(), data=payload)
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
                "entry": message.entry,
                "tone": message.tone.value,
                "answer_type": message.answer_type.value
            }
            return formatted_response
        
        except Exception as e:
            return {"status": "error", "message": "Failed to create chat demo", "details": str(e)}
        
        
    def create_chat_demo(self, message_request: MessageDemoRequest):
        
        # Create corpus
        corpus_key = self.create_corpus()
        
        # Use Groq
        groq_client = GroqClient()
        query_data = groq_client.generate_news_query(user_description=message_request.entry)
        query_content = query_data["query"] 
        query_language = query_data["language"]
        
        # Use Webscrapping
        google_scraper = GoogleNewsWebScraper()
        concatenatedGoogle = google_scraper.get_news(query=query_content, language=query_language, max_results=5)
        
        bing_scraper = BingNewsWebScraper()
        concatenatedBing = bing_scraper.get_news(query=query_content, language=query_language, max_results=5)
        
        # Use Vectara
        self.index_document(concatenatedBing, query_language, corpus_key)
        self.index_document(concatenatedGoogle, query_language, corpus_key)
        message = self.create_new_turn_demo(message_request, corpus_key)
        return message