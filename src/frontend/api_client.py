"""
Cliente API para el Frontend Streamlit.
Encapsula las llamadas HTTP a FastAPI con gestión de timeouts, reintentos y errores de red.
"""

from typing import Any, Dict, Optional
import httpx

from src.core.config import settings
from src.core.logger import logger


class IntelligentQAClient:
    """Cliente HTTP síncrono optimizado para el ciclo de vida de Streamlit."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        """Consulta el estado del backend y el modelo LLM activo."""
        url = f"{self.base_url}/api/v1/health"
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning(f"Backend no disponible en {url}: {exc}")
            return {"status": "unreachable", "model": "N/A", "error": str(exc)}

    def upload_file(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Envía un archivo al backend para someterlo al guardrail y clasificación.

        Args:
            filename: Nombre del archivo cargado.
            file_bytes: Contenido binario del archivo.

        Returns:
            Diccionario con la respuesta de ClassificationResponse.
        """
        url = f"{self.base_url}/api/v1/upload"
        files = {"file": (filename, file_bytes, "application/octet-stream")}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, files=files)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error HTTP en upload ({exc.response.status_code}): {exc.response.text}")
            return {
                "filename": filename,
                "classification": "INVALID",
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Fallo del servidor ({exc.response.status_code}) al procesar el archivo.",
                "rejection_message": exc.response.json().get("detail", "Error del servidor."),
                "content": None
            }
        except Exception as exc:
            logger.error(f"Excepción de conexión en upload: {exc}")
            return {
                "filename": filename,
                "classification": "INVALID",
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"No se pudo conectar con el backend: {str(exc)}",
                "rejection_message": "Error de comunicación con el servicio backend.",
                "content": None
            }

    def execute_task(
        self,
        filename: str,
        file_type: str,
        task: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Solicita la ejecución de una herramienta al agente correspondiente en LangGraph.

        Args:
            filename: Nombre del archivo de origen.
            file_type: 'REQUIREMENT', 'JAVA_CODE' o 'PYTHON_CODE'.
            task: Identificador de la acción a ejecutar.
            content: Contenido del archivo validado.

        Returns:
            Diccionario con la respuesta de ExecuteTaskResponse.
        """
        url = f"{self.base_url}/api/v1/execute-task"
        payload = {
            "filename": filename,
            "file_type": file_type,
            "task": task,
            "content": content
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text
            logger.error(f"Error HTTP en execute-task: {error_detail}")
            return {
                "task": task,
                "file_type": file_type,
                "success": False,
                "result": None,
                "error": f"Error del backend ({exc.response.status_code}): {error_detail}",
                "execution_time_seconds": 0.0
            }
        except Exception as exc:
            logger.error(f"Excepción de conexión en execute-task: {exc}")
            return {
                "task": task,
                "file_type": file_type,
                "success": False,
                "result": None,
                "error": f"Error de comunicación con el backend: {str(exc)}",
                "execution_time_seconds": 0.0
            }


# Instancia singleton del cliente para su reutilización en la UI
api_client = IntelligentQAClient()