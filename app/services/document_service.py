from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import UploadFile, HTTPException
from typing import Optional, List
from uuid import UUID
import math

from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentMetadata, DocumentResponse, DocumentsListResponse
from app.utils.file_utils import FileProcessor
from app.config import settings

class DocumentService:
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_document(
        self, 
        file: UploadFile, 
        metadata: Optional[DocumentMetadata] = None
    ) -> DocumentResponse:
        """Subir y procesar un documento"""
        
        # Validaciones
        if not FileProcessor.validate_file_type(file.filename, file.content_type):
            raise HTTPException(
                status_code=400, 
                detail="Tipo de archivo no permitido. Use PDF, DOCX o TXT"
            )
        
        # Leer el contenido para obtener el tamaño
        content = await file.read()
        file_size = len(content)
        
        if not FileProcessor.validate_file_size(file_size, settings.max_file_size):
            raise HTTPException(
                status_code=400, 
                detail=f"Archivo muy grande. Máximo {settings.max_file_size // (1024*1024)}MB"
            )
        
        # Resetear el puntero del archivo
        await file.seek(0)
        
        try:
            # Guardar archivo
            file_path, unique_filename = await FileProcessor.save_file(file)
            
            # Crear registro en BD
            document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                content_type=file.content_type,
                file_size=file_size,
                status=DocumentStatus.PROCESSING
            )
            
            # Agregar metadata si existe
            if metadata:
                document.educational_level = metadata.educational_level
                document.subject = metadata.subject
                document.course_code = metadata.course_code
                document.additional_metadata = metadata.additional_metadata
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            # Procesar contenido
            try:
                text_content = await FileProcessor.extract_text_content(
                    file_path, 
                    file.content_type
                )
                
                # Actualizar documento con contenido
                document.text_content = text_content
                document.status = DocumentStatus.PROCESSED
                self.db.commit()
                self.db.refresh(document)
                
            except Exception as e:
                # Si falla el procesamiento, marcar como error
                document.status = DocumentStatus.ERROR
                self.db.commit()
                raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")
            
            return self._document_to_response(document)
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error subiendo documento: {str(e)}")
    
    def get_documents(
        self, 
        page: int = 1, 
        limit: int = 10, 
        search: Optional[str] = None
    ) -> DocumentsListResponse:
        """Obtener lista de documentos con paginación"""
        
        query = self.db.query(Document)
        
        # Filtro de búsqueda
        if search:
            search_filter = or_(
                Document.original_filename.ilike(f"%{search}%"),
                Document.subject.ilike(f"%{search}%"),
                Document.course_code.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Total de documentos
        total = query.count()
        
        # Paginación
        offset = (page - 1) * limit
        documents = query.offset(offset).limit(limit).all()
        
        # Calcular páginas
        pages = math.ceil(total / limit)
        
        return DocumentsListResponse(
            documents=[self._document_to_list_response(doc) for doc in documents],
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    
    def get_document_by_id(self, document_id: UUID) -> DocumentResponse:
        """Obtener documento específico por ID"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return self._document_to_response(document)
    
    def delete_document(self, document_id: UUID) -> dict:
        """Eliminar documento"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Eliminar archivo físico
        FileProcessor.delete_file(document.file_path)
        
        # Eliminar de BD
        self.db.delete(document)
        self.db.commit()
        
        return {"message": "Documento eliminado exitosamente"}
    
    def _document_to_response(self, document: Document) -> DocumentResponse:
        """Convertir modelo a respuesta completa"""
        metadata = None
        if any([document.educational_level, document.subject, document.course_code, document.additional_metadata]):
            metadata = DocumentMetadata(
                educational_level=document.educational_level,
                subject=document.subject,
                course_code=document.course_code,
                additional_metadata=document.additional_metadata
            )
        
        return DocumentResponse(
            document_id=document.id,
            filename=document.original_filename,
            status=document.status,
            text_content=document.text_content,
            units=[],  # TODO: implementar units después
            metadata=metadata,
            created_at=document.created_at
        )
    
    def _document_to_list_response(self, document: Document):
        """Convertir modelo a respuesta de lista"""
        metadata = None
        if any([document.educational_level, document.subject, document.course_code, document.additional_metadata]):
            metadata = DocumentMetadata(
                educational_level=document.educational_level,
                subject=document.subject,
                course_code=document.course_code,
                additional_metadata=document.additional_metadata
            )
        
        return {
            "document_id": document.id,
            "filename": document.original_filename,
            "status": document.status,
            "metadata": metadata,
            "created_at": document.created_at
        }