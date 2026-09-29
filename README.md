# 🧪 Intelligent QA (MVP)
### Sistema Agentic con LangGraph & Gemini para Auditoría de Requisitos y Análisis de Código Legacy
**Trabajo de Fin de Máster (TFM)**

---

## 📌 1. Descripción del Proyecto

**Intelligent QA** es un sistema modular de Aseguramiento de Calidad de Software impulsado por Inteligencia Artificial generativa. Su arquitectura desacoplada resuelve dos desafíos críticos en el ciclo de vida del software:

1. **Flujo A (Auditoría de Requisitos):** Detecta inconsistencias lógicas, evalúa la conformidad con estándares internacionales (**ISO/IEC/IEEE 29148** e **IEEE 830**) y genera suites de casos de prueba funcionales (Happy Path, Negativos y Casos de Borde).
2. **Flujo B (Modernización de Código Legacy):** Reconstruye especificaciones funcionales formales mediante ingeniería inversa sobre código fuente no documentado (**Java** y **Python**) y sintetiza suites completas de pruebas unitarias (**JUnit 5** y **Pytest**).

El núcleo del sistema opera bajo un **Guardrail Estricto de Entrada** que rechaza de forma inmediata archivos no válidos, documentos mixtos o lenguajes no soportados, garantizando la integridad de los agentes de orquestación.

---

## 🏛️ 2. Arquitectura de la Solución

El sistema sigue una arquitectura por capas desacopladas mediante APIs REST y grafos de estado dirigidos:

[ Usuario / Tribunal ]
│
▼
┌─────────────────────────┐
│   Streamlit Frontend    │  (Puerto 8501: UI Reactiva con st.session_state)
└────────────┬────────────┘
│ HTTP (httpx)
▼
┌─────────────────────────┐
│     FastAPI Backend     │  (Puerto 8000: CORS, Middlewares, Lifespan Check)
└────────────┬────────────┘
│
├───► [ Guardrail / FileClassifier ] ──► (gemini-3.8-flash)
│        │
│        ├─ Rechazo: "La documentación adjunta no es un requisito..."
│        └─ Aprobado: (REQUIREMENT | JAVA_CODE | PYTHON_CODE)
│
├───► [ RequirementsAgent ] (LangGraph StateGraph)
│        ├── check_document_inconsistencies
│        ├── verify_requirements_standards (ISO/IEEE)
│        └── generate_test_cases
│
└───► [ CodeAgent ] (LangGraph StateGraph)
├── reverse_engineer_requirements
└── generate_unit_tests (JUnit 5 / Pytest)

### Principios de Diseño Implementados:
- **Externalización Absoluta de Prompts:** Ningún archivo Python contiene plantillas hardcodeadas. Todos los prompts residen en `data/prompts/` y son validados en el arranque por `src/core/config.py`.
- **Modelo LLM Obligatorio:** Todas las inferencias semánticas utilizan `gemini-3.8-flash` a través del SDK oficial de Google GenAI / LangChain.
- **Fail-Closed & Safe Rejection:** Cualquier fallo de decodificación o análisis de guardrail bloquea el acceso con el mensaje normativo del proyecto.

---

## 📂 3. Estructura del Repositorio

```text
intelligent-qa/
├── .env.example                     # Plantilla de variables de entorno
├── .gitignore                       # Filtros de exclusión de Git
├── README.md                        # Documentación técnica para evaluación
├── requirements.txt                 # Dependencias fijadas del proyecto
├── leeme.txt                        # Pasos para ejecutar la aplicación
├── src/
│   ├── frontend/                    # Capa de presentación (Streamlit)
│   │   ├── __init__.py
│   │   ├── app.py                   # UI y orquestación con session_state
│   │   ├── components.py            # Componentes visuales y alertas
│   │   └── api_client.py            # Cliente HTTP contra FastAPI
│   ├── backend/                     # Capa de servicios REST (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py                  # Servidor, ciclo de vida y middlewares
│   │   ├── routes.py                # Endpoints /upload y /execute-task
│   │   └── schemas.py               # Modelos de datos Pydantic V2
│   └── core/                        # Núcleo de Inteligencia Artificial
│       ├── __init__.py
│       ├── config.py                # Settings Pydantic y Loader de prompts
│       ├── logger.py                # Logging estructurado y telemetría
│       └── agents/                  # Clasificador y agentes LangGraph
│           ├── __init__.py
│           ├── classifier.py        # Guardrail y clasificación de entrada
│           ├── requirements_agent.py# Grafo de requisitos
│           ├── code_agent.py        # Grafo de código legacy
│           └── tools/
│               ├── __init__.py
│               ├── requirements_tools.py
│               └── code_tools.py
├── data/
│   ├── prompts/                     # Plantillas externas obligatorias
│   │   ├── classifier_guardrail.txt
│   │   ├── inconsistencies.txt
│   │   ├── standards.txt
│   │   ├── test_cases.txt
│   │   ├── reverse_engineering.txt
│   │   └── unit_tests.txt
│   ├── sample_requirements/         # Casos de prueba para el tribunal
│   │   ├── valid_requirement.md
│   │   └── ambiguous_requirement.md
│   └── sample_code/                 # Código fuente para el tribunal
│       ├── sample_order_service.java
│       └── sample_discount_calculator.py
├── scripts/
│   ├── run_backend.sh               # Lanzador del Backend
│   └── run_frontend.sh              # Lanzador del Frontend
└── tests/
    ├── test_classifier.py           # Tests del Guardrail y Clasificador
    ├── test_agents.py               # Tests de los Grafos de LangGraph
    └── test_api.py                  # Tests de integración de la API