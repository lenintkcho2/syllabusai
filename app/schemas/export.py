from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.export import ExportStatus, ExportType
from app.models.template import TemplateFormat

# Request schemas
class ExportSettings(BaseModel):
    include_metadata: bool = Field(default=True, description="Incluir metadata en la exportación")
    include_images: bool = Field(default=True, description="Incluir imágenes")
    paper_size: str = Field(default="A4", description="Tamaño de papel")
    font_size: str = Field(default="12pt", description="Tamaño de fuente")
    margins: Optional[str] = Field(None, description="Márgenes personalizados")
    header_footer: bool = Field(default=True, description="Incluir header y footer")
    page_numbers: bool = Field(default=True, description="Incluir números de página")
    table_of_contents: bool = Field(default=False, description="Incluir tabla de contenidos")

class IndividualExportRequest(BaseModel):
    content_id: UUID = Field(..., description="ID del contenido a exportar")
    format: str = Field(..., description="Formato de exportación (pdf, docx, latex)")
    template_id: Optional[UUID] = Field(None, description="ID de plantilla opcional")
    export_settings: Optional[ExportSettings] = Field(default_factory=ExportSettings)

class CombinedExportRequest(BaseModel):
    content_ids: List[UUID] = Field(..., min_items=1, description="IDs de contenidos a combinar")
    format: str = Field(..., description="Formato de exportación (pdf, docx, latex)")
    template_id: Optional[UUID] = Field(None, description="ID de plantilla opcional")
    export_settings: Optional[ExportSettings] = Field(default_factory=ExportSettings)
    title: Optional[str] = Field(None, description="Título del documento combinado")

# Response schemas
class TemplateResponse(BaseModel):
    template_id: UUID
    name: str
    format: TemplateFormat
    description: Optional[str] = None
    preview_url: Optional[str] = None
    is_default: bool = False
    tags: Optional[List[str]] = []
    
    class Config:
        from_attributes = True

class TemplatesListResponse(BaseModel):
    templates: List[TemplateResponse]

class ExportResponse(BaseModel):
    export_id: UUID
    status: ExportStatus
    estimated_completion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ExportStatusResponse(BaseModel):
    export_id: UUID
    status: ExportStatus
    progress: int = Field(ge=0, le=100)
    download_url: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ExportListItem(BaseModel):
    export_id: UUID
    export_type: ExportType
    format: str
    status: ExportStatus
    filename: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExportListResponse(BaseModel):
    exports: List[ExportListItem]
    total: int
    page: int
    limit: int
    pages: int