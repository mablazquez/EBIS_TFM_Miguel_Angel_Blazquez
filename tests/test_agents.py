"""
Pruebas de Integración y de Enrutamiento para los Grafos de LangGraph.
Verifica que RequirementsAgent y CodeAgent ejecuten sus nodos correspondientes,
gestionen estados válidos y aíslen peticiones con acciones no permitidas.
"""

from unittest.mock import patch, MagicMock
import pytest

from src.core.agents.requirements_agent import (
    RequirementsAgent,
    build_requirements_graph,
    RequirementsState,
)
from src.core.agents.code_agent import (
    CodeAgent,
    build_code_graph,
    CodeState,
)


# ==============================================================================
# 1. Pruebas del Grafo del Agente de Requisitos (Flujo A)
# ==============================================================================

@pytest.fixture
def requirements_agent():
    return RequirementsAgent()


@patch("src.core.agents.requirements_agent.check_document_inconsistencies.invoke")
def test_requirements_agent_route_inconsistencies(mock_tool, requirements_agent):
    """Verifica que 'check_inconsistencies' enrute al nodo de inconsistencias y retorne éxito."""
    mock_tool.return_value = "Reporte de Inconsistencias: Sin contradicciones críticas."

    response = requirements_agent.run(
        content="# SRS: Módulo de Facturación",
        action="check_inconsistencies"
    )

    assert response["success"] is True
    assert response["action"] == "check_inconsistencies"
    assert "Sin contradicciones críticas" in response["result"]
    assert response["error"] is None
    mock_tool.assert_called_once()


@patch("src.core.agents.requirements_agent.verify_requirements_standards.invoke")
def test_requirements_agent_route_standards(mock_tool, requirements_agent):
    """Verifica que 'verify_standards' enrute al nodo de evaluación ISO/IEEE."""
    mock_tool.return_value = "Reporte Normativa ISO 29148: Madurez 92/100."

    response = requirements_agent.run(
        content="# [REQ-01] El sistema debe responder en menos de 2s.",
        action="verify_standards"
    )

    assert response["success"] is True
    assert response["action"] == "verify_standards"
    assert "Madurez 92/100" in response["result"]
    assert response["error"] is None
    mock_tool.assert_called_once()


@patch("src.core.agents.requirements_agent.generate_test_cases.invoke")
def test_requirements_agent_route_test_cases(mock_tool, requirements_agent):
    """Verifica que 'generate_test_cases' enrute al nodo de casos de prueba."""
    mock_tool.return_value = "### Caso de Prueba: TC-001 - Login Exitoso"

    response = requirements_agent.run(
        content="# [REQ-01] Autenticación de usuario",
        action="generate_test_cases"
    )

    assert response["success"] is True
    assert response["action"] == "generate_test_cases"
    assert "TC-001" in response["result"]
    assert response["error"] is None
    mock_tool.assert_called_once()


def test_requirements_agent_invalid_action_routes_to_error_node(requirements_agent):
    """Verifica que una acción desconocida derive al nodo de error sin romper el grafo."""
    response = requirements_agent.run(
        content="Contenido de prueba",
        action="unsupported_action"
    )

    assert response["success"] is False
    assert response["result"] is None
    assert "Acción no soportada para requisitos" in response["error"]


@patch("src.core.agents.requirements_agent.check_document_inconsistencies.invoke")
def test_requirements_agent_node_exception_handling(mock_tool, requirements_agent):
    """Verifica el aislamiento de fallos si la tool lanza una excepción durante la ejecución."""
    mock_tool.side_effect = RuntimeError("Error en conexión con el LLM")

    response = requirements_agent.run(
        content="Requisito de prueba",
        action="check_inconsistencies"
    )

    assert response["success"] is False
    assert response["result"] is None
    assert "Fallo al analizar inconsistencias" in response["error"]


# ==============================================================================
# 2. Pruebas del Grafo del Agente de Código Legacy (Flujo B)
# ==============================================================================

@pytest.fixture
def code_agent():
    return CodeAgent()


@patch("src.core.agents.code_agent.reverse_engineer_requirements.invoke")
def test_code_agent_route_reverse_engineering(mock_tool, code_agent):
    """Verifica el enrutamiento a ingeniería inversa normalizando el lenguaje a Java."""
    mock_tool.return_value = "## 1. Ficha Técnica\n- Lenguaje: Java\n- Regla: RN-001"

    response = code_agent.run(
        content="public class OrderService {}",
        language="JAVA_CODE",
        action="reverse_engineer"
    )

    assert response["success"] is True
    assert response["language"] == "Java"
    assert "RN-001" in response["result"]
    assert response["error"] is None
    mock_tool.assert_called_once_with({"content": "public class OrderService {}", "language": "Java"})


@patch("src.core.agents.code_agent.generate_unit_tests.invoke")
def test_code_agent_route_unit_tests_python(mock_tool, code_agent):
    """Verifica la generación de tests unitarios normalizando el lenguaje a Python."""
    mock_tool.return_value = "```python\ndef test_calc(): assert True\n```"

    response = code_agent.run(
        content="def calc(a, b): return a + b",
        language="PYTHON_CODE",
        action="generate_unit_tests"
    )

    assert response["success"] is True
    assert response["language"] == "Python"
    assert "test_calc" in response["result"]
    assert response["error"] is None
    mock_tool.assert_called_once_with({"content": "def calc(a, b): return a + b", "language": "Python"})


def test_code_agent_invalid_action_routes_to_error_node(code_agent):
    """Verifica que una acción inválida en el agente de código derive al nodo de error."""
    response = code_agent.run(
        content="def sample(): pass",
        language="Python",
        action="invalid_code_task"
    )

    assert response["success"] is False
    assert response["result"] is None
    assert "Acción no soportada para código" in response["error"]


@patch("src.core.agents.code_agent.generate_unit_tests.invoke")
def test_code_agent_node_exception_handling(mock_tool, code_agent):
    """Verifica el aislamiento de fallos en el nodo de tests unitarios si ocurre una excepción."""
    mock_tool.side_effect = TimeoutError("Tiempo de espera agotado en la API")

    response = code_agent.run(
        content="def test(): pass",
        language="Python",
        action="generate_unit_tests"
    )

    assert response["success"] is False
    assert response["result"] is None
    assert "Fallo en generación de tests unitarios" in response["error"]