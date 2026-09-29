"""
Punto de Entrada de la Aplicación FastAPI.
Configura middlewares de observabilidad, CORS y validación de prompts al inicio.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.backend.routes import router
from src.core.config import settings, prompt_loader
from src.core.logger import logger, StructuredLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida del backend:
    Valida al arranque que todos los prompts existan en disco (Regla 1).
    """
    logger.info("Iniciando Intelligent QA Backend...")
    try:
        # Falla de forma inmediata al iniciar si falta alguna plantilla en data/prompts/
        prompt_loader.validate_all_prompts()
        logger.info("Todas las plantillas de prompts externas fueron validadas correctamente.")
    except Exception as exc:
        logger.critical(f"FATAL: Fallo al validar plantillas de prompts: {exc}")
        raise exc

    yield

    logger.info("Apagando Intelligent QA Backend...")


app = FastAPI(
    title="Intelligent QA (MVP) - API",
    description="Backend para análisis inteligente de requisitos y código legacy para TFM.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS permitiendo acceso desde el frontend de Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción o despliegue local permite llamadas desde localhost:8501
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Middleware para trazar el tiempo de respuesta y estado HTTP de cada petición."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Loguear llamadas a endpoints de la API
    if request.url.path.startswith("/api/"):
        logger.info(
            f"HTTP {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s"
        )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo de excepciones no controladas para evitar fugas de traza inseguras."""
    StructuredLogger.log_error(f"Excepción global en {request.method} {request.url.path}", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Consulte los logs del sistema."}
    )


# Registro de rutas de la API
app.include_router(router)