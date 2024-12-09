import os
import json
import random
import string
import requests
from dotenv import load_dotenv

load_dotenv()


class VectaraClient:
    """
    A client for interacting with the Vectara API, including creating corpora
    and indexing documents.
    """

    BASE_URL = "https://api.vectara.io/v2"
    API_KEY = os.getenv("VECTARA_API_KEY")

    def __init__(self):
        if not self.API_KEY:
            raise ValueError("VECTARA_API_KEY is not set in the environment.")

    def _get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.API_KEY
        }

    def create_corpus(self, description: str = "Documents for prompt-based responses") -> str:
        """
        Creates a new corpus in Vectara.
        """
        corpus_key = ''.join(random.choices(string.ascii_letters + string.digits + "_=-", k=32))
        payload = json.dumps({
            "key": corpus_key,
            "name": corpus_key,
            "description": description,
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

        response = requests.post(f"{self.BASE_URL}/corpora", headers=self._get_headers(), data=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("key")

    def index_document(self, text: str, lang: str, corpus_key: str) -> dict:
        """
        Indexes a document in the specified corpus.
        """
        payload = json.dumps({
            "id": "doc-" + ''.join(random.choices(string.ascii_letters + string.digits, k=8)),
            "type": "core",
            "metadata": {
                "title": "Indexed Document",
                "lang": lang
            },
            "document_parts": [
                {
                    "text": text,
                    "metadata": {"rank": random.randint(1, 100)},
                }
            ]
        })

        response = requests.post(f"{self.BASE_URL}/corpora/{corpus_key}/documents",
                                 headers=self._get_headers(), data=payload)
        response.raise_for_status()
        return {"status": "success", "message": "Document indexed successfully"}

    def create_new_turn(self, query_payload: dict) -> dict:
        """
        Submits a query to Vectara and retrieves a response.
        """
        response = requests.post(f"{self.BASE_URL}/chats", headers=self._get_headers(), data=json.dumps(query_payload))
        response.raise_for_status()
        return response.json()

    def create_reply(self, chat_id: str, turn_payload: dict) -> dict:
        """
        Adds a reply to an existing Vectara chat session.
        """
        response = requests.post(f"{self.BASE_URL}/chats/{chat_id}/turns", headers=self._get_headers(), data=json.dumps(turn_payload))
        response.raise_for_status()
        return response.json()
