from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import documents, content, export

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API para generar contenido educativo con IA",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(content.router, prefix="/api/v1", tags=["content"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])

@app.get("/")
async def root():
    return {"message": "SyllabusAI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}