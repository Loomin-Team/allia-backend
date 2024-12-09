import os
import json
from groq import Groq

# Cliente Groq inicializado fuera del handler para reutilizarlo entre invocaciones
client = Groq(
    api_key=os.environ['GROQ_API_KEY']
)

# Constantes
LANG_DETECT_MODEL = "llama3-8b-8192"
QUERY_GEN_MODEL = "llama-3.3-70b-versatile"


def detect_language(text):
    """Detecta el idioma del texto y devuelve código ISO 639-1."""
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
        response = client.chat.completions.create(
            messages=messages,
            model=LANG_DETECT_MODEL,
            max_tokens=2,
            temperature=0
        )
        language = response.choices[0].message.content.strip().upper()
        return language if len(language) == 2 and language.isalpha() else 'EN'
    except:
        return 'EN'


def generate_news_query(user_description):
    """Genera una query de búsqueda basada en la descripción del usuario."""
    language = detect_language(user_description)

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
        response = client.chat.completions.create(
            messages=messages,
            model=QUERY_GEN_MODEL,
            max_tokens=50
        )
        query = response.choices[0].message.content.strip()
    except:
        query = ' '.join(word for word in user_description.split() if len(word) > 2)[:10]

    return {
        "query": query,
        "language": language
    }


def lambda_handler(event, context):
    """
    Handler principal de AWS Lambda.
    Espera recibir un evento con el siguiente formato:
    {
        "description": "texto de la noticia a buscar"
    }
    """
    try:
        # Verificar si el evento viene de API Gateway
        if 'body' in event:
            body = json.loads(event['body'])
            user_description = body.get('description', '')
        else:
            user_description = event.get('description', '')

        if not user_description:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Se requiere el campo "description" en el cuerpo de la petición'
                })
            }

        result = generate_news_query(user_description)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error interno del servidor: {str(e)}'
            })
        }