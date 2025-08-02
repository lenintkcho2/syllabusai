from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncio
import math
from datetime import datetime, timedelta

from app.models.content import Generation, Content, GenerationStatus, ContentType, AIProvider
from app.models.document import Document
from app.schemas.content import (
    GenerateContentRequest, GenerationResponse, GenerationStatusResponse,
    ContentResponse, ContentListResponse, UpdateContentRequest, ContentDeleteResponse
)
from app.services.ai_service import MultiAIService, AIServiceFactory
from app.config import settings

class ContentService:
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = self._initialize_ai_service()
    
    def _initialize_ai_service(self) -> MultiAIService:
        """Inicializar servicio de IA con múltiples proveedores"""
        ai_service = MultiAIService()
        
        # Configurar proveedores disponibles
        if settings.openai_api_key:
            ai_service.add_provider(AIProvider.OPENAI, settings.openai_api_key, "gpt-4")
        
        if settings.claude_api_key:
            ai_service.add_provider(AIProvider.CLAUDE, settings.claude_api_key, "claude-3-sonnet-20240229")
        
        if settings.gemini_api_key:
            ai_service.add_provider(AIProvider.GEMINI, settings.gemini_api_key, "gemini-pro")
        
        if settings.groq_api_key:
            ai_service.add_provider(AIProvider.GROQ, settings.groq_api_key, "mixtral-8x7b-32768", is_primary=True)
        
        if settings.cohere_api_key:
            ai_service.add_provider(AIProvider.COHERE, settings.cohere_api_key, "command")
        
        return ai_service
    
    async def generate_content(self, request: GenerateContentRequest) -> GenerationResponse:
        """Iniciar generación de contenido"""
        
        # Verificar que el documento existe (sin usar relaciones)
        document = self.db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Crear registro de generación
        generation = Generation(
            document_id=request.document_id,
            content_type=request.content_type,
            scope=request.scope,
            ai_provider=request.ai_provider,
            ai_model=request.configuration.ai_model,
            configuration=request.configuration.model_dump(),
            estimated_completion=datetime.utcnow() + timedelta(minutes=5)
        )
        
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        
        # Iniciar generación asíncrona
        asyncio.create_task(self._process_generation(generation.id))
        
        return GenerationResponse(
            generation_id=generation.id,
            status=generation.status,
            estimated_completion=generation.estimated_completion,
            message="Generación iniciada. Use GET /api/v1/content/generation/{generation_id} para monitorear el progreso."
        )
    
    async def _process_generation(self, generation_id: UUID):
        """Procesar generación de contenido en background"""
        generation = self.db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return
        
        try:
            # Actualizar estado
            generation.status = GenerationStatus.IN_PROGRESS
            generation.started_at = datetime.utcnow()
            generation.progress = 10
            self.db.commit()
            
            # Obtener documento y su contenido
            document = self.db.query(Document).filter(Document.id == generation.document_id).first()
            
            # Generar prompt basado en configuración
            prompt = self._build_prompt(document, generation)
            system_prompt = self._build_system_prompt(generation)
            
            # Actualizar progreso
            generation.progress = 30
            self.db.commit()
            
            # Generar contenido con IA
            ai_content = await self.ai_service.generate_content(
                prompt=prompt,
                provider=generation.ai_provider,
                system_prompt=system_prompt,
                max_tokens=generation.configuration.get("content_length", 5) * 400,
                temperature=0.7
            )
            
            # Actualizar progreso
            generation.progress = 70
            self.db.commit()
            
            # Procesar y estructurar contenido generado
            structured_content = self._structure_content(ai_content, generation.content_type)
            
            # Crear registro de contenido
            content = Content(
                generation_id=generation.id,
                document_id=generation.document_id,
                title=structured_content["title"],
                content_type=generation.content_type,
                markdown_content=structured_content["markdown"],
                sections=structured_content["sections"],
                content_metadata={
                    "ai_provider": generation.ai_provider.value,
                    "ai_model": generation.ai_model,
                    "generation_config": generation.configuration
                }
            )
            
            self.db.add(content)
            
            # Finalizar generación
            generation.status = GenerationStatus.COMPLETED
            generation.progress = 100
            generation.completed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            # Manejar errores
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            generation.completed_at = datetime.utcnow()
            self.db.commit()
    
    def _build_prompt(self, document: Document, generation: Generation) -> str:
        """Construir prompt para la IA basado en el documento y configuración"""
        config = generation.configuration
        
        base_prompt = f"""
        Basándote en el siguiente contenido del sílabo, genera {generation.content_type.value} 
        para el nivel {config.get('educational_level', 'universitario')}.
        
        Contenido del sílabo:
        {document.text_content[:3000]}  # Limitar contenido
        
        Configuración:
        - Enfoque pedagógico: {config.get('pedagogical_approach', 'Basado en competencias')}
        - Longitud de contenido: {config.get('content_length', 5)} secciones
        - Idioma: {config.get('language', 'español')}
        
        Instrucciones adicionales:
        {config.get('additional_instructions', 'Ninguna')}
        
        Genera contenido educativo estructurado, práctico y aplicable.
        """
        
        return base_prompt
    
    def _build_system_prompt(self, generation: Generation) -> str:
        """Construir system prompt específico por tipo de contenido"""
        
        prompts = {
            ContentType.CLASS_SESSION: """
            Eres un experto en diseño instruccional. Genera una sesión de clase completa que incluya:
            1. Introducción y objetivos claros
            2. Desarrollo del tema con actividades
            3. Conclusiones y evaluación
            4. Recursos y materiales necesarios
            Usa formato markdown y estructura pedagógica sólida.
            """,
            
            ContentType.STUDY_GUIDE: """
            Eres un especialista en materiales educativos. Crea una guía de estudio que incluya:
            1. Resumen de conceptos clave
            2. Ejercicios prácticos
            3. Preguntas de autoevaluación
            4. Referencias adicionales
            Usa formato markdown y enfoque didáctico.
            """,
            
            ContentType.PRESENTATION: """
            Eres un diseñador de presentaciones educativas. Crea contenido para diapositivas que incluya:
            1. Diapositivas de título y agenda
            2. Contenido principal con puntos clave
            3. Diapositivas de actividades interactivas
            4. Diapositiva de conclusiones
            Usa formato markdown optimizado para presentaciones.
            """
        }
        
        return prompts.get(generation.content_type, prompts[ContentType.CLASS_SESSION])
    
    def _structure_content(self, ai_content: str, content_type: ContentType) -> Dict[str, Any]:
        """Estructurar contenido generado por la IA"""
        
        # Extraer título (primera línea con #)
        lines = ai_content.split('\n')
        title = "Contenido Generado"
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Dividir en secciones básicas
        sections = {
            "introduction": "",
            "objectives": "",
            "development": "",
            "conclusion": ""
        }
        
        # Lógica simple para dividir contenido en secciones
        # (se puede mejorar con regex más sofisticado)
        current_section = "development"
        section_content = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["introducción", "introduction", "objetivo"]):
                if section_content:
                    sections[current_section] = '\n'.join(section_content)
                    section_content = []
                current_section = "introduction"
            elif any(keyword in line.lower() for keyword in ["objetivo", "objective"]):
                if section_content:
                    sections[current_section] = '\n'.join(section_content)
                    section_content = []
                current_section = "objectives"
            elif any(keyword in line.lower() for keyword in ["conclusión", "conclusion", "resumen"]):
                if section_content:
                    sections[current_section] = '\n'.join(section_content)
                    section_content = []
                current_section = "conclusion"
            
            section_content.append(line)
        
        # Agregar último contenido
        if section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return {
            "title": title,
            "markdown": ai_content,
            "sections": sections
        }
    
    def get_generation_status(self, generation_id: UUID) -> GenerationStatusResponse:
        """Obtener estado de una generación"""
        generation = self.db.query(Generation).filter(Generation.id == generation_id).first()
        
        if not generation:
            raise HTTPException(status_code=404, detail="Generación no encontrada")
        
        # Obtener contenidos generados
        contents = self.db.query(Content).filter(Content.generation_id == generation_id).all()
        
        return GenerationStatusResponse(
            generation_id=generation.id,
            status=generation.status,
            progress=generation.progress,
            results=[
                {
                    "content_id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "content_metadata": content.content_metadata
                }
                for content in contents
            ],
            error_message=generation.error_message,
            created_at=generation.created_at,
            completed_at=generation.completed_at
        )
    
    def get_contents(
        self, 
        document_id: Optional[UUID] = None,
        content_type: Optional[ContentType] = None,
        page: int = 1,
        limit: int = 10
    ) -> ContentListResponse:
        """Obtener lista de contenidos"""
        
        query = self.db.query(Content).filter(Content.is_active == True)
        
        if document_id:
            query = query.filter(Content.document_id == document_id)
        
        if content_type:
            query = query.filter(Content.content_type == content_type)
        
        # Total
        total = query.count()
        
        # Paginación
        offset = (page - 1) * limit
        contents = query.offset(offset).limit(limit).all()
        
        # Calcular páginas
        pages = math.ceil(total / limit)
        
        return ContentListResponse(
            contents=[
                {
                    "content_id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "document_id": content.document_id,
                    "created_at": content.created_at
                }
                for content in contents
            ],
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    
    def get_content_by_id(self, content_id: UUID) -> ContentResponse:
        """Obtener contenido específico"""
        content = self.db.query(Content).filter(
            and_(Content.id == content_id, Content.is_active == True)
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Contenido no encontrado")
        
        return ContentResponse(
            content_id=content.id,
            title=content.title,
            content_type=content.content_type,
            markdown_content=content.markdown_content,
            sections=content.sections,
            content_metadata=content.content_metadata,
            document_id=content.document_id,
            generation_id=content.generation_id,
            version=content.version,
            created_at=content.created_at,
            updated_at=content.updated_at
        )
    
    def update_content(self, content_id: UUID, request: UpdateContentRequest) -> ContentResponse:
        """Actualizar contenido existente"""
        content = self.db.query(Content).filter(
            and_(Content.id == content_id, Content.is_active == True)
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Contenido no encontrado")
        
        # Actualizar campos si se proporcionan
        if request.title is not None:
            content.title = request.title
        
        if request.markdown_content is not None:
            content.markdown_content = request.markdown_content
        
        if request.sections is not None:
            content.sections = request.sections
        
        # Incrementar versión
        content.version += 1
        content.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(content)
        
        return self.get_content_by_id(content_id)
    
    def delete_content(self, content_id: UUID) -> ContentDeleteResponse:
        """Eliminar contenido (soft delete)"""
        content = self.db.query(Content).filter(
            and_(Content.id == content_id, Content.is_active == True)
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Contenido no encontrado")
        
        # Soft delete
        content.is_active = False
        content.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return ContentDeleteResponse(message="Contenido eliminado exitosamente")