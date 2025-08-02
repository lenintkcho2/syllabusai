from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum

class ContentType(str, enum.Enum):
    CLASS_SESSION = "class_session"
    STUDY_GUIDE = "study_guide"
    PRESENTATION = "presentation"
    WORKSHEET = "worksheet"
    ASSESSMENT = "assessment"

class GenerationStatus(str, enum.Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AIProvider(str, enum.Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROQ = "groq"
    COHERE = "cohere"
    OLLAMA = "ollama"
    XAI = "xai"

class ContentScope(str, enum.Enum):
    SPECIFIC_SESSION = "specific_session"
    COMPLETE_UNIT = "complete_unit"
    COMPLETE_SYLLABUS = "complete_syllabus"

class Generation(Base):
    """Tabla para trackear generaciones de contenido"""
    __tablename__ = "generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relación con documento
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Configuración de generación
    content_type = Column(Enum(ContentType), nullable=False)
    scope = Column(Enum(ContentScope), nullable=False)
    ai_provider = Column(Enum(AIProvider), nullable=False)
    ai_model = Column(String(100), nullable=False)
    
    # Estado de generación
    status = Column(Enum(GenerationStatus), default=GenerationStatus.STARTED, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    
    # Configuración específica
    configuration = Column(JSON, nullable=True)
    
    # Tiempos
    estimated_completion = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Relaciones (sin back_populates para evitar problemas circulares)
    document = relationship("Document")
    contents = relationship("Content", cascade="all, delete-orphan")

class Content(Base):
    """Tabla para contenido generado"""
    __tablename__ = "contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relaciones
    generation_id = Column(UUID(as_uuid=True), ForeignKey("generations.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Información básica
    title = Column(String(500), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    
    # Contenido
    markdown_content = Column(Text, nullable=False)
    
    # Secciones estructuradas
    sections = Column(JSON, nullable=True)  # {introduction, objectives, development, conclusion}
    
    # Metadata (usando nombre diferente porque 'metadata' está reservado)
    content_metadata = Column(JSON, nullable=True)
    
    # Control de versiones
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones (sin back_populates para evitar problemas circulares)
    generation = relationship("Generation")
    document = relationship("Document")

# Actualizar el modelo Document para incluir relaciones
# Esto se debe agregar al archivo app/models/document.py existente:
"""
Agregar estas líneas al modelo Document:

# Relaciones con contenido
generations = relationship("Generation", back_populates="document", cascade="all, delete-orphan")
contents = relationship("Content", back_populates="document", cascade="all, delete-orphan")
"""