import aiofiles
import os
from pathlib import Path
from typing import BinaryIO, Optional
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import uuid

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class FileProcessor:
    
    @staticmethod
    def validate_file_type(filename: str, content_type: str) -> bool:
        """Validar tipo de archivo permitido"""
        allowed_extensions = ['.pdf', '.docx', '.txt']
        allowed_content_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        file_extension = Path(filename).suffix.lower()
        return file_extension in allowed_extensions and content_type in allowed_content_types
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """Validar tamaño de archivo (default: 10MB)"""
        return file_size <= max_size
    
    @staticmethod
    async def save_file(file: UploadFile) -> tuple[str, str]:
        """Guardar archivo y retornar path y filename único"""
        # Generar nombre único
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Guardar archivo
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return str(file_path), unique_filename
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extraer texto de archivo PDF"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extraer texto de archivo DOCX"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando DOCX: {str(e)}")
    
    @staticmethod
    async def extract_text_from_txt(file_path: str) -> str:
        """Extraer texto de archivo TXT"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando TXT: {str(e)}")
    
    @staticmethod
    async def extract_text_content(file_path: str, content_type: str) -> str:
        """Extraer contenido de texto según el tipo de archivo"""
        if content_type == 'application/pdf':
            return FileProcessor.extract_text_from_pdf(file_path)
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return FileProcessor.extract_text_from_docx(file_path)
        elif content_type == 'text/plain':
            return await FileProcessor.extract_text_from_txt(file_path)
        else:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Eliminar archivo del sistema"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False