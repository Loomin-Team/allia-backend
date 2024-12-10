import os
import logging
from pathlib import Path
from typing import Dict, Optional
from openai import OpenAI
import requests
from tqdm import tqdm
import colorama
from colorama import Fore, Style

colorama.init()

class ThemedImageGenerator:
    """Generador de sets de imágenes temáticas usando IA"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self._setup_directories()
        self.available_styles = [
            'realista fotográfico',
            'ilustración digital',
            'estilo minimalista',
            'estilo cinematográfico',
            'estilo documental'
        ]
    
    def _setup_directories(self) -> None:
        """Crea los directorios necesarios"""
        for directory in ['output', 'temp', 'logs']:
            Path(directory).mkdir(exist_ok=True)
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Mejora el prompt para generar mejores imágenes"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                    Mejora el prompt para DALL-E incluyendo:
                    1. Estilo visual específico
                    2. Composición y encuadre
                    3. Iluminación y colores
                    4. Detalles técnicos
                    El prompt debe ser claro y detallado.
                    """},
                    {"role": "user", "content": f"Mejora este prompt: {prompt}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error mejorando prompt: {str(e)}")
            return prompt
    
    def _generate_single_image(self, prompt: str) -> Optional[str]:
        """Genera una única imagen"""
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            
            output_path = f"temp/generated_image_{os.urandom(4).hex()}.png"
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generando imagen: {str(e)}")
            return None

    def generate_image_set(self, prompt: str, style: str = 'realista fotográfico') -> Dict[str, str]:
        """
        Genera un set de 4 imágenes temáticas basadas en el prompt
        
        Args:
            prompt: Idea o concepto base
            style: Estilo visual a aplicar
            
        Returns:
            Dict con las rutas de las imágenes generadas
        """
        try:
            self.logger.info(f"{Fore.BLUE}🎨 Generando set de imágenes temáticas...{Style.RESET_ALL}")
            
            variations = [
                ("principal", "imagen principal que capture la esencia central del concepto"),
                ("detalle", "close-up detallado mostrando elementos específicos y texturas"),
                ("contexto", "vista amplia que muestre el ambiente y contexto completo"),
                ("alternativa", "interpretación artística o abstracta del concepto")
            ]
            
            results = {}
            with tqdm(total=4, desc="Generando imágenes", colour='cyan') as pbar:
                for variant_name, variant_desc in variations:
                    # Crear y mejorar prompt específico
                    variant_prompt = f"{prompt} - {variant_desc} - en estilo {style}"
                    enhanced_prompt = self._enhance_prompt(variant_prompt)
                    
                    # Generar imagen
                    image_path = self._generate_single_image(enhanced_prompt)
                    
                    if image_path:
                        # Mover a ubicación final
                        final_path = f"output/themed_{variant_name}_{os.urandom(4).hex()}.png"
                        os.rename(image_path, final_path)
                        results[variant_name] = final_path
                    
                    pbar.update(1)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generando set de imágenes: {str(e)}")
            return {}