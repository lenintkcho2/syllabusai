from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.document import DocumentStatus, EducationalLevel

# Request schemas
class DocumentMetadata(BaseModel):
    educational_level: Optional[EducationalLevel] = None
    subject: Optional[str] = Field(None, max_length=100)
    course_code: Optional[str] = Field(None, max_length=50)
    additional_metadata: Optional[Dict[str, Any]] = None

class DocumentUpload(BaseModel):
    metadata: Optional[DocumentMetadata] = None

# Response schemas
class UnitResponse(BaseModel):
    unit_id: UUID
    title: str
    sessions: Optional[List[Dict[str, Any]]] = []

class DocumentResponse(BaseModel):
    document_id: UUID
    filename: str
    status: DocumentStatus
    text_content: Optional[str] = None
    units: Optional[List[UnitResponse]] = []
    metadata: Optional[DocumentMetadata] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    document_id: UUID
    filename: str
    status: DocumentStatus
    metadata: Optional[DocumentMetadata] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentsListResponse(BaseModel):
    documents: List[DocumentListResponse]
    total: int
    page: int
    limit: int
    pages: int

class DocumentDeleteResponse(BaseModel):
    message: str