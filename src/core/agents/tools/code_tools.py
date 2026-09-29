"""
Módulo de Herramientas para el Agente de Código Legacy.
Carga las plantillas externalizadas (reverse_engineering.txt y unit_tests.txt)
y ejecuta gemini-3.8-flash trazando tiempos de ejecución y metadatos.
"""

from typing import Optional
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings, prompt_loader
from src.core.logger import StructuredLogger, measure_execution_time


def _get_llm(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    """Instancia el modelo gemini-3.8-flash con la configuración centralizada."""
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.gemini_api_key,
        temperature=temperature
    )


def normalize_language_name(language: str) -> str:
    """Normaliza identificadores técnicos de lenguaje a nombres canónicos."""
    lang_upper = language.upper()
    if "JAVA" in lang_upper:
        return "Java"
    elif "PYTHON" in lang_upper or "PY" in lang_upper:
        return "Python"
    return language.strip()


@tool
def reverse_engineer_requirements(content: str, language: str = "Java") -> str:
    """
    Realiza ingeniería inversa sobre código fuente legacy para reconstruir
    especificaciones funcionales formales, deducir reglas de negocio y contratos.

    Args:
        content: Código fuente completo a analizar.
        language: Lenguaje de programación ("Java" o "Python").

    Returns:
        Documento en Markdown con ficha técnica, catálogo de reglas de negocio y requisitos derivados.
    """
    normalized_lang = normalize_language_name(language)
    template = prompt_loader.get_prompt("reverse_engineering.txt")
    formatted_prompt = template.format(
        language=normalized_lang,
        content=content
    )

    with measure_execution_time(agent_name="CodeAgent", task="reverse_engineer_requirements"):
        llm = _get_llm(temperature=0.1)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content if hasattr(response, "content") else str(response)


@tool
def generate_unit_tests(content: str, language: str = "Java") -> str:
    """
    Genera una suite completa de pruebas unitarias (JUnit 5 para Java o Pytest para Python)
    cubriendo Happy Paths, casos de borde y gestión de excepciones.

    Args:
        content: Código fuente de la clase o módulo a testear.
        language: Lenguaje de programación de destino ("Java" o "Python").

    Returns:
        Reporte en Markdown con el código de tests auto-contenido, instrucciones y matriz de trazabilidad.
    """
    normalized_lang = normalize_language_name(language)
    template = prompt_loader.get_prompt("unit_tests.txt")
    formatted_prompt = template.format(
        language=normalized_lang,
        content=content
    )

    with measure_execution_time(agent_name="CodeAgent", task="generate_unit_tests"):
        llm = _get_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content if hasattr(response, "content") else str(response)