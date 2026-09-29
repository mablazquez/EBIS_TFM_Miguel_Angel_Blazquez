"""
Módulo del Agente de Requisitos con LangGraph.
Orquesta la ejecución condicional de las herramientas de auditoría y generación
según la acción solicitada por el usuario o el backend.
"""

from typing import Any, Dict, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from src.core.agents.tools.requirements_tools import (
    check_document_inconsistencies,
    verify_requirements_standards,
    generate_test_cases,
)
from src.core.logger import StructuredLogger

RequirementsAction = Literal[
    "check_inconsistencies",
    "verify_standards",
    "generate_test_cases"
]


class RequirementsState(TypedDict):
    """Estado compartido a lo largo del grafo de requisitos."""
    content: str
    action: str
    result: Optional[str]
    error: Optional[str]


def inconsistencies_node(state: RequirementsState) -> Dict[str, Any]:
    """Nodo ejecutor para la detección de inconsistencias."""
    try:
        report = check_document_inconsistencies.invoke({"content": state["content"]})
        return {"result": report, "error": None}
    except Exception as exc:
        StructuredLogger.log_error("Error en nodo inconsistencies_node", exc)
        return {"result": None, "error": f"Fallo al analizar inconsistencias: {str(exc)}"}


def standards_node(state: RequirementsState) -> Dict[str, Any]:
    """Nodo ejecutor para la verificación de normativa ISO/IEEE."""
    try:
        report = verify_requirements_standards.invoke({"content": state["content"]})
        return {"result": report, "error": None}
    except Exception as exc:
        StructuredLogger.log_error("Error en nodo standards_node", exc)
        return {"result": None, "error": f"Fallo al evaluar normativa: {str(exc)}"}


def test_cases_node(state: RequirementsState) -> Dict[str, Any]:
    """Nodo ejecutor para la generación de casos de prueba."""
    try:
        report = generate_test_cases.invoke({"content": state["content"]})
        return {"result": report, "error": None}
    except Exception as exc:
        StructuredLogger.log_error("Error en nodo test_cases_node", exc)
        return {"result": None, "error": f"Fallo al generar casos de prueba: {str(exc)}"}


def route_action(state: RequirementsState) -> str:
    """Enrutador condicional que determina el nodo de destino según la acción solicitada."""
    action = state.get("action", "")
    if action == "check_inconsistencies":
        return "inconsistencies_node"
    elif action == "verify_standards":
        return "standards_node"
    elif action == "generate_test_cases":
        return "test_cases_node"
    else:
        return "error_node"


def error_node(state: RequirementsState) -> Dict[str, Any]:
    """Nodo sumidero cuando la acción solicitada no es reconocida."""
    action = state.get("action")
    error_msg = (
        f"Acción no soportada para requisitos: '{action}'. "
        "Las acciones válidas son: 'check_inconsistencies', 'verify_standards', 'generate_test_cases'."
    )
    StructuredLogger.log_error("RequirementsAgent acción inválida", ValueError(error_msg))
    return {"result": None, "error": error_msg}


def build_requirements_graph() -> Any:
    """
    Construye y compila el StateGraph de LangGraph para el Agente de Requisitos.
    """
    graph = StateGraph(RequirementsState)

    # Registro de nodos
    graph.add_node("inconsistencies_node", inconsistencies_node)
    graph.add_node("standards_node", standards_node)
    graph.add_node("test_cases_node", test_cases_node)
    graph.add_node("error_node", error_node)

    # Enrutamiento condicional desde el inicio
    graph.add_conditional_edges(
        START,
        route_action,
        {
            "inconsistencies_node": "inconsistencies_node",
            "standards_node": "standards_node",
            "test_cases_node": "test_cases_node",
            "error_node": "error_node",
        }
    )

    # Conexión de nodos al final
    graph.add_edge("inconsistencies_node", END)
    graph.add_edge("standards_node", END)
    graph.add_edge("test_cases_node", END)
    graph.add_edge("error_node", END)

    return graph.compile()


class RequirementsAgent:
    """
    Fachada orientada a servicios para invocar el grafo de requisitos.
    """

    def __init__(self) -> None:
        self.app = build_requirements_graph()

    def run(self, content: str, action: str) -> Dict[str, Any]:
        """
        Ejecuta una acción sobre un documento de requisitos a través del grafo.

        Args:
            content: Contenido del documento de requisitos validado.
            action: Acción a ejecutar ('check_inconsistencies', 'verify_standards', 'generate_test_cases').

        Returns:
            Diccionario con las claves 'result', 'error' y metadatos de ejecución.
        """
        initial_state: RequirementsState = {
            "content": content,
            "action": action,
            "result": None,
            "error": None
        }

        final_state = self.app.invoke(initial_state)

        return {
            "action": action,
            "success": final_state.get("error") is None,
            "result": final_state.get("result"),
            "error": final_state.get("error")
        }