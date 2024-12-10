import moviepy as mp
from typing import List, Dict, Optional, Any, Tuple
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path
import srt
from datetime import timedelta
from openai import OpenAI
import tempfile
from dotenv import load_dotenv
import sys

class VideoAssembler:
    def __init__(self, api_key: Optional[str] = None, openai_client: Optional[OpenAI] = None):
        self.logger = self._setup_logging()
        self.logger.info("Iniciando VideoAssembler")
        
        try:
            self.font_path = Path('assets/fonts/OpenSans-Bold.ttf')
            self._ensure_directories()
            
            if openai_client:
                self.client = openai_client
                self.logger.info("Usando cliente OpenAI proporcionado")
            else:
                if not api_key:
                    load_dotenv()
                    api_key = os.getenv('OPENAI_API_KEY')
                    if not api_key:
                        raise ValueError("No se encontró API key de OpenAI")
                self.client = OpenAI(api_key=api_key)
                self.logger.info("Cliente OpenAI inicializado con API key")
        except Exception as e:
            self.logger.error(f"Error en inicialización: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('VideoAssembler')
        logger.setLevel(logging.DEBUG)
        
        # Limpiar handlers existentes
        if logger.handlers:
            logger.handlers.clear()
        
        # Crear formateador detallado
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Handler para archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path('logs') / f'video_assembler_{timestamp}.log'
        file_handler = logging.FileHandler(str(log_path), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_directories(self) -> None:
        try:
            for directory in ['temp', 'output', 'logs']:
                path = Path(directory)
                path.mkdir(exist_ok=True)
                self.logger.debug(f"Directorio asegurado: {path}")
        except Exception as e:
            self.logger.error(f"Error creando directorios: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _normalize_timestamp(self, time_value: Any) -> float:
        """Normaliza valores de tiempo a float"""
        self.logger.debug(f"Normalizando timestamp: {time_value} (tipo: {type(time_value)})")
        try:
            if isinstance(time_value, (int, float)):
                return float(time_value)
            elif isinstance(time_value, str):
                return float(time_value.replace(',', '.'))
            return 0.0
        except Exception as e:
            self.logger.error(f"Error normalizando timestamp: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def transcribe_audio(self, audio_path: str) -> List[Dict]:
        self.logger.info(f"Iniciando transcripción de audio: {audio_path}")
        try:
            with open(audio_path, 'rb') as audio_file:
                self.logger.debug("Enviando archivo a API de Whisper")
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            self.logger.debug(f"Respuesta recibida de Whisper. Tipo: {type(response)}")
            self.logger.debug(f"Estructura de respuesta: {response}")
            
            segments = []
            for i, segment in enumerate(response.segments):
                try:
                    processed_segment = {
                        "start": self._normalize_timestamp(segment.start),
                        "end": self._normalize_timestamp(segment.end),
                        "text": str(segment.text).strip()
                    }
                    segments.append(processed_segment)
                    self.logger.debug(f"Segmento {i} procesado: {processed_segment}")
                except Exception as e:
                    self.logger.error(f"Error procesando segmento {i}: {str(e)}\n{traceback.format_exc()}")
                    continue
            
            self.logger.info(f"Transcripción completada. {len(segments)} segmentos procesados")
            return segments
            
        except Exception as e:
            self.logger.error(f"Error en transcribe_audio: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _get_position(self, base_pos: Any) -> Tuple[int, int]:
        """
        Convierte una posición a una tupla de enteros
        """
        if isinstance(base_pos, tuple):
            x, y = base_pos
            return (int(float(str(x)) if x else 0), int(float(str(y)) if y else 0))
        return (0, 0)
    
    def export_srt(self, segments: List[Dict], output_path: str) -> None:
        self.logger.info(f"Iniciando exportación de SRT a: {output_path}")
        try:
            srt_subtitles = []
            
            for i, segment in enumerate(segments, start=1):
                try:
                    self.logger.debug(f"Procesando segmento {i} para SRT: {segment}")
                    start = timedelta(seconds=segment["start"])
                    end = timedelta(seconds=segment["end"])
                    
                    subtitle = srt.Subtitle(
                        index=i,
                        start=start,
                        end=end,
                        content=str(segment["text"])
                    )
                    srt_subtitles.append(subtitle)
                except Exception as e:
                    self.logger.error(f"Error procesando segmento {i} para SRT: {str(e)}\n{traceback.format_exc()}")
                    continue
            
            with open(output_path, 'w', encoding='utf-8') as f:
                content = srt.compose(srt_subtitles)
                f.write(content)
                self.logger.debug(f"Archivo SRT escrito con {len(srt_subtitles)} subtítulos")
                
            self.logger.info("Exportación de SRT completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en export_srt: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _calculate_center_position(self, clip_size: Tuple[int, int], video_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calcula la posición central para un clip dado el tamaño del video"""
        return (
            (video_size[0] - clip_size[0]) // 2,
            (video_size[1] - clip_size[1]) // 2
        )

    def create_subtitle_clips(self, segments: List[Dict], video_size: tuple) -> List[mp.VideoClip]:
        self.logger.info("Iniciando creación de clips de subtítulos")
        subtitle_clips = []
        
        for i, segment in enumerate(segments):
            try:
                self.logger.debug(f"Procesando segmento {i}: {segment}")
                duration = segment["end"] - segment["start"]
                
                if duration <= 0:
                    self.logger.warning(f"Duración inválida para segmento {i}: {duration}")
                    continue
                
                # Crear el texto principal con posición fija en la parte inferior
                text = str(segment["text"])
                y_position = video_size[1] - 150  # Posición fija desde abajo
                
                text_clip = (mp.TextClip(
                    text=text,
                    font=str(self.font_path),
                    color='white',
                    font_size=60,
                    size=(video_size[0] - 100, None),
                    method='caption'
                ))
                
                # Calcular la posición x central
                x_position = (video_size[0] - text_clip.w) // 2
                
                # Aplicar la posición como tupla de números
                text_clip = (text_clip
                           .with_position((x_position, y_position))
                           .with_duration(duration)
                           .with_start(segment["start"]))
                
                # Crear la sombra con un offset fijo
                shadow = (mp.TextClip(
                    text=text,
                    font=str(self.font_path),
                    color='black',
                    font_size=60,
                    size=(video_size[0] - 100, None),
                    method='caption'
                )
                .with_position((x_position + 2, y_position + 2))
                .with_duration(duration)
                .with_start(segment["start"]))
                
                subtitle_clips.extend([shadow, text_clip])
                self.logger.debug(f"Clip de subtítulo {i} creado exitosamente en posición ({x_position}, {y_position})")
                
            except Exception as e:
                self.logger.error(f"Error creando clip de subtítulo {i}: {str(e)}\n{traceback.format_exc()}")
                continue
        
        self.logger.info(f"Creación de clips de subtítulos completada. {len(subtitle_clips)} clips creados")
        return subtitle_clips

    def create_panning_clip(self, image_path: str, duration: float, video_size: Tuple[int, int], start_time: float) -> mp.VideoClip:
        """
        Crea un clip con efecto de paneo vertical de arriba hacia abajo
        """
        # Cargar la imagen y redimensionarla manteniendo el aspect ratio
        img_clip = mp.ImageClip(str(image_path))
        
        # Calcular el tamaño para que cubra el ancho del video
        aspect_ratio = img_clip.size[0] / img_clip.size[1]
        target_height = int(video_size[0] / aspect_ratio)
        
        # Asegurarse de que la altura sea suficiente para el paneo
        if target_height < video_size[1]:
            target_height = int(video_size[1] * 1.5)  # Hacer la imagen más alta para permitir el paneo
        
        # Redimensionar la imagen
        img_clip = img_clip.resized(width=video_size[0], height=target_height)
        
        def move_function(t):
            """Función de movimiento suave de arriba hacia abajo"""
            # Calcular el rango total de movimiento
            total_movement = target_height - video_size[1]
            
            # Calcular la posición actual usando una función suave
            progress = t / duration
            y_position = -total_movement * progress
            
            return ('center', y_position)
        
        # Crear el clip con el movimiento
        moving_clip = (img_clip
                      .with_position(move_function)
                      .with_duration(duration)
                      .with_start(start_time))
        
        # Recortar el clip al tamaño del video
        final_clip = mp.CompositeVideoClip([moving_clip], size=video_size)
        
        return final_clip

    def assemble_video(self, paragraphs: List[str], images: List[str], audio_path: str) -> str:
        try:
            self.logger.info("Iniciando ensamblaje de video")
            self.logger.info(f"Número de imágenes a procesar: {len(images)}")
            
            if len(paragraphs) != len(images):
                raise ValueError(f"El número de párrafos ({len(paragraphs)}) no coincide con el número de imágenes ({len(images)})")
            
            segments = self.transcribe_audio(audio_path)
            
            audio = mp.AudioFileClip(audio_path)
            total_duration = float(audio.duration)
            duration_per_image = total_duration / len(images)
            
            self.logger.info(f"Duración total: {total_duration}s")
            self.logger.info(f"Duración por imagen: {duration_per_image}s")
            
            video_size = (1920, 1080)
            clips = []
            
            # Crear clips de imágenes con efecto de paneo
            for i, image_path in enumerate(images):
                start_time = i * duration_per_image
                self.logger.info(f"Procesando imagen {i+1}/{len(images)}: {image_path}")
                self.logger.debug(f"Tiempo inicio: {start_time}s, Duración: {duration_per_image}s")
                
                panning_clip = self.create_panning_clip(
                    image_path=image_path,
                    duration=duration_per_image,
                    video_size=video_size,
                    start_time=start_time
                )
                
                clips.append(panning_clip)
            
            # Agregar subtítulos
            subtitle_clips = self.create_subtitle_clips(segments, video_size)
            clips.extend(subtitle_clips)
            
            # Componer video final
            final_clip = (mp.CompositeVideoClip(clips, size=video_size)
                         .with_audio(audio))
            
            # Generar nombres de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output")
            video_path = str(output_dir / f"video_{timestamp}.mp4")
            srt_path = str(output_dir / f"subtitles_{timestamp}.srt")
            
            # Exportar SRT
            self.export_srt(segments, srt_path)
            
            # Renderizar video
            final_clip.write_videofile(
                video_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                preset='medium'
            )
            
            self.logger.info(f"Video generado exitosamente con {len(images)} imágenes: {video_path}")
            self.logger.info(f"Subtítulos generados: {srt_path}")
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Error en assemble_video: {str(e)}\n{traceback.format_exc()}")
            raise