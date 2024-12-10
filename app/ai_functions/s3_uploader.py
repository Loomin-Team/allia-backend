import boto3
import logging
from pathlib import Path
from botocore.exceptions import ClientError
from typing import Optional
import os

class S3Uploader:
    """Manejador de subidas a Amazon S3"""
    
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, 
                 region: str, bucket: str):
        """
        Inicializa el uploader de S3
        
        Args:
            aws_access_key_id: AWS Access Key ID
            aws_secret_access_key: AWS Secret Access Key
            region: Región de AWS (ej: 'us-east-1')
            bucket: Nombre del bucket de S3
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        self.bucket = bucket
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, folder: str = '') -> Optional[str]:
        """
        Sube un archivo a S3
        
        Args:
            file_path: Ruta local del archivo
            folder: Carpeta en S3 (opcional)
            
        Returns:
            URL del archivo subido o None si hay error
        """
        try:
            file_name = Path(file_path).name
            s3_key = f"{folder}/{file_name}" if folder else file_name
            
            # Subir archivo
            self.s3_client.upload_file(file_path, self.bucket, s3_key)
            
            # Generar URL
            url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            self.logger.info(f"Archivo subido exitosamente a: {url}")
            
            return url
            
        except ClientError as e:
            self.logger.error(f"Error subiendo archivo a S3: {str(e)}")
            return None

    def upload_files(self, file_paths: dict, folder: str = '') -> dict:
        """
        Sube múltiples archivos a S3
        
        Args:
            file_paths: Diccionario con identificadores y rutas
            folder: Carpeta en S3 (opcional)
            
        Returns:
            Diccionario con identificadores y URLs de S3
        """
        results = {}
        for key, path in file_paths.items():
            url = self.upload_file(path, folder)
            if url:
                results[key] = url
        return results