from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime, timedelta
import enum

class ExportStatus(str, enum.Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ExportType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMBINED = "combined"

class Export(Base):
    """Tabla para exportaciones de contenido"""
    __tablename__ = "exports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Tipo de exportación
    export_type = Column(Enum(ExportType), nullable=False)
    
    # Relaciones
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    
    # Contenidos a exportar (JSON array de UUIDs)
    content_ids = Column(JSON, nullable=False)  # ["uuid1", "uuid2", ...]
    
    # Configuración de exportación
    format = Column(String(20), nullable=False)  # pdf, docx, latex
    export_settings = Column(JSON, nullable=True)
    
    # Estado de exportación
    status = Column(Enum(ExportStatus), default=ExportStatus.STARTED, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    
    # Archivo generado
    filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    download_url = Column(String(500), nullable=True)
    
    # Tiempo de vida del archivo
    expires_at = Column(DateTime, nullable=True)
    
    # Tiempos
    estimated_completion = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Relaciones
    template = relationship("Template")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Por defecto, los archivos expiran en 24 horas
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)