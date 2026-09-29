"""
Pruebas Unitarias para el Clasificador y Guardrail Estricto de Entrada.
Verifica la aceptación de especificaciones funcionales y código (Java/Python),
así como el rechazo mandatario ante archivos inválidos o sintácticamente corruptos.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.core.agents.classifier import (
    FileClassifier,
    ClassificationResult,
    LLMClassificationOutput,
    MANDATORY_REJECTION_MESSAGE
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def mock_llm():
    """Fixture que proporciona una instancia mockeada de ChatGoogleGenerativeAI."""
    mock = MagicMock()
    return mock


@pytest.fixture
def classifier(mock_llm):
    """Instancia de FileClassifier inyectando el LLM mockeado."""
    return FileClassifier(llm=mock_llm)


# ==============================================================================
# 1. Pruebas de Pre-validación Sintáctica y Determinista (Sin coste LLM)
# ==============================================================================

def test_empty_content_rejected_immediately(classifier, mock_llm):
    """Verifica que un archivo vacío o con solo espacios sea rechazado sin invocar al LLM."""
    result = classifier.classify(filename="empty.py", content="   \n\t  ")

    assert result.is_valid is False
    assert result.classification == "INVALID"
    assert result.rejection_message == MANDATORY_REJECTION_MESSAGE
    mock_llm.invoke.assert_not_called()


def test_python_syntax_error_rejected(classifier, mock_llm):
    """Verifica que un archivo .py con errores de sintaxis irrecuperables sea rechazado."""
    broken_python_code = "def invalid_func(x:\n    return x + "
    result = classifier.classify(filename="broken.py", content=broken_python_code)

    assert result.is_valid is False
    assert result.classification == "INVALID"
    assert result.rejection_message == MANDATORY_REJECTION_MESSAGE
    assert "Error sintáctico Python" in result.reason
    mock_llm.invoke.assert_not_called()


def test_java_without_class_or_interface_rejected(classifier, mock_llm):
    """Verifica que un archivo .java sin definición de clase/interfaz sea rechazado."""
    snippet = "public void doSomething() { System.out.println('Hello'); }"
    result = classifier.classify(filename="Malformed.java", content=snippet)

    assert result.is_valid is False
    assert result.classification == "INVALID"
    assert result.rejection_message == MANDATORY_REJECTION_MESSAGE
    mock_llm.invoke.assert_not_called()


# ==============================================================================
# 2. Pruebas de Clasificación Semántica Válida (Mock LLM)
# ==============================================================================

def test_classify_valid_python_code(classifier, mock_llm):
    """Verifica la correcta clasificación de un script Python válido."""
    python_code = """
def calculate_vat(subtotal: float, rate: float = 0.21) -> float:
    return round(subtotal * rate, 2)
"""
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = LLMClassificationOutput(
        classification="PYTHON_CODE",
        confidence=0.98,
        reason="Módulo Python con sintaxis válida y tipado de funciones."
    )
    mock_llm.with_structured_output.return_value = mock_structured

    result = classifier.classify(filename="tax_calculator.py", content=python_code)

    assert result.is_valid is True
    assert result.classification == "PYTHON_CODE"
    assert result.confidence >= 0.9
    assert result.rejection_message is None


def test_classify_valid_java_code(classifier, mock_llm):
    """Verifica la correcta clasificación de una clase Java válida."""
    java_code = """
package com.demo;
public class UserRegistry {
    private final String id;
    public UserRegistry(String id) { this.id = id; }
    public String getId() { return this.id; }
}
"""
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = LLMClassificationOutput(
        classification="JAVA_CODE",
        confidence=0.99,
        reason="Definición formal de clase POJO en Java."
    )
    mock_llm.with_structured_output.return_value = mock_structured

    result = classifier.classify(filename="UserRegistry.java", content=java_code)

    assert result.is_valid is True
    assert result.classification == "JAVA_CODE"
    assert result.confidence >= 0.9
    assert result.rejection_message is None


def test_classify_valid_requirement_specification(classifier, mock_llm):
    """Verifica la clasificación satisfactoria de un documento de requisitos funcionales."""
    req_doc = """
# SRS: Sistema de Autenticación
### [REQ-AUTH-01] Bloqueo de Cuenta
El sistema debe bloquear la cuenta del usuario si se introducen 3 contraseñas incorrectas consecutivas.
"""
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = LLMClassificationOutput(
        classification="REQUIREMENT",
        confidence=0.95,
        reason="Especificación funcional con identificadores de requisitos y criterios comprobables."
    )
    mock_llm.with_structured_output.return_value = mock_structured

    result = classifier.classify(filename="auth_spec.md", content=req_doc)

    assert result.is_valid is True
    assert result.classification == "REQUIREMENT"
    assert result.rejection_message is None


# ==============================================================================
# 3. Pruebas del Guardrail Estricto ante Contenido No Válido
# ==============================================================================

@pytest.mark.parametrize("filename,content,reason", [
    (
        "notes.txt",
        "Recordar llamar a Juan el martes a las 10:00 y revisar el presupuesto.",
        "Texto plano informal sin estructura de requisitos de software."
    ),
    (
        "main.cpp",
        "#include <iostream>\nint main() { std::cout << 'C++'; return 0; }",
        "Código en lenguaje C++, no soportado por el sistema."
    ),
    (
        "mixed_document.txt",
        "El sistema debe ser rápido. Aquí un trozo de código: let x = 10; function run(){}",
        "Documento mixto informal con fragmentos de JavaScript."
    )
])
def test_guardrail_rejection_for_invalid_content(classifier, mock_llm, filename, content, reason):
    """Verifica que cualquier contenido no admitido active el rechazo mandatario exacto."""
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = LLMClassificationOutput(
        classification="INVALID",
        confidence=0.99,
        reason=reason
    )
    mock_llm.with_structured_output.return_value = mock_structured

    result = classifier.classify(filename=filename, content=content)

    assert result.is_valid is False
    assert result.classification == "INVALID"
    assert result.rejection_message == MANDATORY_REJECTION_MESSAGE


def test_fail_closed_on_llm_exception(classifier, mock_llm):
    """Verifica que ante un fallo de conectividad o excepción del LLM se rechace de forma segura (Fail-Closed)."""
    mock_llm.with_structured_output.side_effect = RuntimeError("Conexión con Gemini interrumpida")

    result = classifier.classify(
        filename="requirement.md",
        content="# [REQ-01] Validar token de sesión en cada petición."
    )

    assert result.is_valid is False
    assert result.classification == "INVALID"
    assert result.rejection_message == MANDATORY_REJECTION_MESSAGE
    assert "Excepción en proceso de clasificación" in result.reason


# ==============================================================================
# 4. Prueba de Integración con Datos de Prueba Reales (data/sample_*)
# ==============================================================================

def test_samples_pass_pre_validation():
    """Comprueba que los datos de prueba creados en la Etapa 2 superen la validación estática preliminar."""
    classifier_instance = FileClassifier(llm=MagicMock())

    sample_py = PROJECT_ROOT / "data" / "sample_code" / "sample_discount_calculator.py"
    sample_java = PROJECT_ROOT / "data" / "sample_code" / "sample_order_service.java"

    if sample_py.exists():
        pre_py = classifier_instance._pre_validate_syntax(sample_py.read_text("utf-8"), ".py")
        assert pre_py is None, "El archivo Python de muestra no debería fallar en validación estática"

    if sample_java.exists():
        pre_java = classifier_instance._pre_validate_syntax(sample_java.read_text("utf-8"), ".java")
        assert pre_java is None, "El archivo Java de muestra no debería fallar en validación estática"