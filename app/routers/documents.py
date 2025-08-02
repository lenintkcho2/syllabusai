from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import json

from app.database import get_db
from app.services.document_service import DocumentService
from app.schemas.document import (
    DocumentResponse, 
    DocumentsListResponse, 
    DocumentMetadata,
    DocumentDeleteResponse
)

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Subir y procesar un documento de sílabo
    """
    
    # Debug: Imprimir información recibida
    print(f"DEBUG: file recibido: {file}")
    print(f"DEBUG: file.filename: {file.filename if file else 'None'}")
    print(f"DEBUG: file.content_type: {file.content_type if file else 'None'}")
    print(f"DEBUG: metadata recibido: {metadata}")
    
    # Validar que file no sea None
    if file is None:
        raise HTTPException(status_code=400, detail="No se recibió archivo")
    
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Nombre de archivo vacío")
    
    # Parsear metadata si existe
    document_metadata = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            document_metadata = DocumentMetadata(**metadata_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Metadata inválido: {str(e)}"
            )
    
    service = DocumentService(db)
    return await service.upload_document(file, document_metadata)

@router.get("/documents", response_model=DocumentsListResponse)
def get_documents(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Texto de búsqueda"),
    db: Session = Depends(get_db)
):
    """
    Listar documentos del usuario con paginación y búsqueda
    
    - **page**: Número de página (mínimo 1)
    - **limit**: Elementos por página (1-100)
    - **search**: Buscar en nombre de archivo, materia o código de curso
    """
    service = DocumentService(db)
    return service.get_documents(page=page, limit=limit, search=search)

@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener detalles de un documento específico
    
    - **document_id**: UUID del documento
    """
    service = DocumentService(db)
    return service.get_document_by_id(document_id)

@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Eliminar un documento
    
    - **document_id**: UUID del documento a eliminar
    """
    service = DocumentService(db)
    result = service.delete_document(document_id)
    return DocumentDeleteResponse(**result)

@router.get("/documents/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Descargar archivo original del documento
    
    - **document_id**: UUID del documento
    """
    # TODO: Implementar descarga de archivo
    raise HTTPException(status_code=501, detail="Endpoint no implementado aún")

@router.patch("/documents/{document_id}/metadata")
def update_document_metadata(
    document_id: UUID,
    metadata: DocumentMetadata,
    db: Session = Depends(get_db)
):
    """
    Actualizar metadata de un documento
    
    - **document_id**: UUID del documento
    - **metadata**: Nuevos metadatos del documento
    """
    # TODO: Implementar actualización de metadata
    raise HTTPException(status_code=501, detail="Endpoint no implementado aún")