import os
import requests
import json

from sqlalchemy import null

from app.chat.models.corpus_model import Corpus

class ChatService:
    @staticmethod
    def create_corpus(db: requests.Session):
        """
        Creates a new corpus in Vectara and returns the corpus key.

        Args:
            db (requests.Session): The database session.

        Returns:
            str: The corpus key of the newly created corpus.

        Raises:
            Exception: If the API call fails or the corpus key is not returned.
        """
        
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
    def create_chat(entry: str, corpus_key: str):
        try:
            url = "https://api.vectara.io/v2/chats"

            payload = json.dumps({
            "query": entry,
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
                return {"status": "success", "message": "Chat created successfully", "data": response.json()}
            else:
                return {"status": "error", "message": "Failed to create chat", "details": response.text}
                
        except Exception as e:
            return {"status": "error", "message": "An error occurred", "details": str(e)}

    @staticmethod
    def create_reply(entry: str, chat_id: str, db: requests.Session):
        pass

    @staticmethod
    def get_chat_history(chat_id: str, db: requests.Session):
        pass