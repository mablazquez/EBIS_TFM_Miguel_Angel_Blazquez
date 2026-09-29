"""
Módulo del Agente de Código Legacy con LangGraph.
Orquesta el análisis de código mediante ingeniería inversa o generación de pruebas unitarias.
"""

from typing import Any, Dict, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from src.core.agents.tools.code_tools import (
    reverse_engineer_requirements,
    generate_unit_tests,
    normalize_language_name,
)
from src.core.logger import StructuredLogger

CodeAction = Literal["reverse_engineer", "generate_unit_tests"]


class CodeState(TypedDict):
    """Estado compartido a lo largo del grafo del agente de código."""
    content: str
    language: str
    action: str
    result: Optional[str]
    error: Optional[str]


def reverse_engineering_node(state: CodeState) -> Dict[str, Any]:
    """Nodo ejecutor de ingeniería inversa sobre el código."""
    try:
        report = reverse_engineer_requirements.invoke({
            "content": state["content"],
            "language": state["language"]
        })
        return {"result": report, "error": None}
    except Exception as exc:
        StructuredLogger.log_error("Error en nodo reverse_engineering_node", exc)
        return {"result": None, "error": f"Fallo en ingeniería inversa: {str(exc)}"}


def unit_tests_node(state: CodeState) -> Dict[str, Any]:
    """Nodo ejecutor para la generación de pruebas unitarias."""
    try:
        report = generate_unit_tests.invoke({
            "content": state["content"],
            "language": state["language"]
        })
        return {"result": report, "error": None}
    except Exception as exc:
        StructuredLogger.log_error("Error en nodo unit_tests_node", exc)
        return {"result": None, "error": f"Fallo en generación de tests unitarios: {str(exc)}"}


def error_node(state: CodeState) -> Dict[str, Any]:
    """Nodo sumidero cuando la acción no es reconocida por el agente."""
    action = state.get("action")
    error_msg = (
        f"Acción no soportada para código: '{action}'. "
        "Las acciones válidas son: 'reverse_engineer' o 'generate_unit_tests'."
    )
    StructuredLogger.log_error("CodeAgent acción inválida", ValueError(error_msg))
    return {"result": None, "error": error_msg}


def route_code_action(state: CodeState) -> str:
    """Enrutador condicional que inspecciona la acción solicitada en el estado."""
    action = state.get("action", "")
    if action == "reverse_engineer":
        return "reverse_engineering_node"
    elif action == "generate_unit_tests":
        return "unit_tests_node"
    else:
        return "error_node"


def build_code_graph() -> Any:
    """
    Construye y compila el StateGraph de LangGraph para el Agente de Código.
    """
    graph = StateGraph(CodeState)

    # Nodos de procesamiento
    graph.add_node("reverse_engineering_node", reverse_engineering_node)
    graph.add_node("unit_tests_node", unit_tests_node)
    graph.add_node("error_node", error_node)

    # Enrutamiento condicional desde el inicio
    graph.add_conditional_edges(
        START,
        route_code_action,
        {
            "reverse_engineering_node": "reverse_engineering_node",
            "unit_tests_node": "unit_tests_node",
            "error_node": "error_node",
        }
    )

    # Cierre de conexiones
    graph.add_edge("reverse_engineering_node", END)
    graph.add_edge("unit_tests_node", END)
    graph.add_edge("error_node", END)

    return graph.compile()


class CodeAgent:
    """
    Fachada orientada a servicios para invocar el grafo de código legacy.
    """

    def __init__(self) -> None:
        self.app = build_code_graph()

    def run(self, content: str, language: str, action: str) -> Dict[str, Any]:
        """
        Ejecuta la acción requerida sobre el artefacto de código fuente.

        Args:
            content: Código fuente verificado (Java o Python).
            language: 'JAVA_CODE', 'PYTHON_CODE', 'Java' o 'Python'.
            action: Acción solicitada ('reverse_engineer', 'generate_unit_tests').

        Returns:
            Diccionario con las claves 'result', 'error', 'language' y 'success'.
        """
        normalized_language = normalize_language_name(language)

        initial_state: CodeState = {
            "content": content,
            "language": normalized_language,
            "action": action,
            "result": None,
            "error": None
        }

        final_state = self.app.invoke(initial_state)

        return {
            "action": action,
            "language": normalized_language,
            "success": final_state.get("error") is None,
            "result": final_state.get("result"),
            "error": final_state.get("error")
        }