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
            # Cargar la fuente IMPACT
            try:
                font_path = Path('assets/fonts/impact.ttf')
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

            def get_wrapped_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, max_height: int) -> Tuple[str, int]:
                """Ajusta el texto para que quepa en el ancho y alto máximo"""
                words = text.split()
                lines = []
                current_line = []
                current_height = 0
                line_spacing = int(font.size * 1.2)
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = font.getbbox(test_line)
                    
                    if bbox[2] <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            line = ' '.join(current_line)
                            line_height = font.getbbox(line)[3]
                            if current_height + line_height + line_spacing > max_height:
                                # Reducir el texto si excede la altura máxima
                                if lines:
                                    lines[-1] = lines[-1] + "..."
                                break
                            lines.append(line)
                            current_height += line_height + line_spacing
                            current_line = [word]
                        else:
                            lines.append(word)
                            current_height += font.getbbox(word)[3] + line_spacing
                            current_line = []
                
                if current_line:
                    line = ' '.join(current_line)
                    if current_height + font.getbbox(line)[3] <= max_height:
                        lines.append(line)
                
                return '\n'.join(lines), current_height

            def draw_text_with_outline(draw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, text_color: str = 'white', outline_color: str = 'black'):
                """Dibuja texto con contorno"""
                outline_size = max(int(font.size * 0.08), 3)
                
                for angle in range(0, 360, 45):
                    radian = math.radians(angle)
                    offset_x = int(outline_size * math.cos(radian))
                    offset_y = int(outline_size * math.sin(radian))
                    
                    draw.text(
                        (x + offset_x, y + offset_y),
                        text,
                        font=font,
                        fill=outline_color
                    )
                
                draw.text((x, y), text, font=font, fill=text_color)

            # Abrir imagen original
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Configurar márgenes y tamaños
            margin_x = int(width * 0.05)
            margin_y = int(height * 0.05)
            available_width = width - (2 * margin_x)
            
            # Altura máxima para cada sección de texto (25% de la altura total)
            max_text_height = int(height * 0.25)
            
            # Calcular tamaño de fuente inicial
            base_font_size = int(height * 0.15)
            min_font_size = base_font_size
            
            # Ajustar tamaño de fuente para ambos textos
            for text in texts:
                size = base_font_size
                while size > 10:
                    test_font = ImageFont.truetype(str(font_path), size)
                    wrapped, text_height = get_wrapped_text(
                        text.upper(), 
                        test_font, 
                        available_width,
                        max_text_height
                    )
                    
                    if text_height <= max_text_height:
                        break
                    size = int(size * 0.9)
                min_font_size = min(min_font_size, size)
            
            # Usar el mismo tamaño de fuente para ambos textos
            font = ImageFont.truetype(str(font_path), min_font_size)
            
            # Dibujar textos
            y_positions = [margin_y, height - max_text_height - margin_y]
            
            for text, y_base in zip(texts, y_positions):
                wrapped_text, text_height = get_wrapped_text(
                    text.upper(),
                    font,
                    available_width,
                    max_text_height
                )
                
                bbox = draw.textbbox((0, 0), wrapped_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x_pos = (width - text_width) / 2
                y_pos = y_base
                
                draw_text_with_outline(draw, wrapped_text, x_pos, y_pos, font)
            
            # Guardar resultado
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