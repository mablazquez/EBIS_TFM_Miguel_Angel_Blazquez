"""
Módulo de Clasificación y Guardrail Estricto de Entrada.
Filtra documentos no válidos, archivos mixtos y lenguajes no soportados,
garantizando la invocación de agentes únicamente sobre artefactos verificados.
"""

import ast
import json
import re
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.core.config import settings, prompt_loader
from src.core.logger import StructuredLogger, measure_execution_time

# Mensaje exacto de rechazo mandatario (Regla 3)
MANDATORY_REJECTION_MESSAGE = (
    "La documentación adjunta no es un requisito ni un fichero de código fuente de Java o Python."
)

ValidClassificationType = Literal["REQUIREMENT", "JAVA_CODE", "PYTHON_CODE", "INVALID"]


class LLMClassificationOutput(BaseModel):
    """Esquema de salida estructurada esperado del modelo LLM."""
    classification: ValidClassificationType = Field(
        ...,
        description="Categoría asignada: REQUIREMENT, JAVA_CODE, PYTHON_CODE o INVALID"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Nivel de certeza en la clasificación (0.0 a 1.0)"
    )
    reason: str = Field(
        ...,
        description="Justificación técnica de la decisión de clasificación"
    )


class ClassificationResult(BaseModel):
    """Resultado final expuesto al backend y capas superiores."""
    filename: str
    classification: ValidClassificationType
    is_valid: bool
    confidence: float
    reason: str
    rejection_message: Optional[str] = None


class FileClassifier:
    """
    Clasificador y Guardrail de Entrada.
    Combina análisis heurístico/sintáctico con evaluación semántica mediante gemini-3.8-flash.
    """

    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None) -> None:
        self.llm = llm or ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0
        )
        # Carga el prompt externalizado (falla de inmediato si el archivo no existe)
        self.prompt_template = prompt_loader.get_prompt("classifier_guardrail.txt")

    def _pre_validate_syntax(self, content: str, extension: str) -> Optional[ClassificationResult]:
        """
        Realiza validaciones preliminares sintácticas y de integridad estructural.
        Si detecta fallos deterministas irrecuperables, rechaza sin consumir tokens del LLM.
        """
        # Contenido vacío o compuesto únicamente de espacios en blanco
        if not content or not content.strip():
            return ClassificationResult(
                filename="unknown",
                classification="INVALID",
                is_valid=False,
                confidence=1.0,
                reason="El contenido del archivo está vacío.",
                rejection_message=MANDATORY_REJECTION_MESSAGE
            )

        # Validación sintáctica para archivos Python
        if extension.lower() == ".py":
            try:
                ast.parse(content)
            except SyntaxError as e:
                return ClassificationResult(
                    filename="unknown",
                    classification="INVALID",
                    is_valid=False,
                    confidence=1.0,
                    reason=f"Error sintáctico Python irrecuperable: línea {e.lineno}, {e.msg}",
                    rejection_message=MANDATORY_REJECTION_MESSAGE
                )

        # Validación estructural mínima para archivos Java
        if extension.lower() == ".java":
            has_class_or_interface = re.search(r"\b(class|interface|enum|record)\s+\w+", content)
            if not has_class_or_interface:
                return ClassificationResult(
                    filename="unknown",
                    classification="INVALID",
                    is_valid=False,
                    confidence=1.0,
                    reason="El archivo Java no define clases, interfaces, enums ni records válidos.",
                    rejection_message=MANDATORY_REJECTION_MESSAGE
                )

        return None

    def _call_llm_classifier(
        self,
        filename: str,
        extension: str,
        content: str
    ) -> LLMClassificationOutput:
        """
        Ejecuta la llamada a gemini-3.8-flash inyectando el prompt externalizado
        mediante reemplazo seguro para no entrar en conflicto con el JSON schema.
        """
        prompt = (
            self.prompt_template
            .replace("{filename}", filename)
            .replace("{extension}", extension)
            .replace("{content}", content)
        )

        try:
            structured_llm = self.llm.with_structured_output(LLMClassificationOutput)
            result = structured_llm.invoke([HumanMessage(content=prompt)])
            return result
        except Exception:
            raw_response = self.llm.invoke([HumanMessage(content=prompt)])
            raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
            
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json.strip(), flags=re.MULTILINE)

            parsed = json.loads(cleaned_json)
            return LLMClassificationOutput(**parsed)

    def classify(self, filename: str, content: str) -> ClassificationResult:
        """
        Punto de entrada principal para clasificar y aplicar el guardrail sobre un archivo.

        Args:
            filename: Nombre del archivo con su extensión.
            content: Contenido textual del archivo.

        Returns:
            ClassificationResult con el veredicto, validez y mensaje estricto si aplica.
        """
        extension = f".{filename.split('.')[-1]}" if "." in filename else ""

        # Registrar recepción de archivo
        StructuredLogger.log_file_metadata(
            filename=filename,
            size_bytes=len(content.encode("utf-8")),
            extension=extension
        )

        # 1. Comprobación sintáctica previa determinista
        pre_check = self._pre_validate_syntax(content=content, extension=extension)
        if pre_check:
            pre_check.filename = filename
            StructuredLogger.log_classification(
                filename=filename,
                verdict=pre_check.classification,
                confidence_or_reason=pre_check.reason
            )
            return pre_check

        # 2. Evaluación semántica con gemini-3.8-flash y medición de latencia
        try:
            with measure_execution_time(agent_name="FileClassifier", task="classify_file"):
                llm_output = self._call_llm_classifier(
                    filename=filename,
                    extension=extension,
                    content=content
                )

            is_valid = llm_output.classification in ["REQUIREMENT", "JAVA_CODE", "PYTHON_CODE"]
            rejection_message = None if is_valid else MANDATORY_REJECTION_MESSAGE

            result = ClassificationResult(
                filename=filename,
                classification=llm_output.classification,
                is_valid=is_valid,
                confidence=llm_output.confidence,
                reason=llm_output.reason,
                rejection_message=rejection_message
            )

        except Exception as exc:
            StructuredLogger.log_error(f"Fallo en clasificación LLM para '{filename}'", exc)
            # En caso de error crítico imprevisto, se rechaza de forma segura (fail-closed)
            result = ClassificationResult(
                filename=filename,
                classification="INVALID",
                is_valid=False,
                confidence=0.0,
                reason=f"Excepción en proceso de clasificación: {str(exc)}",
                rejection_message=MANDATORY_REJECTION_MESSAGE
            )

        # 3. Registro del veredicto estructurado
        StructuredLogger.log_classification(
            filename=filename,
            verdict=result.classification,
            confidence_or_reason=result.reason
        )

        return result