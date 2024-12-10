from openai import OpenAI
import requests
from keybert import KeyBERT
import os
from pathlib import Path
import logging
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio
import colorama
from colorama import Fore, Style
from tqdm import tqdm
from datetime import datetime, time

colorama.init()

class ContentGenerator:
    """Gestiona la generación de contenido para videos usando IA"""
    
    def __init__(self, api_key: str):
        """
        Inicializa el generador de contenido
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.kw_model = KeyBERT()
        self.logger = logging.getLogger(__name__)
        self._setup_directories()
        # Available voices and image styles
        self.available_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        self.available_image_styles = [
            'realista fotográfico',
            'ilustración digital',
            'estilo minimalista',
            'estilo cinematográfico',
            'estilo documental'
        ]
    
    def _setup_directories(self) -> None:
        """Crea los directorios necesarios si no existen"""
        for directory in ['temp', 'output', 'logs']:
            Path(directory).mkdir(exist_ok=True)
    
    def _summarize_context(self, text: str, max_tokens: int = 500) -> str:
        """
        Resume el contexto usando GPT para mantenerlo dentro del límite de tokens
        
        Args:
            text: Texto a resumir
            max_tokens: Máximo número de tokens para el resumen
            
        Returns:
            Texto resumido
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""
                    Resume el siguiente texto manteniendo los puntos más importantes.
                    El resumen debe:
                    - Ser conciso pero informativo
                    - Mantener los datos clave y cifras importantes
                    - No exceder {max_tokens} tokens
                    - Preservar el tono objetivo
                    """},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error resumiendo contexto: {str(e)}")
            raise
    
    def _extract_keywords(self, prompt: str, num_keywords: int) -> List[str]:
        """Extrae keywords relevantes del prompt"""
        try:
            self.logger.debug(f"Extrayendo {num_keywords} keywords")
            keywords = self.kw_model.extract_keywords(prompt, top_n=num_keywords+2)
            return [kw[0] for kw in keywords[:num_keywords]]
            
        except Exception as e:
            self.logger.error(f"Error en extract_keywords: {str(e)}")
            raise

    def _generate_story_paragraphs(self, context: str, num_paragraphs: int) -> List[str]:
        """
        Genera una serie de párrafos que cuentan una historia progresiva
        
        Args:
            context: Contexto resumido
            num_paragraphs: Número de párrafos a generar
            
        Returns:
            Lista de párrafos que forman una narrativa coherente
        """
        try:
            prompt = f"""
            En su idioma, Basándote en este contexto resumido:
            {context}
            
            Genera {num_paragraphs} párrafos que cuenten esta historia de forma progresiva.
            Si es 1 párrafo, resume toda la historia.
            Si son más párrafos, desarrolla la historia gradualmente.
            Cada párrafo debe tener máximo 25 palabras y complementar al anterior.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""
                    Genera una narrativa progresiva en {num_paragraphs} párrafos:
                    - Cada párrafo máximo 25 palabras
                    - Los párrafos deben complementarse, no repetirse
                    - Mantén el tono objetivo y profesional
                    - Estructura la historia de forma lógica:
                        * Si es 1 párrafo: resumen completo
                        * Si son 2-3 párrafos: inicio, desarrollo/conclusión
                        * Si son 4-5 párrafos: introduce detalles y desarrollo más extenso
                    - No uses marcadores numéricos ni viñetas
                    - Devuelve los párrafos separados por |||
                    """},
                    {"role": "user", "content": prompt}
                ]
            )
            
            paragraphs = response.choices[0].message.content.strip().split('|||')
            paragraphs = [p.strip() for p in paragraphs]
            
            return paragraphs
            
        except Exception as e:
            self.logger.error(f"Error generando párrafos narrativos: {str(e)}")
            raise

    def _create_audio(self, text: str, voice: str = 'nova') -> Optional[str]:
        """
        Genera audio a partir del texto con la voz seleccionada
        
        Args:
            text: Texto a convertir en audio
            voice: Modelo de voz a usar (default: 'nova')
        """
        try:
            if voice not in self.available_voices:
                self.logger.warning(f"Voz {voice} no válida. Usando nova por defecto.")
                voice = 'nova'
                
            audio_path = "temp/audio.mp3"
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=1.1
            )
            
            response.stream_to_file(audio_path)
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Error generando audio: {str(e)}")
            return None

    def _generate_image(self, keyword: str, index: int, context: str, image_style: str = 'realista fotográfico') -> Optional[str]:
        """
        Genera una imagen contextualmente relevante
        
        Args:
            keyword: Palabra clave para la imagen
            index: Índice de la imagen
            context: Contexto para la generación
            image_style: Estilo visual deseado para la imagen
        """
        try:
            if image_style not in self.available_image_styles:
                self.logger.warning(f"Estilo {image_style} no válido. Usando estilo realista por defecto.")
                image_style = 'realista fotográfico'
                
            prompt = f"""
            Genera una imagen en {image_style} que ilustre específicamente este texto:
            {context}
            
            La imagen debe enfocarse en mostrar: {keyword}
            
            Requisitos específicos:
            1. La imagen DEBE representar fielmente el contenido y contexto del texto proporcionado
            2. Mantener un estilo {image_style}
            3. Incluir elementos visuales que reflejen el tema principal del texto
            4. Evitar elementos genéricos o no relacionados con el contexto
            5. Asegurar que la composición y los elementos visuales apoyen la narrativa del texto
            
            Notas adicionales:
            - La imagen debe ser coherente con el párrafo específico que está ilustrando
            - Los elementos visuales deben reflejar precisamente los detalles mencionados en el texto
            - El tono y ambiente de la imagen debe coincidir con la narrativa del texto
            """
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            
            output_path = f"temp/image_{index}.png"
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            return output_path
            
        except Exception as e:
            if 'rate_limit_exceeded' in str(e):
                self.logger.error("Límite de rate excedido. Esperando antes de reintentar...")
                time.sleep(60)
            self.logger.error(f"Error generando imagen: {str(e)}")
            return None

    def generate_complete_content(self, context: str, num_images: int = 4, voice: str = 'nova', image_style: str = 'realista fotográfico') -> Dict[str, Union[List[str], str]]:
        """
        Genera todo el contenido necesario para el video de forma optimizada
        
        Args:
            context: Contexto proporcionado para la generación
            num_images: Número de imágenes a generar (default: 4)
            voice: Modelo de voz a usar (default: 'nova')
            image_style: Estilo visual para las imágenes (default: 'realista fotográfico')
            
        Returns:
            Dict con párrafos, rutas de imágenes y ruta del audio
        """
        try:
            self.logger.info("Resumiendo contexto...")
            summarized_context = self._summarize_context(context)
            
            self.logger.info("Generando narrativa...")
            paragraphs = self._generate_story_paragraphs(summarized_context, num_images)
            
            keywords = []
            for paragraph in paragraphs:
                kws = self._extract_keywords(paragraph, 3)
                keywords.append(" y ".join(kws))
            
            with ThreadPoolExecutor() as executor:
                image_futures = [
                    executor.submit(
                        self._generate_image, 
                        keyword, 
                        idx, 
                        paragraph,
                        image_style
                    )
                    for idx, (keyword, paragraph) in enumerate(zip(keywords, paragraphs))
                ]
                
                image_paths = [f.result() for f in image_futures]
                
                if None in image_paths:
                    raise ValueError("Error generando una o más imágenes")
            
            audio_path = self._create_audio(" ".join(paragraphs), voice)
            if not audio_path:
                raise ValueError("Error generando el audio")
            
            return {
                'paragraphs': paragraphs,
                'images': image_paths,
                'audio': audio_path
            }
            
        except Exception as e:
            self.logger.error(f"Error en generate_complete_content: {str(e)}")
            raise