from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime
import enum

class TemplateFormat(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    LATEX = "latex"
    HTML = "html"
    MARKDOWN = "markdown"

class Template(Base):
    """Tabla para plantillas de exportación"""
    __tablename__ = "templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Información básica
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(Enum(TemplateFormat), nullable=False)
    
    # Template content
    template_content = Column(Text, nullable=False)  # Template actual (LaTeX, HTML, etc.)
    preview_image = Column(String(500), nullable=True)  # URL de imagen preview
    
    # Configuración
    default_settings = Column(JSON, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Metadata
    version = Column(String(20), default="1.0")
    author = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)  # ["academic", "formal", "modern"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)