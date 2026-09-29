"""
Módulo de Herramientas para el Agente de Requisitos.
Cada herramienta carga su prompt externalizado a través de prompt_loader y
ejecuta gemini-3.8-flash garantizando métricas de rendimiento y logging estructurado.
"""

from typing import Optional
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings, prompt_loader
from src.core.logger import StructuredLogger, measure_execution_time


def _get_llm(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    """Instancia el modelo gemini-3.8-flash con los parámetros configurados."""
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.gemini_api_key,
        temperature=temperature
    )


@tool
def check_document_inconsistencies(content: str) -> str:
    """
    Audita una especificación de requisitos en busca de contradicciones directas,
    ambigüedades de estado, vacíos lógicos y condiciones de borde no cubiertas.

    Args:
        content: Texto íntegro del documento de requisitos.

    Returns:
        Reporte en Markdown con el resumen ejecutivo, inconsistencias críticas y matriz lógica.
    """
    template = prompt_loader.get_prompt("inconsistencies.txt")
    formatted_prompt = template.format(content=content)

    with measure_execution_time(agent_name="RequirementsAgent", task="check_document_inconsistencies"):
        llm = _get_llm(temperature=0.0)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content if hasattr(response, "content") else str(response)


@tool
def verify_requirements_standards(content: str) -> str:
    """
    Evalúa la calidad del documento de requisitos conforme a los atributos de la
    norma ISO/IEC/IEEE 29148 e IEEE 830 (univocidad, atomicidad, completitud, verificabilidad).

    Args:
        content: Texto íntegro del documento de requisitos.

    Returns:
        Reporte en Markdown con calificación de madurez, tabla de atributos y reescritura normalizada.
    """
    template = prompt_loader.get_prompt("standards.txt")
    formatted_prompt = template.format(content=content)

    with measure_execution_time(agent_name="RequirementsAgent", task="verify_requirements_standards"):
        llm = _get_llm(temperature=0.1)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content if hasattr(response, "content") else str(response)


@tool
def generate_test_cases(content: str) -> str:
    """
    Genera una suite de casos de prueba funcionales (Happy Path, Negativos y Edge Cases)
    a partir de la especificación de requisitos proporcionada.

    Args:
        content: Texto íntegro del documento de requisitos.

    Returns:
        Reporte en Markdown con resumen de cobertura y fichas detalladas de casos de prueba.
    """
    template = prompt_loader.get_prompt("test_cases.txt")
    formatted_prompt = template.format(content=content)

    with measure_execution_time(agent_name="RequirementsAgent", task="generate_test_cases"):
        llm = _get_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content if hasattr(response, "content") else str(response)