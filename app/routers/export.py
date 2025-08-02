from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import os

from app.database import get_db
from app.services.export_service import ExportService
from app.schemas.export import (
    IndividualExportRequest,
    CombinedExportRequest,
    ExportResponse,
    ExportStatusResponse,
    TemplatesListResponse
)

router = APIRouter()

@router.get("/templates", response_model=TemplatesListResponse)
def get_templates(
    format: Optional[str] = Query(None, description="Filtrar por formato (pdf, docx, latex)"),
    db: Session = Depends(get_db)
):
    """
    Obtener plantillas disponibles para exportación
    
    - **format**: Filtrar plantillas por formato específico (opcional)
    
    Formatos soportados:
    - **pdf**: Plantillas para exportar a PDF
    - **docx**: Plantillas para exportar a Word
    - **latex**: Plantillas LaTeX
    - **html**: Plantillas HTML
    - **markdown**: Plantillas Markdown
    """
    service = ExportService(db)
    return service.get_templates(format_filter=format)

@router.post("/export/individual", response_model=ExportResponse)
async def export_individual_content(
    request: IndividualExportRequest,
    db: Session = Depends(get_db)
):
    """
    Exportar contenido individual a un formato específico
    
    - **content_id**: UUID del contenido a exportar
    - **format**: Formato de exportación (pdf, docx, latex)
    - **template_id**: ID de plantilla opcional para personalizar el formato
    - **export_settings**: Configuraciones de exportación (tamaño papel, fuente, etc.)
    
    El proceso de exportación es asíncrono. Use GET /export/{export_id} 
    para monitorear el progreso.
    """
    service = ExportService(db)
    return await service.export_individual(request)

@router.post("/export/combined", response_model=ExportResponse)
async def export_combined_content(
    request: CombinedExportRequest,
    db: Session = Depends(get_db)
):
    """
    Exportar múltiples contenidos combinados en un solo documento
    
    - **content_ids**: Lista de UUIDs de contenidos a combinar
    - **format**: Formato de exportación (pdf, docx, latex)
    - **template_id**: ID de plantilla opcional
    - **export_settings**: Configuraciones de exportación
    - **title**: Título opcional para el documento combinado
    
    Los contenidos se combinan en el orden especificado en el array.
    """
    service = ExportService(db)
    return await service.export_combined(request)

@router.get("/export/{export_id}", response_model=ExportStatusResponse)
def get_export_status(
    export_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener el estado de una exportación en progreso
    
    - **export_id**: UUID de la exportación a consultar
    
    Estados posibles:
    - **started**: Exportación iniciada
    - **in_progress**: En proceso de generación
    - **completed**: Completada exitosamente (archivo listo para descarga)
    - **failed**: Falló con error
    
    Una vez completada, usar GET /export/{export_id}/download para descargar.
    """
    service = ExportService(db)
    return service.get_export_status(export_id)

@router.get("/export/{export_id}/download")
def download_exported_file(
    export_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Descargar archivo exportado
    
    - **export_id**: UUID de la exportación completada
    
    Retorna el archivo binario con headers apropiados para descarga.
    Los archivos expiran automáticamente después de 24 horas.
    
    Headers de respuesta:
    - Content-Type: application/pdf | application/vnd.openxmlformats-officedocument.wordprocessingml.document | text/plain
    - Content-Disposition: attachment; filename="archivo.ext"
    - Content-Length: tamaño del archivo
    """
    service = ExportService(db)
    
    try:
        file_path = service.get_file_path(export_id)
        
        # Obtener información de la exportación para headers
        export_info = service.get_export_status(export_id)
        
        # Determinar content type según formato
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'latex': 'text/plain',
            'html': 'text/html',
            'txt': 'text/plain'
        }
        
        # Extraer formato del filename
        file_extension = export_info.filename.split('.')[-1] if export_info.filename else 'txt'
        content_type = content_types.get(file_extension, 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            filename=export_info.filename,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{export_info.filename}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@router.get("/templates/{template_id}/preview")
def get_template_preview(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener vista previa de una plantilla
    
    - **template_id**: UUID de la plantilla
    
    TODO: Implementar generación de preview de plantillas
    """
    raise HTTPException(status_code=501, detail="Vista previa de plantillas no implementada aún")

@router.get("/exports")
def list_exports(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=50, description="Elementos por página"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    format: Optional[str] = Query(None, description="Filtrar por formato"),
    db: Session = Depends(get_db)
):
    """
    Listar exportaciones del usuario
    
    - **page**: Número de página (mínimo 1)
    - **limit**: Elementos por página (1-50)
    - **status**: Filtrar por estado (started, in_progress, completed, failed)
    - **format**: Filtrar por formato (pdf, docx, latex)
    
    TODO: Implementar listado de exportaciones con filtros
    """
    raise HTTPException(status_code=501, detail="Listado de exportaciones no implementado aún")

@router.delete("/export/{export_id}")
def delete_export(
    export_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Eliminar una exportación y su archivo asociado
    
    - **export_id**: UUID de la exportación a eliminar
    
    TODO: Implementar eliminación de exportaciones
    """
    raise HTTPException(status_code=501, detail="Eliminación de exportaciones no implementada aún")

@router.get("/formats")
def get_supported_formats():
    """
    Obtener formatos de exportación soportados
    
    Retorna lista de formatos disponibles con sus características.
    """
    return {
        "formats": [
            {
                "value": "pdf",
                "label": "PDF",
                "description": "Portable Document Format - ideal para impresión y distribución",
                "extensions": [".pdf"],
                "supports_images": True,
                "supports_formatting": True
            },
            {
                "value": "docx",
                "label": "Microsoft Word",
                "description": "Documento Word editable",
                "extensions": [".docx"],
                "supports_images": True,
                "supports_formatting": True
            },
            {
                "value": "latex",
                "label": "LaTeX",
                "description": "Código LaTeX para compilación académica",
                "extensions": [".tex"],
                "supports_images": True,
                "supports_formatting": True
            },
            {
                "value": "html",
                "label": "HTML",
                "description": "Página web estática",
                "extensions": [".html"],
                "supports_images": True,
                "supports_formatting": True
            },
            {
                "value": "markdown",
                "label": "Markdown",
                "description": "Texto plano con formato Markdown",
                "extensions": [".md"],
                "supports_images": False,
                "supports_formatting": True
            }
        ]
    }