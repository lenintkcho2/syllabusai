from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./syllabusai.db"  # SQLite por defecto
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # AI Services (múltiples proveedores)
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Claude (Anthropic) 
    claude_api_key: Optional[str] = None
    
    # Google Gemini
    gemini_api_key: Optional[str] = None
    
    # Groq
    groq_api_key: Optional[str] = None
    
    # Cohere
    cohere_api_key: Optional[str] = None
    
    # Configuración de IA
    primary_ai_provider: str = "groq"  # Proveedor principal
    fallback_ai_providers: str = "gemini,claude,openai"  # Proveedores de respaldo
    
    # App Settings
    app_name: str = "SyllabusAI API"
    debug: bool = False
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".docx", ".txt"]
    
    class Config:
        env_file = ".env"

settings = Settings()