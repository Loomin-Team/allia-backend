import os
import requests
import json

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
    def index_document(text: str, corpus_key: str, db: requests.Session):
        try:
            url = f"https://api.vectara.io/v2/corpora/{corpus_key}/documents"
            payload = json.dumps({
                "id": "my-doc-id",
                "type": "core",
                "metadata": {
                    "title": "A Nice Document",
                    "lang": "eng"
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
            
            response = requests.post(url, headers=headers, data=payload)

            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Documented added successfully", "data": response.json()}
            else:
                return {"status": "error", "message": "Failed to add document", "details": response.text}
                
        except Exception as e:
            return {"status": "error", "message": "An error occurred", "details": str(e)}
        