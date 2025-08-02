from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.services.content_service import ContentService
from app.models.content import ContentType
from app.schemas.content import (
    GenerateContentRequest,
    GenerationResponse,
    GenerationStatusResponse,
    ContentResponse,
    ContentListResponse,
    UpdateContentRequest,
    ContentDeleteResponse
)

router = APIRouter()

@router.post("/content/generate", response_model=GenerationResponse)
async def generate_content(
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generar contenido educativo (sesiones de clase o guías de estudio)
    
    - **document_id**: UUID del documento base para generar contenido
    - **content_type**: Tipo de contenido (class_session, study_guide, presentation, etc.)
    - **scope**: Alcance de la generación (specific_session, complete_unit, complete_syllabus)
    - **ai_provider**: Proveedor de IA a usar (groq, openai, claude, gemini, etc.)
    - **configuration**: Configuración detallada de la generación
    """
    service = ContentService(db)
    return await service.generate_content(request)

@router.get("/content/generation/{generation_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    generation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener el estado de una generación en progreso
    
    - **generation_id**: UUID de la generación a consultar
    
    Estados posibles:
    - **started**: Generación iniciada
    - **in_progress**: En proceso
    - **completed**: Completada exitosamente
    - **failed**: Falló con error
    """
    service = ContentService(db)
    return service.get_generation_status(generation_id)

@router.get("/content", response_model=ContentListResponse)
def get_contents(
    document_id: Optional[UUID] = Query(None, description="Filtrar por documento"),
    content_type: Optional[ContentType] = Query(None, description="Filtrar por tipo de contenido"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Elementos por página"),
    db: Session = Depends(get_db)
):
    """
    Listar contenido generado del usuario
    
    - **document_id**: Filtrar por documento específico (opcional)
    - **content_type**: Filtrar por tipo de contenido (opcional)
    - **page**: Número de página (mínimo 1)
    - **limit**: Elementos por página (1-100)
    """
    service = ContentService(db)
    return service.get_contents(
        document_id=document_id,
        content_type=content_type,
        page=page,
        limit=limit
    )

@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener contenido específico
    
    - **content_id**: UUID del contenido a obtener
    
    Retorna el contenido completo incluyendo:
    - Contenido en markdown
    - Secciones estructuradas
    - Metadata de generación
    """
    service = ContentService(db)
    return service.get_content_by_id(content_id)

@router.put("/content/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: UUID,
    request: UpdateContentRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar contenido existente
    
    - **content_id**: UUID del contenido a actualizar
    - **title**: Nuevo título (opcional)
    - **markdown_content**: Nuevo contenido en markdown (opcional)
    - **sections**: Nuevas secciones estructuradas (opcional)
    
    Incrementa automáticamente la versión del contenido.
    """
    service = ContentService(db)
    return service.update_content(content_id, request)

@router.delete("/content/{content_id}", response_model=ContentDeleteResponse)
def delete_content(
    content_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Eliminar contenido
    
    - **content_id**: UUID del contenido a eliminar
    
    Nota: Realiza eliminación lógica (soft delete), el contenido se marca como inactivo
    pero permanece en la base de datos para auditoría.
    """
    service = ContentService(db)
    return service.delete_content(content_id)

@router.get("/content/{content_id}/versions")
def get_content_versions(
    content_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener historial de versiones de un contenido
    
    - **content_id**: UUID del contenido
    
    TODO: Implementar sistema de versionado completo
    """
    raise HTTPException(status_code=501, detail="Endpoint no implementado aún")

@router.post("/content/{content_id}/duplicate")
def duplicate_content(
    content_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Duplicar contenido existente
    
    - **content_id**: UUID del contenido a duplicar
    
    TODO: Implementar duplicación de contenido
    """
    raise HTTPException(status_code=501, detail="Endpoint no implementado aún")

@router.get("/content/types")
def get_content_types():
    """
    Obtener tipos de contenido disponibles
    
    Retorna lista de tipos de contenido que se pueden generar
    """
    return {
        "content_types": [
            {
                "value": "class_session",
                "label": "Sesión de Clase",
                "description": "Sesión completa de clase con objetivos, desarrollo y evaluación"
            },
            {
                "value": "study_guide",
                "label": "Guía de Estudio",
                "description": "Material de estudio con resúmenes, ejercicios y autoevaluación"
            },
            {
                "value": "presentation",
                "label": "Presentación",
                "description": "Contenido estructurado para diapositivas"
            },
            {
                "value": "worksheet",
                "label": "Hoja de Trabajo",
                "description": "Ejercicios prácticos y actividades"
            },
            {
                "value": "assessment",
                "label": "Evaluación",
                "description": "Exámenes, quizzes y rúbricas"
            }
        ]
    }

@router.get("/ai/providers")
def get_ai_providers():
    """
    Obtener proveedores de IA disponibles
    
    Retorna lista de proveedores de IA configurados y su estado
    """
    # TODO: Implementar verificación de estado de proveedores
    return {
        "providers": [
            {
                "value": "groq",
                "label": "Groq",
                "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
                "status": "available"
            },
            {
                "value": "gemini",
                "label": "Google Gemini",
                "models": ["gemini-pro", "gemini-1.5-pro"],
                "status": "available"
            },
            {
                "value": "openai",
                "label": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "status": "configured"
            },
            {
                "value": "claude",
                "label": "Anthropic Claude",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "status": "configured"
            }
        ]
    }