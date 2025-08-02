from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

class AIProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"  
    GEMINI = "gemini"
    GROQ = "groq"
    COHERE = "cohere"
    OLLAMA = "ollama"
    XAI = "xai"

class AIServiceBase(ABC):
    """Clase base para todos los proveedores de IA"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generar contenido usando el proveedor específico"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles para este proveedor"""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validar que la conexión al proveedor funcione"""
        pass

class GroqService(AIServiceBase):
    """Implementación para Groq"""
    
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        super().__init__(api_key, model)
        try:
            # Simulamos el import para evitar errores si no está instalado
            # import groq
            # self.client = groq.Groq(api_key=api_key)
            pass
        except ImportError:
            print("Warning: groq package not installed")
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        # Por ahora retornamos contenido simulado
        # TODO: Implementar llamada real a Groq
        return f"""
# Sesión de Clase Generada por IA

## Introducción
Esta es una sesión de clase generada automáticamente basada en el contenido del sílabo proporcionado.

## Objetivos
- Comprender los conceptos fundamentales del tema
- Aplicar los conocimientos en ejercicios prácticos
- Desarrollar habilidades de análisis crítico

## Desarrollo del Tema

### Conceptos Clave
- Concepto 1: Definición y características principales
- Concepto 2: Aplicaciones prácticas
- Concepto 3: Relación con otros temas

### Actividades
1. **Actividad Introductoria** (10 minutos)
   - Lluvia de ideas sobre conocimientos previos
   - Presentación de casos reales

2. **Desarrollo Teórico** (20 minutos)
   - Explicación de conceptos fundamentales
   - Ejemplos ilustrativos

3. **Práctica Guiada** (15 minutos)
   - Ejercicios en grupo
   - Resolución de problemas típicos

## Conclusiones
- Resumen de puntos clave
- Conexión con la siguiente sesión
- Tareas para casa

## Recursos Necesarios
- Presentación digital
- Material impreso
- Acceso a internet
- Pizarra o proyector

## Evaluación
- Participación en clase: 40%
- Ejercicios prácticos: 60%

*Contenido generado por IA - Proveedor: {self.model}*
        """
    
    def get_available_models(self) -> List[str]:
        return ["mixtral-8x7b-32768", "llama2-70b-4096", "gemma-7b-it"]
    
    async def validate_connection(self) -> bool:
        # Por ahora siempre retorna True
        return True

# Factory Pattern para crear servicios
class AIServiceFactory:
    """Factory para crear instancias de servicios de IA"""
    
    @staticmethod
    def create_service(
        provider: AIProvider, 
        api_key: str, 
        model: Optional[str] = None
    ) -> AIServiceBase:
        """Crear servicio de IA según el proveedor"""
        
        if provider == AIProvider.GROQ:
            return GroqService(api_key, model or "mixtral-8x7b-32768")
        # Por ahora solo implementamos Groq
        # elif provider == AIProvider.OPENAI:
        #     return OpenAIService(api_key, model or "gpt-4")
        else:
            # Por ahora usamos Groq como fallback
            return GroqService(api_key, model or "mixtral-8x7b-32768")

# Servicio principal que maneja múltiples IAs
class MultiAIService:
    """Servicio que puede usar múltiples proveedores de IA"""
    
    def __init__(self):
        self.services: Dict[AIProvider, AIServiceBase] = {}
        self.primary_provider: Optional[AIProvider] = None
        self.fallback_providers: List[AIProvider] = []
    
    def add_provider(
        self, 
        provider: AIProvider, 
        api_key: str, 
        model: Optional[str] = None,
        is_primary: bool = False
    ):
        """Agregar un proveedor de IA"""
        service = AIServiceFactory.create_service(provider, api_key, model)
        self.services[provider] = service
        
        if is_primary:
            self.primary_provider = provider
        else:
            self.fallback_providers.append(provider)
    
    async def generate_content(
        self, 
        prompt: str, 
        provider: Optional[AIProvider] = None,
        **kwargs
    ) -> str:
        """Generar contenido usando el proveedor especificado o el primario"""
        
        # Usar proveedor específico si se especifica
        if provider and provider in self.services:
            return await self.services[provider].generate_content(prompt, **kwargs)
        
        # Intentar con proveedor primario
        if self.primary_provider and self.primary_provider in self.services:
            try:
                return await self.services[self.primary_provider].generate_content(prompt, **kwargs)
            except Exception as e:
                print(f"Error con proveedor primario {self.primary_provider}: {e}")
        
        # Intentar con proveedores de respaldo
        for fallback_provider in self.fallback_providers:
            if fallback_provider in self.services:
                try:
                    return await self.services[fallback_provider].generate_content(prompt, **kwargs)
                except Exception as e:
                    print(f"Error con proveedor de respaldo {fallback_provider}: {e}")
                    continue
        
        # Si no hay proveedores configurados, retornar contenido demo
        return """
# Contenido Demo

Este es contenido de demostración generado porque no hay proveedores de IA configurados.

## Para configurar un proveedor:
1. Obtén una API key del proveedor (ej: Groq)
2. Agrega la key al archivo .env.docker
3. Reinicia Docker

## Proveedores soportados:
- Groq (gratuito)
- OpenAI (pago)
- Claude (pago)
- Gemini (gratuito con límites)
        """
    
    async def health_check(self) -> Dict[AIProvider, bool]:
        """Verificar el estado de todos los proveedores"""
        health_status = {}
        for provider, service in self.services.items():
            health_status[provider] = await service.validate_connection()
        return health_status