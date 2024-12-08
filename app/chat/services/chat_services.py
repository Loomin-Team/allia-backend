from datetime import datetime
import os
import requests
import json

from sqlalchemy import null

from app.chat.models.chat_model import Chat
from app.chat.models.corpus_model import Corpus
from app.chat.schemas.chat_schema import ChatRequest
from app.profiles.services.profiles_services import ProfileService

class ChatService:
    @staticmethod
    def create_corpus(db: requests.Session):
        new_corpus = Corpus()

        db.add(new_corpus)
        db.commit()
        db.refresh(new_corpus)

        try:
            url = "https://api.vectara.io/v2/corpora"
            
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
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-api-key': os.getenv("VECTARA_API_KEY")
            }

            response = requests.post(url, headers=headers, data=payload)

            if response.status_code in [200, 201]:
                response_data = response.json()
                corpus_key = response_data.get("key")
                if not corpus_key:
                    raise Exception("Corpus key not returned by API.")
                return corpus_key
            else:
                raise Exception(f"Failed to create corpus: {response.text}")

        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")
        
    @staticmethod
    def index_document(text: str, lang: str, corpus_key: str):
        try:
            url = f"https://api.vectara.io/v2/corpora/{corpus_key}/documents"
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
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-api-key': os.getenv("VECTARA_API_KEY")
            }
            
            requests.post(url, headers=headers, data=payload)

        except Exception as e:
            return {"status": "error", "message": "An error occurred", "details": str(e)}
        
    @staticmethod
    def create_chat(chat: ChatRequest, corpus_key: str, db: requests.Session):
        
        try:
            url = "https://api.vectara.io/v2/chats"

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
            headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': os.getenv("VECTARA_API_KEY")
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            
            if response.status_code in [200, 201]:
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
            else:
                return {"status": "error", "message": "Failed to create chat", "details": response.text}
                    
        except Exception as e:
            return {"status": "error", "message": "An error occurred", "details": str(e)}
        