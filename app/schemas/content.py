from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.content import ContentType, GenerationStatus, AIProvider, ContentScope

# Request schemas
class GenerationConfiguration(BaseModel):
    educational_level: str = Field(..., description="Nivel educativo")
    pedagogical_approach: str = Field(default="Competency-based", description="Enfoque pedagógico")
    ai_model: str = Field(..., description="Modelo de IA específico")
    content_length: int = Field(default=5, ge=1, le=20, description="Longitud del contenido (1-20)")
    include_web_content: bool = Field(default=True, description="Incluir contenido web")
    include_images: bool = Field(default=True, description="Incluir imágenes")
    include_rich_content: bool = Field(default=True, description="Incluir contenido enriquecido")
    language: str = Field(default="es", description="Idioma del contenido")
    additional_instructions: Optional[str] = Field(None, description="Instrucciones adicionales")

class GenerateContentRequest(BaseModel):
    document_id: UUID = Field(..., description="ID del documento base")
    content_type: ContentType = Field(..., description="Tipo de contenido a generar")
    scope: ContentScope = Field(..., description="Alcance de la generación")
    target_unit: Optional[UUID] = Field(None, description="ID de unidad específica")
    target_session: Optional[UUID] = Field(None, description="ID de sesión específica")
    ai_provider: AIProvider = Field(default=AIProvider.GROQ, description="Proveedor de IA")
    configuration: GenerationConfiguration = Field(..., description="Configuración de generación")

class UpdateContentRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    markdown_content: Optional[str] = Field(None)
    sections: Optional[Dict[str, str]] = Field(None, description="Secciones del contenido")

# Response schemas
class GenerationResponse(BaseModel):
    generation_id: UUID
    status: GenerationStatus
    estimated_completion: Optional[datetime] = None
    message: str
    
    class Config:
        from_attributes = True

class ContentSummary(BaseModel):
    content_id: UUID
    title: str
    content_type: ContentType
    content_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class GenerationStatusResponse(BaseModel):
    generation_id: UUID
    status: GenerationStatus
    progress: int = Field(ge=0, le=100)
    results: List[ContentSummary] = []
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ContentResponse(BaseModel):
    content_id: UUID
    title: str
    content_type: ContentType
    markdown_content: str
    sections: Optional[Dict[str, str]] = None
    content_metadata: Optional[Dict[str, Any]] = None
    document_id: UUID
    generation_id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ContentListItem(BaseModel):
    content_id: UUID
    title: str
    content_type: ContentType
    document_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ContentListResponse(BaseModel):
    contents: List[ContentListItem]
    total: int
    page: int
    limit: int
    pages: int

class ContentDeleteResponse(BaseModel):
    message: str

# Schemas para AI Service
class AIPromptTemplate(BaseModel):
    system_prompt: str
    user_prompt: str
    max_tokens: int = 2000
    temperature: float = 0.7

class AIResponse(BaseModel):
    content: str
    provider: AIProvider
    model: str
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None