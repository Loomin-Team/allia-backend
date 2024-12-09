import requests
import json
import datetime

from app.chat.schemas.message_schema import MessageDemoRequest, MessageRequest, MessageResponse, MessageTurnRequest
from app.utils.vectara import VectaraClient
from app.utils.groq import GroqClient
from app.utils.google_news_scraper import GoogleNewsWebScraper, BingNewsWebScraper
from app.models.chat_model import Chat, Message

class ChatService:
    @staticmethod
    def create_chat(self, message_request: MessageRequest, db: Session, is_demo: bool = False):
        """
        Creates a chat or a demo chat depending on the `is_demo` flag.

        Args:
            message_request (MessageRequest): The message request object.
            db (Session): The database session.
            is_demo (bool): Indicates if this is a demo request.

        Returns:
            dict or Chat: The created chat or a dictionary with the chat demo details.
        """
        # Create a corpus
        corpus_description = "Demo corpus for user interaction" if is_demo else "Documents with important information for the prompt."
        corpus_key = self.create_corpus(description=corpus_description)

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
        self.index_document(concatenated_google, query_language, corpus_key)
        self.index_document(concatenated_bing, query_language, corpus_key)

        # If it's a demo, create a demo response
        if is_demo:
            message_demo_request = MessageDemoRequest(
                entry=message_request.entry,
                tone=message_request.tone,
                answer_type=message_request.answer_type,
            )
            demo_response = self.create_new_turn_demo(message_demo_request, corpus_key)
            return demo_response

        # Otherwise, proceed with regular chat creation
        try:
            message = self.create_new_turn(message_request, query_content, corpus_key, db)
            return message
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