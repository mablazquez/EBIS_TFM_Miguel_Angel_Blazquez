"""
Sistema de logging estructurado para Intelligent QA.
Provee trazabilidad de metadatos, veredictos de clasificación,
latencias de inferencia, llamadas al LLM y excepciones.
"""

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional

from src.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """Formateador que serializa registros de log en formato JSON estructurado."""

    def format(self, record: logging.LogRecord) -> str:
        env_value = getattr(settings, "ENVIRONMENT", getattr(settings, "environment", "development"))
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": env_value,
        }

        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            log_entry["metadata"] = record.metadata

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name: str = "intelligent_qa") -> logging.Logger:
    """Configura y retorna el logger centralizado con salida estructurada."""
    logger_instance = logging.getLogger(name)
    level_str = getattr(settings, "LOG_LEVEL", getattr(settings, "log_level", "INFO")).upper()
    logger_instance.setLevel(getattr(logging, level_str, logging.INFO))

    if not logger_instance.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level_str, logging.INFO))
        console_handler.setFormatter(StructuredJsonFormatter())
        logger_instance.addHandler(console_handler)

    logger_instance.propagate = False
    return logger_instance


# Instancia base del logger
logger = setup_logger()
get_logger = setup_logger


class StructuredLogger:
    """
    Fachada requerida por el clasificador, agentes y backend para trazar eventos.
    """

    @staticmethod
    def log_file_metadata(filename: str, size_bytes: int, extension: str) -> None:
        payload = {
            "event": "FILE_UPLOAD_RECEIVED",
            "filename": filename,
            "size_bytes": size_bytes,
            "extension": extension
        }
        logger.info(f"[METADATA] Archivo recibido: {filename}", extra={"metadata": payload})

    @staticmethod
    def log_classification(
        filename: str,
        verdict: str,
        confidence_or_reason: Optional[str] = None
    ) -> None:
        payload = {
            "event": "CLASSIFICATION_VERDICT",
            "filename": filename,
            "verdict": verdict,
            "details": confidence_or_reason or "N/A"
        }
        msg = f"[CLASSIFIER] Veredicto: {verdict} para {filename}"
        if verdict == "INVALID":
            logger.warning(msg, extra={"metadata": payload})
        else:
            logger.info(msg, extra={"metadata": payload})

    @staticmethod
    def log_llm_call(
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        payload = {
            "event": "LLM_EXECUTION",
            "agent": agent_name,
            "task": task,
            "duration_sec": round(duration_seconds, 3),
            "success": success,
            "metadata": extra or {}
        }
        msg = f"[LLM_CALL] {agent_name} ejecutó {task} ({payload['duration_sec']}s)"
        if success:
            logger.info(msg, extra={"metadata": payload})
        else:
            logger.error(msg, extra={"metadata": payload})

    @staticmethod
    def log_error(context_message: str, error: Exception) -> None:
        payload = {
            "event": "APPLICATION_ERROR",
            "context": context_message,
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        }
        logger.error(f"[ERROR] {context_message}", exc_info=True, extra={"metadata": payload})


@contextmanager
def measure_execution_time(agent_name: str, task: str) -> Generator[None, None, None]:
    """
    Context manager requerido por las tools y el clasificador para medir latencias.
    """
    start_time = time.perf_counter()
    success = False
    try:
        yield
        success = True
    except Exception as exc:
        StructuredLogger.log_error(f"Fallo en ejecución de '{task}' ({agent_name})", exc)
        raise
    finally:
        elapsed = time.perf_counter() - start_time
        StructuredLogger.log_llm_call(
            agent_name=agent_name,
            task=task,
            duration_seconds=elapsed,
            success=success
        )