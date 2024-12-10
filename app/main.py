import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Import database components
from app.config.db import create_all_tables
from app.router import routes

# Import content generators
from app.ai_functions.social_content_generator import SocialContentGenerator
from app.ai_functions.video_content_generator import ContentGenerator
from app.ai_functions.video_assembler import VideoAssembler
from app.ai_functions.themed_image_generator import ThemedImageGenerator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Media Content Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include database routes
app.include_router(routes)

#Create database tables
try:
    create_all_tables()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error al crear tablas: {e}")

class ContentRequest(BaseModel):
    user_prompt: str
    context: str = ""

class ContentResponse(BaseModel):
    status: str
    s3_url: Optional[str] = None
    error: Optional[str] = None

class S3Handler:
    """Handles Amazon S3 uploads"""
    
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, 
                 region: str, bucket: str):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        self.bucket = bucket
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, folder: str = '') -> Optional[str]:
        try:
            file_name = Path(file_path).name
            s3_key = f"{folder}/{file_name}" if folder else file_name
            
            self.s3_client.upload_file(file_path, self.bucket, s3_key)
            url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            
            return url
        except ClientError as e:
            self.logger.error(f"Error uploading file to S3: {str(e)}")
            return None

class ContentAnalyzer:
    """Analyzer for prompts to determine content parameters"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.available_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        self.available_image_styles = [
            'realistic photographic',
            'digital illustration',
            'minimalist style',
            'cinematic style',
            'documentary style'
        ]
        
    def analyze_params(self, prompt_user: str, contexto: str, content_type: str) -> Dict:
        """Analyze prompt to determine parameters based on content type"""
        try:
            system_prompts = {
                'video': f"""
                Analyze the prompt and extract or suggest the following parameters for a video:
                - num_images: number of images (1-5)
                - voice: voice to use (available options: {', '.join(self.available_voices)})
                - style: visual style (available options: {', '.join(self.available_image_styles)})
                
                If a parameter is not specified, use default values:
                - num_images: 4
                - voice: nova
                - style: realistic photographic
                
                Return a JSON with the parameters.
                """,
                'images': f"""
                Analyze the prompt and extract or suggest the following parameters for images:
                - style: visual style (available options: {', '.join(self.available_image_styles)})
                - num_variants: number of variants (1-4)
                
                If a parameter is not specified, use default values:
                - style: realistic photographic
                - num_variants: 2
                
                Return a JSON with the parameters.
                """,
                'meme': """
                Analyze the prompt and extract or suggest the following parameters for a meme:
                - style: meme style (humorous, sarcastic, ironic)
                - format: meme format (image_text, collage, comic)
                - tone: content tone (casual, formal, humorous)
                
                If a parameter is not specified, use default values:
                - style: humorous
                - format: image_text
                - tone: casual
                
                Return a JSON with the parameters.
                """
            }
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompts[content_type]},
                    {"role": "user", "content": f"""
                    Prompt: {prompt_user}
                    Context: {contexto}
                    """}
                ]
            )
            
            params = eval(response.choices[0].message.content.strip())
            return self._apply_defaults(params, content_type)
            
        except Exception as e:
            return self._get_defaults(content_type)
    
    def _apply_defaults(self, params: Dict, content_type: str) -> Dict:
        defaults = self._get_defaults(content_type)
        
        for key, value in defaults.items():
            if key not in params or not params[key]:
                params[key] = value
                
        if content_type == 'video':
            if 'voice' in params and params['voice'] not in self.available_voices:
                params['voice'] = 'nova'
            if 'style' in params and params['style'] not in self.available_image_styles:
                params['style'] = 'realistic photographic'
                
        if content_type == 'images':
            if 'style' in params and params['style'] not in self.available_image_styles:
                params['style'] = 'realistic photographic'
                
        return params
    
    def _get_defaults(self, content_type: str) -> Dict:
        defaults = {
            'video': {
                'num_images': 2,
                'voice': 'nova',
                'style': 'realistic photographic'
            },
            'images': {
                'style': 'realistic photographic',
                'num_variants': 2
            },
            'meme': {
                'style': 'humorous',
                'format': 'image_text',
                'tone': 'casual'
            }
        }
        return defaults[content_type]

class MediaCreator:
    """Main class for multimedia content creation"""
    
    def __init__(self, api_key: str):
        self.openai_client = OpenAI(api_key=api_key)
        self.content_generator = ContentGenerator(api_key)
        self.video_assembler = VideoAssembler(openai_client=self.openai_client)
        self.image_generator = ThemedImageGenerator(api_key)             
        self.social_generator = SocialContentGenerator(api_key)
        self.content_analyzer = ContentAnalyzer(self.openai_client)
        
        # Configure S3
        self.s3_handler = S3Handler(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region=os.getenv('AWS_REGION'),
            bucket=os.getenv('S3_BUCKET')
        )
        
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        Path('logs').mkdir(exist_ok=True)
        
        log_file = Path('logs') / f'media_creator_{datetime.now():%Y%m%d}.log'
        handlers = [
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
        
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def create_video(self, prompt_user: str, contexto: str) -> Optional[str]:
        """Create video and return S3 URL"""
        try:
            self.logger.info("🎥 Analyzing parameters for video...")
            params = self.content_analyzer.analyze_params(prompt_user, contexto, 'video')
            
            self.logger.info("🎥 Generating video...")
            content = self.content_generator.generate_complete_content(
                context=contexto,  # Add this line to pass the context
                num_images=params['num_images'],
                voice=params['voice'],
                image_style=params['style']
            )
            
            video_path = self.video_assembler.assemble_video(
                paragraphs=content['paragraphs'],
                images=content['images'],
                audio_path=content['audio']
            )
            
            if video_path:
                return self.s3_handler.upload_file(
                    video_path, 
                    folder=os.getenv('S3_VIDEOS_FOLDER', 'videos')
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def create_meme(self, prompt_user: str, contexto: str) -> Optional[str]:
        """Create meme and return S3 URL"""
        try:
            self.logger.info("🎨 Analyzing parameters for meme...")
            params = self.content_analyzer.analyze_params(prompt_user, contexto, 'meme')
            
            self.logger.info("🎨 Generating meme...")
            meme_prompt = f"Create a meme in style {params['style']} with format {params['format']} and tone {params['tone']} about: {prompt_user}"
            meme_prompt, meme_texts = self.social_generator._generate_meme_concept(meme_prompt)
            
            meme_base_path = self.social_generator._generate_image(meme_prompt)
            if meme_base_path:
                meme_path = self.social_generator._add_text_to_image(
                    meme_base_path, 
                    meme_texts
                )
                if meme_path:
                    return self.s3_handler.upload_file(
                        meme_path, 
                        folder=os.getenv('S3_MEMES_FOLDER', 'memes')
                    )
            return None
                
        except Exception as e:
            self.logger.error(f"Error creating meme: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def create_themed_images(self, prompt_user: str, contexto: str) -> Optional[str]:
        """Generate images and return S3 URL of the first variant"""
        try:
            self.logger.info("🎨 Analyzing parameters for images...")
            params = self.content_analyzer.analyze_params(prompt_user, contexto, 'images')
            
            results = self.image_generator.generate_image_set(prompt_user, params['style'])
            if results and len(results) > 0:
                first_image_path = next(iter(results.values()))
                return self.s3_handler.upload_file(
                    first_image_path, 
                    folder=os.getenv('S3_IMAGES_FOLDER', 'images')
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating images: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @property
    def available_voices(self):
        return self.content_generator.available_voices

    @property
    def available_image_styles(self):
        return self.image_generator.available_styles

# Verify required environment variables
required_vars = [
    'OPENAI_API_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_REGION',
    'S3_BUCKET'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize MediaCreator
creator = MediaCreator(os.getenv('OPENAI_API_KEY'))

@app.post("/generate/video", response_model=ContentResponse)
async def generate_video(request: ContentRequest):
    """Generate a video based on the provided prompt"""
    try:
        s3_url = await creator.create_video(request.user_prompt, request.context)
        if s3_url:
            return ContentResponse(status="success", s3_url=s3_url)
        return ContentResponse(status="error", error="Failed to generate video")
    except Exception as e:
        return ContentResponse(status="error", error=str(e))

@app.post("/generate/meme", response_model=ContentResponse)
async def generate_meme(request: ContentRequest):
    """Generate a meme based on the provided prompt"""
    try:
        s3_url = creator.create_meme(request.user_prompt, request.context)
        if s3_url:
            return ContentResponse(status="success", s3_url=s3_url)
        return ContentResponse(status="error", error="Failed to generate meme")
    except Exception as e:
        return ContentResponse(status="error", error=str(e))

@app.post("/generate/images", response_model=ContentResponse)
async def generate_images(request: ContentRequest):
    """Generate themed images based on the provided prompt"""
    try:
        s3_url = creator.create_themed_images(request.user_prompt, request.context)
        if s3_url:
            return ContentResponse(status="success", s3_url=s3_url)
        return ContentResponse(status="error", error="Failed to generate images")
    except Exception as e:
        return ContentResponse(status="error", error=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)