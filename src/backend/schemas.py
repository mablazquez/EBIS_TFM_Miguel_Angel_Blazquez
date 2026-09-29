"""
Esquemas Pydantic para el API REST de Intelligent QA.
Define contratos de entrada y salida para clasificación y ejecución de agentes.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# Tipos permitidos por el clasificador y guardrail
ClassificationType = Literal["REQUIREMENT", "JAVA_CODE", "PYTHON_CODE", "INVALID"]

# Acciones soportadas por los agentes
RequirementsTaskType = Literal[
    "check_inconsistencies",
    "verify_standards",
    "generate_test_cases"
]
CodeTaskType = Literal[
    "reverse_engineer",
    "generate_unit_tests"
]
AllowedTaskType = Literal[RequirementsTaskType, CodeTaskType]


class HealthResponse(BaseModel):
    """Respuesta del endpoint de comprobación de salud del sistema."""
    status: str = Field(default="ok", example="ok")
    model: str = Field(..., example="gemini-3.8-flash")
    version: str = Field(default="1.0.0", example="1.0.0")


class ClassificationResponse(BaseModel):
    """Resultado devuelto tras procesar la subida y clasificación de un archivo."""
    filename: str = Field(..., description="Nombre original del archivo subido")
    classification: ClassificationType = Field(..., description="Veredicto de clasificación")
    is_valid: bool = Field(..., description="Indica si el archivo superó el guardrail")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de certeza (0.0 a 1.0)")
    reason: str = Field(..., description="Explicación técnica de la clasificación")
    rejection_message: Optional[str] = Field(
        default=None,
        description="Mensaje mandatario si el archivo es rechazado por el guardrail"
    )
    content: Optional[str] = Field(
        default=None,
        description="Contenido textual del archivo validado para subsiguiente procesamiento"
    )


class ExecuteTaskRequest(BaseModel):
    """Petición para ejecutar una tarea especializada sobre un contenido verificado."""
    filename: str = Field(default="document.txt", description="Nombre del archivo de origen")
    file_type: Literal["REQUIREMENT", "JAVA_CODE", "PYTHON_CODE"] = Field(
        ...,
        description="Tipo de artefacto previamente clasificado"
    )
    task: AllowedTaskType = Field(
        ...,
        description="Acción concreta a solicitar al agente respectivo"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Contenido textual completo a procesar"
    )


class ExecuteTaskResponse(BaseModel):
    """Resultado de la ejecución de una tarea por un agente de LangGraph."""
    task: str = Field(..., description="Identificador de la tarea ejecutada")
    file_type: str = Field(..., description="Tipo de archivo procesado")
    success: bool = Field(..., description="Indica si la ejecución culminó sin errores")
    result: Optional[str] = Field(
        default=None,
        description="Informe técnico en Markdown o código generado"
    )
    error: Optional[str] = Field(
        default=None,
        description="Mensaje de error descriptivo en caso de fallo"
    )
    execution_time_seconds: float = Field(
        ...,
        description="Tiempo total transcurrido durante la invocación del agente"
    )