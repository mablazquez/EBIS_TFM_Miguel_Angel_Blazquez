"""
Componentes Visuales Reutilizables para Streamlit.
Define el layout, alertas estandarizadas de guardrail y visores de auditoría/código.
"""

from typing import Any, Dict, Optional
import streamlit as st


def render_header(backend_status: Dict[str, Any]) -> None:
    """Muestra el encabezado principal con badge de estado y modelo activo."""
    st.markdown(
        """
        <div style="padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 1.5rem;">
            <h1 style="margin: 0; color: #1e3a8a;">🧪 Intelligent QA (MVP)</h1>
            <p style="margin: 0.25rem 0 0 0; color: #475569; font-size: 1.05rem;">
                Sistema Agentic con LangGraph & Gemini para Auditoría de Requisitos y Análisis de Código Legacy
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    is_online = backend_status.get("status") == "ok"
    status_color = "#16a34a" if is_online else "#dc2626"
    status_text = "Backend Online" if is_online else "Backend Offline"
    model_name = backend_status.get("model", "N/A")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"**Trabajo de Fin de Máster (TFM)** | Modelo: `{model_name}`")
    with col2:
        st.markdown(
            f"""
            <div style="text-align: right;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: {status_color}; border-radius: 50%; margin-right: 5px;"></span>
                <span style="font-weight: 600; color: {status_color}; font-size: 0.9rem;">{status_text}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_guardrail_rejection_alert(message: str, reason: Optional[str] = None) -> None:
    """
    Renderiza la alerta roja estricta ante el bloqueo por guardrail (Regla 3).
    Muestra obligatoriamente la cadena exacta exigida.
    """
    st.markdown(
        f"""
        <div style="background-color: #fef2f2; border-left: 6px solid #dc2626; padding: 1.2rem; border-radius: 4px; margin: 1rem 0;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 0.75rem;">⛔</span>
                <h4 style="margin: 0; color: #991b1b; font-weight: 700;">ACCESO BLOQUEADO POR GUARDRAIL</h4>
            </div>
            <p style="margin: 0.75rem 0 0 0; font-size: 1.05rem; font-weight: 600; color: #b91c1c;">
                {message}
            </p>
            {f'<p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #6b7280;"><em>Detalle técnico: {reason}</em></p>' if reason else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_classification_badge(classification: str, confidence: float, reason: str) -> None:
    """Muestra un panel informativo del artefacto validado."""
    badge_colors = {
        "REQUIREMENT": "#0284c7",
        "JAVA_CODE": "#d97706",
        "PYTHON_CODE": "#059669"
    }
    labels = {
        "REQUIREMENT": "Especificación de Requisitos",
        "JAVA_CODE": "Código Fuente Java (.java)",
        "PYTHON_CODE": "Código Fuente Python (.py)"
    }

    color = badge_colors.get(classification, "#64748b")
    label = labels.get(classification, classification)

    st.markdown(
        f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 700;">Artefacto Verificado</span>
                <span style="background-color: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600;">
                    {label} ({int(confidence * 100)}% certeza)
                </span>
            </div>
            <p style="margin: 0; color: #334155; font-size: 0.95rem;">
                <strong>Diagnóstico:</strong> {reason}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_task_result(
    task_name: str,
    result_text: str,
    execution_time: float,
    file_type: str
) -> None:
    """Presenta el resultado de la tarea con visor adecuado y botón de descarga."""
    st.markdown("---")
    st.markdown(f"### 📋 Resultado de la Tarea: `{task_name}`")
    st.caption(f"⏱️ Tiempo de respuesta del agente: **{execution_time:.2f} s**")

    # Si el resultado es código puro o contiene bloques de código, se muestra en markdown enriquecido
    st.markdown(result_text)

    # Preparación de descarga
    ext = ".py" if "PYTHON" in file_type else (".java" if "JAVA" in file_type else ".md")
    download_filename = f"resultado_{task_name}{ext}"
    
    st.download_button(
        label="📥 Descargar Resultado",
        data=result_text,
        file_name=download_filename,
        mime="text/plain",
        use_container_width=True
    )