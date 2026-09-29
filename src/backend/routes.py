"""
Rutas y Endpoints de la API REST de Intelligent QA.
Gestiona el upload con guardrail y la ejecución asíncrona de agentes.
"""

import time
from typing import Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.backend.schemas import (
    ClassificationResponse,
    ExecuteTaskRequest,
    ExecuteTaskResponse,
    HealthResponse,
)
from src.core.agents.classifier import FileClassifier, MANDATORY_REJECTION_MESSAGE
from src.core.agents.requirements_agent import RequirementsAgent
from src.core.agents.code_agent import CodeAgent
from src.core.config import settings
from src.core.logger import StructuredLogger

router = APIRouter(prefix="/api/v1", tags=["Intelligent QA API"])

# Instancias singleton de los servicios del Core
classifier = FileClassifier()
requirements_agent = RequirementsAgent()
code_agent = CodeAgent()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Verifica la operatividad del backend y el modelo LLM configurado."""
    return HealthResponse(
        status="ok",
        model=settings.llm_model,
        version="1.0.0"
    )


@router.post(
    "/upload",
    response_model=ClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Subida de archivo y clasificación con guardrail estricto"
)
async def upload_and_classify_file(
    file: UploadFile = File(..., description="Fichero fuente (.java, .py) o documento de requisitos")
) -> ClassificationResponse:
    """
    Recibe un fichero, valida su codificación y contenido, y lo somete al
    clasificador y guardrail estricto de entrada.

    Si no es válido, retorna is_valid=False y el mensaje obligatorio de rechazo:
    'La documentación adjunta no es un requisito ni un fichero de código fuente de Java o Python.'
    """
    filename = file.filename or "unknown_file"

    try:
        raw_bytes = await file.read()
    except Exception as exc:
        StructuredLogger.log_error(f"Fallo al leer archivo recibido '{filename}'", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en la lectura del archivo: {str(exc)}"
        )

    # Intento de decodificación segura UTF-8 con fallback latino
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = raw_bytes.decode("latin-1")
        except Exception:
            # Ficheros binarios o ilegibles son rechazados de inmediato
            return ClassificationResponse(
                filename=filename,
                classification="INVALID",
                is_valid=False,
                confidence=1.0,
                reason="El archivo no contiene texto legible ni codificación UTF-8/Latin-1 válida.",
                rejection_message=MANDATORY_REJECTION_MESSAGE,
                content=None
            )

    # Evaluación mediante el clasificador / guardrail
    classification_result = classifier.classify(filename=filename, content=content)

    return ClassificationResponse(
        filename=filename,
        classification=classification_result.classification,
        is_valid=classification_result.is_valid,
        confidence=classification_result.confidence,
        reason=classification_result.reason,
        rejection_message=classification_result.rejection_message,
        content=content if classification_result.is_valid else None
    )


@router.post(
    "/execute-task",
    response_model=ExecuteTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecución de tareas especializadas sobre artefactos verificados"
)
async def execute_agent_task(payload: ExecuteTaskRequest) -> ExecuteTaskResponse:
    """
    Ejecuta de forma dirigida la herramienta solicitada a través del grafo
    correspondiente (RequirementsAgent o CodeAgent).
    """
    start_time = time.perf_counter()

    # 1. Validación de compatibilidad entre Tipo de Archivo y Tarea Solicitada
    valid_req_tasks = {"check_inconsistencies", "verify_standards", "generate_test_cases"}
    valid_code_tasks = {"reverse_engineer", "generate_unit_tests"}

    if payload.file_type == "REQUIREMENT":
        if payload.task not in valid_req_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tarea '{payload.task}' no permitida para artefactos de tipo 'REQUIREMENT'. "
                    f"Opciones válidas: {list(valid_req_tasks)}"
                )
            )
        # Despacho al grafo de Requisitos
        agent_output = requirements_agent.run(
            content=payload.content,
            action=payload.task
        )

    elif payload.file_type in ["JAVA_CODE", "PYTHON_CODE"]:
        if payload.task not in valid_code_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tarea '{payload.task}' no permitida para código fuente. "
                    f"Opciones válidas: {list(valid_code_tasks)}"
                )
            )
        # Despacho al grafo de Código
        agent_output = code_agent.run(
            content=payload.content,
            language=payload.file_type,
            action=payload.task
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo '{payload.file_type}' no procesable para ejecución de tareas."
        )

    elapsed_time = round(time.perf_counter() - start_time, 3)

    return ExecuteTaskResponse(
        task=payload.task,
        file_type=payload.file_type,
        success=agent_output.get("success", False),
        result=agent_output.get("result"),
        error=agent_output.get("error"),
        execution_time_seconds=elapsed_time
    )