# social_text_generator.py
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from openai import OpenAI
from tqdm import tqdm
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

colorama.init()
load_dotenv()

class SocialTextGenerator:
    """Generador de textos optimizados para redes sociales basado en JSON inputs"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._setup_directories()
        
    def _setup_logging(self) -> None:
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/social_generator.log'),
                logging.StreamHandler()
            ]
        )
        
    def _setup_directories(self) -> None:
        """Crea los directorios necesarios"""
        for directory in ['output', 'temp', 'logs']:
            Path(directory).mkdir(exist_ok=True)
            
    def _clean_context(self, context: str) -> str:
        """Limpia y optimiza el contexto usando IA"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
                    Eres un experto en análisis y síntesis de información.
                    Limpia y estructura el contexto proporcionado, eliminando información irrelevante
                    y destacando los puntos clave para crear contenido en redes sociales.
                    """},
                    {"role": "user", "content": f"Limpia y optimiza este contexto: {context}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error limpiando contexto: {str(e)}")
            return context
            
    def _detect_platform(self, prompt: str) -> str:
        """Detecta la plataforma solicitada en el prompt"""
        platforms = {
            'instagram': ['instagram', 'ig', 'insta'],
            'linkedin': ['linkedin', 'linked in', 'li'],
            'twitter': ['twitter', 'tw', 'x'],
            'facebook': ['facebook', 'fb', 'face']
        }
        
        prompt_lower = prompt.lower()
        for platform, keywords in platforms.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return platform
        return 'facebook'  # plataforma por defecto
        
    def generate_content(self, prompt: str) -> Dict:
        """
        Genera contenido de texto optimizado para diferentes plataformas
        
        Args:
            prompt: String con el prompt del usuario
            
        Returns:
            Dict con el contenido generado para cada plataforma
        """
        try:
            if not prompt:
                raise ValueError("El prompt no puede estar vacío")
                
            self.logger.info(f"{Fore.BLUE}📝 Procesando contenido social...{Style.RESET_ALL}")
            
            results = {}
            platforms = ['facebook', 'instagram', 'linkedin', 'twitter']
            
            for platform in platforms:
                platform_prompts = {
                    'facebook': "en el idioma del input, tono casual y cercano, con llamada a la acción clara",
                    'instagram': "en el idioma del input,estilo visual con emojis y hashtags relevantes",
                    'linkedin': "en el idioma del input,tono profesional y formal, estructurado en párrafos",
                    'twitter': "en el idioma del input,máximo 280 caracteres, hashtags estratégicos"
                }
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"""
                        Genera contenido optimizado para {platform} con estas características:
                        {platform_prompts[platform]}
                        """},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                generated_text = response.choices[0].message.content.strip()
                
                # Guardar resultado
                file_id = os.urandom(4).hex()
                file_path = f"output/social_{platform}_{file_id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(generated_text)
                    
                results[platform] = {
                    'text': generated_text,
                    'file': file_path
                }
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error en la generación de contenido: {str(e)}")
            return {}