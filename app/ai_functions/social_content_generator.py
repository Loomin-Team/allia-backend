import math
from openai import OpenAI
import requests
from pathlib import Path
import logging
from typing import Dict, Optional, Union, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import os

class SocialContentGenerator:
    """Generador de contenido para redes sociales usando IA"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        for directory in ['output', 'temp', 'logs']:
            Path(directory).mkdir(exist_ok=True)
    
    def _enhance_image_prompt(self, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                    Eres un experto en crear prompts para DALL-E.
                    Debes tomar el prompt del usuario y mejorarlo para generar una imagen de alta calidad.
                    
                    El prompt debe incluir:
                    1. Estilo visual específico (fotorrealista, cartoon, 3D, etc.)
                    2. Composición y encuadre
                    3. Iluminación y colores
                    4. Detalles de los elementos principales
                    5. Ambiente y contexto
                    6. Aspectos técnicos (resolución, calidad)
                    
                    El formato debe ser claro y estructurado.
                    """},
                    {"role": "user", "content": f"Mejora este prompt para generar una imagen: {user_prompt}"}
                ]
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error mejorando prompt de imagen: {str(e)}")
            raise
    
    def _generate_meme_concept(self, user_prompt: str) -> Tuple[str, List[str]]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                    Eres un experto creador de memes.
                    Basado en el prompt del usuario, genera:
                    1. Un prompt para crear la imagen base del meme
                    2. Los textos que irán en la imagen (texto superior e inferior)
                    
                    Los textos deben ser concisos para evitar problemas de espacio.
                    Máximo 6-8 palabras por línea.
                    
                    Devuelve el resultado en formato JSON:
                    {
                        "image_prompt": "descripción detallada de la imagen",
                        "texts": ["texto superior", "texto inferior"]
                    }
                    """},
                    {"role": "user", "content": f"Crea un concepto de meme para: {user_prompt}"}
                ]
            )
            
            result = eval(response.choices[0].message.content.strip())
            return result["image_prompt"], result["texts"]
            
        except Exception as e:
            self.logger.error(f"Error generando concepto de meme: {str(e)}")
            raise
    
    def _generate_image(self, prompt: str) -> Optional[str]:
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
    
    def _add_text_to_image(self, image_path: str, texts: List[str]) -> Optional[str]:
        try:
            # Load IMPACT font
            try:
                font_path = Path('app/ai_functions/assets/fonts/impact.ttf')
                if not font_path.exists():
                    font_path.parent.mkdir(exist_ok=True)
                    
                    import requests
                    font_url = "https://github.com/flutter/flutter/raw/master/packages/flutter_tools/test/data/asset_test/fonts/Impact.ttf"
                    response = requests.get(font_url)
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                
            except Exception as font_error:
                self.logger.warning(f"No se pudo cargar la fuente IMPACT: {font_error}")
                return None

            def calculate_font_size(text: str, max_width: int, max_height: int, font_path: str, start_size: int = 200) -> Tuple[int, List[str]]:
                """Calculate optimal font size and wrapped lines for text to fit within constraints"""
                size = start_size
                min_size = 20  # Minimum readable font size
                
                while size > min_size:
                    font = ImageFont.truetype(str(font_path), size)
                    
                    # Split text into words and try to form lines
                    words = text.upper().split()
                    lines = []
                    current_line = []
                    total_height = 0
                    line_spacing = int(size * 0.3)  # 30% of font size for spacing
                    
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        bbox = font.getbbox(test_line)
                        width = bbox[2] - bbox[0]
                        
                        if width <= max_width:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                            else:
                                lines.append(word)
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Calculate total height with line spacing
                    total_height = (font.getbbox('Aj')[3] * len(lines)) + (line_spacing * (len(lines) - 1))
                    
                    if total_height <= max_height:
                        return size, lines
                    
                    size = int(size * 0.9)
                
                return min_size, textwrap.wrap(text.upper(), width=20)

            def draw_text_with_outline(draw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, text_color: str = 'white', outline_color: str = 'black'):
                """Draw text with outline for better visibility"""
                outline_size = max(int(font.size * 0.08), 2)
                
                # Draw outline
                for dx in range(-outline_size, outline_size + 1, 2):
                    for dy in range(-outline_size, outline_size + 1, 2):
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
                
                # Draw main text
                draw.text((x, y), text, font=font, fill=text_color)

            # Open original image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Configure margins and sizes
            margin_x = int(width * 0.05)
            margin_y = int(height * 0.05)
            available_width = width - (2 * margin_x)
            max_text_height = int(height * 0.3)  # Increased to 30% of image height
            
            # Process each text block (top and bottom)
            y_positions = [margin_y, height - max_text_height - margin_y]
            
            for text, y_base in zip(texts, y_positions):
                # Calculate optimal font size and wrap text
                font_size, lines = calculate_font_size(
                    text,
                    available_width,
                    max_text_height,
                    font_path
                )
                
                font = ImageFont.truetype(str(font_path), font_size)
                line_spacing = int(font_size * 0.3)
                
                # Calculate total text block height
                total_height = (font.getbbox('Aj')[3] * len(lines)) + (line_spacing * (len(lines) - 1))
                
                # Adjust vertical position for bottom text to align with bottom margin
                if y_base > height / 2:
                    y_base = height - total_height - margin_y
                
                # Draw each line
                current_y = y_base
                for line in lines:
                    # Center text horizontally
                    bbox = font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    x_pos = (width - text_width) / 2
                    
                    draw_text_with_outline(draw, line, x_pos, current_y, font)
                    current_y += font.getbbox('Aj')[3] + line_spacing
            
            # Save result
            output_path = f"output/meme_{os.urandom(4).hex()}.png"
            image.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error agregando texto a imagen: {str(e)}")
            self.logger.exception("Detalles del error:")
            return None

    def generate_social_content(self, prompt: str) -> Dict[str, Union[str, Dict[str, str]]]:
        try:
            results = {}
            
            # Generar imagen principal con prompt mejorado
            enhanced_prompt = self._enhance_image_prompt(prompt)
            image_path = self._generate_image(enhanced_prompt)
            results['image'] = image_path
            
            # Generar meme
            meme_prompt, meme_texts = self._generate_meme_concept(prompt)
            meme_base_path = self._generate_image(meme_prompt)
            if meme_base_path:
                meme_path = self._add_text_to_image(meme_base_path, meme_texts)
                results['meme'] = meme_path
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generando contenido social: {str(e)}")
            raise