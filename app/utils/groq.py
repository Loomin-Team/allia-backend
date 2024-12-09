import os
from dotenv import load_dotenv
from groq import Groq

class GroqClient:
    """
    A class to encapsulate Groq client operations for language detection and query generation.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Groq client.
        :param api_key: API key for Groq. If not provided, it will be loaded from environment variables.
        """
        load_dotenv()  # Load environment variables
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        self.client = Groq(api_key=self.api_key)
        self.LANG_DETECT_MODEL = "llama3-8b-8192"
        self.QUERY_GEN_MODEL = "llama-3.3-70b-versatile"

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the input text and returns its ISO 639-1 code.
        :param text: The input text.
        :return: The language code (e.g., "EN" for English).
        """
        messages = [
            {
                "role": "system",
                "content": """Detecta el idioma y responde SOLO con el código ISO 639-1 (dos letras).
                Ejemplos: ES (español), EN (inglés), FR (francés), DE (alemán), JA (japonés),
                KO (coreano), ZH (chino), AR (árabe), etc.
                NO agregues NADA más que el código de dos letras."""
            },
            {
                "role": "user",
                "content": text
            }
        ]

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.LANG_DETECT_MODEL,
                max_tokens=2,
                temperature=0
            )
            language = response.choices[0].message.content.strip().upper()
            return language if len(language) == 2 and language.isalpha() else 'EN'
        except Exception as e:
            print(f"Error detecting language: {e}")
            return 'EN'

    def generate_news_query(self, user_description: str) -> dict:
        """
        Generates a concise search query for news based on user description.
        :param user_description: Description of the news to generate the query.
        :return: A dictionary with the query and detected language.
        """
        language = self.detect_language(user_description)

        messages = [
            {
                "role": "system",
                "content": f"""Eres un experto en generar queries de búsqueda CORTAS para noticias.
                IMPORTANTE: Genera la query en el MISMO IDIOMA del texto original.
                La query NO DEBE exceder 12 palabras.

                Debes crear la query más efectiva y CONCISA posible priorizando:
                1. Nombres propios de personas o entidades
                2. Nombres de países o lugares
                3. Verbos o acciones principales
                4. Números y cantidades importantes
                5. Palabras clave del tema principal

                REGLAS ESTRICTAS:
                - MÁXIMO 10 palabras
                - Mantener el idioma original del texto ({language})
                - NO traducir a otros idiomas
                - NO incluir artículos, preposiciones o palabras innecesarias
                - NO usar comillas ni caracteres especiales
                - SOLO genera la query, nada más
                - Ser lo más conciso posible"""
            },
            {
                "role": "user",
                "content": user_description
            }
        ]

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.QUERY_GEN_MODEL,
                max_tokens=50
            )
            query = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating query: {e}")
            query = ' '.join(word for word in user_description.split() if len(word) > 2)[:10]

        return {
            "query": query,
            "language": language
        }