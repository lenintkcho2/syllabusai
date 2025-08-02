from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum

class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"

class EducationalLevel(str, enum.Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    UNDERGRADUATE = "Undergraduate"
    GRADUATE = "Graduate"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Content
    text_content = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    
    # Metadata
    educational_level = Column(Enum(EducationalLevel), nullable=True)
    subject = Column(String(100), nullable=True)
    course_code = Column(String(50), nullable=True)
    additional_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - Se definirán después para evitar imports circulares
    # units = relationship("Unit", back_populates="document", cascade="all, delete-orphan")