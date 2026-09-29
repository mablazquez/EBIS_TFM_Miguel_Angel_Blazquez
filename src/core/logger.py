"""Sistema de logging estructurado para Intelligent QA.

Provee trazabilidad completa de metadatos de archivos, veredictos de clasificación,
latencias de inferencia, llamadas al LLM y excepciones.
"""

import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

from src.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """Formateador que serializa registros de log en formato JSON estructurado."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.ENVIRONMENT,
        }

        # Extraer metadatos contextuales si fueron pasados en 'extra'
        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            log_entry["metadata"] = record.metadata

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name: str = "intelligent_qa") -> logging.Logger:
    """Configura y retorna el logger centralizado con salida estructurada."""
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(settings.LOG_LEVEL.upper())

    # Evitar duplicar handlers en reinicios o tests
    if not logger_instance.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.LOG_LEVEL.upper())
        console_handler.setFormatter(StructuredJsonFormatter())
        logger_instance.addHandler(console_handler)

    logger_instance.propagate = False
    return logger_instance


class AppLogger:
    """Clase envoltorio con métodos semánticos para el pipeline de QA."""

    def __init__(self, base_logger: logging.Logger) -> None:
        self._logger = base_logger

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, extra={"metadata": kwargs} if kwargs else None)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, extra={"metadata": kwargs} if kwargs else None)

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        self._logger.error(
            message,
            exc_info=exc_info,
            extra={"metadata": kwargs} if kwargs else None,
        )

    def log_file_received(self, filename: str, file_size_bytes: int, extension: str) -> None:
        """Registra la recepción de un documento o archivo de código."""
        self.info(
            "Archivo recibido para procesamiento",
            event="FILE_RECEIVED",
            filename=filename,
            file_size_bytes=file_size_bytes,
            extension=extension,
        )

    def log_classification_verdict(
        self,
        filename: str,
        verdict: str,
        is_accepted: bool,
        rejection_reason: str | None = None,
    ) -> None:
        """Registra el resultado del guardrail de clasificación."""
        self.info(
            "Veredicto de clasificación emitido por el Guardrail",
            event="CLASSIFICATION_VERDICT",
            filename=filename,
            verdict=verdict,
            is_accepted=is_accepted,
            rejection_reason=rejection_reason,
        )

    def log_llm_call(
        self,
        task: str,
        model: str,
        prompt_name: str,
        duration_seconds: float,
    ) -> None:
        """Registra la invocación a la API de Gemini con sus métricas."""
        self.info(
            "Invocación de LLM completada",
            event="LLM_CALL",
            task=task,
            model=model,
            prompt_name=prompt_name,
            duration_seconds=round(duration_seconds, 4),
        )

    @contextmanager
    def measure_latency(self, operation_name: str) -> Generator[dict[str, float], None, None]:
        """Context manager para cronometrar latencias de cualquier operación."""
        start_time = time.perf_counter()
        metrics: dict[str, float] = {}
        try:
            yield metrics
        finally:
            elapsed = time.perf_counter() - start_time
            metrics["elapsed_seconds"] = elapsed
            self.info(
                f"Operación finalizada: {operation_name}",
                event="LATENCY_METRIC",
                operation=operation_name,
                duration_seconds=round(elapsed, 4),
            )


# Instancia lista para importar
logger = AppLogger(setup_logger())


def get_logger(module_name: str) -> AppLogger:
    """Retorna un logger contextualizado por módulo."""
    return AppLogger(setup_logger(f"intelligent_qa.{module_name}"))