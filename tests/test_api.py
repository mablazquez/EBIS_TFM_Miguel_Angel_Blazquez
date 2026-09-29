"""
Pruebas de Integración para los Endpoints de la API Backend.
Verifica /health, /upload (incluyendo el guardrail estricto) y /execute-task.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from src.backend.main import app
from src.core.agents.classifier import ClassificationResult, MANDATORY_REJECTION_MESSAGE

client = TestClient(app)


# ==============================================================================
# 1. Pruebas de Healthcheck
# ==============================================================================

def test_health_check_endpoint():
    """Verifica que el endpoint /health devuelva estado ok y el modelo correcto."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "gemini-3.8-flash"
    assert "version" in data


# ==============================================================================
# 2. Pruebas del Endpoint /upload (Clasificación y Guardrail)
# ==============================================================================

@patch("src.backend.routes.classifier.classify")
def test_upload_valid_python_file(mock_classify):
    """Verifica la subida exitosa de un archivo Python válido."""
    mock_classify.return_value = ClassificationResult(
        filename="service.py",
        classification="PYTHON_CODE",
        is_valid=True,
        confidence=0.99,
        reason="Código Python válido con funciones definidas."
    )

    file_content = b"def sum_two(a: int, b: int) -> int:\n    return a + b\n"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("service.py", file_content, "text/x-python")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "service.py"
    assert data["is_valid"] is True
    assert data["classification"] == "PYTHON_CODE"
    assert data["rejection_message"] is None
    assert data["content"] is not None


@patch("src.backend.routes.classifier.classify")
def test_upload_invalid_file_triggers_strict_guardrail_message(mock_classify):
    """Verifica que un archivo inválido devuelva el mensaje exacto mandatario."""
    mock_classify.return_value = ClassificationResult(
        filename="shopping_list.txt",
        classification="INVALID",
        is_valid=False,
        confidence=1.0,
        reason="Texto no técnico sin estructura de requisitos ni código.",
        rejection_message=MANDATORY_REJECTION_MESSAGE
    )

    file_content = b"Comprar leche, huevos y pan para la semana."
    response = client.post(
        "/api/v1/upload",
        files={"file": ("shopping_list.txt", file_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["classification"] == "INVALID"
    # Verificación del mensaje no negociable
    assert data["rejection_message"] == MANDATORY_REJECTION_MESSAGE
    assert data["content"] is None


# ==============================================================================
# 3. Pruebas del Endpoint /execute-task
# ==============================================================================

@patch("src.backend.routes.requirements_agent.run")
def test_execute_requirements_task_success(mock_agent_run):
    """Verifica la ejecución satisfactoria de una tarea sobre requisitos."""
    mock_agent_run.return_value = {
        "success": True,
        "result": "## 1. Resumen de Inconsistencias\n- No se encontraron inconsistencias críticas.",
        "error": None
    }

    payload = {
        "filename": "requirements.md",
        "file_type": "REQUIREMENT",
        "task": "check_inconsistencies",
        "content": "# [REQ-01] El sistema debe permitir inicio de sesión seguro."
    }

    response = client.post("/api/v1/execute-task", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task"] == "check_inconsistencies"
    assert "Resumen de Inconsistencias" in data["result"]
    assert data["execution_time_seconds"] >= 0.0


@patch("src.backend.routes.code_agent.run")
def test_execute_code_task_success(mock_agent_run):
    """Verifica la generación de tests unitarios sobre código fuente."""
    mock_agent_run.return_value = {
        "success": True,
        "result": "```python\ndef test_dummy():\n    assert True\n```",
        "error": None
    }

    payload = {
        "filename": "calculator.py",
        "file_type": "PYTHON_CODE",
        "task": "generate_unit_tests",
        "content": "def add(x, y): return x + y"
    }

    response = client.post("/api/v1/execute-task", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task"] == "generate_unit_tests"
    assert "test_dummy" in data["result"]


def test_execute_task_incompatible_type_and_action():
    """Verifica que solicitar una tarea de código sobre un requisito sea rechazado con 400 Bad Request."""
    payload = {
        "filename": "requirements.md",
        "file_type": "REQUIREMENT",
        "task": "generate_unit_tests",  # Incompatible con REQUIREMENT
        "content": "# [REQ-01] Validar login."
    }

    response = client.post("/api/v1/execute-task", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "no permitida para artefactos de tipo 'REQUIREMENT'" in data["detail"]