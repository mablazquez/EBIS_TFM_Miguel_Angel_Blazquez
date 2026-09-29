"""Módulo de herramientas (tools) para los agentes de Intelligent QA."""

from src.core.agents.tools.requirements_tools import (
    check_document_inconsistencies,
    verify_requirements_standards,
    generate_test_cases,
)
from src.core.agents.tools.code_tools import (
    reverse_engineer_requirements,
    generate_unit_tests,
    normalize_language_name,
)

__all__ = [
    "check_document_inconsistencies",
    "verify_requirements_standards",
    "generate_test_cases",
    "reverse_engineer_requirements",
    "generate_unit_tests",
    "normalize_language_name",
]