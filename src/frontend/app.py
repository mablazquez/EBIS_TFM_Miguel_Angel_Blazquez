"""
Punto de Entrada del Frontend de Streamlit para Intelligent QA.
Gestiona el estado de sesión persistente, el upload de ficheros y el despacho de tareas.
"""

import streamlit as st

from src.frontend.api_client import api_client
from src.frontend.components import (
    render_header,
    render_guardrail_rejection_alert,
    render_classification_badge,
    render_task_result,
)

# 1. Configuración de la página
st.set_page_config(
    page_title="Intelligent QA (MVP)",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inicialización estricta de Session State para evitar reinicios al pulsar botones
def init_session_state() -> None:
    defaults = {
        "uploaded_filename": None,
        "file_content": None,
        "classification": None,
        "is_valid": False,
        "confidence": 0.0,
        "reason": None,
        "rejection_message": None,
        "task_result": None,
        "current_task": None,
        "execution_time": 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# 3. Comprobación de salud del Backend
backend_status = api_client.check_health()
render_header(backend_status)

# 4. Barra lateral: Subida de Fichero y Metadatos
with st.sidebar:
    st.header("📂 Carga de Documentación o Código")
    uploaded_file = st.file_uploader(
        label="Selecciona un archivo (.md, .txt, .java, .py)",
        type=["md", "txt", "java", "py"],
        help="Sube una especificación de requisitos formal o un archivo de código fuente Java/Python."
    )

    # Detección de subida o cambio de archivo
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.uploaded_filename:
            with st.spinner("Analizando y clasificando archivo con guardrail..."):
                file_bytes = uploaded_file.getvalue()
                classification_data = api_client.upload_file(
                    filename=uploaded_file.name,
                    file_bytes=file_bytes
                )

                # Persistencia en session_state
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.is_valid = classification_data.get("is_valid", False)
                st.session_state.classification = classification_data.get("classification")
                st.session_state.confidence = classification_data.get("confidence", 0.0)
                st.session_state.reason = classification_data.get("reason", "")
                st.session_state.rejection_message = classification_data.get("rejection_message")
                st.session_state.file_content = classification_data.get("content")
                # Reiniciar resultados previos
                st.session_state.task_result = None
                st.session_state.current_task = None
                st.session_state.execution_time = 0.0
                st.rerun()

    if st.session_state.uploaded_filename:
        st.markdown("---")
        st.caption(f"**Archivo actual:** `{st.session_state.uploaded_filename}`")
        if st.button("🗑️ Limpiar / Reiniciar", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# 5. Cuerpo Principal: Enrutamiento según el estado de validación

# CASO A: Aún no se ha cargado ningún archivo
if not st.session_state.uploaded_filename:
    st.info(
        "👋 **Bienvenido al entorno de pruebas de Intelligent QA.**\n\n"
        "Para comenzar, sube un archivo desde la barra lateral izquierda:\n"
        "- **Especificación de Requisitos:** `.md` o `.txt` con historias de usuario o SRS.\n"
        "- **Código Fuente Legacy:** `.java` o `.py` estructurado.\n\n"
        "*Cualquier archivo informal o mixto será bloqueado de inmediato por el guardrail de entrada.*"
    )

# CASO B: Archivo rechazado por el Guardrail (Regla 3)
elif not st.session_state.is_valid:
    rejection_msg = (
        st.session_state.rejection_message
        or "La documentación adjunta no es un requisito ni un fichero de código fuente de Java o Python."
    )
    render_guardrail_rejection_alert(
        message=rejection_msg,
        reason=st.session_state.reason
    )

# CASO C: Archivo Válido y Clasificado
else:
    # 1. Panel de clasificación
    render_classification_badge(
        classification=st.session_state.classification,
        confidence=st.session_state.confidence,
        reason=st.session_state.reason
    )

    # 2. Acordeón con vista previa del contenido analizado
    with st.expander("👁️ Ver contenido del archivo analizado", expanded=False):
        syntax = "python" if st.session_state.classification == "PYTHON_CODE" else (
            "java" if st.session_state.classification == "JAVA_CODE" else "markdown"
        )
        st.code(st.session_state.file_content or "", language=syntax)

    st.subheader("⚡ Acciones Disponibles")

    # 3. Flujo dinámico según la categoría del artefacto
    task_to_execute = None

    if st.session_state.classification == "REQUIREMENT":
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 Auditar Inconsistencias", use_container_width=True):
                task_to_execute = "check_inconsistencies"
        with col2:
            if st.button("📏 Evaluar Normativa ISO/IEEE", use_container_width=True):
                task_to_execute = "verify_standards"
        with col3:
            if st.button("🧪 Generar Casos de Prueba", use_container_width=True):
                task_to_execute = "generate_test_cases"

    elif st.session_state.classification in ["JAVA_CODE", "PYTHON_CODE"]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📐 Reconstruir Requisitos (Ing. Inversa)", use_container_width=True):
                task_to_execute = "reverse_engineer"
        with col2:
            button_label = "🧪 Generar Tests Pytest" if st.session_state.classification == "PYTHON_CODE" else "🧪 Generar Tests JUnit 5"
            if st.button(button_label, use_container_width=True):
                task_to_execute = "generate_unit_tests"

    # 4. Despacho y ejecución de la tarea seleccionada
    if task_to_execute:
        with st.spinner(f"El agente de LangGraph está procesando '{task_to_execute}' con {backend_status.get('model', 'Gemini')}..."):
            response = api_client.execute_task(
                filename=st.session_state.uploaded_filename,
                file_type=st.session_state.classification,
                task=task_to_execute,
                content=st.session_state.file_content
            )

            if response.get("success"):
                st.session_state.task_result = response.get("result")
                st.session_state.current_task = task_to_execute
                st.session_state.execution_time = response.get("execution_time_seconds", 0.0)
            else:
                st.error(f"Fallo en la ejecución: {response.get('error')}")

    # 5. Renderizado persistente del resultado si ya existe en session_state
    if st.session_state.task_result:
        render_task_result(
            task_name=st.session_state.current_task,
            result_text=st.session_state.task_result,
            execution_time=st.session_state.execution_time,
            file_type=st.session_state.classification
        )