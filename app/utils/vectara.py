from datetime import datetime
import os
import json
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.chat.models.chat_model import Chat
from app.chat.models.corpus_model import Corpus
from app.chat.schemas.chat_schema import ChatRequest
from app.profiles.services.profiles_services import ProfileService  

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

    def create_corpus(self, db: Session) -> str:
        """
        Creates a new corpus in Vectara and stores it in the database.

        Args:
            db (Session): The database session.

        Returns:
            str: The corpus key of the newly created corpus.

        Raises:
            Exception: If the API call fails or the corpus key is not returned.
        """
        new_corpus = Corpus()
        db.add(new_corpus)
        db.commit()
        db.refresh(new_corpus)

        payload = json.dumps({
            "key": str(new_corpus.id),
            "name": str(new_corpus.id),
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

    def create_new_turn(self, chat: ChatRequest, corpus_key: str, db: Session) -> Chat:
        """
        Creates a new chat with the specified query and corpus.

        Args:
            entry (str): The query for the chat.
            corpus_key (str): The key of the corpus.

        Returns:
            dict: A status dictionary indicating success or error.
        """
        payload = json.dumps({
            "query": chat.entry,
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
                "prompt_template": "[\n  {\"role\": \"system\", \"content\": \"You are a helpful search assistant.\"},\n  #foreach ($qResult in $vectaraQueryResults)\n     {\"role\": \"user\", \"content\": \"Given the $vectaraIdxWord[$foreach.index] search result.\"},\n     {\"role\": \"assistant\", \"content\": \"${qResult.getText()}\" },\n  #end\n  {\"role\": \"user\", \"content\": \"Generate a summary for the query '${vectaraQuery}' based on the above results.\"}\n]\n",
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
            response = requests.post(f"{self.BASE_URL}/chats", headers=self._get_headers(), data=payload)
            response.raise_for_status()
            response_data = response.json()  

            answer = response_data.get('answer', "No answer available")
            chat_id = response_data.get('chat_id', "No chat id available")
            sender_fullname = ProfileService.get_fullname_by_id(chat.sender_id, db)
                
            new_chat = Chat(
                sender_id=chat.sender_id,
                sender_name=sender_fullname,
                chat_id=chat_id,
                entry=chat.entry,
                answer_type=chat.answer_type,
                answer=answer,
                created_at=datetime.now()
            )

            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            return new_chat
        
        except Exception as e:
            return {"status": "error", "message": "Failed to create chat", "details": str(e)}
        
    
    def create_chat(self, chat: ChatRequest, db: Session):
        corpus_key = self.create_corpus(db)
        self.index_document("tech is the application of scientific knowledge for practical purposes, especially in industry", "us", corpus_key)
        chat = self.create_new_turn(chat, corpus_key,db)
        return chat