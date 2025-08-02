from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List
from uuid import UUID
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.models.export import Export, ExportStatus, ExportType
from app.models.template import Template
from app.models.content import Content
from app.schemas.export import (
    IndividualExportRequest, CombinedExportRequest, ExportResponse,
    ExportStatusResponse, TemplatesListResponse, ExportListResponse
)

class ExportService:
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def get_templates(self, format_filter: Optional[str] = None) -> TemplatesListResponse:
        """Obtener plantillas disponibles"""
        query = self.db.query(Template).filter(Template.is_active == True)
        
        if format_filter:
            query = query.filter(Template.format == format_filter)
        
        templates = query.all()
        
        return TemplatesListResponse(
            templates=[
                {
                    "template_id": template.id,
                    "name": template.name,
                    "format": template.format,
                    "description": template.description,
                    "preview_url": f"/api/v1/templates/{template.id}/preview" if template.preview_image else None,
                    "is_default": template.is_default,
                    "tags": template.tags or []
                }
                for template in templates
            ]
        )
    
    async def export_individual(self, request: IndividualExportRequest) -> ExportResponse:
        """Exportar contenido individual"""
        
        # Verificar que el contenido existe
        content = self.db.query(Content).filter(Content.id == request.content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Contenido no encontrado")
        
        # Verificar template si se especifica
        template = None
        if request.template_id:
            template = self.db.query(Template).filter(Template.id == request.template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Crear registro de exportación
        export = Export(
            export_type=ExportType.INDIVIDUAL,
            template_id=request.template_id,
            content_ids=[str(request.content_id)],
            format=request.format,
            export_settings=request.export_settings.model_dump() if request.export_settings else {},
            estimated_completion=datetime.utcnow() + timedelta(minutes=2)
        )
        
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        
        # Iniciar proceso de exportación en background
        asyncio.create_task(self._process_individual_export(export.id))
        
        return ExportResponse(
            export_id=export.id,
            status=export.status,
            estimated_completion=export.estimated_completion
        )
    
    async def export_combined(self, request: CombinedExportRequest) -> ExportResponse:
        """Exportar múltiples contenidos combinados"""
        
        # Verificar que todos los contenidos existen
        contents = self.db.query(Content).filter(Content.id.in_(request.content_ids)).all()
        if len(contents) != len(request.content_ids):
            raise HTTPException(status_code=404, detail="Algunos contenidos no fueron encontrados")
        
        # Crear registro de exportación
        export = Export(
            export_type=ExportType.COMBINED,
            template_id=request.template_id,
            content_ids=[str(cid) for cid in request.content_ids],
            format=request.format,
            export_settings=request.export_settings.model_dump() if request.export_settings else {},
            estimated_completion=datetime.utcnow() + timedelta(minutes=3)
        )
        
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        
        # Iniciar proceso de exportación en background
        asyncio.create_task(self._process_combined_export(export.id))
        
        return ExportResponse(
            export_id=export.id,
            status=export.status,
            estimated_completion=export.estimated_completion
        )
    
    async def _process_individual_export(self, export_id: UUID):
        """Procesar exportación individual en background"""
        export = self.db.query(Export).filter(Export.id == export_id).first()
        if not export:
            return
        
        try:
            # Actualizar estado
            export.status = ExportStatus.IN_PROGRESS
            export.started_at = datetime.utcnow()
            export.progress = 10
            self.db.commit()
            
            # Obtener contenido
            content_id = UUID(export.content_ids[0])
            content = self.db.query(Content).filter(Content.id == content_id).first()
            
            export.progress = 30
            self.db.commit()
            
            # Generar archivo según formato
            filename = f"content_{content_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export.format}"
            file_path = self.export_dir / filename
            
            export.progress = 60
            self.db.commit()
            
            # Generar contenido del archivo
            if export.format == "pdf":
                file_content = self._generate_pdf_content(content, export.export_settings)
            elif export.format == "docx":
                file_content = self._generate_docx_content(content, export.export_settings)
            elif export.format == "latex":
                file_content = self._generate_latex_content(content, export.export_settings)
            else:
                raise ValueError(f"Formato no soportado: {export.format}")
            
            # Escribir archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Actualizar export con información del archivo
            export.filename = filename
            export.file_path = str(file_path)
            export.file_size = file_path.stat().st_size
            export.download_url = f"/api/v1/export/{export.id}/download"
            export.status = ExportStatus.COMPLETED
            export.progress = 100
            export.completed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            # Manejar errores
            export.status = ExportStatus.FAILED
            export.error_message = str(e)
            export.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def _process_combined_export(self, export_id: UUID):
        """Procesar exportación combinada en background"""
        export = self.db.query(Export).filter(Export.id == export_id).first()
        if not export:
            return
        
        try:
            # Actualizar estado
            export.status = ExportStatus.IN_PROGRESS
            export.started_at = datetime.utcnow()
            export.progress = 10
            self.db.commit()
            
            # Obtener todos los contenidos
            content_ids = [UUID(cid) for cid in export.content_ids]
            contents = self.db.query(Content).filter(Content.id.in_(content_ids)).all()
            
            export.progress = 30
            self.db.commit()
            
            # Generar archivo combinado
            filename = f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export.format}"
            file_path = self.export_dir / filename
            
            export.progress = 60
            self.db.commit()
            
            # Combinar contenidos
            combined_content = self._combine_contents(contents, export.export_settings)
            
            # Generar archivo según formato
            if export.format == "pdf":
                file_content = self._generate_combined_pdf(combined_content, export.export_settings)
            elif export.format == "docx":
                file_content = self._generate_combined_docx(combined_content, export.export_settings)
            elif export.format == "latex":
                file_content = self._generate_combined_latex(combined_content, export.export_settings)
            else:
                raise ValueError(f"Formato no soportado: {export.format}")
            
            # Escribir archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Actualizar export
            export.filename = filename
            export.file_path = str(file_path)
            export.file_size = file_path.stat().st_size
            export.download_url = f"/api/v1/export/{export.id}/download"
            export.status = ExportStatus.COMPLETED
            export.progress = 100
            export.completed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            export.status = ExportStatus.FAILED
            export.error_message = str(e)
            export.completed_at = datetime.utcnow()
            self.db.commit()
    
    def _generate_pdf_content(self, content: Content, settings: dict) -> str:
        """Generar contenido para PDF (LaTeX)"""
        latex_content = f"""
\\documentclass[{settings.get('font_size', '12pt')}]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[spanish]{{babel}}
\\usepackage[{settings.get('paper_size', 'a4paper')}]{{geometry}}

\\title{{{content.title}}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

{content.markdown_content}

\\end{{document}}
        """
        return latex_content
    
    def _generate_docx_content(self, content: Content, settings: dict) -> str:
        """Generar contenido para DOCX (HTML)"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{content.title}</title>
    <style>
        body {{ font-size: {settings.get('font_size', '12pt')}; }}
    </style>
</head>
<body>
    <h1>{content.title}</h1>
    <div>{content.markdown_content}</div>
</body>
</html>
        """
        return html_content
    
    def _generate_latex_content(self, content: Content, settings: dict) -> str:
        """Generar contenido LaTeX puro"""
        return self._generate_pdf_content(content, settings)
    
    def _combine_contents(self, contents: List[Content], settings: dict) -> str:
        """Combinar múltiples contenidos"""
        combined = ""
        for i, content in enumerate(contents, 1):
            combined += f"\\section{{{content.title}}}\n"
            combined += content.markdown_content + "\n\n"
        return combined
    
    def _generate_combined_pdf(self, combined_content: str, settings: dict) -> str:
        """Generar PDF combinado"""
        latex_content = f"""
\\documentclass[{settings.get('font_size', '12pt')}]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[spanish]{{babel}}
\\usepackage[{settings.get('paper_size', 'a4paper')}]{{geometry}}

\\title{{Documento Combinado}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents
\\newpage

{combined_content}

\\end{{document}}
        """
        return latex_content
    
    def _generate_combined_docx(self, combined_content: str, settings: dict) -> str:
        """Generar DOCX combinado"""
        return f"<html><body><h1>Documento Combinado</h1>{combined_content}</body></html>"
    
    def _generate_combined_latex(self, combined_content: str, settings: dict) -> str:
        """Generar LaTeX combinado"""
        return self._generate_combined_pdf(combined_content, settings)
    
    def get_export_status(self, export_id: UUID) -> ExportStatusResponse:
        """Obtener estado de exportación"""
        export = self.db.query(Export).filter(Export.id == export_id).first()
        
        if not export:
            raise HTTPException(status_code=404, detail="Exportación no encontrada")
        
        return ExportStatusResponse(
            export_id=export.id,
            status=export.status,
            progress=export.progress,
            download_url=export.download_url,
            filename=export.filename,
            file_size=export.file_size,
            expires_at=export.expires_at,
            error_message=export.error_message,
            created_at=export.created_at,
            completed_at=export.completed_at
        )
    
    def get_file_path(self, export_id: UUID) -> str:
        """Obtener path del archivo para descarga"""
        export = self.db.query(Export).filter(Export.id == export_id).first()
        
        if not export:
            raise HTTPException(status_code=404, detail="Exportación no encontrada")
        
        if export.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Exportación no completada")
        
        if export.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Archivo expirado")
        
        if not export.file_path or not os.path.exists(export.file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        return export.file_path